"""Visual references: ordering, privacy, persistence and prompt semantics."""
import json
import zipfile

import pytest
from PIL import Image

from modules.visual_brief import (
    MODES,
    Reference,
    analysis_input,
    generation_request,
    load_image,
    load_project,
    save_project,
    validate,
)


def references(count=2):
    return [Reference(Image.new("RGB", (100, 60), color), role, f"ref-{i}")
            for i, (color, role) in enumerate(
                [("red", "Personaje"), ("blue", "Escenario"), ("green", "Estilo"), ("white", "Producto")][:count])]


@pytest.mark.parametrize("mode,count", [(MODES[0], 0), (MODES[0], 2), (MODES[1], 2),
                                      (MODES[2], 1), (MODES[2], 3), (MODES[3], 1)])
def test_invalid_reference_counts(mode, count):
    with pytest.raises(ValueError):
        validate(mode, references(count))


def test_start_end_joint_analysis_and_swap():
    refs = references()
    board, prompt = analysis_input(MODES[2], refs)
    assert "A: INICIO" in prompt and "B: FINAL" in prompt
    assert "Compara A y B" in prompt
    assert board.getpixel((400, 435)) == (255, 0, 0)
    assert board.getpixel((1200, 435)) == (0, 0, 255)
    swapped, _ = analysis_input(MODES[2], list(reversed(refs)))
    assert swapped.getpixel((400, 435)) == (0, 0, 255)
    assert refs[0].image.size == (100, 60)


def test_reference_roles_preserved():
    _, prompt = analysis_input(MODES[3], references(4))
    assert "A: Personaje" in prompt and "B: Escenario" in prompt
    assert "C: Estilo" in prompt and "D: Producto" in prompt


def request(mode=MODES[2], analysis="A sentado, B de pie", idea="Se levanta"):
    return generation_request(mode, references(), analysis, idea, "ropa", "pose", "5",
                              "9:16", "Inglés", "Modelo sin capacidades confirmadas")


def test_user_constraints_and_no_invented_capability():
    text = request()
    for expected in ("Se levanta", "CONSERVAR: ropa", "CAMBIAR: pose", "5 segundos", "9:16",
                     "no la confirma", "no uses morphing", "ANÁLISIS REVISADO"):
        assert expected in text


def test_empty_analysis_or_video_idea_rejected():
    with pytest.raises(ValueError):
        request(analysis="")
    with pytest.raises(ValueError):
        request(idea="")


def test_transparency_and_exif_normalization(tmp_path):
    path = tmp_path / "transparent.png"
    Image.new("RGBA", (20, 10), (255, 0, 0, 0)).save(path)
    assert load_image(path).getpixel((0, 0)) == (255, 255, 255)
    exif = Image.Exif()
    exif[274] = 6
    Image.new("RGB", (20, 10)).save(path, exif=exif)
    assert load_image(path).size == (10, 20)


def test_large_image_rejected_before_decode(tmp_path):
    path = tmp_path / "large.png"
    with path.open("wb") as stream:
        stream.truncate(26 * 1024 * 1024)
    with pytest.raises(ValueError, match="25 MB"):
        load_image(path)


def fields():
    return dict(mode=MODES[2], idea="Abrir puerta", preserve="Rostro", change="Pose",
                analysis="Dos referencias", output="PROMPT: ...", aspect="9:16", duration="5",
                language="Inglés", api_key="must-not-be-saved")


def test_project_portable_roundtrip_does_not_store_secrets(tmp_path):
    path = tmp_path / "scene.gprompt"
    save_project(path, references(), fields())
    refs, restored = load_project(path)
    assert refs[1].image.getpixel((0, 0)) == (0, 0, 255)
    assert refs[1].role == "Escenario"
    assert restored["idea"] == "Abrir puerta"
    assert "api_key" not in restored
    with zipfile.ZipFile(path) as archive:
        assert "must-not-be-saved" not in archive.read("project.json").decode()


def test_unsupported_project_keeps_existing_file(tmp_path):
    path = tmp_path / "bad.gprompt"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("project.json", json.dumps({"version": 55}))
    with pytest.raises(ValueError, match="compatible"):
        load_project(path)


def test_archive_path_traversal_rejected(tmp_path):
    path = tmp_path / "bad.gprompt"
    data = {"version": 1, "fields": fields(), "references": [
        {"file": "../outside.png", "role": "Estilo", "name": "attack"}]}
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("project.json", json.dumps(data))
    with pytest.raises(ValueError, match="Referencia"):
        load_project(path)
    assert not (tmp_path / "outside.png").exists()


