"""Las capturas existen y el README las enseña.

09-sep-2026. Preparando la publicación se descubrió que en todo el repo
había exactamente dos imágenes —`assets/icon.ico` y `assets/icon.png`— y el
README no mostraba ninguna: solo insignias. Para una aplicación de
escritorio con interfaz eso es la peor debilidad de la ficha, más que la
falta de firma: nadie descarga 118 MB de un desconocido sin ver antes qué
compra, y un proyecto visual sin capturas se lee como abandonado.

Se generan con `tools/capturas.py`, que arranca la app de verdad y recorta
la ventana pidiendo la geometría a Tk. Dos trampas que costaron tres
intentos y quedan resueltas ahí:

  · a 1180 px de alto la ventana se metía DETRÁS de la barra de tareas y el
    recorte capturaba la barra del autor;
  · sin `-topmost` se colaba una ventana de Chrome por delante y la captura
    salía con el escritorio del autor en vez de con la app.
"""
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CAPTURAS = RAIZ / "docs" / "capturas"
ESPERADAS = ("01-pantalla-principal.png", "02-catalogo-modelos.png",
             "03-paleta-comandos.png")


class TestLasCapturasExisten:

    def test_estan_las_tres(self):
        for n in ESPERADAS:
            p = CAPTURAS / n
            assert p.is_file(), f"falta {n}"

    def test_no_estan_vacias(self):
        # Un PNG de pocos KB es una ventana a medio pintar: pasó al
        # capturar sin dejar girar el bucle de eventos de Tk.
        for n in ESPERADAS:
            kb = (CAPTURAS / n).stat().st_size / 1024
            assert kb > 30, f"{n} pesa {kb:.0f} KB: parece a medio pintar"

    def test_son_png_de_verdad(self):
        for n in ESPERADAS:
            with open(CAPTURAS / n, "rb") as f:
                assert f.read(8) == b"\x89PNG\r\n\x1a\n", f"{n} no es un PNG"


class TestElReadmeLasEnsena:

    def _readme(self):
        return (RAIZ / "README.md").read_text(encoding="utf-8")

    def test_la_principal_va_arriba(self):
        txt = self._readme()
        i = txt.find("docs/capturas/01-pantalla-principal.png")
        assert i != -1, "la captura principal no está en el README"
        assert i < txt.find("## Dudas"), "debería ir antes del pie"

    def test_todas_las_capturas_referenciadas_existen(self):
        # Un enlace roto en el README de portada es peor que no poner nada.
        import re
        for ruta in re.findall(r"\(docs/capturas/([^)]+)\)", self._readme()):
            assert (CAPTURAS / ruta).is_file(), f"README apunta a {ruta}, que no existe"

    def test_llevan_texto_alternativo(self):
        # Accesibilidad y, si la imagen no carga, sigue contando qué era.
        import re
        for alt in re.findall(r"!\[([^\]]*)\]\(docs/capturas/", self._readme()):
            assert len(alt) > 20, f"alt demasiado corto: {alt!r}"


class TestElGeneradorEsReproducible:

    def test_existe_la_herramienta(self):
        assert (RAIZ / "tools" / "capturas.py").is_file()

    def test_no_lleva_rutas_del_autor(self):
        # Con la ruta fija, nadie más puede regenerar las capturas.
        txt = (RAIZ / "tools" / "capturas.py").read_text(encoding="utf-8")
        assert "C:\\Proyectos" not in txt and "C:/Proyectos" not in txt

    def test_pone_la_ventana_al_frente(self):
        txt = (RAIZ / "tools" / "capturas.py").read_text(encoding="utf-8")
        assert "-topmost" in txt, (
            "sin topmost, cualquier ventana ajena se cuela en la captura")
