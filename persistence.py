"""
G-Prompt Studio v1.0 — Persistencia de datos.
DataStore centraliza toda la lectura/escritura de JSON con escrituras atómicas.
"""
import json
import logging
import os
import pathlib
import tempfile

from config import ARCHIVOS
from logging_utils import log_operation

logger = logging.getLogger("gprompt")


class DataStore:
    """Almacén centralizado con escrituras atómicas (temp + os.replace)."""

    def __init__(self):
        self._archivos_corruptos: list = []
        self.historial: list = self._cargar("historial")
        self.favoritos: list = self._cargar("favoritos")
        self.personajes: list = self._cargar("personajes")
        self.plantillas: list = self._cargar("plantillas")
        self.loras: list = self._cargar("loras")
        self.estrellas: list = self._cargar("estrellas")
        self.paletas: list = self._cargar("paletas")

        if self._archivos_corruptos:
            logger.warning(f"Archivos corruptos detectados: {[x[0] for x in self._archivos_corruptos]}")

        # Migraciones de plataforma (rebrand/deprecaciones)
        self._migrar_plataformas()

        # Crear ejemplos SOLO la primera vez. Si el usuario los borra, no vuelven a aparecer.
        # Esto se controla con el flag `_ejemplos_iniciados` en preferencias.
        prefs = self.cargar_preferencias()
        ejemplos_iniciados = prefs.get("_ejemplos_iniciados", False)
        if not ejemplos_iniciados:
            if not self.plantillas:
                self._crear_plantillas_ejemplo()
            self._crear_formulas_ejemplo()
            # Marcar como iniciado para que no vuelvan a aparecer si el usuario los borra
            prefs["_ejemplos_iniciados"] = True
            self.guardar_preferencias(prefs)

    # ── Lectura / Escritura atómica ───────────────────────────────

    def _cargar(self, nombre: str) -> list:
        path = ARCHIVOS[nombre]
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except json.JSONDecodeError as e:
                logger.warning(f"{nombre}.json corrupto (línea {e.lineno}), renombrando a .corrupt")
                corrupt_path = path.with_suffix(".json.corrupt")
                path.rename(corrupt_path)
                self._archivos_corruptos.append((nombre, str(corrupt_path)))
                return []
            except OSError as e:
                logger.error(f"No se pudo leer {nombre}.json: {e}")
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
        if len(self.historial) > 500:
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

    # ── Genérico: borrar una entrada por índice ───────────────────

    @log_operation("borrar_entrada")
    def borrar_entrada(self, coleccion: str, idx: int) -> bool:
        """Borra una entrada por índice de la colección dada.

        Args:
            coleccion: nombre de la colección ("historial", "favoritos",
                "estrellas", "loras", "personajes", "plantillas", "paletas")
            idx: índice de la entrada a borrar
        Returns:
            True si se borró, False si el índice o colección no es válido.
        """
        if not hasattr(self, coleccion):
            logger.warning(f"borrar_entrada: colección desconocida '{coleccion}'")
            return False
        lista = getattr(self, coleccion)
        if not isinstance(lista, list) or not (0 <= idx < len(lista)):
            return False
        del lista[idx]
        try:
            self._guardar(coleccion)
        except Exception as e:
            logger.warning(f"borrar_entrada({coleccion}): _guardar falló: {e}")
            return False
        return True

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

    def _migrar_plataformas(self):
        """
        Migraciones automáticas de plataforma al arrancar.

        Reglas actuales:
        - Freepik AI → Magnific (rebrand oficial abril 2026)
        - DALL-E (ChatGPT) → ChatGPT / GPT Image (rebrand mayo 2026,
            tras retirada oficial de DALL-E 2/3 de la API el 12 mayo 2026)
        - Tomoviee.ai → redirigido según el modo del item:
            • modo "imagen"  → Magnific
            • modo "video"   → Kling AI
            • desconocido    → Magnific (fallback)

        NO toca 'Freepik community' (es un destino de publicación, no la plataforma).
        Solo escribe a disco lo que cambió. Idempotente (correr varias veces no rompe).
        """
        MAP_DIRECTO = {
            "Freepik AI": "Magnific",
            "DALL-E (ChatGPT)": "ChatGPT / GPT Image",
        }
        # Tomoviee: requiere lookup del modo
        TOMOVIEE_FALLBACK_POR_MODO = {
            "imagen": "Magnific",
            "video":  "Kling AI",
            "audio":  "Magnific",  # nunca debería pasar pero por si acaso
        }

        def _resolver_nueva_plataforma(item: dict) -> str | None:
            """Devuelve el valor nuevo si el item necesita migrar, o None si no."""
            valor = item.get("plataforma")
            if valor in MAP_DIRECTO:
                return MAP_DIRECTO[valor]
            if valor == "Tomoviee.ai":
                modo = item.get("modo", "imagen")
                return TOMOVIEE_FALLBACK_POR_MODO.get(modo, "Magnific")
            return None

        def _migrar_lista(lista: list) -> bool:
            modificada = False
            for item in lista:
                if not isinstance(item, dict):
                    continue
                nueva = _resolver_nueva_plataforma(item)
                if nueva is not None:
                    item["plataforma"] = nueva
                    modificada = True
            return modificada

        cambios = []
        for nombre in ("historial", "favoritos", "plantillas", "estrellas"):
            lista = getattr(self, nombre, [])
            if _migrar_lista(lista):
                self._guardar(nombre)
                cambios.append(nombre)

        # Preferencias y fórmulas guardadas
        prefs = self.cargar_preferencias()
        prefs_modificadas = False
        valor_pref = prefs.get("plataforma")
        if valor_pref in MAP_DIRECTO:
            prefs["plataforma"] = MAP_DIRECTO[valor_pref]
            prefs_modificadas = True
        elif valor_pref == "Tomoviee.ai":
            # En preferencias no hay "modo" claro — usamos Magnific como fallback
            prefs["plataforma"] = "Magnific"
            prefs_modificadas = True
        # Fórmulas guardadas dentro de preferencias
        for formula in prefs.get("formulas", []):
            if not isinstance(formula, dict):
                continue
            nueva = _resolver_nueva_plataforma(formula)
            if nueva is not None:
                formula["plataforma"] = nueva
                prefs_modificadas = True
        if prefs_modificadas:
            self.guardar_preferencias(prefs)
            cambios.append("preferencias")

        if cambios:
            logger.info(f"Migración de plataformas aplicada en: {', '.join(cambios)}")

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

    def _crear_formulas_ejemplo(self):
        """Crea fórmulas de ejemplo para nuevos usuarios."""
        prefs = self.cargar_preferencias()
        formulas_existentes = prefs.get("formulas", [])
        # Verificar si ya existe la fórmula "Animal Emergente"
        existe = any(f.get("nombre") == "🐾 Animal Emergente" for f in formulas_existentes)
        if existe:
            return
        formulas_ejemplo = {
                "nombre": "🐾 Animal Emergente",
                "positive": "{animal} powerfully breaking through a dark matte surface barrier, head is a hybrid of animal texture seamlessly integrated with geometric crystal fragments, polished chrome plates and iridized glass, intricate internal patterns, eyes intensely glowing with electric bioluminescent energy, jagged violent break with debris flying, pulsating bioluminescent filaments (electric blue, gold, purple) revealed within fracture, scattered geometric crystal and metal shards floating, dramatic directional spotlight from top combined with powerful internal light, dark infinite matte void, high-resolution photorealistic 3D conceptual art render, 8k, masterpiece",
                "negative": "blurry, low quality, distorted, deformed, ugly, watermark, text",
                "fecha": "2026-05-12"
            }
        formulas_existentes.append(formulas_ejemplo)
        prefs["formulas"] = formulas_existentes
        self.guardar_preferencias(prefs)
