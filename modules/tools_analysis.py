"""Analysis Tools Mixin - Statistics, Auto-improve, Critique, Scoring, Education Mode, etc."""
import logging
import re
from collections import Counter
from typing import TYPE_CHECKING

import customtkinter as ctk
import pyperclip

from modules import paleta as P
from modules.comfy_export import COMFY_NODE_SLOTS
from modules.gprompt_window import GPromptWindow
from modules.i18n import get_idioma, tr
from workers import limpiar_marcadores, log_future_exc

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    pass


# ── Helpers puros de scoring (módulo-level, testeables sin UI) ──────
# Extraídos de _cmd_scoring (sesión 19) para poder reutilizarlos en el
# optimizador en bucle y cubrirlos con tests unitarios.

# Máximos válidos para los scores por categoría — filtra falsas
# capturas tipo "- usa ratio 1/2" en las secciones de texto libre.
_SCORE_MAXIMOS_VALIDOS = (10, 20, 25, 50, 100)

_PATTERN_SCORE_CAT = re.compile(r"-\s*([^:]+):\s*(\d+)\s*/\s*(\d+)")
_PATTERN_SCORE_TOTAL = re.compile(r"TOTAL\s*:\s*(\d+)\s*/\s*(\d+)", re.IGNORECASE)


def color_para_score(valor: int, maximo: int) -> str:
    """Color hex según el porcentaje: verde ≥80%, amarillo ≥50%, rojo <50%."""
    if maximo <= 0:
        return P.TXT_MUTED
    pct = (valor / maximo) * 100
    if pct >= 80:
        return P.TXT_OK
    elif pct >= 50:
        return "#f39c12"
    return P.TXT_ERROR


def construir_peticion_scoring(prompt: str, modelo_info: str = "") -> str:
    """Petición al LLM para puntuar un prompt en formato parseable.

    modelo_info (opcional): bloque de reglas/specs del modelo destino
    (de inyectar_specs_modelo). Si se pasa, el evaluador puntúa la
    ADECUACIÓN AL MODELO además de la calidad genérica (sesión 19)."""
    contexto = ""
    if modelo_info:
        contexto = (
            f"CONTEXTO DEL MODELO DESTINO — evalúa la adecuación del prompt al "
            f"FORMATO y a las fortalezas del modelo, y refleja en PUNTOS DÉBILES "
            f"los incumplimientos de formato o estilo. "
            f"IMPORTANTE: NO evalúes, cuentes ni menciones la longitud o el número "
            f"de caracteres del prompt — no puedes contar caracteres de forma "
            f"fiable y la longitud se verifica aparte por código. NUNCA afirmes "
            f"que el prompt supera el límite de caracteres:\n{modelo_info}\n\n"
        )
    return (
        f"{contexto}"
        f"Analiza este prompt de IA y devuelve EXACTAMENTE en este formato (mantén las etiquetas):\n\n"
        f"PUNTUACIÓN (0-100):\n"
        f"- Claridad del sujeto: X/25\n"
        f"- Detalle de estilo: X/25\n"
        f"- Composición y cámara: X/25\n"
        f"- Calidad y atmósfera: X/25\n"
        f"TOTAL: X/100\n\n"
        f"✅ PUNTOS FUERTES:\n"
        f"- (lista 2-3 cosas que están bien)\n\n"
        f"⚠️ PUNTOS DÉBILES:\n"
        f"- (lista 2-3 cosas que faltan o sobran)\n\n"
        f"💡 SUGERENCIA:\n"
        f"- (1-2 consejos específicos accionables)\n\n"
        f"PROMPT:\n{prompt}"
    )


def _extraer_seccion(texto: str, marcador: str, siguiente_marcadores: list) -> str:
    """Devuelve el texto entre `marcador` y el primer marcador siguiente."""
    idx = texto.find(marcador)
    if idx == -1:
        return ""
    inicio = idx + len(marcador)
    fin = len(texto)
    for sig in siguiente_marcadores:
        i = texto.find(sig, inicio)
        if i != -1 and i < fin:
            fin = i
    return texto[inicio:fin].strip().lstrip(":").strip()


def parsear_scoring(resp: str) -> dict:
    """Parsea la respuesta del LLM al formato de scoring.

    Devuelve dict con:
      - scores_cat: lista de (nombre, valor, maximo) por categoría.
      - total: (valor, maximo) o None si no se encontró.
      - fuertes / debiles / sugerencia: secciones de texto (str, "" si faltan).
    """
    scores_cat = []
    for m in _PATTERN_SCORE_CAT.finditer(resp):
        nombre, val, maxv = m.group(1).strip(), int(m.group(2)), int(m.group(3))
        if maxv in _SCORE_MAXIMOS_VALIDOS and val <= maxv:
            scores_cat.append((nombre, val, maxv))

    m_total = _PATTERN_SCORE_TOTAL.search(resp)
    total = (int(m_total.group(1)), int(m_total.group(2))) if m_total else None

    return {
        "scores_cat": scores_cat,
        "total": total,
        "fuertes": _extraer_seccion(resp, "✅ PUNTOS FUERTES",
                                    ["⚠️ PUNTOS DÉBILES", "💡 SUGERENCIA", "PROMPT:"]),
        "debiles": _extraer_seccion(resp, "⚠️ PUNTOS DÉBILES",
                                    ["💡 SUGERENCIA", "PROMPT:"]),
        "sugerencia": _extraer_seccion(resp, "💡 SUGERENCIA", ["PROMPT:"]),
    }


def construir_peticion_mejora(prompt: str, debiles: str = "", sugerencia: str = "",
                              modelo_info: str = "") -> str:
    """Petición de mejora. Si hay feedback del scoring (debiles/sugerencia),
    se inyecta para que la mejora ataque los puntos débiles concretos en
    lugar de la mejora genérica. Si el prompt usa etiquetas POSITIVE/
    NEGATIVE PROMPT, se exige conservarlas (los LLM tienden a pelarlas).
    modelo_info (opcional): reglas del modelo destino — la mejora debe
    respetar su formato y límite de caracteres (sesión 19)."""
    feedback = ""
    if debiles:
        feedback += f"\nPUNTOS DÉBILES DETECTADOS (corrígelos):\n{debiles}\n"
    if sugerencia:
        feedback += f"\nSUGERENCIAS A APLICAR:\n{sugerencia}\n"
    contexto = ""
    if modelo_info:
        contexto = (
            f"\nREGLAS DEL MODELO DESTINO (la mejora DEBE respetarlas — "
            f"formato y límite de caracteres incluidos):\n{modelo_info}\n"
        )
    formato = ""
    if "POSITIVE PROMPT" in prompt.upper():
        formato = (
            "\n⚠️ FORMATO DE SALIDA OBLIGATORIO: el prompt original usa las "
            "etiquetas 'POSITIVE PROMPT:' y 'NEGATIVE PROMPT:'. Tu respuesta "
            "DEBE conservar EXACTAMENTE esas etiquetas y su estructura.\n"
        )
    return (
        f"Mejora este prompt de IA manteniendo la idea original pero añadiendo:\n"
        f"- Más detalle en sujeto y estilo\n"
        f"- Especificaciones de cámara e iluminación\n"
        f"- Tags de calidad apropiados\n"
        f"- Composición más interesante\n"
        f"{feedback}{contexto}{formato}\n"
        f"Mantén una longitud similar a la original (no la dupliques).\n"
        f"Devuelve SOLO el prompt mejorado, sin explicaciones:\n\n{prompt}"
    )


def construir_peticion_adaptar(prompt: str, modelo_info: str) -> str:
    """Petición para REESCRIBIR el prompt al formato exacto del modelo destino
    sin alterar la idea.

    A diferencia de construir_peticion_mejora (que añade calidad/detalle), aquí
    el objetivo es de FORMA: convertir entre natural y tags, respetar (o no) los
    pesos, ajustar al max_chars y a la política de negativos del modelo. La idea
    creativa se conserva intacta — solo cambia la sintaxis y la longitud."""
    formato = ""
    if "POSITIVE PROMPT" in prompt.upper():
        formato = (
            "\n⚠️ Conserva EXACTAMENTE las etiquetas 'POSITIVE PROMPT:' y "
            "'NEGATIVE PROMPT:' y su estructura.\n"
        )
    return (
        "Reescribe el siguiente prompt para que cumpla AL 100% las reglas del "
        "modelo destino (formato natural vs tags, uso o no de pesos, límite de "
        "caracteres, negativos). NO cambies la idea ni el contenido creativo: "
        "solo adapta la forma, la sintaxis y la longitud.\n\n"
        f"REGLAS DEL MODELO DESTINO:\n{modelo_info}\n"
        f"{formato}\n"
        f"Devuelve SOLO el prompt adaptado, sin explicaciones:\n\n{prompt}"
    )


def asegurar_etiquetas_prompt(texto_original: str, texto_mejorado: str) -> str:
    """Reconstruye la etiqueta 'POSITIVE PROMPT:' si el LLM la peló.

    Bug sesión 19 (mismo patrón que Iterar/Usar en sesión 7): pese a la
    instrucción de formato, algunos LLM devuelven la mejora sin la
    etiqueta inicial. Si el original la tenía y la mejora no, se
    antepone para no romper el coloreado ni los botones POS/NEG."""
    if not texto_mejorado:
        return texto_mejorado
    if ("POSITIVE PROMPT" in texto_original.upper()
            and "POSITIVE PROMPT" not in texto_mejorado.upper()):
        return "POSITIVE PROMPT:\n" + texto_mejorado.lstrip()
    return texto_mejorado


def ejecutar_loop_optimizacion(texto_inicial: str, puntuar, mejorar,
                               score_objetivo: float = 85,
                               max_iteraciones: int = 3,
                               on_progreso=None) -> dict:
    """Bucle generar → puntuar → mejorar hasta score objetivo o N iteraciones.

    Args:
        texto_inicial: prompt de partida.
        puntuar: callable(texto) -> (score_pct | None, debiles, sugerencia).
            score_pct en escala 0-100; None si la respuesta no fue parseable.
        mejorar: callable(texto, debiles, sugerencia) -> texto_mejorado.
        score_objetivo: porcentaje 0-100 al que parar.
        max_iteraciones: máximo de rondas de mejora (cada una = 2 llamadas LLM).
        on_progreso: callable(iteracion, score, texto) opcional, se invoca
            tras cada puntuación (iteración 0 = prompt original).

    Returns dict:
        - mejor: {"texto", "score", "iteracion"} — la versión con mayor score
          vista en todo el bucle (puede ser la original).
        - historial: lista de {"iteracion", "score", "texto"}.
        - alcanzado: bool, si se llegó al objetivo.
        - iteraciones: rondas de mejora ejecutadas.
        - error: str solo si el score inicial no fue parseable.
    """
    score, debiles, sugerencia = puntuar(texto_inicial)
    if score is None:
        return {"error": "El LLM no devolvió un score parseable para el prompt inicial.",
                "mejor": None, "historial": [], "alcanzado": False, "iteraciones": 0}

    historial = [{"iteracion": 0, "score": score, "texto": texto_inicial}]
    mejor = {"texto": texto_inicial, "score": score, "iteracion": 0}
    if on_progreso:
        on_progreso(0, score, texto_inicial)

    texto = texto_inicial
    iteracion = 0
    while mejor["score"] < score_objetivo and iteracion < max_iteraciones:
        iteracion += 1
        texto_nuevo = (mejorar(texto, debiles, sugerencia) or "").strip()
        if not texto_nuevo:
            iteracion -= 1
            break
        score_nuevo, debiles, sugerencia = puntuar(texto_nuevo)
        if score_nuevo is None:
            # Mejora no evaluable → descartarla y parar con lo que hay.
            iteracion -= 1
            break
        historial.append({"iteracion": iteracion, "score": score_nuevo, "texto": texto_nuevo})
        if score_nuevo > mejor["score"]:
            mejor = {"texto": texto_nuevo, "score": score_nuevo, "iteracion": iteracion}
        if on_progreso:
            on_progreso(iteracion, score_nuevo, texto_nuevo)
        texto = texto_nuevo

    return {"mejor": mejor, "historial": historial,
            "alcanzado": mejor["score"] >= score_objetivo,
            "iteraciones": iteracion}