def test_close_during_request_never_updates_destroyed_widgets():
    from types import SimpleNamespace

    from modules.visual_studio import VisualStudio
    callbacks = []
    future = SimpleNamespace(done=lambda: True, result=lambda: "late")
    fake = SimpleNamespace(busy=False, closed=False, mode=SimpleNamespace(get=lambda: MODES[0]),
                           set_controls=lambda state: None,
                           app=SimpleNamespace(_executor=SimpleNamespace(submit=lambda task: future)),
                           after=lambda delay, callback: callbacks.append(callback))
    results = []
    VisualStudio.submit(fake, lambda: None, results.append)
    fake.closed = True
    callbacks[0]()
    assert results == []


def test_async_error_reenables_controls():
    from types import SimpleNamespace

    from modules.visual_studio import VisualStudio
    callbacks, states, errors = [], [], []

    def failed():
        raise RuntimeError("provider unavailable")

    future = SimpleNamespace(done=lambda: True, result=failed)
    fake = SimpleNamespace(busy=False, closed=False, mode=SimpleNamespace(get=lambda: MODES[0]),
                           set_controls=states.append, status=SimpleNamespace(set=errors.append),
                           app=SimpleNamespace(_executor=SimpleNamespace(submit=lambda task: future)),
                           after=lambda delay, callback: callbacks.append(callback))
    VisualStudio.submit(fake, lambda: None, lambda result: None)
    callbacks[0]()
    assert states == ["disabled", "normal"]
    assert fake.busy is False
    assert "provider unavailable" in errors[0]


@pytest.mark.parametrize("value", ["12", "12.5", "12,5", " 12 "])
def test_custom_durations(value):
    from modules.visual_brief import duration_seconds
    assert float(duration_seconds(value)) in (12, 12.5)


@pytest.mark.parametrize("value", ["", "nan", "inf", "-1", "0", "601", "abc"])
def test_bad_durations(value):
    from modules.visual_brief import duration_seconds
    with pytest.raises(ValueError):
        duration_seconds(value)


def test_video_references_are_not_forced_to_image():
    from modules.visual_brief import MODE_HELP, output_kind
    assert output_kind(MODES[3], "Vídeo") == "video"
    assert "inicio" not in MODE_HELP[MODES[3]].lower()
    text = generation_request(MODES[3], references(), "Dos imágenes", "Camina", "Rostro",
                              "Fondo", "12", "9:16", "Inglés", "Kling", target="Vídeo")
    assert "Crea un prompt de vídeo" in text
    assert "12 segundos" in text


def test_project_restores_custom_duration_and_destination(tmp_path):
    values = fields() | dict(duration="12", target="Vídeo", platform="Kling AI", model="Kling")
    path = tmp_path / "twelve.gprompt"
    save_project(path, references(), values)
    _, loaded = load_project(path)
    assert loaded["duration"] == "12"
    assert loaded["model"] == "Kling"


def test_foreground_is_temporary():
    from types import SimpleNamespace

    from modules.visual_studio import VisualStudio
    calls = []
    fake = SimpleNamespace(closed=False, lift=lambda: calls.append("lift"),
                           attributes=lambda *args: calls.append(args),
                           focus_force=lambda: calls.append("focus"),
                           after=lambda delay, callback: callback())
    fake.release_topmost = lambda: VisualStudio.release_topmost(fake)
    VisualStudio.bring_forward(fake)
    assert calls == ["lift", ("-topmost", True), "focus", ("-topmost", False)]


def test_text_only_prompt_is_self_contained_and_allows_transformation():
    text = generation_request(MODES[0], references(1), "Auriculares sobre un soporte",
                              "Un chico anime lleva los auriculares", "Diseño del producto", "Escenario",
                              "5", "9:16", "Inglés", "Z-Image-Base")
    assert "el generador NO recibirá imágenes" in text
    assert "NO obliga a conservar la base" in text
    assert "NO es una contradicción" in text
    assert '"prompt"' in text


def test_output_image_count_is_not_input_support():
    from modules.visual_brief import check_attachment, reference_capability
    specs = {"max_imagenes": 8}
    assert reference_capability(specs, MODES[3], 3) is None
    with pytest.raises(ValueError, match="sin confirmar"):
        check_attachment(specs, MODES[3], 3, True, False)
    check_attachment(specs, MODES[3], 3, False, False)
    check_attachment(specs, MODES[3], 3, True, True)


def test_explicit_unsupported_mode_cannot_be_confirmed_away():
    from modules.visual_brief import check_attachment
    with pytest.raises(ValueError, match="no admite"):
        check_attachment({"input_capabilities": {"start_end": False}}, MODES[2], 2, True, True)


