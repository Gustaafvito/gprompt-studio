"""El estilo visual del Generador de Dataset LoRA sigue al modelo.

09-oct-2026: el usuario generó un dataset con Anima y el estilo visual en
«Fotorrealista» (el primero de la lista), y los 50 prompts acababan en
«photorealistic, professional studio photography, 85mm lens». Anima no hace
fotorrealismo, a propósito. Ahora, con un modelo de anime, el estilo se pone
solo en Anime, como el combo «Estilo» de la ventana principal; con uno de
foto vuelve al de siempre, y una elección a mano manda.
"""
import pytest

from modules.avatar_prompts import conservar_acabado, ensamblar_dataset_edicion
from modules.avatar_ui import AvatarFrame
from modules.i18n import tr

PLATAFORMAS = {"SeaArt / Tensor.Art": [
    ("── Anime / Ilustración ──", ["Anima", "Illustrious XL V3.6"]),
    ("── Realismo SD ──", ["Juggernaut XL"]),
]}


@pytest.fixture
def ventana(tk_root):
    def crear(modelo):
        f = AvatarFrame(tk_root, llm_call=lambda s, u: "x", modelo_destino=modelo,
                        plataformas_destino=PLATAFORMAS)
        tk_root.update_idletasks()
        return f
    creadas = []
    yield lambda m: creadas.append(crear(m)) or creadas[-1]
    for f in creadas:
        f.destroy()


def _elegir_modelo(f, grupo, modelo):
    f.menu_grupo.set(tr(grupo))
    f._on_grupo_change(tr(grupo))
    f.menu_modelo.set(modelo)
    f._on_modelo_change(modelo)


def test_con_anima_sale_anime(ventana):
    assert ventana("Anima").menu_estilo.get() == tr("Anime")


def test_con_un_modelo_de_foto_el_de_siempre(ventana):
    assert ventana("Juggernaut XL").menu_estilo.get() == tr("Fotorrealista")


def test_sigue_al_modelo_al_cambiarlo(ventana):
    f = ventana("Juggernaut XL")
    _elegir_modelo(f, "── Anime / Ilustración ──", "Anima")
    assert f.menu_estilo.get() == tr("Anime")
    _elegir_modelo(f, "── Realismo SD ──", "Juggernaut XL")
    assert f.menu_estilo.get() == tr("Fotorrealista")


def test_una_eleccion_a_mano_manda(ventana):
    f = ventana("Anima")
    f.menu_estilo.set(tr("Ilustración digital"))
    f._on_estilo_manual(tr("Ilustración digital"))
    _elegir_modelo(f, "── Realismo SD ──", "Juggernaut XL")
    assert f.menu_estilo.get() == tr("Ilustración digital")


def test_otro_tipo_de_lora_vuelve_a_seguir_al_modelo(ventana):
    f = ventana("Anima")
    f._on_estilo_manual(tr("Fotorrealista"))
    f._on_tipo_change(tr("🏔 Paisaje"))
    assert f.menu_estilo.get() == tr("Anime")


# Los prompts de edición (con imagen de referencia) acababan siempre en
# «Preserve photorealistic detail and natural skin texture», también con el
# estilo en Anime: le pedían al editor una foto de un personaje dibujado.
ANIME = "anime style, clean lineart, cel shading, high quality anime illustration"
FOTO = "photorealistic, professional studio photography, sharp focus"


def test_la_edicion_en_anime_no_pide_fotos():
    it = ensamblar_dataset_edicion("tw", ["face_front"], "", estilo_sufijo=ANIME)[0]
    assert "photorealistic" not in it["prompt"]
    assert it["prompt"].endswith(
        f"Keep the same art style as the reference image: {ANIME}.")


def test_con_estilo_de_foto_o_sin_estilo_lo_de_siempre():
    siempre = "Preserve photorealistic detail and natural skin texture"
    assert conservar_acabado(FOTO) == conservar_acabado("") == siempre
    it = ensamblar_dataset_edicion("tw", ["face_front"], "")[0]
    assert it["prompt"].endswith(siempre + ".")
