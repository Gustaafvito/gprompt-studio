"""Tests del detector de palabras polisémicas españolas."""
from modules.clarity_hints import AMBIGUOUS_WORDS, detect_ambiguous


class TestDetectAmbiguous:
    def test_texto_vacio_no_devuelve_nada(self):
        assert detect_ambiguous("") == []
        assert detect_ambiguous(None) == []

    def test_texto_sin_palabras_polisemicas(self):
        assert detect_ambiguous("hola que tal amigos") == []
        assert detect_ambiguous("un atardecer en la playa") == []

    def test_detecta_pulso_singular(self):
        r = detect_ambiguous("un duelo de pulso épico")
        assert len(r) == 1
        assert r[0]["word"] == "pulso"
        assert "arm wrestling" in r[0]["meanings"][0].lower()

    def test_detecta_pulso_plural(self):
        # Caso real que motivó la feature: "duelo de pulsos" no se
        # detectaba en la primera iteración por no manejar plurales.
        r = detect_ambiguous("Un duelo de pulsos inesperado")
        assert len(r) == 1
        assert r[0]["word"] == "pulso"

    def test_detecta_multiples_palabras(self):
        r = detect_ambiguous("Una vela con la pluma encima")
        palabras = {h["word"] for h in r}
        assert palabras == {"vela", "pluma"}

    def test_plurales_multiples(self):
        r = detect_ambiguous("Tres velas y dos plumas")
        palabras = {h["word"] for h in r}
        assert palabras == {"vela", "pluma"}

    def test_plural_irregular_rey(self):
        # "reyes" no es "rey+s" → necesita entrada especial en
        # PLURALES_IRREGULARES.
        r = detect_ambiguous("Los reyes magos")
        palabras = {h["word"] for h in r}
        assert "rey" in palabras

    def test_case_insensitive(self):
        r1 = detect_ambiguous("PULSO")
        r2 = detect_ambiguous("Pulso")
        r3 = detect_ambiguous("pulso")
        assert len(r1) == len(r2) == len(r3) == 1

    def test_no_match_dentro_de_palabra(self):
        # "manga" como subcadena dentro de otra palabra (poco común,
        # pero validemos word boundaries).
        # "pulsoso" no debe detectar "pulso".
        r = detect_ambiguous("pulsoso es una palabra inventada")
        assert r == []

    def test_cada_entrada_tiene_estructura_completa(self):
        # Sanity: todas las entradas del dict tienen las 2 claves.
        for palabra, data in AMBIGUOUS_WORDS.items():
            assert "meanings" in data, f"{palabra} sin meanings"
            assert "hint" in data, f"{palabra} sin hint"
            assert isinstance(data["meanings"], list)
            assert len(data["meanings"]) >= 2, f"{palabra} con <2 meanings"
            assert isinstance(data["hint"], str)
            assert len(data["hint"]) > 20, f"{palabra} hint demasiado corto"

    def test_devuelve_word_meanings_y_hint(self):
        r = detect_ambiguous("un pulso")
        assert r[0]["word"] == "pulso"
        assert isinstance(r[0]["meanings"], list)
        assert isinstance(r[0]["hint"], str)