def test_result_separates_notes_and_unsupported_negative():
    from modules.visual_brief import parse_visual_result
    answer = json.dumps({"prompt": "Anime boy wearing black headphones", "negative": "blur", "notes": "Sin soporte"})
    positive, negative, notes = parse_visual_result(answer, {"has_negative": False})
    assert positive == "Anime boy wearing black headphones"
    assert notes == "Sin soporte"
    positive, negative, _ = parse_visual_result(answer, {"has_negative": True})
    assert negative == "blur"
    assert "blur" not in positive


@pytest.mark.parametrize("answer", ['{"notes": "Contradicciones"}', 'Solo contradicciones', '{"prompt": ""}'])
def test_commentary_without_prompt_is_rejected(answer):
    from modules.visual_brief import parse_visual_result
    with pytest.raises(ValueError):
        parse_visual_result(answer, {})


def test_overlength_prompt_not_silently_truncated():
    from modules.visual_brief import parse_visual_result
    with pytest.raises(ValueError, match="límite"):
        parse_visual_result(json.dumps({"prompt": "x" * 21}), {"max_chars": 20})


@pytest.mark.parametrize("invalid_response", [False, True])
def test_generation_uses_isolated_request_not_main_history(monkeypatch, invalid_response):
    from types import SimpleNamespace

    from modules import visual_studio as ui
    calls, inserted, deleted = [], {}, []

    def widget(value, name=""):
        return SimpleNamespace(get=lambda *args: value, delete=lambda *args: deleted.append(name),
                               insert=lambda position, text: inserted.update({name: text}))

    def batch(system, request, **kwargs):
        calls.append((system, request))
        if invalid_response:
            return "{\"notes\": \"No prompt\"}"
        return json.dumps({"prompt": "Anime boy wearing black headphones.", "notes": "Nueva escena", "negative": ""})

    fake = SimpleNamespace(busy=False, analysis_stale=False, checkpoint=lambda: True,
        revision_specs=lambda: {"has_negative": False, "max_chars": 2000}, direction=lambda: "",
        catalog={"SeaArt / Tensor.Art": ["Z-Image-Base"]}, negative=widget("", "negative"),
        mode=widget(MODES[0]), target=widget("Imagen"),
        model=widget("Z-Image-Base"), platform=widget("SeaArt / Tensor.Art"),
        reference_use=widget("Solo texto"), attachment_confirmed=widget(False),
        refs=references(1), analysis=widget("Auriculares"), idea=widget("Chico anime"),
        preserve=widget("Producto"), change=widget("Escenario"), duration=widget("5"),
        aspect=widget("9:16"), language=widget("Inglés"), output=widget("", "output"),
        notes=widget("", "notes"), status=SimpleNamespace(set=lambda text: None),
        app=SimpleNamespace(deepseek=SimpleNamespace(generar_batch=batch)),
        submit=lambda task, done: done(task()))
    monkeypatch.setattr(ui, "get_image_model_specs", lambda name: {"has_negative": False})
    if invalid_response:
        with pytest.raises(ValueError):
            ui.VisualStudio.generate(fake)
        assert not deleted and not inserted
        return
    ui.VisualStudio.generate(fake)
    assert len(calls) == 1
    assert "Z-Image-Base" in calls[0][1]
    assert inserted["output"] == "Anime boy wearing black headphones."
    assert inserted["notes"] == "Nueva escena"


def test_history_keeps_versions_and_separates_sessions(tmp_path):
    from modules.visual_history import VisualHistory
    first = VisualHistory(tmp_path, keep=2)
    second = VisualHistory(tmp_path, keep=2)
    for text in ("one", "two", "three"):
        first.save(references(1), fields() | {"output": text})
    second.save(references(1), fields() | {"output": "other"})
    assert len(first.versions()) == 3
    outputs = {load_project(p)[1]["output"] for p in first.versions()}
    assert outputs == {"two", "three", "other"}
    first.save(references(1), fields() | {"output": "three"})
    assert len(first.versions()) == 3


def test_failed_snapshot_preserves_previous(tmp_path, monkeypatch):
    from modules import visual_history
    history = visual_history.VisualHistory(tmp_path)
    history.save(references(1), fields() | {"output": "saved"})
    def fail(*args):
        raise OSError("Disk full")
    monkeypatch.setattr(visual_history, "save_project", fail)
    with pytest.raises(OSError):
        history.save(references(1), fields() | {"output": "new"})
    assert load_project(history.versions()[0])[1]["output"] == "saved"


