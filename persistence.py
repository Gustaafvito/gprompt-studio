"""
G-Prompt Studio v1.0 — Persistencia de datos.
DataStore centraliza toda la lectura/escritura de JSON con escrituras atómicas.
"""
import json
import os
import tempfile
from config import ARCHIVOS
from logging_utils import log_operation


class DataStore:
    """Almacén centralizado con escrituras atómicas (temp + os.replace)."""

    def __init__(self):
        self.historial: list = self._cargar("historial")
        self.favoritos: list = self._cargar("favoritos")
        self.personajes: list = self._cargar("personajes")
        self.plantillas: list = self._cargar("plantillas")
        self.loras: list = self._cargar("loras")
        self.estrellas: list = self._cargar("estrellas")

        if not self.plantillas:
            self._crear_plantillas_ejemplo()

    # ── Lectura / Escritura atómica ───────────────────────────────

    def _cargar(self, nombre: str) -> list:
        path = ARCHIVOS[nombre]
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, Exception):
                return []
        return []

    def _guardar(self, nombre: str):
        """Escritura atómica: escribe a archivo temporal y luego renombra."""
        data = getattr(self, nombre)
        path = ARCHIVOS[nombre]
        tmp_path = str(path) + ".tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, str(path))
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise

    # ── Historial ─────────────────────────────────────────────────

    @log_operation("historial.agregar")
    def agregar_historial(self, entrada: dict):
        self.historial.insert(0, entrada)
        if len(self.historial) > 100:
            self.historial.pop()
        self._guardar("historial")

    @log_operation("historial.limpiar")
    def limpiar_historial(self):
        self.historial.clear()
        self._guardar("historial")

    # ── Favoritos ─────────────────────────────────────────────────

    @log_operation("favoritos.agregar")
    def agregar_favorito(self, entrada: dict):
        self.favoritos.insert(0, entrada)
        self._guardar("favoritos")

    @log_operation("favoritos.limpiar")
    def limpiar_favoritos(self):
        self.favoritos.clear()
        self._guardar("favoritos")

    # ── Estrellas ─────────────────────────────────────────────────

    @log_operation("estrellas.agregar")
    def agregar_estrella(self, entrada: dict):
        self.estrellas.insert(0, entrada)
        self._guardar("estrellas")

    @log_operation("estrellas.limpiar")
    def limpiar_estrellas(self):
        self.estrellas.clear()
        self._guardar("estrellas")

    # ── Personajes ────────────────────────────────────────────────

    @log_operation("personajes.guardar")
    def guardar_personaje(self, nombre: str, descripcion: str) -> bool:
        """Añade o sobreescribe un personaje. Devuelve True si sobreescribió."""
        for p in self.personajes:
            if p["nombre"] == nombre:
                p["descripcion"] = descripcion
                self._guardar("personajes")
                return True
        self.personajes.insert(0, {"nombre": nombre, "descripcion": descripcion})
        self._guardar("personajes")
        return False

    @log_operation("personajes.borrar")
    def borrar_personaje(self, idx: int):
        if 0 <= idx < len(self.personajes):
            del self.personajes[idx]
            self._guardar("personajes")

    @log_operation("personajes.descripcion")
    def descripcion_personaje(self, nombre: str) -> str:
        for p in self.personajes:
            if p["nombre"] == nombre:
                return p["descripcion"]
        return ""

    def nombres_personajes(self) -> list[str]:
        return ["— Sin personaje —"] + [p["nombre"] for p in self.personajes]

    # ── LoRAs ─────────────────────────────────────────────────────

    @log_operation("loras.guardar")
    def guardar_lora(self, nombre: str, trigger: str, descripcion: str = "", familia: str = "") -> bool:
        for l in self.loras:
            if l["nombre"] == nombre:
                l["trigger"] = trigger
                l["descripcion"] = descripcion
                if familia:
                    l["familia"] = familia
                self._guardar("loras")
                return True
        nuevo = {"nombre": nombre, "trigger": trigger, "descripcion": descripcion}
        if familia:
            nuevo["familia"] = familia
        self.loras.insert(0, nuevo)
        self._guardar("loras")
        return False

    @log_operation("loras.borrar")
    def borrar_lora(self, idx: int):
        if 0 <= idx < len(self.loras):
            del self.loras[idx]
            self._guardar("loras")

    def trigger_lora(self, nombre: str) -> str:
        for l in self.loras:
            if l["nombre"] == nombre:
                return l.get("trigger", "")
        return ""

    def nombres_loras(self) -> list[str]:
        return ["— Sin LoRA —"] + [l["nombre"] for l in self.loras]

    # ── Plantillas ────────────────────────────────────────────────

    @log_operation("plantillas.guardar")
    def guardar_plantilla(self, plantilla: dict) -> bool:
        nombre = plantilla["nombre"]
        for i, p in enumerate(self.plantillas):
            if p["nombre"] == nombre:
                self.plantillas[i] = plantilla
                self._guardar("plantillas")
                return True
        self.plantillas.insert(0, plantilla)
        self._guardar("plantillas")
        return False

    @log_operation("plantillas.borrar")
    def borrar_plantilla(self, nombre: str) -> bool:
        for i, p in enumerate(self.plantillas):
            if p["nombre"] == nombre:
                del self.plantillas[i]
                self._guardar("plantillas")
                return True
        return False

    def obtener_plantilla(self, nombre: str) -> dict | None:
        for p in self.plantillas:
            if p["nombre"] == nombre:
                return p
        return None

    def nombres_plantillas(self) -> list[str]:
        return ["— Sin plantilla —"] + [p["nombre"] for p in self.plantillas]

    # ── Preferencias (dict, no lista) ─────────────────────────────

    @log_operation("preferencias.guardar")
    def guardar_preferencias(self, prefs: dict):
        """Escritura atómica para preferencias."""
        path = ARCHIVOS["preferencias"]
        tmp_path = str(path) + ".tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as f:
                json.dump(prefs, f, ensure_ascii=False, indent=2)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, str(path))
        except Exception:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
            raise

    def cargar_preferencias(self) -> dict:
        path = ARCHIVOS["preferencias"]
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _crear_plantillas_ejemplo(self):
        """Crea plantillas de ejemplo para nuevos usuarios."""
        ejemplos = [
            {"nombre": "📸 Retrato realista SD", "modo": "imagen", "plataforma": "SeaArt / Tensor.Art", "modelo_img": "Z Image Turbo", "ratio": "2:3", "estilos": ["Fotografía Realista", "Retrato"], "nsfw": False, "destino": "Instagram"},
            {"nombre": "🎬 Cinematic video Kling", "modo": "video", "plataforma": "SeaArt Video", "modelo_vid": "Kling 3.0", "ratio": "16:9", "estilos": ["Cinematográfico", "Épico"], "nsfw": False, "destino": "YouTube"},
            {"nombre": "🌸 Anime ColorPop", "modo": "imagen", "plataforma": "SeaArt / Tensor.Art", "modelo_img": "NiwaStyle - Animax ColorPop", "ratio": "1:1", "estilos": ["Anime/Manga", "Vibrant Colors"], "nsfw": False, "destino": "— Personal —"},
            {"nombre": "🎵 Pop español Suno", "modo": "audio", "plataforma": "Suno", "modelo_aud": "Suno v5", "estilos": ["Pop", "Latino"], "nsfw": False, "destino": "TikTok"},
            {"nombre": "🏆 Concurso Anthum 9:16", "modo": "imagen", "plataforma": "SeaArt / Tensor.Art", "modelo_img": "FLUX.1 [dev]", "ratio": "9:16", "estilos": ["Arte Digital", "Concept Art"], "nsfw": False, "destino": "Anthum (concurso)", "brief": True},
        ]
        self.plantillas = ejemplos
        self._guardar("plantillas")