class ToolsAnalysisService:
    """23 herramientas de análisis: crítica, automejora, stats, scoring,
    seeds, autocompletado tags, traducción, etc.

    A1 fase 2 (sesión 14): servicio aislado con app por composición.
    """

    def __init__(self, app):
        self.app = app

    def _cmd_modo_educativo(self) -> None:
        """Abre el glosario de términos AI desde data/glosario.json.

        56 entradas en 5 categorías, con buscador, filtro y botón "▶ Probar"
        en las entradas que mapean a funciones reales de la app.
        """
        from modules.glosario import abrir_glosario
        abrir_glosario(self.app)

    def _cmd_critica_historial(self) -> None:
        """LLM analiza tus ideas (no los prompts) y te da consejos sobre qué generas."""
        items = self.app.store.historial or []
        if len(items) < 5:
            return self.app.dialogs.set_estado(tr("⚠️ Necesitas al menos 5 prompts en historial."), P.TXT_AVISO)

        # ── Selector N + comprobar caché ──
        vent_sel = GPromptWindow(self.app)
        vent_sel.title(tr("📝 Crítica historial — ¿Cuántos prompts analizar?"))
        vent_sel.geometry("440x290")
        vent_sel.transient(self.app)
        ctk.CTkLabel(vent_sel, text=tr("📝 Crítica de historial"),
                     font=ctk.CTkFont(size=P.FUENTE_TITULO, weight="bold")).pack(pady=(20, 4))
        ctk.CTkLabel(vent_sel,
                     text=tr('Tienes {0} prompts en historial.\n¿Cuántos analizar?').format(len(items)),
                     font=ctk.CTkFont(size=P.FUENTE_CUERPO), text_color=P.TXT_MUTED).pack(pady=(0, 14))

        n_var = ctk.IntVar(value=min(30, len(items)))
        n_max = min(100, len(items))
        slider = ctk.CTkSlider(vent_sel, from_=5, to=max(5, n_max),
                               number_of_steps=max(1, n_max - 5),
                               variable=n_var)
        slider.pack(fill="x", padx=30, pady=(0, 4))
        lbl_n = ctk.CTkLabel(vent_sel, text=tr('Últimos {0} prompts').format(n_var.get()),
                             font=ctk.CTkFont(size=P.FUENTE_SECCION, weight="bold"))
        lbl_n.pack(pady=(0, 8))
        slider.configure(command=lambda v: lbl_n.configure(text=tr('Últimos {0} prompts').format(int(v))))

        # Aviso si hay caché
        prefs_cache = self.app.store.cargar_preferencias() or {}
        cache_critica = prefs_cache.get("_cache_critica_historial", {})
        cache_hash = cache_critica.get("hash_historial")
        cache_n = cache_critica.get("n", 0)
        actual_hash = f"{len(items)}_{items[0].get('fecha','') if items and isinstance(items[0], dict) else ''}"
        lbl_cache_info = ctk.CTkLabel(vent_sel, text="", font=ctk.CTkFont(size=P.FUENTE_PEQUENA),
                                      text_color=P.TXT_OK)
        lbl_cache_info.pack(pady=(0, 8))
        if cache_hash == actual_hash and cache_critica.get("resp"):
            lbl_cache_info.configure(text=tr('💾 Hay un análisis cacheado de {0} prompts (mismo historial)').format(cache_n))

        def _lanzar():
            n = int(n_var.get())
            usar_cache = (cache_hash == actual_hash and cache_critica.get("resp") and cache_n == n)
            vent_sel.destroy()
            if usar_cache:
                self.app.after(0, lambda: self._critica_mostrar(cache_critica["resp"], n, cacheado=True))
            else:
                self._critica_ejecutar(items[:n])

        ctk.CTkButton(vent_sel, text=tr("▶ Analizar"), width=160, height=34,
                      fg_color=P.BTN_EXITO, command=_lanzar).pack(pady=4)
        ctk.CTkButton(vent_sel, text=tr("Cancelar"), width=100, height=28,
                      fg_color=P.BTN_NEUTRO, hover_color=P.BTN_NEUTRO_HOVER,
                      command=vent_sel.destroy).pack(pady=2)

    def _critica_ejecutar(self, ultimos: list) -> None:
        self.app.dialogs.set_estado(tr('🔍 Analizando {0} ideas y patrones...').format(len(ultimos)), P.TXT_ACENTO)

        modelos_usados = Counter()
        plataformas_usadas = Counter()
        modos_usados = Counter()
        estilos_usados = Counter()
        temas = []

        for it in ultimos:
            if isinstance(it, dict):
                if it.get("modelo"): modelos_usados[it["modelo"]] += 1
                if it.get("plataforma"): plataformas_usadas[it["plataforma"]] += 1
                if it.get("modo"): modos_usados[it["modo"]] += 1
                est = it.get("estilos", "")
                if est:
                    for e in est.split(","):
                        e = e.strip()
                        if e: estilos_usados[e] += 1
                contenido = it.get("contenido", "")
                if contenido:
                    m = re.search(r'POSITIVE\s+PROMPT\s*:\s*([^,\n]+)', contenido, re.IGNORECASE)
                    if m:
                        temas.append(m.group(1).strip()[:80])

        resumen = (
            f"DATOS DEL USUARIO (sus últimos {len(ultimos)} prompts):\n\n"
            f"📊 Modelos más usados: {', '.join([f'{m} ({n}x)' for m, n in modelos_usados.most_common(5)]) or 'N/A'}\n"
            f"🌐 Plataformas: {', '.join([f'{p} ({n}x)' for p, n in plataformas_usadas.most_common(5)]) or 'N/A'}\n"
            f"📱 Modos: {', '.join([f'{m} ({n}x)' for m, n in modos_usados.most_common()]) or 'N/A'}\n"
            f"🎨 Estilos más marcados: {', '.join([f'{e} ({n}x)' for e, n in estilos_usados.most_common(8)]) or 'N/A'}\n\n"
            f"📝 Primeros elementos de cada prompt (lo que pidió el usuario):\n"
        )
        for i, t in enumerate(temas[:20], 1):
            resumen += f"  {i}. {t}\n"

        peticion = (
            f"{resumen}\n\n"
            f"Analiza los PATRONES de USO del usuario y dale consejos sobre QUÉ TIPO DE COSAS GENERA, no sobre la calidad técnica del prompt.\n\n"
            f"RESPONDE EN {'INGLÉS' if get_idioma() == 'en' else 'ESPAÑOL'}.\n"
            f"FORMATO DE RESPUESTA (traduce las cabeceras al idioma de respuesta):\n\n"
            f"📊 PERFIL DETECTADO:\n"
            f"   - 2-3 frases describiendo qué tipo de creador es (¿retratista? ¿paisajista? ¿conceptual?)\n\n"
            f"🎯 TEMAS RECURRENTES:\n"
            f"   - 3-5 temas o sujetos que más repite\n\n"
            f"🔄 PATRONES (lo que repite mucho):\n"
            f"   - Estilos, modelos o tipos de escena que predominan\n\n"
            f"💡 SUGERENCIAS DE EXPERIMENTACIÓN:\n"
            f"   - 5 cosas NUEVAS que NO ha probado y le podrían interesar:\n"
            f"     * Estilos diferentes a los suyos típicos\n"
            f"     * Modelos que aún no usa\n"
            f"     * Géneros/temas que podrían enriquecer su trabajo\n\n"
            f"⚠️ POSIBLES MEJORAS EN SUS IDEAS:\n"
            f"   - Si sus ideas son muy cortas/genéricas, sugerir cómo enriquecerlas\n"
            f"   - Si solo prueba 1 estilo, recomendar combinaciones\n"
            f"   - Si no usa modelos avanzados, animar a probar (Mystic, GPT 2, etc.)\n\n"
            f"NOTA: Enfócate en QUÉ GENERA y CÓMO PUEDE EXPLORAR MÁS, no en cómo escribir prompts."
        )

        def _worker():
            try:
                resp = self.app.deepseek.generar(peticion, temperature=0.5, max_tokens=2500)
                resp = limpiar_marcadores(resp)
                # Persistir caché
                try:
                    items_all = self.app.store.historial or []
                    cache_h = f"{len(items_all)}_{items_all[0].get('fecha','') if items_all and isinstance(items_all[0], dict) else ''}"
                    prefs_p = self.app.store.cargar_preferencias() or {}
                    prefs_p["_cache_critica_historial"] = {
                        "hash_historial": cache_h,
                        "n": len(ultimos),
                        "resp": resp,
                    }
                    self.app.store.guardar_preferencias(prefs_p)
                except Exception as e:
                    logger.debug(f"Cache crítica no se pudo guardar: {e}")
                self.app.after(0, lambda: self._critica_mostrar(resp, len(ultimos), cacheado=False))
            except Exception as e:
                self.app.after(0, lambda: self.app.dialogs.set_estado(tr('❌ Error: {0}').format(e), P.TXT_ERROR))

        self.app._executor.submit(_worker).add_done_callback(log_future_exc)

    def _critica_mostrar(self, resp: str, n: int, cacheado: bool = False) -> None:
        """Ventana de resultados de la crítica."""
        vent = GPromptWindow(self.app)
        vent.title(tr("🔍 Análisis de tus patrones") + (tr(" (caché)") if cacheado else ""))
        vent.geometry("750x650")
        vent.transient(self.app)
        ctk.CTkLabel(vent, text=tr("🔍 Análisis de tus patrones creativos"),
                     font=ctk.CTkFont(size=P.FUENTE_TITULO, weight="bold")).pack(pady=(10, 3))
        sub = tr("Análisis de tus últimas {0} ideas — patrones, temas y sugerencias").format(n)
        if cacheado:
            sub += "  ·  " + tr("💾 caché")
        ctk.CTkLabel(vent, text=sub,
                     font=ctk.CTkFont(size=P.FUENTE_PEQUENA), text_color=P.TXT_MUTED).pack(pady=(0, 8))
        txt = ctk.CTkTextbox(vent, font=ctk.CTkFont(size=P.FUENTE_CUERPO), wrap="word")
        txt.pack(fill="both", expand=True, padx=15, pady=(0, 5))
        txt.insert("1.0", resp)

        btn_row = ctk.CTkFrame(vent, fg_color="transparent")
        btn_row.pack(pady=10)

        def _copiar_todo():
            pyperclip.copy(resp)
            self.app.dialogs.set_estado(tr("📋 Análisis copiado al portapapeles"), P.TXT_OK)

        def _copiar_seleccion():
            try:
                sel = txt.get("sel.first", "sel.last")
                if sel:
                    pyperclip.copy(sel)
                    self.app.dialogs.set_estado(tr('📋 {0} caracteres copiados').format(len(sel)), P.TXT_OK)
            except Exception:
                self.app.dialogs.set_estado(tr("⚠️ Selecciona texto primero arrastrando con el ratón"), P.TXT_AVISO)

        def _regenerar():
            # Borra caché y vuelve a llamar a la crítica desde cero
            try:
                prefs_p = self.app.store.cargar_preferencias() or {}
                prefs_p.pop("_cache_critica_historial", None)
                self.app.store.guardar_preferencias(prefs_p)
            except Exception as e:
                logger.debug(f"Borrar caché crítica falló: {e}")
            vent.destroy()
            self._cmd_critica_historial()

        ctk.CTkButton(btn_row, text=tr("📋 Copiar todo"), width=140, height=30,
                      fg_color=P.BTN_EXITO, hover_color=P.BTN_EXITO_HOVER,
                      command=_copiar_todo).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text=tr("📋 Copiar selección"), width=160, height=30,
                      command=_copiar_seleccion).pack(side="left", padx=4)
        if cacheado:
            ctk.CTkButton(btn_row, text=tr("🔄 Regenerar"), width=120, height=30,
                          **P.estilo_boton(P.BTN_ACENTO),
                          command=_regenerar).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text=tr("Cerrar"), width=90, height=30,
                      fg_color=P.BTN_NEUTRO, hover_color=P.BTN_NEUTRO_HOVER,
                      command=vent.destroy).pack(side="left", padx=4)

        self.app.dialogs.set_estado(tr("🔍 Análisis listo") + (tr(" (caché)") if cacheado else ""), P.TXT_OK)

    def _cmd_automejora_periodica(self) -> None:
        """Revisa los últimos prompts y sugiere mejoras automáticas."""
        items = self.app.store.historial or []
        if len(items) < 3:
            return self.app.dialogs.set_estado(tr("⚠️ Necesitas al menos 3 prompts en historial."), P.TXT_AVISO)

        # ── Selector "últimos N" ──
        vent_sel = GPromptWindow(self.app)
        vent_sel.title(tr("🚀 Auto-mejora — ¿Cuántos prompts analizar?"))
        vent_sel.geometry("440x300")
        vent_sel.transient(self.app)
        ctk.CTkLabel(vent_sel, text=tr("🚀 Auto-mejora"),
                     font=ctk.CTkFont(size=P.FUENTE_TITULO, weight="bold")).pack(pady=(20, 4))
        ctk.CTkLabel(vent_sel,
                     text=tr('Tienes {0} prompts en el historial.\n¿Cuántos quieres analizar?').format(len(items)),
                     font=ctk.CTkFont(size=P.FUENTE_CUERPO), text_color=P.TXT_MUTED).pack(pady=(0, 14))

        n_var = ctk.IntVar(value=min(10, len(items)))
        n_max = min(50, len(items))
        slider = ctk.CTkSlider(vent_sel, from_=1, to=n_max,
                               number_of_steps=max(1, n_max - 1),
                               variable=n_var)
        slider.pack(fill="x", padx=30, pady=(0, 4))
        lbl_n = ctk.CTkLabel(vent_sel, text=tr('Últimos {0} prompts').format(n_var.get()),
                             font=ctk.CTkFont(size=P.FUENTE_SECCION, weight="bold"))
        lbl_n.pack(pady=(0, 14))
        slider.configure(command=lambda v: lbl_n.configure(text=tr('Últimos {0} prompts').format(int(v))))

        # ── Caché (mismo patrón que Crítica historial): si el historial no ha
        # cambiado y se pide el mismo N, reusa el análisis previo sin gastar tokens.
        prefs_cache = self.app.store.cargar_preferencias() or {}
        cache_am = prefs_cache.get("_cache_automejora", {})
        actual_hash = f"{len(items)}_{items[0].get('fecha', '') if items and isinstance(items[0], dict) else ''}"
        lbl_cache_info = ctk.CTkLabel(vent_sel, text="", font=ctk.CTkFont(size=P.FUENTE_PEQUENA),
                                      text_color=P.TXT_OK)
        lbl_cache_info.pack(pady=(0, 6))
        if cache_am.get("hash") == actual_hash and cache_am.get("resp"):
            lbl_cache_info.configure(
                text=tr('💾 Hay un análisis cacheado de {0} prompts').format(cache_am.get('n', 0)))

        def _lanzar():
            n = int(n_var.get())
            usar_cache = (cache_am.get("hash") == actual_hash
                          and cache_am.get("resp") and cache_am.get("n") == n)
            vent_sel.destroy()
            if usar_cache:
                self.app.after(0, lambda: self._auto_mejora_mostrar(
                    items[:n], cache_am.get("resultados"), cache_am["resp"], cacheado=True))
            else:
                self._auto_mejora_ejecutar(items[:n])

        ctk.CTkButton(vent_sel, text=tr("▶ Analizar"), width=160, height=34,
                      fg_color=P.BTN_EXITO, command=_lanzar).pack(pady=4)
        ctk.CTkButton(vent_sel, text=tr("Cancelar"), width=100, height=28,
                      fg_color=P.BTN_NEUTRO, hover_color=P.BTN_NEUTRO_HOVER,
                      command=vent_sel.destroy).pack(pady=2)

    def _auto_mejora_ejecutar(self, ultimos: list) -> None:
        """Lanza la auto-mejora con un set concreto de prompts."""
        self.app.dialogs.set_estado(tr('🚀 Auto-mejora: analizando {0} prompts...').format(len(ultimos)), P.TXT_ACENTO)

        prompts = []
        for i, it in enumerate(ultimos, 1):
            contenido = it.get("contenido", "") if isinstance(it, dict) else str(it)
            prompts.append(f"{i}. {contenido[:300]}")

        peticion = (
            f"Aquí tienes {len(ultimos)} prompts del usuario:\n\n"
            f"{chr(10).join(prompts)}\n\n"
            f"Analiza cada uno y devuelve EXCLUSIVAMENTE un JSON array válido. "
            f"Cada elemento del array debe tener esta estructura:\n"
            f'{{"n": <numero 1..N>, "bien": "...", "mejorar": "...", "mejorado": "..."}}\n\n'
            f"- bien: 1 frase de qué está bien\n"
            f"- mejorar: 1 frase específica de qué mejorar\n"
            f"- mejorado: versión mejorada COMPLETA del prompt (no resumen)\n\n"
            f"Escribe 'bien' y 'mejorar' en {'INGLÉS' if get_idioma() == 'en' else 'ESPAÑOL'} "
            f"(el campo 'mejorado' siempre en inglés, es el prompt).\n"
            f"Devuelve SOLO el array JSON, sin texto antes ni después, sin markdown."
        )

        def _worker():
            try:
                resp = self.app.deepseek.generar(peticion, temperature=0.5, max_tokens=6000)
                resp = limpiar_marcadores(resp).strip()
                # Recuperar el JSON aunque venga con cosas alrededor
                import json as _json
                m = re.search(r'\[\s*\{.*\}\s*\]', resp, re.DOTALL)
                resultados = None
                if m:
                    try:
                        resultados = _json.loads(m.group(0))
                    except Exception as e:
                        logger.debug(f"JSON parse falló: {e}")
                # Guardar en caché para no re-gastar tokens si se repite el mismo set.
                try:
                    prefs_p = self.app.store.cargar_preferencias() or {}
                    am_hash = (f"{len(ultimos)}_"
                               f"{ultimos[0].get('fecha', '') if ultimos and isinstance(ultimos[0], dict) else ''}")
                    prefs_p["_cache_automejora"] = {
                        "hash": am_hash, "n": len(ultimos),
                        "resultados": resultados, "resp": resp,
                    }
                    self.app.store.guardar_preferencias(prefs_p)
                except Exception as e:
                    logger.debug(f"[silent] cache automejora: {e}")
                self.app.after(0, lambda: self._auto_mejora_mostrar(ultimos, resultados, resp))
            except Exception as e:
                self.app.after(0, lambda e=e: self.app.dialogs.set_estado(tr('❌ Error: {0}').format(e), P.TXT_ERROR))

        self.app._executor.submit(_worker).add_done_callback(log_future_exc)

    def _auto_mejora_mostrar(self, originales: list, resultados, resp_raw: str,
                             cacheado: bool = False) -> None:
        """Render cards colapsables con originales/sugerencias y botón Aplicar."""
        is_lt = ctk.get_appearance_mode().lower() == "light"
        bg_card = "#ffffff" if is_lt else "#1a1a2e"
        text_main = "#111827" if is_lt else "#e5e7eb"
        text_muted = "#4b5563" if is_lt else "#9ca3af"
        accent = "#2563eb" if is_lt else "#60a5fa"
        success = "#16a34a" if is_lt else "#22c55e"

        vent = GPromptWindow(self.app)
        vent.title(tr("🚀 Auto-mejora de prompts"))
        vent.geometry("900x720")
        vent.transient(self.app)

        ctk.CTkLabel(vent, text=tr("🚀 Sugerencias de mejora"),
                     font=ctk.CTkFont(size=P.FUENTE_TITULO, weight="bold")).pack(pady=(10, 3))
        ctk.CTkLabel(vent, text=tr('Análisis de {0} prompts').format(len(originales)),
                     font=ctk.CTkFont(size=P.FUENTE_PEQUENA), text_color=text_muted).pack(pady=(0, 8))

        scroll = ctk.CTkScrollableFrame(vent,
                                        fg_color=("#f3f4f6" if is_lt else "#0d1117"))
        scroll.pack(fill="both", expand=True, padx=10, pady=(0, 8))

        if not resultados:
            # Fallback: si el LLM no devolvió JSON parseable, muestro texto plano
            ctk.CTkLabel(scroll,
                         text=tr("⚠️ El LLM no devolvió JSON parseable. Muestro la respuesta cruda:"),
                         text_color=P.TXT_AVISO).pack(pady=4)
            txt = ctk.CTkTextbox(scroll, wrap="word", font=ctk.CTkFont(size=P.FUENTE_CUERPO), height=500)
            txt.pack(fill="both", expand=True, padx=4, pady=4)
            txt.insert("1.0", resp_raw)
        else:
            for r in resultados:
                n = r.get("n", 0)
                bien = r.get("bien", "")
                mejorar = r.get("mejorar", "")
                mejorado = r.get("mejorado", "")
                orig_text = ""
                if 0 < n <= len(originales):
                    o = originales[n - 1]
                    orig_text = (o.get("contenido", "") if isinstance(o, dict) else str(o))

                card = ctk.CTkFrame(scroll, fg_color=bg_card, corner_radius=8)
                card.pack(fill="x", pady=4, padx=2)

                ctk.CTkLabel(card, text=tr('Prompt #{0}').format(n),
                             font=ctk.CTkFont(size=P.FUENTE_SECCION, weight="bold"),
                             text_color=accent, anchor="w").pack(anchor="w", padx=12, pady=(8, 2))

                # Original (truncado)
                if orig_text:
                    orig_short = orig_text[:200] + ("..." if len(orig_text) > 200 else "")
                    ctk.CTkLabel(card, text=f"📝 {orig_short}",
                                 text_color=text_muted, anchor="w", wraplength=820,
                                 justify="left", font=ctk.CTkFont(size=P.FUENTE_PEQUENA)).pack(fill="x", padx=12, pady=(0, 4))

                if bien:
                    ctk.CTkLabel(card, text=f"✅ {bien}",
                                 text_color=success, anchor="w", wraplength=820,
                                 justify="left", font=ctk.CTkFont(size=P.FUENTE_PEQUENA)).pack(fill="x", padx=12)
                if mejorar:
                    ctk.CTkLabel(card, text=f"💡 {mejorar}",
                                 text_color=P.TXT_AVISO, anchor="w", wraplength=820,
                                 justify="left", font=ctk.CTkFont(size=P.FUENTE_PEQUENA)).pack(fill="x", padx=12)

                if mejorado:
                    ctk.CTkLabel(card, text=tr("✨ Versión mejorada:"),
                                 text_color=text_main, anchor="w",
                                 font=ctk.CTkFont(size=P.FUENTE_PEQUENA, weight="bold")).pack(fill="x", padx=12, pady=(6, 0))
                    txt_mejor = ctk.CTkTextbox(card, wrap="word",
                                               height=80,
                                               font=ctk.CTkFont(size=P.FUENTE_PEQUENA),
                                               fg_color=("#f9fafb" if is_lt else "#0f172a"),
                                               text_color=text_main)
                    txt_mejor.pack(fill="x", padx=12, pady=(2, 6))
                    txt_mejor.insert("1.0", mejorado)
                    txt_mejor.configure(state="disabled")

                    fila_btn = ctk.CTkFrame(card, fg_color="transparent")
                    fila_btn.pack(fill="x", padx=12, pady=(0, 10))

                    def _aplicar(texto=mejorado):
                        try:
                            if hasattr(self.app, "txt_salida"):
                                self.app.txt_salida.delete("1.0", "end")
                                self.app.txt_salida.insert("1.0", texto)
                                self.app.dialogs.set_estado(tr("✨ Versión mejorada aplicada en el área de salida"), P.TXT_OK)
                        except Exception as e:
                            self.app.dialogs.set_estado(tr('❌ No se pudo aplicar: {0}').format(e), P.TXT_ERROR)

                    def _copiar(texto=mejorado):
                        pyperclip.copy(texto)
                        self.app.dialogs.set_estado(tr("📋 Versión mejorada copiada"), P.TXT_OK)

                    ctk.CTkButton(fila_btn, text=tr("✨ Aplicar versión"),
                                  width=160, height=28, fg_color=success,
                                  command=_aplicar).pack(side="left", padx=4)
                    ctk.CTkButton(fila_btn, text=tr("📋 Copiar"),
                                  width=100, height=28,
                                  command=_copiar).pack(side="left", padx=4)

        fila_final = ctk.CTkFrame(vent, fg_color="transparent")
        fila_final.pack(pady=8)
        if cacheado:
            def _regenerar():
                try:
                    prefs_r = self.app.store.cargar_preferencias() or {}
                    prefs_r.pop("_cache_automejora", None)
                    self.app.store.guardar_preferencias(prefs_r)
                except Exception as e:
                    logger.debug(f"[silent] {e}")
                vent.destroy()
                self._auto_mejora_ejecutar(originales)
            ctk.CTkButton(fila_final, text=tr("🔄 Regenerar"), width=120, height=30,
                          **P.estilo_boton(P.BTN_ACENTO),
                          command=_regenerar).pack(side="left", padx=4)
        ctk.CTkButton(fila_final, text=tr("Cerrar"), width=120, height=30,
                      fg_color=P.BTN_NEUTRO, hover_color=P.BTN_NEUTRO_HOVER,
                      command=vent.destroy).pack(side="left", padx=4)

        self.app.dialogs.set_estado(
            tr("🚀 Auto-mejora lista ({0} cards)").format(len(resultados) if resultados else 0)
            + (f" ({tr('💾 caché')})" if cacheado else ""), P.TXT_OK)

    def _abrir_estadisticas(self) -> None:
        """Ventana con estadísticas detalladas + filtro por rango de fechas."""
        import datetime as _dt
        from collections import Counter, defaultdict
        prefs = self.app.store.cargar_preferencias()
        hist_full = self.app.store.historial or []
        favs = self.app.store.favoritos or []
        stars = self.app.store.estrellas or []
        seeds = prefs.get("seeds_favoritos", [])

        vent = GPromptWindow(self.app)
        vent.title(tr("📈 Estadísticas detalladas"))
        vent.geometry("780x720")
        vent.transient(self.app)

        is_lt = ctk.get_appearance_mode().lower() == "light"
        c_card = "#161b22" if not is_lt else "#ffffff"
        c_text = "#e6edf3" if not is_lt else "#24292f"
        c_muted = "#7d8590" if not is_lt else "#656d76"
        c_accent = "#58a6ff" if not is_lt else "#0969da"

        # ── Cabecera + filtro de rango ──
        header = ctk.CTkFrame(vent, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(8, 4))
        ctk.CTkLabel(header, text=tr("📈 Estadísticas detalladas"),
                     font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=c_text).pack(side="left")

        filtro_var = ctk.StringVar(value=tr("Todo"))
        seg = ctk.CTkSegmentedButton(
            header, values=["7d", "30d", "90d", tr("Todo")],
            variable=filtro_var,
            command=lambda _v: _render(),
        )
        seg.pack(side="right")

        # ── Área scrollable que se re-renderiza al cambiar el filtro ──
        scroll = ctk.CTkScrollableFrame(vent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=10, pady=5)

        def _filtrar_por_rango(hist_all: list, rango: str) -> list:
            if rango == tr("Todo"):
                return list(hist_all)
            dias = {"7d": 7, "30d": 30, "90d": 90}.get(rango)
            if not dias:
                return list(hist_all)
            cutoff = (_dt.datetime.now() - _dt.timedelta(days=dias))
            cutoff_iso = cutoff.strftime("%Y-%m-%d")
            out = []
            for it in hist_all:
                if not isinstance(it, dict):
                    continue
                fecha = it.get("fecha", "")
                if not fecha:
                    continue
                # Las fechas suelen ir como "AAAA-MM-DD ..." — comparar prefijo
                if fecha[:10] >= cutoff_iso:
                    out.append(it)
            return out

        def _seccion(parent, titulo):
            ctk.CTkLabel(parent, text=titulo, font=ctk.CTkFont(size=P.FUENTE_SECCION, weight="bold"),
                         text_color=c_accent).pack(pady=(15, 8), anchor="w", padx=5)

        def _barra(parent, texto, count, max_val, color="#58a6ff"):
            bar_frame = ctk.CTkFrame(parent, fg_color=c_card, corner_radius=6)
            bar_frame.pack(fill="x", pady=2, padx=2)
            pct = int(count / max_val * 100) if max_val else 0
            ctk.CTkLabel(bar_frame, text=f"  {texto}",
                         font=ctk.CTkFont(size=P.FUENTE_PEQUENA), text_color=c_text,
                         anchor="w").pack(side="left", padx=5, pady=5)
            barra = ctk.CTkProgressBar(bar_frame, width=150, height=6,
                                       progress_color=color)
            barra.pack(side="left", padx=(5, 5), pady=5)
            barra.set(pct / 100)
            ctk.CTkLabel(bar_frame, text=tr('{0}x ({1}%)').format((count), (pct)),
                         font=ctk.CTkFont(size=P.FUENTE_HINT), text_color=c_muted).pack(side="right", padx=(0, 8))

        def _render():
            for w in scroll.winfo_children():
                w.destroy()

            rango = filtro_var.get()
            hist = _filtrar_por_rango(hist_full, rango)

            # ── Rango de fechas del filtro ──
            if hist:
                fechas = [h.get("fecha", "") for h in hist if isinstance(h, dict) and h.get("fecha")]
                rango_txt = f"{fechas[-1] if fechas else '—'} → {fechas[0] if fechas else '—'}"
                sub = tr("📅 {0} · {1} prompts ({2})").format(rango_txt, len(hist), rango)
            else:
                sub = tr("📅 Sin prompts en el rango ({0})").format(rango)
            ctk.CTkLabel(scroll, text=sub, font=ctk.CTkFont(size=P.FUENTE_PEQUENA),
                         text_color=c_muted).pack(pady=(0, 8))

            # ── Stats generales (no dependen del rango) ──
            _seccion(scroll, tr("📊 Colecciones"))
            grid = ctk.CTkFrame(scroll, fg_color="transparent")
            grid.pack(fill="x", padx=5)
            stats_gen = [
                (tr("📋 Historial"), len(hist_full), P.TXT_INFO),
                (tr("⭐ Favoritos"), len(favs), "#f1c40f"),
                (tr("🌟 Estrellas"), len(stars), P.TXT_ERROR),
                (tr("💎 Seeds"), len(seeds), "#9b59b6"),
                (tr("🧑 Personajes"), len(self.app.store.personajes or []), P.TXT_OK),
                (tr("🔗 LoRAs"), len(self.app.store.loras or []), P.TXT_AVISO),
                (tr("🏷️ Snippets"), len(prefs.get("snippets", [])), "#1abc9c"),
                (tr("📐 Fórmulas"), len(prefs.get("formulas", [])), "#e91e63"),
                (tr("🧬 ADNs"), len(prefs.get("adns_guardados", [])), "#00bcd4"),
            ]
            for i, (label, val, color) in enumerate(stats_gen):
                col, row = i % 3, i // 3
                card = ctk.CTkFrame(grid, fg_color=c_card, corner_radius=8,
                                    border_color="#30363d", border_width=1)
                card.grid(row=row, column=col, padx=5, pady=4, sticky="nsew")
                ctk.CTkLabel(card, text=str(val), font=ctk.CTkFont(size=20, weight="bold"),
                             text_color=color).pack(pady=(8, 2))
                ctk.CTkLabel(card, text=label, font=ctk.CTkFont(size=P.FUENTE_HINT),
                             text_color=c_muted).pack(pady=(0, 8))
            for c in range(3):
                grid.grid_columnconfigure(c, weight=1)

            if not hist:
                return

            # ── Stats por modelo / plataforma / ratio / estilos / longitud ──
            modelos = Counter()
            plataformas = Counter()
            ratios = Counter()
            estilos_count = Counter()
            largos = []
            for it in hist:
                if not isinstance(it, dict):
                    continue
                if it.get("modelo"): modelos[it["modelo"]] += 1
                if it.get("plataforma"): plataformas[it["plataforma"]] += 1
                if it.get("ratio"): ratios[it["ratio"]] += 1
                est = it.get("estilos", [])
                if isinstance(est, list):
                    for e in est:
                        if e: estilos_count[e] += 1
                elif isinstance(est, str) and est:
                    for e in est.split(","):
                        e = e.strip()
                        if e: estilos_count[e] += 1
                contenido = it.get("contenido", "")
                if contenido:
                    largos.append(len(str(contenido).split()))

            if modelos:
                _seccion(scroll, tr("🏆 Top modelos usados"))
                top_m = modelos.most_common(8)
                max_m = top_m[0][1] if top_m else 1
                for modelo, count in top_m:
                    _barra(scroll, modelo, count, max_m, "#58a6ff")

            if plataformas:
                _seccion(scroll, tr("🌐 Top plataformas"))
                top_p = plataformas.most_common(6)
                max_p = top_p[0][1] if top_p else 1
                for plat, count in top_p:
                    _barra(scroll, plat, count, max_p, "#3fb950")

            if ratios:
                _seccion(scroll, tr("📐 Ratios más usados"))
                top_r = ratios.most_common(8)
                max_r = top_r[0][1] if top_r else 1
                for r_lbl, count in top_r:
                    _barra(scroll, r_lbl, count, max_r, "#f78166")

            # Top estilos (antes omitido, ahora útil para identificar tendencias)
            if estilos_count:
                _seccion(scroll, tr("🎨 Top estilos marcados"))
                top_e = estilos_count.most_common(10)
                max_e = top_e[0][1] if top_e else 1
                for est_lbl, count in top_e:
                    _barra(scroll, est_lbl, count, max_e, "#a78bfa")

            if largos:
                _seccion(scroll, tr("📏 Longitud de prompts (palabras)"))
                media = sum(largos) // len(largos)
                info = ctk.CTkFrame(scroll, fg_color=c_card, corner_radius=8,
                                    border_color="#30363d", border_width=1)
                info.pack(fill="x", pady=5, padx=2)
                ctk.CTkLabel(info,
                             text=tr('📊 Media: ~{0}  ·  Mín: {1}  ·  Máx: {2}').format((media), (min(largos)), (max(largos))),
                             font=ctk.CTkFont(size=P.FUENTE_CUERPO),
                             text_color=c_accent).pack(padx=10, pady=10)

            # ── Actividad por mes ──
            meses = defaultdict(int)
            for it in hist:
                if isinstance(it, dict):
                    fecha = it.get("fecha", "")
                    if len(fecha) >= 7:
                        meses[fecha[:7]] += 1
            if meses:
                _seccion(scroll, tr("📅 Prompts por mes"))
                top_mes = sorted(meses.items(), reverse=True)[:12]
                max_mes = max(v for _, v in top_mes) if top_mes else 1
                for mes, count in top_mes:
                    _barra(scroll, mes, count, max_mes, "#ffa657")

            # ── Top seeds aplicados ──
            if seeds:
                _seccion(scroll, tr("💎 Seeds más usados (en este rango)"))
                seed_usage = Counter()
                for it in hist:
                    if isinstance(it, dict):
                        sn = it.get("seed_nombre", "")
                        if sn: seed_usage[sn] += 1
                if seed_usage:
                    top_s = seed_usage.most_common(5)
                    max_s = top_s[0][1] if top_s else 1
                    for nombre, count in top_s:
                        _barra(scroll, nombre, count, max_s, "#9b59b6")
                else:
                    ctk.CTkLabel(scroll,
                                 text=tr("  Sin datos de uso de seeds en este rango"),
                                 font=ctk.CTkFont(size=P.FUENTE_PEQUENA),
                                 text_color=c_muted).pack(anchor="w", padx=10)

        # ── Pie: Exportar CSV (usa hist_full siempre) ──
        def _exportar_csv():
            import csv
            from tkinter import filedialog
            path = filedialog.asksaveasfilename(defaultextension=".csv",
                                                filetypes=[("CSV", "*.csv")], parent=vent)
            if not path:
                return
            with open(path, "w", newline="", encoding="utf-8") as f:
                w = csv.writer(f)
                w.writerow([tr("Fecha"), tr("Modelo"), tr("Plataforma"), tr("Ratio"), tr("Estilos"), tr("Longitud (palabras)")])
                for it in (hist_full or []):
                    if not isinstance(it, dict):
                        continue
                    est = it.get("estilos", [])
                    if isinstance(est, list):
                        est_s = ", ".join(est)
                    else:
                        est_s = str(est)
                    cont = it.get("contenido", "")
                    w.writerow([
                        it.get("fecha", ""),
                        it.get("modelo", ""),
                        it.get("plataforma", ""),
                        it.get("ratio", ""),
                        est_s,
                        len(str(cont).split()) if cont else 0,
                    ])
            self.app.dialogs.set_estado(tr('📊 CSV exportado: {0}').format(path.split('/')[-1]), P.TXT_OK)

        pie = ctk.CTkFrame(vent, fg_color="transparent")
        pie.pack(fill="x", padx=10, pady=8)
        ctk.CTkButton(pie, text=tr("📊 Exportar CSV completo"), width=200, height=32,
                      fg_color=P.BTN_EXITO, command=_exportar_csv).pack(side="left")
        ctk.CTkButton(pie, text=tr("Cerrar"), width=120, height=30,
                      command=vent.destroy).pack(side="right")

        _render()

    def _cmd_scoring(self) -> None:
        """Puntúa el prompt actual y genera versión mejorada.

        Renderizado con código de colores: cada score se detecta con
        regex y se colorea según su valor (verde >= 80%, amarillo
        50-79%, rojo < 50%). El TOTAL se destaca en grande.
        """
        actual = self.app.txt_salida.get("1.0", "end").strip()
        if not actual or len(actual) < 20:
            return self.app.dialogs.set_estado(tr("⚠️ Genera un prompt primero."), P.TXT_AVISO)

        self.app.dialogs.set_estado(tr("📝 Analizando y puntuando prompt..."), P.TXT_ACENTO)

        # Specs del modelo activo → el scoring evalúa adecuación al modelo
        modelo_info = self._contexto_modelo_activo()
        peticion = construir_peticion_scoring(actual, modelo_info)
        _color_para_score = color_para_score

        def _worker():
            try:
                resp = self.app.deepseek.generar(peticion, temperature=0.3, max_tokens=2000)
                resp = limpiar_marcadores(resp)

                parsed = parsear_scoring(resp)
                scores_cat = parsed["scores_cat"]
                total_val, total_max = parsed["total"] if parsed["total"] else (None, None)
                fuertes = parsed["fuertes"]
                debiles = parsed["debiles"]
                sugerencia = parsed["sugerencia"]

                def _mostrar():
                    is_lt = ctk.get_appearance_mode().lower() == "light"
                    try:
                        from config import get_theme_colors
                        c = get_theme_colors(is_lt)
                    except Exception:
                        c = {"panel_text": "#111827" if is_lt else "#e5e7eb",
                             "panel_bg": "#f9fafb" if is_lt else "#0f1318",
                             "muted_text": "#4b5563" if is_lt else "#9ca3af",
                             "card_bg": "#ffffff" if is_lt else "#111820",
                             "card_border": "#d1d5db" if is_lt else "#1f2937"}

                    vent = GPromptWindow(self.app)
                    vent.title(tr("📝 Scoring de prompt"))
                    vent.geometry("720x640")
                    vent.transient(self.app)
                    vent.configure(fg_color=c.get("panel_bg"))

                    ctk.CTkLabel(vent, text=tr("📝 Análisis de calidad del prompt"),
                                 font=ctk.CTkFont(size=P.FUENTE_TITULO, weight="bold"),
                                 text_color=c.get("panel_text")).pack(pady=(12, 4))

                    # ── Bloque TOTAL grande ─────────────────────────
                    if total_val is not None:
                        total_color = _color_para_score(total_val, total_max)
                        total_frame = ctk.CTkFrame(vent, fg_color=c.get("card_bg"),
                                                    border_color=total_color, border_width=2,
                                                    corner_radius=10)
                        total_frame.pack(padx=20, pady=(4, 10), fill="x")

                        # Etiqueta calidad textual
                        pct = (total_val / total_max) * 100 if total_max else 0
                        if pct >= 85: etiqueta = tr("🏆 Excelente")
                        elif pct >= 70: etiqueta = tr("✨ Bueno")
                        elif pct >= 50: etiqueta = tr("🟡 Mejorable")
                        else: etiqueta = tr("⚠️ Necesita trabajo")

                        ctk.CTkLabel(total_frame, text=f"{total_val} / {total_max}",
                                     font=ctk.CTkFont(size=36, weight="bold"),
                                     text_color=total_color).pack(pady=(10, 0))
                        ctk.CTkLabel(total_frame, text=etiqueta,
                                     font=ctk.CTkFont(size=P.FUENTE_SECCION, weight="bold"),
                                     text_color=total_color).pack(pady=(0, 10))

                    # ── Categorías con barras de color ──────────────
                    if scores_cat:
                        cat_frame = ctk.CTkFrame(vent, fg_color="transparent")
                        cat_frame.pack(padx=20, pady=4, fill="x")

                        for nombre, val, maxv in scores_cat[:4]:  # primeros 4 por seguridad
                            row = ctk.CTkFrame(cat_frame, fg_color="transparent")
                            row.pack(fill="x", pady=2)

                            color = _color_para_score(val, maxv)
                            # Nombre categoría
                            ctk.CTkLabel(row, text=nombre, anchor="w",
                                         font=ctk.CTkFont(size=P.FUENTE_CUERPO, weight="bold"),
                                         text_color=c.get("panel_text"),
                                         width=180).pack(side="left", padx=(2, 8))
                            # Barra de progreso
                            try:
                                bar = ctk.CTkProgressBar(row, width=320, height=14,
                                                          progress_color=color)
                                bar.set(val / maxv if maxv else 0)
                                bar.pack(side="left", padx=4)
                            except Exception as _e:
                                logger.debug(f"[silent] {_e}")
                            # Score numérico coloreado
                            ctk.CTkLabel(row, text=f"{val}/{maxv}",
                                         font=ctk.CTkFont(size=P.FUENTE_CUERPO, weight="bold"),
                                         text_color=color, width=60).pack(side="left", padx=4)

                    # ── Texto detallado (puntos fuertes/débiles/sugerencia) ──
                    detail_frame = ctk.CTkScrollableFrame(vent, fg_color="transparent",
                                                           height=180)
                    detail_frame.pack(fill="both", expand=True, padx=20, pady=(8, 4))

                    if fuertes:
                        ctk.CTkLabel(detail_frame, text=tr("✅ Puntos fuertes"),
                                     font=ctk.CTkFont(size=P.FUENTE_SECCION, weight="bold"),
                                     text_color=P.TXT_OK, anchor="w").pack(anchor="w", pady=(2, 1))
                        ctk.CTkLabel(detail_frame, text=fuertes,
                                     font=ctk.CTkFont(size=P.FUENTE_CUERPO), wraplength=620,
                                     justify="left", anchor="w",
                                     text_color=c.get("panel_text")).pack(anchor="w", padx=12, pady=(0, 6))

                    if debiles:
                        ctk.CTkLabel(detail_frame, text=tr("⚠️ Puntos débiles"),
                                     font=ctk.CTkFont(size=P.FUENTE_SECCION, weight="bold"),
                                     text_color=P.TXT_ERROR, anchor="w").pack(anchor="w", pady=(2, 1))
                        ctk.CTkLabel(detail_frame, text=debiles,
                                     font=ctk.CTkFont(size=P.FUENTE_CUERPO), wraplength=620,
                                     justify="left", anchor="w",
                                     text_color=c.get("panel_text")).pack(anchor="w", padx=12, pady=(0, 6))

                    if sugerencia:
                        ctk.CTkLabel(detail_frame, text=tr("💡 Sugerencia"),
                                     font=ctk.CTkFont(size=P.FUENTE_SECCION, weight="bold"),
                                     text_color=P.TXT_INFO, anchor="w").pack(anchor="w", pady=(2, 1))
                        ctk.CTkLabel(detail_frame, text=sugerencia,
                                     font=ctk.CTkFont(size=P.FUENTE_CUERPO), wraplength=620,
                                     justify="left", anchor="w",
                                     text_color=c.get("panel_text")).pack(anchor="w", padx=12, pady=(0, 6))

                    # Si no hubo parseo (formato raro), mostrar todo el texto
                    if not (scores_cat or fuertes or debiles or sugerencia):
                        txt = ctk.CTkTextbox(detail_frame, font=ctk.CTkFont(size=P.FUENTE_CUERPO),
                                              wrap="word", height=160)
                        txt.pack(fill="both", expand=True, padx=4, pady=4)
                        txt.insert("1.0", resp)
                        # Editable para permitir seleccionar texto

                    # ── Botones ─────────────────────────────────────
                    btn_frame = ctk.CTkFrame(vent, fg_color="transparent")
                    btn_frame.pack(pady=10)

                    def _copiar_analisis():
                        pyperclip.copy(resp)
                        self.app.dialogs.set_estado(tr("📋 Análisis copiado al portapapeles"), P.TXT_OK)

                    ctk.CTkButton(btn_frame, text=tr("📋 Copiar análisis"), width=140, height=30,
                                  fg_color=P.BTN_EXITO, hover_color=P.BTN_EXITO_HOVER,
                                  command=_copiar_analisis).pack(side="left", padx=4)

                    def _generar_mejorado():
                        self.app.dialogs.set_estado(tr("✨ Generando versión mejorada..."), P.TXT_ACENTO)
                        # Inyecta los puntos débiles del scoring para que la
                        # mejora ataque lo detectado, no la mejora genérica.
                        peticion_mejora = construir_peticion_mejora(
                            actual, debiles, sugerencia, modelo_info)
                        def _worker_mejorar():
                            try:
                                texto_mejorado = self.app.deepseek.generar(peticion_mejora, temperature=0.3, max_tokens=2000)
                                texto_mejorado = asegurar_etiquetas_prompt(
                                    actual, limpiar_marcadores(texto_mejorado))
                                def _aplicar():
                                    self.app.dialogs.actualizar_salida(texto_mejorado)
                                    vent.destroy()
                                    self.app.dialogs.set_estado(tr("✨ Prompt mejorado aplicado"), P.TXT_OK)
                                self.app.after(0, _aplicar)
                            except Exception as e:
                                self.app.after(0, lambda e=e: self.app.dialogs.set_estado(tr('❌ Error: {0}').format(e), P.TXT_ERROR))
                        self.app._executor.submit(_worker_mejorar).add_done_callback(log_future_exc)

                    ctk.CTkButton(btn_frame, text=tr("✨ Mejorar prompt"), width=140, height=30,
                                  **P.estilo_boton(P.BTN_ACENTO), command=_generar_mejorado).pack(side="left", padx=4)

                    self.app.dialogs.set_estado(tr("📝 Scoring listo"), P.TXT_OK)
                self.app.after(0, _mostrar)
            except Exception as e:
                self.app.after(0, lambda e=e: self.app.dialogs.set_estado(tr('❌ Error: {0}').format(e), P.TXT_ERROR))

        self.app._executor.submit(_worker).add_done_callback(log_future_exc)

    # ── Optimizador en bucle (sesión 19) ──────────────────────────

    _OPTIMIZADOR_SYSTEM_SCORING = (
        "Eres un evaluador estricto y consistente de prompts para IA "
        "generativa. Puntúas con rigor y detectas debilidades concretas. "
        "Respondes EXACTAMENTE en el formato que se te pide."
    )
    _OPTIMIZADOR_SYSTEM_MEJORA = (
        "Eres un ingeniero de prompts experto. Mejoras prompts para IA "
        "generativa atacando los puntos débiles detectados, sin cambiar "
        "la idea original. Devuelves SOLO el prompt mejorado."
    )

    def _contexto_modelo_activo(self) -> str:
        """Bloque de reglas/specs del modelo activo para scoring y mejora.

        Reutiliza inyectar_specs_modelo (lo mismo que ve el generador) y
        lo capa a 1800 chars para no inflar el coste de cada llamada.
        Devuelve "" si no hay modelo con specs (el scoring sigue genérico).
        """
        try:
            info = self.app.prompts.inyectar_specs_modelo("") or ""
            return info.strip()[:1800]
        except Exception as e:
            logger.debug(f"[silent] contexto modelo: {e}")
            return ""

    def _cmd_optimizar_loop(self) -> None:
        """Optimizador en bucle: genera → puntúa → mejora → repite hasta
        alcanzar el score objetivo o agotar las iteraciones máximas.

        Reutiliza el formato de scoring de _cmd_scoring (helpers puros
        parsear_scoring/construir_peticion_*) y conserva siempre la MEJOR
        versión vista, aunque una iteración empeore el score.
        Cada iteración = 2 llamadas LLM (mejorar + puntuar) + 1 inicial.
        """
        actual = self.app.txt_salida.get("1.0", "end").strip()
        if not actual or len(actual) < 20:
            return self.app.dialogs.set_estado(tr("⚠️ Genera un prompt primero."), P.TXT_AVISO)

        try: self.app._sesion_log("🎯 Abrió Optimizador en bucle")
        except Exception as e:
            logger.debug(f"[silent] {e}")

        is_lt = ctk.get_appearance_mode().lower() == "light"
        try:
            from config import get_theme_colors
            c = get_theme_colors(is_lt)
        except Exception:
            c = {"panel_text": "#111827" if is_lt else "#e5e7eb",
                 "muted_text": "#4b5563" if is_lt else "#9ca3af",
                 "fg_dark": "#e5e7eb" if is_lt else "#2b2b2b",
                 "fg_dark_hover": "#d1d5db" if is_lt else "#3a3a3a"}

        # ── Modal de configuración ──
        cfg = GPromptWindow(self.app)
        cfg.title(tr("🎯 Optimizador en bucle"))
        cfg.geometry("460x360")
        cfg.transient(self.app)
        cfg.grab_set()

        ctk.CTkLabel(cfg, text=tr("🎯 Optimizador en bucle"),
                     font=ctk.CTkFont(size=P.FUENTE_TITULO, weight="bold")).pack(pady=(16, 4))
        ctk.CTkLabel(cfg,
                     text=tr("Puntúa el prompt, lo mejora atacando sus puntos débiles,\n"
                          "y repite hasta alcanzar el objetivo. Conserva la mejor versión."),
                     font=ctk.CTkFont(size=P.FUENTE_PEQUENA), text_color=c["muted_text"],
                     justify="center").pack(pady=(0, 14))

        objetivo_var = ctk.IntVar(value=85)
        lbl_obj = ctk.CTkLabel(cfg, text=tr("Score objetivo: 85/100"),
                               font=ctk.CTkFont(size=P.FUENTE_SECCION, weight="bold"))
        lbl_obj.pack()
        sl_obj = ctk.CTkSlider(cfg, from_=60, to=95, number_of_steps=7,
                               variable=objetivo_var,
                               command=lambda v: lbl_obj.configure(
                                   text=tr('Score objetivo: {0}/100').format(int(v))))
        sl_obj.pack(fill="x", padx=40, pady=(2, 12))

        iter_var = ctk.IntVar(value=3)
        lbl_iter = ctk.CTkLabel(cfg, text=tr("Iteraciones máx: 3"),
                                font=ctk.CTkFont(size=P.FUENTE_SECCION, weight="bold"))
        lbl_iter.pack()
        sl_iter = ctk.CTkSlider(cfg, from_=1, to=5, number_of_steps=4,
                                variable=iter_var,
                                command=lambda v: lbl_iter.configure(
                                    text=tr('Iteraciones máx: {0}').format(int(v))))
        sl_iter.pack(fill="x", padx=40, pady=(2, 8))

        lbl_coste = ctk.CTkLabel(cfg, text="",
                                 font=ctk.CTkFont(size=P.FUENTE_HINT, slant="italic"),
                                 text_color=c["muted_text"])
        lbl_coste.pack(pady=(0, 10))

        def _actualizar_coste(*_a):
            n = int(iter_var.get())
            lbl_coste.configure(
                text=tr('Máximo {0} llamadas al LLM (1 scoring inicial + 2 por iteración)').format(1 + 2 * n))
        _actualizar_coste()
        sl_iter.configure(command=lambda v: (lbl_iter.configure(
            text=tr('Iteraciones máx: {0}').format(int(v))), _actualizar_coste()))

        btn_row = ctk.CTkFrame(cfg, fg_color="transparent")
        btn_row.pack(side="bottom", pady=(0, 16))
        ctk.CTkButton(btn_row, text=tr("▶ Optimizar"), width=150, height=34,
                      fg_color=P.BTN_EXITO, hover_color=P.BTN_EXITO_HOVER,
                      font=ctk.CTkFont(size=P.FUENTE_SECCION, weight="bold"),
                      command=lambda: _lanzar()).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text=tr("Cancelar"), width=100, height=34,
                      fg_color=c["fg_dark"], hover_color=c["fg_dark_hover"],
                      command=cfg.destroy).pack(side="left", padx=4)

        def _lanzar():
            objetivo = int(objetivo_var.get())
            max_iter = int(iter_var.get())
            cfg.destroy()
            self._optimizar_loop_ejecutar(actual, objetivo, max_iter)

        cfg.bind("<Return>", lambda _e: _lanzar())

    def _optimizar_loop_ejecutar(self, texto_inicial: str, objetivo: int,
                                 max_iter: int) -> None:
        """Ventana de progreso + worker del bucle de optimización."""
        is_lt = ctk.get_appearance_mode().lower() == "light"
        try:
            from config import get_theme_colors
            c = get_theme_colors(is_lt)
        except Exception:
            c = {"panel_text": "#111827" if is_lt else "#e5e7eb",
                 "muted_text": "#4b5563" if is_lt else "#9ca3af",
                 "card_bg": "#ffffff" if is_lt else "#111820",
                 "card_border": "#d1d5db" if is_lt else "#1f2937",
                 "fg_dark": "#e5e7eb" if is_lt else "#2b2b2b",
                 "fg_dark_hover": "#d1d5db" if is_lt else "#3a3a3a"}

        vent = GPromptWindow(self.app)
        vent.title(tr("🎯 Optimizando…"))
        vent.geometry("680x560")
        vent.transient(self.app)

        ctk.CTkLabel(vent, text=tr('🎯 Optimizando hacia {0}/100 (máx {1} iteraciones)').format((objetivo), (max_iter)),
                     font=ctk.CTkFont(size=P.FUENTE_SECCION, weight="bold")).pack(pady=(12, 6))

        progreso_frame = ctk.CTkScrollableFrame(vent, fg_color="transparent", height=160)
        progreso_frame.pack(fill="x", padx=16, pady=(0, 6))

        resultado_box = ctk.CTkTextbox(vent, wrap="word", font=ctk.CTkFont(size=P.FUENTE_CUERPO))
        resultado_box.pack(fill="both", expand=True, padx=16, pady=(0, 6))
        resultado_box.insert("1.0", texto_inicial)

        estado_lbl = ctk.CTkLabel(vent, text=tr("⏳ Puntuando prompt inicial…"),
                                  font=ctk.CTkFont(size=P.FUENTE_CUERPO),
                                  text_color=c["muted_text"])
        estado_lbl.pack(pady=(0, 4))

        btn_row = ctk.CTkFrame(vent, fg_color="transparent")
        btn_row.pack(pady=(0, 12))

        cancelar = {"v": False}

        def _detener():
            cancelar["v"] = True
            estado_lbl.configure(text=tr("⏹ Deteniendo tras la llamada en curso…"))

        btn_detener = ctk.CTkButton(btn_row, text=tr("⏹ Detener"), width=110, height=30,
                                    fg_color="#b45309", hover_color="#92400e",
                                    command=_detener)
        btn_detener.pack(side="left", padx=4)

        btn_aplicar = ctk.CTkButton(btn_row, text=tr("✅ Aplicar mejor versión"),
                                    width=180, height=30,
                                    fg_color=P.BTN_EXITO, hover_color=P.BTN_EXITO_HOVER,
                                    state="disabled")
        btn_aplicar.pack(side="left", padx=4)

        btn_diff = ctk.CTkButton(btn_row, text=tr("🆚 Ver diff"), width=100, height=30,
                                 fg_color="#1a4a7a", hover_color="#143a5f",
                                 state="disabled")
        btn_diff.pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text=tr("Cerrar"), width=90, height=30,
                      fg_color=c["fg_dark"], hover_color=c["fg_dark_hover"],
                      command=vent.destroy).pack(side="left", padx=4)

        def _fila_progreso(iteracion: int, score: float, texto: str):
            etiqueta = tr("Original") if iteracion == 0 else tr("Iteración {0}").format(iteracion)
            color = color_para_score(int(score), 100)
            row = ctk.CTkFrame(progreso_frame, fg_color="transparent")
            row.pack(fill="x", pady=1)
            ctk.CTkLabel(row, text=f"{etiqueta}:", width=110, anchor="w",
                         font=ctk.CTkFont(size=P.FUENTE_CUERPO, weight="bold")).pack(side="left", padx=(4, 6))
            try:
                bar = ctk.CTkProgressBar(row, width=300, height=12, progress_color=color)
                bar.set(min(score / 100.0, 1.0))
                bar.pack(side="left", padx=4)
            except Exception as _e:
                logger.debug(f"[silent] {_e}")
            ctk.CTkLabel(row, text=f"{int(score)}/100",
                         font=ctk.CTkFont(size=P.FUENTE_CUERPO, weight="bold"),
                         text_color=color, width=60).pack(side="left", padx=4)
            # El textbox muestra siempre la última versión generada
            resultado_box.delete("1.0", "end")
            resultado_box.insert("1.0", texto)

        def _on_progreso(iteracion, score, texto):
            self.app.after(0, lambda: _fila_progreso(iteracion, score, texto))
            if iteracion < max_iter:
                self.app.after(0, lambda: estado_lbl.configure(
                    text=tr('⏳ Iteración {0}: mejorando y re-puntuando…').format(iteracion + 1)))

        # Specs del modelo activo: el bucle puntúa y mejora PARA el
        # modelo destino (formato, max_chars, fortalezas). Sesión 19.
        modelo_info = self._contexto_modelo_activo()

        def _puntuar(texto):
            if cancelar["v"]:
                return None, "", ""
            resp = self.app.deepseek.generar_batch(
                self._OPTIMIZADOR_SYSTEM_SCORING,
                construir_peticion_scoring(texto, modelo_info),
                temperature=0.3, max_tokens=2000)
            parsed = parsear_scoring(limpiar_marcadores(resp))
            if not parsed["total"] or parsed["total"][1] <= 0:
                return None, parsed["debiles"], parsed["sugerencia"]
            val, maxv = parsed["total"]
            return (val / maxv) * 100, parsed["debiles"], parsed["sugerencia"]

        def _mejorar(texto, debiles, sugerencia):
            if cancelar["v"]:
                return ""
            resp = self.app.deepseek.generar_batch(
                self._OPTIMIZADOR_SYSTEM_MEJORA,
                construir_peticion_mejora(texto, debiles, sugerencia, modelo_info),
                temperature=0.5, max_tokens=2000)
            # Reconstruir POSITIVE PROMPT: si el LLM la peló
            return asegurar_etiquetas_prompt(texto, limpiar_marcadores(resp))

        def _worker():
            try:
                r = ejecutar_loop_optimizacion(
                    texto_inicial, _puntuar, _mejorar,
                    score_objetivo=objetivo, max_iteraciones=max_iter,
                    on_progreso=_on_progreso)

                def _finalizar():
                    btn_detener.configure(state="disabled")
                    if r.get("error"):
                        estado_lbl.configure(
                            text=f"❌ {r['error']}", text_color=P.TXT_ERROR)
                        return
                    mejor = r["mejor"]
                    resultado_box.delete("1.0", "end")
                    resultado_box.insert("1.0", mejor["texto"])
                    if cancelar["v"]:
                        resumen = tr("⏹ Detenido — mejor versión: {0}/100").format(int(mejor['score']))
                    elif r["alcanzado"]:
                        resumen = tr("🎯 Objetivo alcanzado: {0}/100 en {1} iteración(es)").format(int(mejor['score']), r['iteraciones'])
                    else:
                        resumen = tr("⏱ Máximo de iteraciones — mejor versión: {0}/100 (iteración {1})").format(int(mejor['score']), mejor['iteracion'])
                    estado_lbl.configure(text=resumen, text_color=c["panel_text"])
                    vent.title(tr("🎯 Optimizador — resultado"))

                    hubo_cambio = mejor["texto"].strip() != texto_inicial.strip()

                    def _ver_diff():
                        try:
                            self.app._abrir_ventana_diff(
                                texto_inicial, mejor["texto"],
                                tr("Original"),
                                tr("Optimizada ({0}/100)").format(int(mejor['score'])))
                        except Exception as e:
                            self.app.dialogs.set_estado(tr('❌ Error abriendo diff: {0}').format(e), P.TXT_ERROR)
                    if hubo_cambio:
                        btn_diff.configure(state="normal", command=_ver_diff)

                    def _aplicar():
                        # Registrar versiones para 📑 Versiones y 📊 Diff:
                        # la original queda como rollback y ambas entran en
                        # la pila de regeneración (antes el diff exigía
                        # pulsar 🔄 Regenerar para tener 2 versiones).
                        try:
                            self.app._guardar_version_prompt()
                        except Exception as e:
                            logger.debug(f"[silent] versión pre-optimización: {e}")
                        try:
                            self.app._regen_push(texto_inicial)
                            self.app._regen_push(mejor["texto"])
                        except Exception as e:
                            logger.debug(f"[silent] regen push: {e}")
                        self.app.dialogs.actualizar_salida(mejor["texto"])
                        vent.destroy()
                        self.app.dialogs.set_estado(
                            tr('🎯 Prompt optimizado aplicado ({0}/100)').format(int(mejor['score'])), P.TXT_OK)
                    btn_aplicar.configure(state="normal", command=_aplicar)

                self.app.after(0, _finalizar)
            except Exception as e:
                self.app.after(0, lambda e=e: estado_lbl.configure(
                    text=tr('❌ Error: {0}').format(e), text_color=P.TXT_ERROR))
                self.app.after(0, lambda: btn_detener.configure(state="disabled"))

        self.app._executor.submit(_worker).add_done_callback(log_future_exc)

    def _cmd_coste_sesion(self) -> None:
        """Muestra el coste estimado de la sesión por proveedor.

        Los tokens se acumulan en api_clients.usage_tracker cada vez que
        un provider completa una llamada. Coste = tokens × precio del modelo
        usado (PRECIOS_USD_1M_MODELO prioriza sobre el precio por proveedor;
        tabla junio 2026). Proveedores gratuitos/locales = 0; OpenRouter = "—".
        """
        from api_clients import LLM_PROVIDERS, coste_dia_usd, usage_tracker

        try: self.app._sesion_log("💰 Abrió Coste de sesión")
        except Exception as e:
            logger.debug(f"[silent] {e}")

        # Volcar el uso pendiente al histórico para que la sección
        # "Histórico" incluya también lo consumido en esta sesión.
        try:
            self.app.data._persistir_uso_api()
        except Exception as e:
            logger.debug(f"[silent] {e}")

        is_lt = ctk.get_appearance_mode().lower() == "light"
        try:
            from config import get_theme_colors
            c = get_theme_colors(is_lt)
        except Exception:
            c = {"panel_text": "#111827" if is_lt else "#e5e7eb",
                 "muted_text": "#4b5563" if is_lt else "#9ca3af",
                 "card_bg": "#ffffff" if is_lt else "#111820",
                 "fg_dark": "#e5e7eb" if is_lt else "#2b2b2b",
                 "fg_dark_hover": "#d1d5db" if is_lt else "#3a3a3a"}

        vent = GPromptWindow(self.app)
        vent.title(tr("💰 Coste de sesión"))
        vent.geometry("620x440")
        vent.transient(self.app)

        ctk.CTkLabel(vent, text=tr("💰 Coste estimado de esta sesión"),
                     font=ctk.CTkFont(size=P.FUENTE_TITULO, weight="bold")).pack(pady=(14, 2))
        ctk.CTkLabel(vent,
                     text=tr("Tokens reales reportados por cada API × precio del modelo usado."),
                     font=ctk.CTkFont(size=P.FUENTE_PEQUENA), text_color=c["muted_text"]).pack(pady=(0, 10))

        cuerpo = ctk.CTkScrollableFrame(vent, fg_color="transparent")
        cuerpo.pack(fill="both", expand=True, padx=16, pady=(0, 6))

        lbl_total = ctk.CTkLabel(vent, text="",
                                 font=ctk.CTkFont(size=P.FUENTE_TITULO, weight="bold"))
        lbl_total.pack(pady=(0, 2))

        ctk.CTkLabel(vent,
                     text=tr("Estimación orientativa (precios junio 2026, por modelo usado)."),
                     font=ctk.CTkFont(size=P.FUENTE_HINT, slant="italic"),
                     text_color=c["muted_text"]).pack(pady=(0, 4))

        def _render():
            for w in cuerpo.winfo_children():
                w.destroy()
            datos = usage_tracker.resumen()
            if not datos:
                ctk.CTkLabel(cuerpo,
                             text=tr("Aún no hay llamadas LLM en esta sesión."),
                             font=ctk.CTkFont(size=P.FUENTE_CUERPO),
                             text_color=c["muted_text"]).pack(pady=20)
                lbl_total.configure(text=tr("Total estimado: 0.0000 $"))
            else:
                # Cabecera
                head = ctk.CTkFrame(cuerpo, fg_color="transparent")
                head.pack(fill="x", pady=(0, 4))
                for texto, ancho in ((tr("Proveedor"), 160), (tr("Llamadas"), 70),
                                     (tr("Tokens entrada"), 110), (tr("Tokens salida"), 110),
                                     (tr("Coste"), 80)):
                    ctk.CTkLabel(head, text=texto, width=ancho, anchor="w",
                                 font=ctk.CTkFont(size=P.FUENTE_PEQUENA, weight="bold"),
                                 text_color=c["muted_text"]).pack(side="left", padx=2)
                # Filas
                for pid in sorted(datos.keys()):
                    d = datos[pid]
                    nombre = LLM_PROVIDERS.get(pid, {}).get("name", pid)
                    coste = d["coste_usd"]
                    coste_txt = "—" if coste is None else f"{coste:.4f} $"
                    row = ctk.CTkFrame(cuerpo, fg_color=c.get("card_bg", "transparent"),
                                       corner_radius=6)
                    row.pack(fill="x", pady=1)
                    for texto, ancho in ((nombre, 160), (str(d["llamadas"]), 70),
                                         (f"{d['tokens_entrada']:,}", 110),
                                         (f"{d['tokens_salida']:,}", 110),
                                         (coste_txt, 80)):
                        ctk.CTkLabel(row, text=texto, width=ancho, anchor="w",
                                     font=ctk.CTkFont(size=P.FUENTE_CUERPO),
                                     text_color=c["panel_text"]).pack(side="left", padx=2, pady=3)
                lbl_total.configure(text=tr('Total estimado: {0:.4f} $').format(usage_tracker.total_usd()))

            # ── Histórico persistente (últimos 14 días) ──
            try:
                historico = self.app.store.cargar_preferencias().get("uso_api_historico", {})
            except Exception:
                historico = {}
            if isinstance(historico, dict) and historico:
                ctk.CTkLabel(cuerpo, text=tr("📅 Histórico (últimos 14 días)"),
                             font=ctk.CTkFont(size=P.FUENTE_SECCION, weight="bold"),
                             text_color=c["panel_text"]).pack(anchor="w", pady=(14, 4))
                head_h = ctk.CTkFrame(cuerpo, fg_color="transparent")
                head_h.pack(fill="x", pady=(0, 4))
                for texto, ancho in ((tr("Fecha"), 110), (tr("Llamadas"), 70),
                                     (tr("Tokens entrada"), 110), (tr("Tokens salida"), 110),
                                     (tr("Coste/día"), 80)):
                    ctk.CTkLabel(head_h, text=texto, width=ancho, anchor="w",
                                 font=ctk.CTkFont(size=P.FUENTE_PEQUENA, weight="bold"),
                                 text_color=c["muted_text"]).pack(side="left", padx=2)
                total_periodo = 0.0
                for fecha in sorted(historico.keys(), reverse=True)[:14]:
                    dia = historico[fecha]
                    if not isinstance(dia, dict):
                        continue
                    llam = sum(d.get("llamadas", 0) for d in dia.values())
                    t_in = sum(d.get("tokens_entrada", 0) for d in dia.values())
                    t_out = sum(d.get("tokens_salida", 0) for d in dia.values())
                    coste = coste_dia_usd(dia)
                    total_periodo += coste
                    row = ctk.CTkFrame(cuerpo, fg_color="transparent")
                    row.pack(fill="x", pady=1)
                    for texto, ancho in ((fecha, 110), (str(llam), 70),
                                         (f"{t_in:,}", 110), (f"{t_out:,}", 110),
                                         (f"{coste:.4f} $", 80)):
                        ctk.CTkLabel(row, text=texto, width=ancho, anchor="w",
                                     font=ctk.CTkFont(size=P.FUENTE_CUERPO),
                                     text_color=c["muted_text"]).pack(side="left", padx=2, pady=2)
                ctk.CTkLabel(cuerpo,
                             text=tr('Total del periodo mostrado: {0:.4f} $').format(total_periodo),
                             font=ctk.CTkFont(size=P.FUENTE_CUERPO, weight="bold"),
                             text_color=c["panel_text"]).pack(anchor="w", pady=(4, 2))

        _render()

        btn_row = ctk.CTkFrame(vent, fg_color="transparent")
        btn_row.pack(pady=(0, 12))
        ctk.CTkButton(btn_row, text=tr("🔄 Actualizar"), width=110, height=30,
                      command=_render).pack(side="left", padx=4)

        def _resetear():
            usage_tracker.reset()
            _render()
        ctk.CTkButton(btn_row, text=tr("🗑 Resetear contador"), width=150, height=30,
                      fg_color="#b45309", hover_color="#92400e",
                      command=_resetear).pack(side="left", padx=4)
        ctk.CTkButton(btn_row, text=tr("Cerrar"), width=90, height=30,
                      fg_color=c["fg_dark"], hover_color=c["fg_dark_hover"],
                      command=vent.destroy).pack(side="left", padx=4)

    def _detectar_nsfw_auto(self, idea: str | None = None) -> bool:
        """Detecta si el prompt actual tiene elementos NSFW y avisa."""
        texto = idea if idea else self.app.txt_salida.get("1.0", "end").strip()
        actual = texto.lower()
        nsfw_terms = ["nude", "naked", "nsfw", "explicit", "xxx", "porn", "sex", "boobs", "butt", "ass"]
        if any(term in actual for term in nsfw_terms):
            if hasattr(self.app, 'nsfw_var'):
                self.app.nsfw_var.set(True)
            self.app.dialogs.set_estado(tr("⚠️ Contenido NSFW detectado — activado modo NSFW"), P.TXT_ERROR)

    def _guardar_seed_favorito(self) -> None:
        """Guarda la configuración actual como seed favorito."""
        from tkinter import simpledialog
        prefs = self.app.store.cargar_preferencias()
        seeds = prefs.get("seeds_favoritos", [])

        # Pedir nombre
        nombre = simpledialog.askstring(tr("💎 Guardar Seed"), tr("Nombre para este seed:"), parent=self.app)
        if not nombre:
            return

        seed = {
            "nombre": nombre,
            "estilos": list(self.app.footer.estilos_seleccionados()),
            "plataforma": self.app.plataforma_var.get() if hasattr(self.app, 'plataforma_var') else "",
            "modelo_img": self.app.modelo_img_var.get() if hasattr(self.app, 'modelo_img_var') else "",
            "modelo_vid": self.app.modelo_vid_var.get() if hasattr(self.app, 'modelo_vid_var') else "",
            "ratio": self.app.ratio_var.get() if hasattr(self.app, 'ratio_var') else "",
        }
        seeds.append(seed)
        prefs["seeds_favoritos"] = seeds
        self.app.store.guardar_preferencias(prefs)
        self.app.dialogs.set_estado(tr("💎 Seed '{0}' guardado").format(nombre), P.TXT_OK)

    def _abrir_seeds_favoritos(self) -> None:
        """Ventana con seeds favoritos para aplicar. Refresca sin cerrar al borrar."""
        from tkinter import messagebox
        is_lt = ctk.get_appearance_mode().lower() == "light"
        from config import get_theme_colors
        c = get_theme_colors(is_lt)

        vent = GPromptWindow(self.app)
        vent.title(tr("💎 Seeds favoritos"))
        vent.geometry("580x500")
        vent.transient(self.app)

        ctk.CTkLabel(vent, text=tr("💎 Seeds favoritos"),
                     font=ctk.CTkFont(size=P.FUENTE_TITULO, weight="bold")).pack(pady=(10, 5))
        ctk.CTkLabel(vent, text=tr("Guarda tu configuración y recupérala rápido"),
                     font=ctk.CTkFont(size=P.FUENTE_PEQUENA),
                     text_color=c["muted_text"]).pack(pady=(0, 4))

        # Buscador
        search_row = ctk.CTkFrame(vent, fg_color="transparent")
        search_row.pack(fill="x", padx=15, pady=(0, 4))
        ctk.CTkLabel(search_row, text="🔍").pack(side="left", padx=(0, 6))
        entry_buscar = ctk.CTkEntry(search_row,
                                    placeholder_text=tr("Buscar por nombre, modelo o plataforma…"),
                                    height=28)
        entry_buscar.pack(side="left", fill="x", expand=True)
        busqueda_pending = {"after_id": None}
        def _on_buscar(_e=None):
            if busqueda_pending["after_id"]:
                try: vent.after_cancel(busqueda_pending["after_id"])
                except Exception as _e2: logger.debug(f"[silent] {_e2}")
            busqueda_pending["after_id"] = vent.after(200, _refrescar)
        entry_buscar.bind("<KeyRelease>", _on_buscar)
        ctk.CTkButton(search_row, text="✕", width=32, height=28,
                      fg_color=P.BTN_NEUTRO, hover_color=P.BTN_NEUTRO_HOVER,
                      command=lambda: (entry_buscar.delete(0, "end"), _refrescar())
                      ).pack(side="left", padx=(6, 0))

        scroll = ctk.CTkScrollableFrame(vent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=15, pady=5)

        def _refrescar():
            for w in scroll.winfo_children():
                w.destroy()
            prefs = self.app.store.cargar_preferencias()
            seeds = prefs.get("seeds_favoritos", [])
            termino = entry_buscar.get().strip().lower()

            # Filtrar por término
            visibles = []
            for i, seed in enumerate(seeds):
                if termino:
                    text = " ".join([
                        seed.get("nombre", ""),
                        seed.get("modelo_img", ""),
                        seed.get("modelo_vid", ""),
                        seed.get("plataforma", ""),
                    ]).lower()
                    if termino not in text:
                        continue
                visibles.append((i, seed))

            if not visibles:
                msg = (tr("Sin resultados para '{0}'").format(termino) if termino
                       else tr("(sin seeds guardados — pulsa '+ Crear nuevo seed')"))
                ctk.CTkLabel(scroll, text=msg,
                             text_color=c["muted_text"]).pack(pady=30)
                return

            for i, seed in visibles:
                card = ctk.CTkFrame(scroll, fg_color=c["fg_frame"], corner_radius=8)
                card.pack(fill="x", pady=4, padx=2)
                ctk.CTkLabel(card, text=f"💎 {seed.get('nombre', '?')}",
                             font=ctk.CTkFont(size=P.FUENTE_SECCION, weight="bold"),
                             text_color=c["hdr_text"]).pack(anchor="w", padx=12, pady=(8, 2))

                modelo = seed.get('modelo_img') or seed.get('modelo_vid') or '?'
                ratio = seed.get('ratio') or ''
                plataforma = seed.get('plataforma') or ''
                estilos_seed = seed.get('estilos', [])
                if isinstance(estilos_seed, list):
                    estilos_txt = ', '.join(estilos_seed[:4]) or tr('Sin estilos')
                else:
                    estilos_txt = str(estilos_seed) or tr('Sin estilos')

                info = f"📱 {modelo}"
                if ratio: info += f" | 📐 {ratio}"
                if plataforma: info += f" | 🌐 {plataforma}"
                ctk.CTkLabel(card, text=info, font=ctk.CTkFont(size=P.FUENTE_PEQUENA),
                             text_color=c["muted_text"]).pack(anchor="w", padx=12)
                ctk.CTkLabel(card, text=f"🎨 {estilos_txt}",
                             font=ctk.CTkFont(size=P.FUENTE_HINT),
                             text_color=c["muted_text"]
                             ).pack(anchor="w", padx=12, pady=(2, 6))

                btn_frame = ctk.CTkFrame(card, fg_color="transparent")
                btn_frame.pack(anchor="e", padx=10, pady=(0, 6))

                def _aplicar(s=seed):
                    self._aplicar_seed(s)
                    vent.destroy()  # OK: tras aplicar tiene sentido cerrar

                def _borrar(idx=i, nombre=seed.get('nombre', '?')):
                    if not messagebox.askyesno(tr("Borrar Seed"),
                                               tr("¿Borrar el seed '{0}'?").format(nombre),
                                               parent=vent):
                        return
                    prefs_b = self.app.store.cargar_preferencias()
                    seeds_act = prefs_b.get("seeds_favoritos", [])
                    if 0 <= idx < len(seeds_act):
                        seeds_act.pop(idx)
                        prefs_b["seeds_favoritos"] = seeds_act
                        self.app.store.guardar_preferencias(prefs_b)
                    _refrescar()  # FIX: antes vent.destroy() cerraba la ventana
                    self.app.dialogs.set_estado(tr("💎 Seed '{0}' eliminado").format(nombre), P.TXT_AVISO)

                ctk.CTkButton(btn_frame, text=tr("✅ Aplicar"), width=90, height=26,
                              fg_color=P.BTN_EXITO, font=ctk.CTkFont(size=P.FUENTE_PEQUENA),
                              command=_aplicar).pack(side="left", padx=3)
                ctk.CTkButton(btn_frame, text=tr("🗑 Borrar"), width=80, height=26,
                              fg_color="#8b2020", font=ctk.CTkFont(size=P.FUENTE_PEQUENA),
                              command=_borrar).pack(side="left", padx=3)

        _refrescar()

        ctk.CTkButton(vent, text=tr("➕ Crear nuevo seed"), width=180, height=28,
                      fg_color="#1a5a8a",
                      command=lambda: (self._guardar_seed_favorito(),
                                       vent.after(300, _refrescar))
                      ).pack(pady=(5, 12))

    def _aplicar_seed(self, seed) -> None:
        """Aplica una configuración guardada como seed."""
        mensajes = []
        aplicado = False

        # Cargar plataforma PRIMERO (esto recarga los modelos disponibles para esa plataforma)
        if seed.get("plataforma") and hasattr(self.app, 'combo_plataforma'):
            valores_plat = list(self.app.combo_plataforma.cget("values") or [])
            if seed["plataforma"] in valores_plat:
                self.app.plataforma_var.set(seed["plataforma"])
                if hasattr(self.app, '_on_plataforma_cambio'):
                    try: self.app.events.on_plataforma_cambio()
                    except Exception: pass
                aplicado = True

        # Ahora que la plataforma está puesta, cargar el modelo de imagen
        if seed.get("modelo_img") and hasattr(self.app, 'combo_modelo_imagen'):
            valores_modelo = list(self.app.combo_modelo_imagen.cget("values") or [])
            if seed["modelo_img"] in valores_modelo:
                self.app.modelo_img_var.set(seed["modelo_img"])
                if hasattr(self.app, '_on_modelo_imagen_cambio'):
                    try: self.app.events.on_modelo_imagen_cambio()
                    except Exception: pass
                aplicado = True
            elif seed["modelo_img"]:
                mensajes.append(f"Modelo '{seed['modelo_img']}' no disponible")

        # Cargar modelo video — FIX: el widget se llama combo_modelo_video
        # (no combo_modelo_vid), por lo que esta rama NUNCA se ejecutaba.
        if seed.get("modelo_vid") and hasattr(self.app, 'combo_modelo_video'):
            valores_vid = list(self.app.combo_modelo_video.cget("values") or [])
            if seed["modelo_vid"] in valores_vid:
                self.app.combo_modelo_video.set(seed["modelo_vid"])
                if hasattr(self.app, '_on_motor_cambio'):
                    try: self.app.events.on_motor_cambio(seed["modelo_vid"])
                    except Exception as _e: logger.debug(f"[silent] {_e}")
                aplicado = True
            elif seed["modelo_vid"]:
                mensajes.append(tr("Modelo vídeo '{0}' no disponible").format(seed['modelo_vid']))

        # Cargar ratio
        if seed.get("ratio") and hasattr(self.app, 'combo_ratio'):
            valores_ratio = list(self.app.combo_ratio.cget("values") or [])
            if seed["ratio"] in valores_ratio:
                self.app.ratio_var.set(seed["ratio"])
                aplicado = True
            elif seed["ratio"]:
                mensajes.append(f"Ratio '{seed['ratio']}' no disponible")

        # Cargar estilos
        if seed.get("estilos") and hasattr(self.app, 'estilo_checks'):
            for nombre, var in self.app.estilo_checks.items():
                var.set(nombre in seed["estilos"])
            aplicado = True

        if aplicado:
            nombre = seed.get('nombre', '?')
            self.app.dialogs.set_estado(tr("💎 Seed '{0}' aplicado").format(nombre), P.TXT_OK)
            if mensajes:
                self.app.dialogs.set_estado(tr('⚠️ {0}').format(', '.join(mensajes)), P.TXT_AVISO)
        else:
            self.app.dialogs.set_estado(tr('⚠️ Seed no pudo aplicarse'), P.TXT_AVISO)

    def _autocompletar_tags(self, event=None) -> None:
        """Auto-completar tags mientras escribe."""
        texto = self.app.txt_salida.get("1.0", "end").strip()
        if not texto:
            return
        # Sugerir tags comunes basados en lo que escribe
        tag_sugerencias = {
            "master": "masterpiece", "best": "best quality", "ultra": "ultra detailed",
            "8k": "8K resolution", "hd": "HD", "photo": "photorealistic",
            "real": "realistic", "cinema": "cinematic lighting", "dof": "depth of field",
            "bokeh": "bokeh", "soft": "soft lighting", "dramatic": "dramatic lighting",
        }
        palabras = texto.lower().split()
        for palabra, tag in tag_sugerencias.items():
            if palabra in texto and tag not in texto:
                pass  # Podría sugerir pero no es crítico

    def _abrir_atajos_tags(self) -> None:
        """Ventana para gestionar atajos de tags (snippets)."""
        prefs = self.app.store.cargar_preferencias()
        atajos = prefs.get("atajos_tags", [])

        vent = GPromptWindow(self.app)
        vent.title(tr("🏷️ Atajos de tags"))
        vent.geometry("600x450")
        vent.transient(self.app)

        ctk.CTkLabel(vent, text=tr("🏷️ Atajos de tags (snippets)"), font=ctk.CTkFont(size=P.FUENTE_TITULO, weight="bold")).pack(pady=(10, 3))
        ctk.CTkLabel(vent, text=tr("Atajos rápidos para insertar tags comunes"),
                     font=ctk.CTkFont(size=P.FUENTE_PEQUENA), text_color=P.TXT_MUTED).pack(pady=(0, 8))

        scroll = ctk.CTkScrollableFrame(vent, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=15, pady=5)

        def refrescar():
            for w in scroll.winfo_children(): w.destroy()
            for i, atajo in enumerate(atajos):
                card = ctk.CTkFrame(scroll, fg_color="#111820", corner_radius=8)
                card.pack(fill="x", pady=3)
                ctk.CTkLabel(card, text=atajo.get("nombre", "?"), font=ctk.CTkFont(size=P.FUENTE_CUERPO, weight="bold"),
                             text_color="#aaccee").pack(anchor="w", padx=10, pady=(6, 2))
                ctk.CTkLabel(card, text=atajo.get("tags", ""), font=ctk.CTkFont(size=P.FUENTE_HINT),
                             text_color=P.TXT_MUTED, wraplength=500).pack(anchor="w", padx=10, pady=(0, 4))
                def _aplicar(tags=atajo.get("tags", "")):
                    self.app._aplicar_atajo_tags(tags)
                    vent.destroy()
                def _borrar(idx=i):
                    atajos.pop(idx)
                    prefs["atajos_tags"] = atajos
                    self.app.store.guardar_preferencias(prefs)
                    refrescar()
                btn_frame = ctk.CTkFrame(card, fg_color="transparent")
                btn_frame.pack(anchor="e", padx=8, pady=(0, 4))
                ctk.CTkButton(btn_frame, text=tr("✅ Aplicar"), width=80, height=22, fg_color=P.BTN_EXITO,
                              font=ctk.CTkFont(size=P.FUENTE_HINT), command=_aplicar).pack(side="left", padx=2)
                ctk.CTkButton(btn_frame, text="🗑", width=24, height=22, fg_color="#c0392b",
                              font=ctk.CTkFont(size=P.FUENTE_HINT), command=_borrar).pack(side="left", padx=2)

        def crear():
            vent_add = GPromptWindow(vent)
            vent_add.title(tr("➕ Nuevo atajo"))
            vent_add.geometry("400x250")
            vent_add.transient(vent)
            ctk.CTkLabel(vent_add, text=tr("Nombre:")).pack(anchor="w", padx=15, pady=(10, 2))
            ent_nombre = ctk.CTkEntry(vent_add, width=350)
            ent_nombre.pack(anchor="w", padx=15)
            ctk.CTkLabel(vent_add, text=tr("Tags:")).pack(anchor="w", padx=15, pady=(10, 2))
            ent_tags = ctk.CTkEntry(vent_add, width=350)
            ent_tags.pack(anchor="w", padx=15)
            def _guardar():
                nombre = ent_nombre.get().strip()
                tags = ent_tags.get().strip()
                if nombre and tags:
                    atajos.append({"nombre": nombre, "tags": tags})
                    prefs["atajos_tags"] = atajos
                    self.app.store.guardar_preferencias(prefs)
                    refrescar()
                    vent_add.destroy()
            ctk.CTkButton(vent_add, text=tr("Guardar"), width=120, height=28, fg_color=P.BTN_EXITO,
                          command=_guardar).pack(pady=15)

        def _copiar_ej():
            pyperclip.copy("masterpiece, best quality, ultra detailed, 8K resolution")
        def _usar_ej():
            self.app._aplicar_atajo_tags("masterpiece, best quality, ultra detailed, 8K resolution")
            vent.destroy()

        btn_frame = ctk.CTkFrame(vent, fg_color="transparent")
        btn_frame.pack(pady=8)
        ctk.CTkButton(btn_frame, text=tr("➕ Nuevo atajo"), width=140, height=28, fg_color=P.BTN_EXITO,
                      command=crear).pack(side="left", padx=4)
        ctk.CTkButton(btn_frame, text=tr("📋 Ejemplo: copiar"), width=160, height=28,
                      command=_copiar_ej).pack(side="left", padx=4)
        ctk.CTkButton(btn_frame, text=tr("✅ Ejemplo: usar"), width=140, height=28, fg_color=P.BTN_EXITO,
                      command=_usar_ej).pack(side="left", padx=4)

        refrescar()

    def _copiar_comfyui_json(self) -> None:
        """Crea y exporta un workflow ComfyUI adaptado al modelo activo.

        Usa comfy_workflow_params (config): CFG/pasos/sampler/scheduler por
        familia + arquitectura de carga correcta (CheckpointLoaderSimple para
        SDXL/SD1.5/Pony/Illustrious; UNETLoader + CLIPLoader + VAELoader para
        diffusion_models Flux/Qwen/Z-Image/Ideogram)."""
        actual = self.app.txt_salida.get("1.0", "end").strip()
        if not actual:
            return self.app.dialogs.set_estado(tr("⚠️ Genera un prompt primero."), P.TXT_AVISO)

        import json

        pos = self.app.extraer_positive() or actual
        neg = self.app.extraer_negative() or ""
        modelo = self.app.combo_modelo_imagen.get() if hasattr(self.app, 'combo_modelo_imagen') else ""
        lora = self._lora_activo_para_workflow()
        workflow = self._construir_workflow_comfy(pos, neg, modelo, lora)
        json_str = json.dumps(workflow, indent=2, ensure_ascii=False)
        self._mostrar_ventana_comfyui(json_str, modelo)

    def _lora_activo_para_workflow(self) -> str:
        """Nombre del LoRA primario seleccionado, o '' si no hay ninguno."""
        try:
            nombre = self.app.combo_lora.get() if hasattr(self.app, "combo_lora") else ""
            if nombre and nombre != tr("— Sin LoRA —"):
                return nombre
        except Exception:
            pass
        return ""

    # La construcción/serialización de workflows vive en modules/comfy_export
    # (módulo PURO, sin UI) para reutilizarla desde el dataset de avatar.
    # Aquí quedan delegadores retrocompat (tests y llamadas existentes).
    _COMFY_NODE_SLOTS = COMFY_NODE_SLOTS

    @classmethod
    def _construir_workflow_comfy(cls, pos: str, neg: str, modelo: str, lora: str = "") -> dict:
        """Delegador retrocompat — ver modules.comfy_export.construir_workflow_comfy."""
        from modules.comfy_export import construir_workflow_comfy
        return construir_workflow_comfy(pos, neg, modelo, lora)

    @classmethod
    def _serializar_workflow_ui(cls, abstractos: list, modelo: str, familia: str) -> dict:
        """Delegador retrocompat — ver modules.comfy_export.serializar_workflow_ui."""
        from modules.comfy_export import serializar_workflow_ui
        return serializar_workflow_ui(abstractos, modelo, familia)

    def _mostrar_ventana_comfyui(self, json_str: str, modelo: str) -> None:
        """Muestra el JSON en una ventana con opciones: Copiar / Pegar en ComfyUI / Guardar."""
        from config import get_theme_colors
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)

        vent = GPromptWindow(self.app)
        vent.title(tr("🔧 Workflow ComfyUI - G-Prompt Studio"))
        vent.geometry("750x550")
        vent.transient(self.app)

        marco = ctk.CTkFrame(vent, fg_color=c.get("tab_bg", "#f3f4f6" if is_lt else "#0f1318"))
        marco.pack(fill="both", expand=True, padx=10, pady=10)

        hdr = ctk.CTkFrame(marco, fg_color="transparent")
        hdr.pack(fill="x", pady=(0, 8))
        ctk.CTkLabel(hdr, text=tr("🔧 Workflow ComfyUI"), font=ctk.CTkFont(size=P.FUENTE_TITULO, weight="bold"),
                     text_color=c["hdr_text"]).pack(side="left")
        ctk.CTkLabel(hdr, text=tr('Modelo: {0}').format(modelo), font=ctk.CTkFont(size=P.FUENTE_CUERPO),
                     text_color=c.get("muted_text", "#888")).pack(side="right")

        info = ctk.CTkLabel(marco, text=tr("📋 Copia este JSON y pégalo en ComfyUI (Edit → Paste) o guarda como .json"),
                            font=ctk.CTkFont(size=P.FUENTE_PEQUENA), text_color=c.get("muted_text", "#888"))
        info.pack(anchor="w", pady=(0, 6))

        # Chuleta del modelo actual (CLIP/VAE/ajustes) — para rellenar los
        # nodos que ComfyUI deje en blanco si el fichero no coincide exacto.
        try:
            from config import comfy_workflow_params
            wp = comfy_workflow_params(modelo)
            if wp["arch"] == "unet":
                chuleta_txt = tr("🧩 CLIP: {0}   ·   VAE: {1}   ·   {2}/{3} · CFG {4} · {5} pasos").format(
                    wp.get("clip") or tr("(elígelo en ComfyUI)"),
                    wp.get("vae") or tr("(elígelo en ComfyUI)"),
                    wp["sampler"], wp["scheduler"], wp["cfg"], wp["steps"])
            else:
                chuleta_txt = tr("🧩 CLIP y VAE integrados en el checkpoint   ·   {0}/{1} · CFG {2} · {3} pasos").format(
                    wp["sampler"], wp["scheduler"], wp["cfg"], wp["steps"])
            ctk.CTkLabel(marco, text=chuleta_txt, font=ctk.CTkFont(size=P.FUENTE_PEQUENA, weight="bold"),
                         text_color=P.TXT_ACENTO, anchor="w").pack(anchor="w", pady=(0, 6))
        except Exception as _e:
            logger.debug(f"[silent chuleta] {_e}")

        txt = ctk.CTkTextbox(marco, wrap="none", font=ctk.CTkFont(family="Consolas", size=P.FUENTE_PEQUENA),
                             fg_color=c.get("entry_bg", "#1a1a2e" if not is_lt else "#ffffff"),
                             text_color=c.get("entry_text", "#e5e7eb" if not is_lt else "#111827"),
                             border_color=c.get("entry_border", "#3a3a5a"))
        txt.insert("1.0", json_str)
        txt.pack(fill="both", expand=True, pady=(0, 10))

        frame_btn = ctk.CTkFrame(marco, fg_color="transparent")
        frame_btn.pack(fill="x")

        def _copiar():
            pyperclip.copy(json_str)
            self.app.dialogs.set_estado(tr("📋 JSON copiado al portapapeles"), P.TXT_OK)

        def _guardar():
            from tkinter import filedialog
            ruta = filedialog.asksaveasfilename(
                title=tr("Guardar workflow ComfyUI"),
                defaultextension=".json",
                filetypes=[("JSON", "*.json"), (tr("Todos"), "*.*")],
                initialfile=f"gprompt_workflow_{modelo.replace(' ', '_')}.json"
            )
            if ruta:
                with open(ruta, "w", encoding="utf-8") as f:
                    f.write(json_str)
                self.app.dialogs.set_estado(tr('💾 Guardado: {0}').format(ruta.split('/')[-1]), P.TXT_OK)

        ctk.CTkButton(frame_btn, text=tr("📋 Copiar JSON"), width=120, fg_color=P.BTN_EXITO,
                      hover_color=P.BTN_EXITO_HOVER, command=_copiar).pack(side="left", padx=(0, 6))
        ctk.CTkButton(frame_btn, text=tr("💾 Guardar .json"), width=120, fg_color="#1e3a8a",
                      hover_color="#172554", command=_guardar).pack(side="left", padx=(0, 6))
        ctk.CTkButton(frame_btn, text=tr("🧩 Chuleta modelos"), width=150,
                      **P.estilo_boton(P.BTN_ACENTO),
                      command=self._mostrar_chuleta_comfy).pack(side="left", padx=(0, 6))
        ctk.CTkButton(frame_btn, text=tr("❌ Cerrar"), width=80, fg_color="#991b1b",
                      hover_color=P.BTN_PELIGRO_HOVER, command=vent.destroy).pack(side="right")

    def _mostrar_chuleta_comfy(self) -> None:
        """Ventana con la chuleta ComfyUI: cada modelo con su CLIP, VAE y
        ajustes de muestreo. Copiable / guardable como .txt."""
        from config import comfy_cheatsheet, get_theme_colors

        filas = comfy_cheatsheet()
        if not filas:
            return self.app.dialogs.set_estado(
                tr("⚠️ No hay modelos ComfyUI detectados (configura la ruta en Ajustes)."), P.TXT_AVISO)

        lineas = [tr("CHULETA ComfyUI — modelo · CLIP · VAE · ajustes"), "=" * 60, ""]
        fam_actual = None
        for f in filas:
            if f["familia"] != fam_actual:
                fam_actual = f["familia"]
                lineas.append(f"\n── {fam_actual.upper()} ──")
            lineas.append(f"• {f['modelo']}")
            lineas.append(f"    CLIP: {f['clip']}")
            lineas.append(f"    VAE:  {f['vae']}")
            lineas.append(f"    {f['ajustes']}")
        texto = "\n".join(lineas)

        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)
        vent = GPromptWindow(self.app)
        vent.title(tr("🧩 Chuleta ComfyUI"))
        vent.geometry("640x560")
        vent.transient(self.app)
        marco = ctk.CTkFrame(vent, fg_color=c.get("tab_bg", "#f3f4f6" if is_lt else "#0f1318"))
        marco.pack(fill="both", expand=True, padx=10, pady=10)
        ctk.CTkLabel(marco, text=tr("🧩 Chuleta ComfyUI"),
                     font=ctk.CTkFont(size=P.FUENTE_TITULO, weight="bold"),
                     text_color=c["hdr_text"]).pack(anchor="w", pady=(0, 6))
        txt = ctk.CTkTextbox(marco, wrap="none",
                             font=ctk.CTkFont(family="Consolas", size=P.FUENTE_PEQUENA),
                             fg_color=c.get("entry_bg", "#1a1a2e" if not is_lt else "#ffffff"),
                             text_color=c.get("entry_text", "#e5e7eb" if not is_lt else "#111827"))
        txt.insert("1.0", texto)
        txt.pack(fill="both", expand=True, pady=(0, 10))
        fila = ctk.CTkFrame(marco, fg_color="transparent")
        fila.pack(fill="x")

        def _copiar():
            pyperclip.copy(texto)
            self.app.dialogs.set_estado(tr("📋 Chuleta copiada al portapapeles"), P.TXT_OK)

        def _guardar():
            from tkinter import filedialog
            ruta = filedialog.asksaveasfilename(
                title=tr("Guardar chuleta"), defaultextension=".txt",
                filetypes=[("TXT", "*.txt"), (tr("Todos"), "*.*")],
                initialfile="chuleta_comfyui.txt")
            if ruta:
                with open(ruta, "w", encoding="utf-8") as fh:
                    fh.write(texto)
                self.app.dialogs.set_estado(tr('💾 Guardado: {0}').format(ruta.split('/')[-1]), P.TXT_OK)

        ctk.CTkButton(fila, text=tr("📋 Copiar"), width=110, fg_color=P.BTN_EXITO,
                      hover_color=P.BTN_EXITO_HOVER, command=_copiar).pack(side="left", padx=(0, 6))
        ctk.CTkButton(fila, text=tr("💾 Guardar .txt"), width=120, fg_color="#1e3a8a",
                      hover_color="#172554", command=_guardar).pack(side="left", padx=(0, 6))
        ctk.CTkButton(fila, text=tr("❌ Cerrar"), width=80, fg_color="#991b1b",
                      hover_color=P.BTN_PELIGRO_HOVER, command=vent.destroy).pack(side="right")

    def _traducir_salida(self) -> None:
        """Traduce el prompt actual al español en una ventana aparte."""
        actual = self.app.txt_salida.get("1.0", "end").strip()
        if not actual or len(actual) < 10:
            return self.app.dialogs.set_estado(tr("⚠️ Genera un prompt primero."), P.TXT_AVISO)

        self.app.dialogs.set_estado(tr("🌐 Traduciendo a español..."), P.TXT_ACENTO)

        def _worker():
            try:
                traducido = self.app.deepseek.traducir_a_espanol(actual)
                self.app.after(0, lambda: self._mostrar_ventana_traduccion(traducido))
                self.app.after(0, lambda: self.app.dialogs.set_estado(tr("🌐 Traducción lista"), P.TXT_OK))
            except Exception as e:
                self.app.after(0, lambda e=e: self.app.dialogs.set_estado(tr('❌ Error: {0}').format(e), P.TXT_ERROR))

        self.app._executor.submit(_worker).add_done_callback(log_future_exc)

    def _mostrar_ventana_traduccion(self, texto: str) -> None:
        """Ventana con la traducción y opciones: Usar / Copiar."""
        from config import get_theme_colors
        is_lt = ctk.get_appearance_mode().lower() == "light"
        c = get_theme_colors(is_lt)

        vent = GPromptWindow(self.app)
        vent.title(tr("🇪🇸 Traducción al español"))
        vent.geometry("580x400")
        vent.transient(self.app)

        marco = ctk.CTkFrame(vent, fg_color=c.get("tab_bg", "#f3f4f6" if is_lt else "#0f1318"))
        marco.pack(fill="both", expand=True, padx=12, pady=12)

        ctk.CTkLabel(marco, text=tr("🇪🇸 Traducción al español"),
                     font=ctk.CTkFont(size=P.FUENTE_TITULO, weight="bold"),
                     text_color=c["hdr_text"]).pack(anchor="w", pady=(0, 6))

        txt = ctk.CTkTextbox(marco, wrap="word", font=ctk.CTkFont(size=P.FUENTE_SECCION),
                             fg_color=c.get("entry_bg", "#ffffff" if is_lt else "#1a1a2e"),
                             text_color=c.get("entry_text", "#111827" if is_lt else "#e5e7eb"),
                             border_color=c.get("entry_border", "#9ca3af" if is_lt else "#2a2a3e"))
        txt.insert("1.0", texto)
        # Editable para permitir seleccionar texto con el ratón
        txt.pack(fill="both", expand=True, pady=(0, 10))

        frame_btn = ctk.CTkFrame(marco, fg_color="transparent")
        frame_btn.pack(fill="x")

        def _usar():
            self.app.dialogs.actualizar_salida(texto)
            vent.destroy()

        def _copiar():
            import pyperclip
            pyperclip.copy(texto)
            self.app.dialogs.set_estado(tr("📋 Traducción copiada"), P.TXT_OK)

        ctk.CTkButton(frame_btn, text=tr("✅ Usar traducción"), width=130,
                      fg_color=P.BTN_PRIMARIO, hover_color=P.BTN_PRIMARIO_HOVER,
                      command=_usar).pack(side="left", padx=(0, 6))
        ctk.CTkButton(frame_btn, text=tr("📋 Copiar"), width=100,
                      fg_color="#4b5563", hover_color="#374151",
                      command=_copiar).pack(side="left", padx=(0, 6))
        ctk.CTkButton(frame_btn, text=tr("❌ Cerrar"), width=80,
                      fg_color=P.BTN_GRIS, hover_color=P.BTN_GRIS_HOVER,
                      command=vent.destroy).pack(side="right")

    def _mostrar_consejo_contextual(self, modelo_name: str, specs: dict) -> None:
        """Muestra consejos rápidos en la barra de estado según el contexto del modelo seleccionado."""
        consejos = []
        nota = specs.get("nota", 0)
        if specs.get("modos_gen") and "Quality" in str(specs.get("modos_gen", "")):
            pass
        if not specs.get("has_negative") and not specs.get("is_natural"):
            consejos.append(tr("💡 Modelo Turbo — usa solo tags limpios"))
        elif not specs.get("has_negative") and specs.get("is_natural"):
            consejos.append(tr("💡 Modelo natural — describe en prosa, no uses tags"))
        elif specs.get("is_natural"):
            consejos.append(tr("💡 Lenguaje natural fluido funciona mejor que tags"))
        if "80" in str(specs.get("coste_energia", "")) or "Mystic" in modelo_name:
            consejos.append(tr("⚠️ Modelo costoso (80+ créditos por imagen)"))
        best_for = specs.get("best_for", "").lower()
        if "lento" in best_for or "1m" in best_for:
            consejos.append(tr("⏱ Modelo lento (~1+ min/imagen)"))
        if consejos:
            import random
            consejo = random.choice(consejos)
            self.app.dialogs.set_estado(consejo, P.TXT_INFO)

    def _validar_compatibilidad_modelo(self) -> None:
        """Valida la compatibilidad del modelo con la configuración actual."""
        modelo = self.app.modelo_img_var.get() if hasattr(self.app, 'modelo_img_var') else ""
        if not modelo:
            return True, ""
        # Aquí iría la lógica de validación
        return True, ""

    def _actualizar_compat_inline(self) -> None:
        """Actualiza la compatibilidad inline en la UI."""
        valido, msg = self._validar_compatibilidad_modelo()
        if hasattr(self.app, 'lbl_compat'):
            if valido:
                self.app.lbl_compat.configure(text=tr("✅ Compatible"), text_color=P.TXT_OK)
            else:
                self.app.lbl_compat.configure(text=f"⚠️ {msg}", text_color=P.TXT_AVISO)

    def _cmd_modal_compatibilidad(self) -> None:
        """Abre modal de compatibilidad de modelos."""
        vent = GPromptWindow(self.app)
        vent.title(tr("🔍 Compatibilidad de modelos"))
        vent.geometry("600x400")
        vent.transient(self.app)
        ctk.CTkLabel(vent, text=tr("🔍 Compatibilidad de modelos"), font=ctk.CTkFont(size=P.FUENTE_TITULO, weight="bold")).pack(pady=(10, 5))
        ctk.CTkLabel(vent, text=tr("Información de compatibilidad entre modelos y configuraciones"),
                     font=ctk.CTkFont(size=P.FUENTE_PEQUENA), text_color=P.TXT_MUTED).pack(pady=(0, 10))
        # Aquí iría la tabla de compatibilidad
        ctk.CTkButton(vent, text=tr("Cerrar"), width=120, height=30, command=vent.destroy).pack(pady=15)