def test_invalidating_does_not_delete_work_and_blocks_generation():
    from types import SimpleNamespace

    from modules.visual_studio import VisualStudio
    messages = []
    fake = SimpleNamespace(busy=False, reset_confirmation=lambda: None,
                           status=SimpleNamespace(set=messages.append))
    VisualStudio.invalidate(fake)
    assert fake.analysis_stale
    # No output, analysis or model widget is accessed while the analysis is stale.
    VisualStudio.generate(fake)
    assert "vuelve a analizar" in messages[-1]


def test_loading_old_output_splits_negative(tmp_path):
    path = tmp_path / "old.gprompt"
    save_project(path, references(1), fields() | {"output": "positive\n\nNEGATIVE:\nblur"})
    with zipfile.ZipFile(path) as z:
        data = json.loads(z.read("project.json"))
        image = z.read("image-0.png")
    data["fields"].pop("negative")
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("project.json", json.dumps(data))
        z.writestr("image-0.png", image)
    loaded = load_project(path)[1]
    assert loaded["output"] == "positive"
    assert loaded["negative"] == "blur"


def test_missing_model_is_preserved_on_restore():
    from types import SimpleNamespace

    from modules.visual_studio import VisualStudio
    changes = []
    fake = SimpleNamespace(catalog={"Platform": ["New model"]},
        platform=SimpleNamespace(get=lambda: "Platform"),
        model=SimpleNamespace(get=lambda: "Old model", set=changes.append),
        model_menu=SimpleNamespace(configure=lambda **kwargs: None), reset_confirmation=lambda: None,
        model_search=SimpleNamespace(set=lambda value: None), filter_model_menu=lambda: None)
    VisualStudio.refresh_models(fake, preserve_missing=True)
    assert changes == []
    VisualStudio.refresh_models(fake)
    assert changes == ["New model"]


def test_recovery_retains_unfinished_duration(tmp_path):
    path = tmp_path / "draft.gprompt"
    save_project(path, [], fields() | {"duration": "", "negative": "blur", "analysis_stale": "true"})
    loaded = load_project(path)[1]
    assert loaded["duration"] == ""
    assert loaded["negative"] == "blur"
    assert loaded["analysis_stale"] == "true"


def test_model_search_orders_filters_and_skips_headers():
    from modules.visual_brief import filter_models
    names = ["Z-Image", "── FLUX ──", "Flux Dev", "anime", "FLUX Krea", "Flux Dev"]
    assert filter_models(names) == ["anime", "Flux Dev", "FLUX Krea", "Z-Image"]
    assert filter_models(names, "  KREA flux ") == ["FLUX Krea"]
    assert filter_models(names, "missing") == []


def test_search_does_not_replace_selected_model_even_with_no_matches():
    from types import SimpleNamespace

    from modules.visual_studio import VisualStudio
    states = []
    fake = SimpleNamespace(catalog={"SeaArt": ["Flux", "Z-Image"]}, busy=False,
        platform=SimpleNamespace(get=lambda: "SeaArt"),
        model_search=SimpleNamespace(get=lambda: "missing"),
        model_menu=SimpleNamespace(configure=lambda **kw: states.append(kw)),
        model_matches=SimpleNamespace(configure=lambda **kw: None))
    # No selection setter exists: filtering must not change the saved model.
    VisualStudio.filter_model_menu(fake)
    assert states[-1]["state"] == "disabled"
    fake.model_search.get = lambda: "flux"
    VisualStudio.filter_model_menu(fake)
    assert states[-1] == {"values": ["Flux"], "state": "normal"}


@pytest.mark.parametrize("positive,negative,expected", [
    ("Scene", "blur", "POSITIVE PROMPT:\nScene\n\nNEGATIVE PROMPT:\nblur"),
    ("Scene", "", "Scene"), ("", "blur", "NEGATIVE PROMPT:\nblur"), ("", "", ""),
])
def test_copy_and_main_output_include_both_prompts(positive, negative, expected):
    from types import SimpleNamespace

    from modules.visual_studio import VisualStudio
    copied, applied = [], []
    fake = SimpleNamespace(output=SimpleNamespace(get=lambda *args: positive),
        negative=SimpleNamespace(get=lambda *args: negative),
        clipboard_clear=lambda: None, clipboard_append=copied.append,
        status=SimpleNamespace(set=lambda value: None),
        app=SimpleNamespace(dialogs=SimpleNamespace(actualizar_salida=applied.append)))
    fake.combined_result = lambda: VisualStudio.combined_result(fake)
    VisualStudio.copy(fake)
    VisualStudio.apply(fake)
    assert copied == applied == ([expected] if expected else [])
    copied.clear()
    VisualStudio.copy_positive(fake)
    assert copied == ([positive] if positive else [])
    copied.clear()
    VisualStudio.copy_negative(fake)
    assert copied == ([negative] if negative else [])


