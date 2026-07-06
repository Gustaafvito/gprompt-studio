"""Tests del módulo Avatar dataset (LoRA) — sesión 19.

Cubre la lógica pura (sin UI ni LLM real): construcción del user
prompt, ensamblado programático del dataset, pipeline con LLM falso
y exportación a disco.
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from modules.avatar_config import (
    ANGLE_GROUPS,
    AVATAR_ANGLES,
    AVATAR_BACKGROUNDS_ROTACION,
    AVATAR_FORM_FIELDS,
    AVATAR_LIGHTING,
    AVATAR_NEGATIVE_PROMPT,
    DEFAULT_ANGLE_SET,
    LORA_TYPES,
)
from modules.avatar_generator import (
    _slug_carpeta,
    adaptar_dataset_a_modelo,
    exportar_dataset,
    generar_dataset_avatar,
    generar_descripcion_canonica,
)
from modules.avatar_prompts import (
    PROMPT_VISION_FICHA,
    SYSTEM_PROMPT_AVATAR_FICHA,
    construir_user_prompt_canonico,
    construir_user_prompt_ficha,
    ensamblar_dataset,
    ensamblar_dataset_edicion,
    fondo_para_indice,
    parsear_ficha_json,
    ratio_sugerido,
)

DESC = ("a 28 year old woman with fair skin, oval face, green eyes, "
        "wavy brown hair, slim build, wearing a white t-shirt and jeans")


def _llm_fake(system, user):
    return DESC


# ── Configuración ─────────────────────────────────────────────────

class TestAvatarConfig:
    def test_angulos_canonicos(self):
        assert len(AVATAR_ANGLES) == 50
        assert DEFAULT_ANGLE_SET == list(AVATAR_ANGLES.keys())
        # Todos los grupos referenciados existen en ANGLE_GROUPS
        grupos_usados = {d["group"] for d in AVATAR_ANGLES.values()}
        assert grupos_usados <= set(ANGLE_GROUPS)

    def test_balanced_angles_son_subconjunto_valido(self):
        # Cada tipo define balanced_angles ⊆ angles, no vacío, sin duplicados.
        for tipo, cfg in LORA_TYPES.items():
            bal = cfg["balanced_angles"]
            assert bal, f"{tipo} sin balanced_angles"
            assert len(bal) == len(set(bal)), f"{tipo} balanced con duplicados"
            assert set(bal) <= set(cfg["angles"]), f"{tipo} balanced fuera de angles"

    def test_balanced_personaje_prioriza_control_y_limita_expresiones(self):
        bal = LORA_TYPES["Personaje"]["balanced_angles"]
        control = [k for k in bal if k.split("_")[0] in ("face", "bust", "full")]
        expresiones = [k for k in bal if k.startswith("expression")]
        # ≥50% planos de control (la guía pide ~60%) y expresiones limitadas (≤5).
        assert len(control) / len(bal) >= 0.5
        assert len(expresiones) <= 5

    def test_balanced_objeto_excluye_vistas_agresivas(self):
        bal = set(LORA_TYPES["Objeto"]["balanced_angles"])
        for agresiva in ("obj_bottom", "obj_isometric", "obj_hero_low"):
            assert agresiva not in bal

    def test_negativo_por_angulo_excluye_personas_solo_donde_toca(self):
        from modules.avatar_config import (
            LANDSCAPE_NEGATIVE_PROMPT,
            STYLE_NEGATIVE_PROMPT,
        )
        from modules.avatar_prompts import negativo_generico_para_angulo as N
        arq = {"prompt": "architectural exterior, no people"}
        ret = {"prompt": "portrait of a woman"}
        urb = {"prompt": "urban street, few people in distance"}
        # Estilo (base SIN personas): arquitectura excluye, retrato/urbano no.
        neg_arq = N(arq, STYLE_NEGATIVE_PROMPT).lower()
        assert "person" in neg_arq
        # También excluye FIGURAS no-humanas (estilos biomecánicos/cyborg).
        assert "robot" in neg_arq and "cyborg" in neg_arq and "android" in neg_arq
        assert "person" not in N(ret, STYLE_NEGATIVE_PROMPT).lower()
        assert "person" not in N(urb, STYLE_NEGATIVE_PROMPT).lower()
        # Paisaje (base YA excluye): no duplica el bloque de personas.
        out = N(arq, LANDSCAPE_NEGATIVE_PROMPT)
        assert out.lower().count("person") == 1
        # neg_extra del ángulo se añade siempre.
        out2 = N({"prompt": "x", "neg_extra": "lens flare"}, STYLE_NEGATIVE_PROMPT)
        assert "lens flare" in out2
        # incluir_negative=False → vacío.
        assert N(arq, STYLE_NEGATIVE_PROMPT, incluir_negative=False) == ""

    def test_refuerzo_antifigura_en_positivo_solo_sin_gente(self):
        # Ángulos sin gente añaden refuerzo anti-figura al POSITIVO (estilos
        # biomecánicos/cyborg metían un humanoide en el paisaje).
        from modules.avatar_config import LORA_TYPES
        from modules.avatar_generator import generar_dataset_lora
        cfg = LORA_TYPES["Estilo"]
        r = generar_dataset_lora(
            "Estilo", _llm_fake, {}, "st", cfg["default_angles"], "", None)
        d = {it["filename"]: it["prompt"] for it in r["dataset"]}
        assert "no robots" in d["03_landscape"]       # paisaje sin gente
        assert "no robots" in d["07_architecture"]     # arquitectura
        assert "no robots" in d["04_urban"]            # urbano (ahora sin gente)
        assert "no robots" not in d["01_portrait_woman"]  # retrato: NO
        assert "no robots" not in d["13_group_people"]    # grupo: NO

    def test_todos_los_tipos_tienen_estilo_anime(self):
        # "Anime" disponible en el combo Estilo visual de los 4 tipos, para
        # crear LoRAs anime de personaje/estilo/objeto/paisaje.
        for tipo, cfg in LORA_TYPES.items():
            assert "Anime" in cfg["styles"], f"{tipo} sin estilo Anime"
            assert "anime" in cfg["styles"]["Anime"].lower()

    def test_vistas_agresivas_de_objeto_tienen_aviso(self):
        # Las vistas agresivas llevan campo "warn" (la UI muestra ⚠ + tooltip).
        angles = LORA_TYPES["Objeto"]["angles"]
        for k in ("obj_top", "obj_bottom", "obj_isometric", "obj_hero_low"):
            assert angles[k].get("warn"), f"{k} sin aviso"
        # Una vista normal NO lleva aviso.
        assert not angles["obj_front"].get("warn")

    def test_angulos_tienen_campos_obligatorios(self):
        for key, datos in AVATAR_ANGLES.items():
            for campo in ("label", "prompt", "framing", "filename", "group"):
                assert campo in datos, f"{key} sin campo {campo}"

    def test_filenames_unicos(self):
        nombres = [d["filename"] for d in AVATAR_ANGLES.values()]
        assert len(nombres) == len(set(nombres))

    def test_form_fields_con_key_y_tipo(self):
        for campo in AVATAR_FORM_FIELDS:
            assert campo["type"] in ("entry", "option")
            assert campo["key"]


# ── construir_user_prompt_canonico ────────────────────────────────

class TestConstruirUserPrompt:
    def test_incluye_campos_rellenos(self):
        p = construir_user_prompt_canonico({"genero": "Mujer", "pelo": "castaña"})
        assert "Género: Mujer" in p
        assert "Pelo: castaña" in p

    def test_omite_campos_vacios(self):
        p = construir_user_prompt_canonico({"genero": "Mujer", "ojos": "  "})
        assert "Ojos" not in p

    def test_pide_la_descripcion(self):
        assert "descripción canónica" in construir_user_prompt_canonico({})


# ── Ficha automática (sesión 19 round 10) ─────────────────────────

class TestFichaAutomatica:
    FICHA_JSON = ('{"trigger": "ohwx_vera", "genero": "Mujer", "edad": "25-35", '
                  '"pelo": "melena negra lisa", "ojos": "marrones grandes", '
                  '"complexion": "Atlética", "ropa": "bomber verde y vaqueros"}')

    def test_system_prompt_exige_json_y_claves(self):
        assert "JSON" in SYSTEM_PROMPT_AVATAR_FICHA
        for clave in ("trigger", "genero", "edad", "complexion", "ropa"):
            assert clave in SYSTEM_PROMPT_AVATAR_FICHA

    def test_user_prompt_con_tema(self):
        p = construir_user_prompt_ficha("guerrera élfica")
        assert "guerrera élfica" in p

    def test_user_prompt_sin_tema_pide_aleatorio(self):
        assert "aleatorio" in construir_user_prompt_ficha("")

    def test_parsea_json_limpio(self):
        f = parsear_ficha_json(self.FICHA_JSON)
        assert f["trigger"] == "ohwx_vera"
        assert f["genero"] == "Mujer"
        assert f["ropa"] == "bomber verde y vaqueros"

    def test_parsea_json_con_texto_y_fences(self):
        sucio = f"Claro, aquí tienes:\n```json\n{self.FICHA_JSON}\n```\n¡Listo!"
        f = parsear_ficha_json(sucio)
        assert f["trigger"] == "ohwx_vera"

    def test_filtra_claves_desconocidas_y_vacias(self):
        f = parsear_ficha_json('{"trigger": "x", "hacker": "no", "pelo": "  "}')
        assert f == {"trigger": "x"}

    def test_respuesta_sin_json_devuelve_vacio(self):
        assert parsear_ficha_json("no hay nada aquí") == {}
        assert parsear_ficha_json("") == {}

    def test_json_invalido_devuelve_vacio(self):
        assert parsear_ficha_json("{trigger: sin comillas}") == {}

    def test_valores_numericos_se_castean(self):
        f = parsear_ficha_json('{"edad": 25, "pelo": "negro"}')
        assert f["edad"] == "25"

    def test_acepta_claves_de_estilo_objeto_paisaje(self):
        # Bug histórico: el parser solo aceptaba claves de Personaje, así que la
        # ficha automática de Estilo/Objeto/Paisaje quedaba vacía (solo trigger).
        f = parsear_ficha_json(
            '{"trigger": "ohwx_estilo_gotico", "nombre_estilo": "gotico oscuro", '
            '"tecnica": "Arte digital 2D", "paleta": "negros y purpuras", '
            '"rasgos_estilo": "ornamentos, alto contraste", "epoca": "victoriana"}')
        assert f["nombre_estilo"] == "gotico oscuro"
        assert f["tecnica"] == "Arte digital 2D"
        assert f["paleta"] and f["rasgos_estilo"] and f["epoca"]
        # Objeto/Paisaje también
        fo = parsear_ficha_json('{"nombre_objeto": "reloj", "materiales": "laton"}')
        assert fo.get("nombre_objeto") == "reloj"

    def test_prompt_vision_exige_json_y_mismas_claves(self):
        # La ficha por visión reutiliza parsear_ficha_json → mismas claves
        assert "JSON" in PROMPT_VISION_FICHA
        for clave in ("trigger", "genero", "edad", "etnia_piel", "pelo",
                      "ojos", "rasgos", "complexion", "ropa"):
            assert clave in PROMPT_VISION_FICHA

    def test_prompt_vision_prohibe_fondo_e_iluminacion(self):
        # El fondo/iluminación los pone el ensamblador, no la ficha
        assert "NO describas el fondo" in PROMPT_VISION_FICHA


# ── ensamblar_dataset (núcleo de la consistencia) ─────────────────

class TestSlugCarpeta:
    def test_trigger_normal(self):
        assert _slug_carpeta("ohwx_anime_rin") == "ohwx_anime_rin"

    def test_trigger_con_caracteres_invalidos(self):
        # Un negative pegado por error no debe romper la creación de carpeta.
        s = _slug_carpeta("blurry, low-res, out of frame: bad/anatomy")
        assert "," not in s and ":" not in s and "/" not in s and " " not in s

    def test_trigger_largo_se_trunca(self):
        assert len(_slug_carpeta("x" * 200)) <= 40

    def test_trigger_vacio_o_basura_da_dataset(self):
        assert _slug_carpeta("") == "dataset"
        assert _slug_carpeta("   ,,,  ") == "dataset"


class TestEnsamblarDataset:
    def test_descripcion_identica_en_todos_los_prompts(self):
        # La identidad (cara/pelo/ojos, todo lo previo a la ropa) es idéntica
        # en TODAS las tomas. La ropa solo se omite en los primeros planos.
        ds = ensamblar_dataset("ohwx_ana", DESC, DEFAULT_ANGLE_SET,
                               "photorealistic", "gray background")
        assert len(ds) == 50
        core = DESC.split(", wearing")[0]  # identidad sin ropa
        for item in ds:
            assert core in item["prompt"]
            assert item["prompt"].startswith("ohwx_ana, ")

    def test_primeros_planos_omiten_la_ropa(self):
        cara = ensamblar_dataset("t", DESC, ["face_front"], "", "")[0]["prompt"]
        full = ensamblar_dataset("t", DESC, ["full_front"], "", "")[0]["prompt"]
        assert "wearing" not in cara                 # headshot: sin ropa
        assert "wearing a white t-shirt" in full     # cuerpo: ropa completa

    def test_estructura_del_prompt(self):
        ds = ensamblar_dataset("trig", DESC, ["face_front"],
                               "estilo_x", "fondo_y")
        p = ds[0]["prompt"]
        # Orden (sesión 20): trigger, ENCUADRE, desc, fondo, iluminación, estilo.
        # El encuadre va ANTES que la descripción: si la desc (con ropa de cuerpo
        # entero) fuese primero, el modelo se aleja a plano entero ignorando el
        # close-up. Liderar con el tipo de plano fuerza el recorte correcto.
        core = DESC.split(", wearing")[0]  # en headshots la ropa se omite
        assert p.index("trig") < p.index("close-up headshot") < p.index(core)
        assert "fondo_y" in p
        assert AVATAR_LIGHTING in p
        assert p.endswith("estilo_x")

    def test_caption_kohya_incluye_fondo_e_iluminacion(self):
        # GUÍA OFICIAL SeaArt: la caption etiqueta fondo/iluminación/pose
        # para que el LoRA no los absorba; la identidad NO va (trigger).
        ds = ensamblar_dataset("ohwx_ana", DESC, ["face_front"], "",
                               "plain gray background, seamless backdrop")
        assert ds[0]["caption"] == ("ohwx_ana, close-up portrait, "
                                    "plain gray background, "
                                    "soft even studio lighting")
        assert DESC not in ds[0]["caption"]

    def test_caption_sin_fondo_omite_el_segmento(self):
        ds = ensamblar_dataset("t", DESC, ["face_front"], "", "")
        assert ds[0]["caption"] == "t, close-up portrait, soft even studio lighting"

    def test_negative_opcional(self):
        con = ensamblar_dataset("t", DESC, ["face_front"], "", "bg",
                                incluir_negative=True)
        sin = ensamblar_dataset("t", DESC, ["face_front"], "", "bg",
                                incluir_negative=False)
        # El negative base siempre está; los primeros planos añaden el recorte.
        assert AVATAR_NEGATIVE_PROMPT in con[0]["negative"]
        assert sin[0]["negative"] == ""

    def test_negative_por_encuadre(self):
        # Cara: añade términos de recorte (full body, legs...) al negative.
        cara = ensamblar_dataset("t", DESC, ["face_front"], "", "bg")[0]["negative"]
        assert "full body" in cara and "boots" in cara
        # Cuerpo entero: ANTI-ZOOM (niega close-up/bust) para alejarse + recorte
        # de pies (fuerza que se vean los pies, no que corte a los tobillos).
        full = ensamblar_dataset("t", DESC, ["full_front"], "", "bg")[0]["negative"]
        assert AVATAR_NEGATIVE_PROMPT in full
        assert "close-up" in full and "headshot" in full
        assert "feet cut off" in full and "cropped at the ankles" in full
        # Busto: añade recorte de piernas pero permite torso.
        busto = ensamblar_dataset("t", DESC, ["bust_front"], "", "bg")[0]["negative"]
        assert "legs" in busto and "full body" in busto
        assert "close-up" not in busto  # el busto SÍ es un primer plano

    def test_cuerpo_entero_fuerza_pies_pero_cowboy_no(self):
        # Cuerpo entero → fuerza pies. Cowboy (medio muslo arriba) NO, ahí
        # recortar por debajo de la cadera es correcto.
        full = ensamblar_dataset("t", DESC, ["full_front"], "", "bg")[0]["negative"]
        cowboy = ensamblar_dataset("t", DESC, ["cowboy_front"], "", "bg")[0]["negative"]
        assert "feet cut off" in full
        assert "feet cut off" not in cowboy
        # ...pero ambos llevan el anti-zoom.
        assert "close-up" in full and "close-up" in cowboy

    def test_antizoom_en_todas_las_tomas_de_cuerpo(self):
        # full, cowboy, sentada y acción deben llevar el anti-zoom.
        for key in ("full_front", "full_back", "cowboy_front",
                    "seated_floor", "dynamic_action"):
            neg = ensamblar_dataset("t", DESC, [key], "", "bg")[0]["negative"]
            assert "close-up" in neg and "zoomed in" in neg, key

    def test_angulos_desconocidos_se_ignoran(self):
        ds = ensamblar_dataset("t", DESC, ["face_front", "no_existe"], "", "bg")
        assert len(ds) == 1

    def test_sin_estilo_no_deja_coma_colgando(self):
        ds = ensamblar_dataset("t", DESC, ["face_front"], "", "bg")
        assert not ds[0]["prompt"].endswith(", ")


# ── Rotación de fondos (consistencia LoRA: máx. 3-6 imágenes por fondo) ──

class TestRotacionFondos:
    def test_fondo_str_se_mantiene(self):
        # Comportamiento clásico: un str es el mismo en cada índice.
        assert fondo_para_indice("gray bg", 0) == "gray bg"
        assert fondo_para_indice("gray bg", 7) == "gray bg"

    def test_fondo_lista_rota_por_indice(self):
        fondos = ["a", "b", "c"]
        assert [fondo_para_indice(fondos, i) for i in range(7)] == \
            ["a", "b", "c", "a", "b", "c", "a"]

    def test_fondo_lista_vacia_o_none_devuelve_vacio(self):
        assert fondo_para_indice([], 0) == ""
        assert fondo_para_indice(None, 0) == ""
        assert fondo_para_indice(["", None], 0) == ""

    def test_dataset_con_lista_varia_el_fondo_entre_imagenes(self):
        angulos = ["face_front", "bust_front", "full_front", "full_back"]
        ds = ensamblar_dataset("t", DESC, angulos, "", AVATAR_BACKGROUNDS_ROTACION)
        # Con 4 ángulos y 4 fondos, los 4 captions llevan fondos distintos.
        fondos_en_caption = {it["caption"] for it in ds}
        assert len(fondos_en_caption) == len(ds)
        # El fondo de cada prompt es el que toca por índice.
        for i, it in enumerate(ds):
            assert AVATAR_BACKGROUNDS_ROTACION[i].split(",")[0] in it["prompt"]

    def test_edicion_tambien_rota_fondos(self):
        angulos = ["face_front", "bust_front"]
        ds = ensamblar_dataset_edicion("t", angulos, AVATAR_BACKGROUNDS_ROTACION)
        assert AVATAR_BACKGROUNDS_ROTACION[0].split(",")[0] in ds[0]["prompt"]
        assert AVATAR_BACKGROUNDS_ROTACION[1].split(",")[0] in ds[1]["prompt"]

    def test_rotacion_son_fondos_neutros_sin_negro(self):
        # Guía: claros/neutros y sin negro puro (funde pelo/ropa oscuros).
        assert len(AVATAR_BACKGROUNDS_ROTACION) >= 3
        texto = " ".join(AVATAR_BACKGROUNDS_ROTACION).lower()
        assert "black" not in texto


# ── Modo edición img2img (sesión 19 round 12) ─────────────────────

class TestDatasetEdicion:
    def test_prompts_de_edicion(self):
        ds = ensamblar_dataset_edicion("ohwx_t", DEFAULT_ANGLE_SET, "gray bg")
        assert len(ds) == 50

    def test_prompt_frontal_conserva_identidad_y_cambia_camara(self):
        # Las tomas frontales (la pose ya coincide con la referencia) clavan
        # identidad y solo cambian cámara/expresión.
        ds = ensamblar_dataset_edicion("t", ["face_front"], "gray bg")
        p = ds[0]["prompt"]
        assert "EXACT same person from the reference image" in p
        assert "Change ONLY the camera" in p
        assert "gray bg" in p

    def test_prompt_angulo_exige_rotacion_y_niega_frontal(self):
        # Las tomas de ángulo lideran con la rotación y meten el frontal en el
        # negative (vence el ancla a la pose frontal de la referencia).
        ds = ensamblar_dataset_edicion("t", ["face_profile_left"], "gray bg")
        p, neg = ds[0]["prompt"], ds[0]["negative"]
        assert "Rotate the subject to a NEW viewpoint" in p
        assert "not the frontal pose of the reference" in p
        assert "full left side profile" in p          # el ángulo concreto sigue
        assert "Change ONLY the camera" not in p       # ya NO es el genérico
        assert "front view" in neg and "no rotation" in neg

    def test_solo_los_angulos_reales_rotan(self):
        from modules.avatar_config import AVATAR_ANGLES
        from modules.avatar_prompts import requiere_rotacion
        rotan = {k for k, a in AVATAR_ANGLES.items() if requiere_rotacion(a)}
        # 3/4, perfiles, espalda y over-shoulder rotan; frontales/expresiones no.
        assert "face_34_left" in rotan and "full_back" in rotan
        assert "over_shoulder" in rotan and "bust_34_right" in rotan
        assert "face_front" not in rotan and "expression_smile" not in rotan
        assert "low_angle" not in rotan and "cowboy_front" not in rotan

    def test_frontal_no_lleva_negative_anti_frontal(self):
        ds = ensamblar_dataset_edicion("t", ["face_front"], "bg")
        assert "no rotation" not in ds[0]["negative"]

    def test_sin_descripcion_canonica(self):
        # La identidad la aporta la imagen — el texto NO describe al personaje
        ds = ensamblar_dataset_edicion("t", ["face_front"], "bg")
        assert DESC not in ds[0]["prompt"]

    def test_caption_identica_al_modo_texto(self):
        texto = ensamblar_dataset("t", DESC, ["face_front"], "", "bg")
        edicion = ensamblar_dataset_edicion("t", ["face_front"], "bg")
        assert edicion[0]["caption"] == texto[0]["caption"]
        assert edicion[0]["filename"] == texto[0]["filename"]

    def test_adaptador_tambien_vacia_negatives_de_edicion(self):
        r = generar_dataset_avatar(_llm_fake, {}, "t", ["face_front"], "", "bg")
        r["dataset_edicion"] = ensamblar_dataset_edicion("t", ["face_front"], "bg")
        adaptar_dataset_a_modelo(r, "Nano Banana", {"has_negative": False})
        assert r["dataset"][0]["negative"] == ""
        assert r["dataset_edicion"][0]["negative"] == ""

    def test_export_incluye_prompts_edicion(self, tmp_path):
        r = generar_dataset_avatar(_llm_fake, {}, "t", ["face_front"], "", "bg")
        r["dataset_edicion"] = ensamblar_dataset_edicion("t", ["face_front"], "bg")
        base = exportar_dataset(r, str(tmp_path))
        assert os.path.isfile(os.path.join(base, "prompts_edicion",
                                           "01_face_front.txt"))
        assert os.path.isfile(os.path.join(base, "prompts_edicion_todos.txt"))
        with open(os.path.join(base, "prompts_edicion_todos.txt"),
                  encoding="utf-8") as f:
            assert "MODO EDICIÓN" in f.read()

    def test_export_edicion_escribe_ratio(self, tmp_path):
        # El modo edición debe traer el RATIO SUGERIDO igual que los
        # prompts text-to-image (antes se perdía al escribir la carpeta).
        r = generar_dataset_avatar(_llm_fake, {}, "t", ["full_front"], "", "bg")
        r["dataset_edicion"] = ensamblar_dataset_edicion("t", ["full_front"], "bg")
        base = exportar_dataset(r, str(tmp_path))
        with open(os.path.join(base, "prompts_edicion", "09_full_front.txt"),
                  encoding="utf-8") as f:
            assert "RATIO SUGERIDO: 9:16" in f.read()
        with open(os.path.join(base, "prompts_edicion_todos.txt"),
                  encoding="utf-8") as f:
            assert "[ratio 9:16]" in f.read()

    def test_export_sin_edicion_no_crea_carpeta(self, tmp_path):
        r = generar_dataset_avatar(_llm_fake, {}, "t", ["face_front"], "", "bg")
        base = exportar_dataset(r, str(tmp_path))
        assert not os.path.isdir(os.path.join(base, "prompts_edicion"))


# ── Pipeline completo + exportación ───────────────────────────────

class TestPipeline:
    def test_descripcion_canonica_sanea_la_respuesta(self):
        def llm_sucio(system, user):
            return f'  "{DESC}"\n```  '
        desc = generar_descripcion_canonica(llm_sucio, {})
        assert desc == DESC

    def test_generar_dataset_avatar_estructura(self):
        r = generar_dataset_avatar(
            _llm_fake, {"genero": "Mujer"}, "ohwx_ana",
            DEFAULT_ANGLE_SET, "photorealistic", "gray bg")
        assert r["trigger_word"] == "ohwx_ana"
        assert r["descripcion_canonica"] == DESC
        assert r["total_prompts"] == 50
        assert len(r["dataset"]) == 50

    def test_adaptar_modelo_sin_negative_vacia_negatives(self):
        r = generar_dataset_avatar(_llm_fake, {}, "t", ["face_front"], "", "bg")
        avisos = adaptar_dataset_a_modelo(r, "Nano Banana", {"has_negative": False})
        assert r["dataset"][0]["negative"] == ""
        assert r["modelo_destino"] == "Nano Banana"
        assert any("NO soporta negative" in a for a in avisos)

    def test_adaptar_modelo_con_negative_no_toca(self):
        r = generar_dataset_avatar(_llm_fake, {}, "t", ["face_front"], "", "bg")
        avisos = adaptar_dataset_a_modelo(r, "Reve 2.0",
                                          {"has_negative": True, "max_chars": 2000})
        assert r["dataset"][0]["negative"] != ""
        assert avisos == []

    def test_adaptar_avisa_si_excede_max_chars_sin_truncar(self):
        r = generar_dataset_avatar(_llm_fake, {}, "t", ["face_front"], "x" * 300, "bg")
        prompt_original = r["dataset"][0]["prompt"]
        avisos = adaptar_dataset_a_modelo(r, "Mini", {"has_negative": True,
                                                      "max_chars": 100})
        assert any("exceden el límite" in a for a in avisos)
        # NO trunca: la identidad entre ángulos es sagrada
        assert r["dataset"][0]["prompt"] == prompt_original

    def test_adaptar_sin_specs_no_hace_nada(self):
        r = generar_dataset_avatar(_llm_fake, {}, "t", ["face_front"], "", "bg")
        assert adaptar_dataset_a_modelo(r, "X", {}) == []
        assert "modelo_destino" not in r

    def test_exportar_dataset_escribe_estructura_completa(self, tmp_path):
        r = generar_dataset_avatar(
            _llm_fake, {}, "ohwx_test", ["face_front", "full_back"],
            "style", "bg")
        base = exportar_dataset(r, str(tmp_path))

        assert os.path.isfile(os.path.join(base, "dataset.json"))
        assert os.path.isfile(os.path.join(base, "prompts_todos.txt"))
        assert os.path.isfile(os.path.join(base, "prompts", "01_face_front.txt"))
        assert os.path.isfile(os.path.join(base, "captions", "01_face_front.txt"))
        assert os.path.isfile(os.path.join(base, "prompts", "12_full_back.txt"))

        with open(os.path.join(base, "dataset.json"), encoding="utf-8") as f:
            d = json.load(f)
        assert d["total_prompts"] == 2

        with open(os.path.join(base, "captions", "01_face_front.txt"),
                  encoding="utf-8") as f:
            assert f.read() == ("ohwx_test, close-up portrait, bg, "
                                "soft even studio lighting")

        # Consejos oficiales de SeaArt incluidos en cada export
        consejos = os.path.join(base, "CONSEJOS_SEAART.txt")
        assert os.path.isfile(consejos)
        with open(consejos, encoding="utf-8") as f:
            assert "25-40 imágenes" in f.read()

        with open(os.path.join(base, "prompts", "01_face_front.txt"),
                  encoding="utf-8") as f:
            contenido = f.read()
        assert "PROMPT:" in contenido
        assert "NEGATIVE PROMPT:" in contenido

    def _resultado_minimo(self, **extra):
        r = {
            "trigger_word": "ohwx_x",
            "descripcion_canonica": "in the style of x",
            "creado": "2026-01-01T00:00:00",
            "total_prompts": 1,
            "dataset": [{
                "angle_key": "a", "label": "L", "filename": "01_x",
                "prompt": "ohwx_x, subject", "negative": "",
                "caption": "ohwx_x, subject",
            }],
        }
        r.update(extra)
        return r

    def test_ratio_sugerido_por_plano(self):
        # Explícito gana siempre.
        assert ratio_sugerido({"ratio": "3:2", "framing": "portrait"}) == "3:2"
        # Cuerpo entero / torres → vertical.
        assert ratio_sugerido({"framing": "full body, front view"}) == "9:16"
        assert ratio_sugerido({"framing": "castle, fortress", "prompt": ""}) == "9:16"
        # Retrato / primer plano / detalle → cuadrado.
        assert ratio_sugerido({"framing": "close-up portrait"}) == "1:1"
        assert ratio_sugerido({"framing": "macro detail, texture"}) == "1:1"
        # Paisaje / escena / abstracto → horizontal.
        assert ratio_sugerido({"framing": "panoramic landscape"}) == "3:2"
        assert ratio_sugerido({"framing": "abstract composition"}) == "3:2"
        # Sin pistas → 1:1 (seguro).
        assert ratio_sugerido({"framing": "", "prompt": ""}) == "1:1"
        # No hay falsos positivos por "bird's eye" / "worm's eye".
        assert ratio_sugerido({"framing": "aerial view",
                               "prompt": "bird's eye perspective"}) == "3:2"

    def test_dataset_incluye_ratio_en_cada_item(self):
        ds = ensamblar_dataset("ohwx_ana", DESC, ["face_front", "full_front"],
                               "photorealistic", "gray background")
        assert ds[0]["ratio"] == "1:1"    # close-up
        assert ds[1]["ratio"] == "9:16"   # full body

    def test_export_escribe_ratio_en_ficha_y_consejos(self, tmp_path):
        r = generar_dataset_avatar(
            _llm_fake, {}, "ohwx_test", ["full_front"], "style", "bg")
        base = exportar_dataset(r, str(tmp_path))
        with open(os.path.join(base, "prompts", "09_full_front.txt"),
                  encoding="utf-8") as f:
            assert "RATIO SUGERIDO: 9:16" in f.read()
        with open(os.path.join(base, "CONSEJOS_SEAART.txt"), encoding="utf-8") as f:
            assert "ASPECT RATIO POR PLANO" in f.read()

    def test_consejos_se_adaptan_al_tipo_de_lora(self, tmp_path):
        # Estilo: consejo de ESTILO, no de personaje.
        base = exportar_dataset(self._resultado_minimo(tipo_lora="Estilo"),
                                str(tmp_path / "estilo"))
        with open(os.path.join(base, "CONSEJOS_SEAART.txt"), encoding="utf-8") as f:
            txt = f.read()
        assert "LoRA DE ESTILO" in txt
        assert "VARÍA EL SUJETO" in txt
        assert "PERSONAJE" not in txt

        # Objeto y Paisaje también tienen su propio consejo.
        for tipo, marca in [("Objeto", "OBJETO"), ("Paisaje", "PAISAJE")]:
            b = exportar_dataset(self._resultado_minimo(tipo_lora=tipo),
                                 str(tmp_path / tipo))
            with open(os.path.join(b, "CONSEJOS_SEAART.txt"), encoding="utf-8") as f:
                assert f"LoRA DE {marca}" in f.read()

        # Sin tipo_lora (pipeline Personaje) → consejo de personaje.
        base_p = exportar_dataset(self._resultado_minimo(), str(tmp_path / "pers"))
        with open(os.path.join(base_p, "CONSEJOS_SEAART.txt"), encoding="utf-8") as f:
            assert "LoRA DE PERSONAJE" in f.read()


class TestTipoNSFW:
    """Candados del tipo NSFW (18+): catálogo, salvaguardas y enrutamiento."""

    def test_catalogo_nsfw(self):
        from modules.avatar_config import (
            LORA_TYPES,
            NSFW_ANGLE_GROUPS,
            NSFW_ANGLES,
            NSFW_BALANCED_ANGLE_SET,
        )
        assert len(NSFW_ANGLES) == 30
        assert "NSFW" in LORA_TYPES
        grupos_usados = {d["group"] for d in NSFW_ANGLES.values()}
        assert grupos_usados <= set(NSFW_ANGLE_GROUPS)
        # El equilibrado es subconjunto del catálogo
        assert set(NSFW_BALANCED_ANGLE_SET) <= set(NSFW_ANGLES)

    def test_salvaguardas_adulto(self):
        """CANDADO de seguridad: no quitar el bloqueo de menores.

        Todos los prompts declaran sujeto adulto y el negative bloquea
        rasgos de menor en TODAS las imágenes del dataset."""
        from modules.avatar_config import NSFW_ANGLES, NSFW_NEGATIVE_PROMPT
        for term in ("child", "teen", "underage", "minor"):
            assert term in NSFW_NEGATIVE_PROMPT
        for key, ang in NSFW_ANGLES.items():
            assert "adult" in ang["prompt"], f"{key} sin 'adult' en el prompt"

    def test_canonico_nsfw_sin_ropa_y_adulto(self):
        from modules.avatar_prompts import (
            SYSTEM_PROMPT_NSFW_CANONICO,
            construir_user_prompt_nsfw,
            system_prompt_canonico_para_tipo,
        )
        assert system_prompt_canonico_para_tipo("NSFW") is SYSTEM_PROMPT_NSFW_CANONICO
        assert "adult" in SYSTEM_PROMPT_NSFW_CANONICO
        assert "NO incluyas ropa" in SYSTEM_PROMPT_NSFW_CANONICO
        up = construir_user_prompt_nsfw({"genero": "Mujer", "edad": "25-35",
                                         "cuerpo_detalle": "tatuaje cadera"})
        assert "18+" in up and "tatuaje cadera" in up

    def test_pipeline_generico_nsfw(self, tmp_path):
        from modules.avatar_generator import exportar_dataset, generar_dataset_lora
        r = generar_dataset_lora(
            tipo="NSFW", llm_call=_llm_fake, form_data={"genero": "Mujer"},
            trigger_word="ohwx_t", angulos_seleccionados=["nsfw_lenc_full_front"],
            estilo_sufijo="photorealistic", fondo=None)
        assert r["tipo_lora"] == "NSFW"
        assert r["total_prompts"] == 1
        item = r["dataset"][0]
        assert "underage" in item["negative"]
        # neg_extra del ángulo (anti-recorte de pies) llega al negative
        assert "cut off feet" in item["negative"]
        # El consejo exportado es el NSFW (aviso 18+)
        base = exportar_dataset(r, str(tmp_path))
        with open(os.path.join(base, "CONSEJOS_SEAART.txt"), encoding="utf-8") as f:
            assert "NSFW (18+)" in f.read()