def test_revision_request_keeps_context_and_adds_length_margin():
    from modules.visual_brief import revision_request
    text = revision_request("person A, station B, style C", "Original scene", "blur", "Keep headphones", 2000, True)
    assert "1800" in text and "2000" in text
    assert "Original scene" in text and "Keep headphones" in text
    assert "station B" in text and "blur" in text


def test_shortening_requires_prompt_and_known_limit():
    from modules.visual_brief import revision_request
    with pytest.raises(ValueError):
        revision_request("brief", "", "", "", 2000, True)
    with pytest.raises(ValueError):
        revision_request("brief", "prompt", "", "", None, True)


def test_oversize_draft_is_available_for_repair_but_revision_is_strict():
    from modules.visual_brief import parse_visual_result
    response = json.dumps({"prompt": "x" * 2288, "negative": "", "notes": "draft"})
    assert len(parse_visual_result(response, {"max_chars": 2000}, enforce_limit=False)[0]) == 2288
    with pytest.raises(ValueError):
        parse_visual_result(response, {"max_chars": 2000})


@pytest.mark.parametrize("answer,success", [("short", True), ("x" * 21, False)])
def test_revision_only_replaces_original_after_valid_response(answer, success):
    from types import SimpleNamespace

    from modules.visual_studio import VisualStudio
    replaced, checkpoints, requests = [], [], []
    def widget(text):
        return SimpleNamespace(get=lambda *a: text, delete=lambda *a: replaced.append("delete"),
                               insert=lambda *a: replaced.append(a[-1]))
    def batch(system, request, **kw):
        requests.append(request)
        return json.dumps({"prompt": answer, "negative": "", "notes": ""})
    fake = SimpleNamespace(busy=False, analysis_stale=False, catalog={"Platform": ["Model"]},
        model=widget("Model"), platform=widget("Platform"), mode=widget(MODES[0]), target=widget("Imagen"),
        revision_specs=lambda: {"max_chars": 20}, direction=lambda: "DIRECCIÓN: niebla sin diálogo", reference_use=widget("Solo texto"),
        attachment_confirmed=widget(False), refs=references(1), analysis=widget("headphones"),
        idea=widget("wearing headphones"), preserve=widget("design"), change=widget("background"),
        duration=widget("5"), aspect=widget("9:16"), language=widget("Inglés"),
        output=widget("original prompt"), negative=widget(""), notes=widget("old notes"),
        revision_instruction=widget("keep design"), status=SimpleNamespace(set=lambda s: None),
        checkpoint=lambda: checkpoints.append(True) or True,
        app=SimpleNamespace(deepseek=SimpleNamespace(generar_batch=batch)),
        submit=lambda task, done: done(task()))
    if success:
        VisualStudio.revise(fake, True)
        assert "short" in replaced and len(checkpoints) == 2
    else:
        with pytest.raises(ValueError):
            VisualStudio.revise(fake, True)
        assert not replaced and len(checkpoints) == 1
    assert len(requests) == 1
    assert "DIRECCIÓN: niebla sin diálogo" in requests[0]


def test_video_direction_preserves_requested_dialogue_and_transition():
    from modules.visual_brief import video_direction
    result = video_direction("Cámara fija", "Niebla lenta", 'Dice: "Hola" en castellano', "Camina hasta B", True)
    assert "Cámara fija" in result and "Camina hasta B" in result
    assert "castellano" in result and "sincronización" in result
    assert "Camina hasta B" not in video_direction("", "", "", "Camina hasta B", False)


def test_project_restores_video_controls_and_name(tmp_path):
    path = tmp_path / "video.gprompt"
    settings = fields() | {"project_name": "Estación", "camera": "Fija", "environment_motion": "Niebla",
        "audio_direction": "Sin diálogo", "transition_direction": "Caminar", "manual_limit": "1800"}
    save_project(path, references(2), settings)
    restored = load_project(path)[1]
    for key in ("project_name", "camera", "environment_motion", "audio_direction", "transition_direction", "manual_limit"):
        assert restored[key] == settings[key]


def test_version_summary_uses_project_title_and_survives_corruption(tmp_path):
    from modules.visual_history import version_label
    path = tmp_path / "version.gprompt"
    save_project(path, references(1), fields() | {"project_name": "Estación", "model": "Test model"})
    assert "Estación" in version_label(path) and "Test model" in version_label(path)
    path.write_text("broken")
    assert "No se puede leer" in version_label(path)
