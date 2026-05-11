# 🔧 Mejoras pendientes para próxima iteración

> Generado tras revisión de la tanda v1.0.9 (retry, macros auto, plantillas, tutorial, cacheo, filtros)
> Estado: app estable, en uso. Estas son **observaciones del revisor**, no bugs urgentes.

---

## 🔴 Prioridad ALTA — Riesgo de pérdida de datos del usuario

### 1. Scoring automático sobreescribe el prompt sin guardar versión previa

**Archivo:** `modules/tools_workflow.py`
**Función:** `_cmd_scoring_auto_en_macro()`

**Problema actual:**
```python
self.after(0, lambda: self.actualizar_salida(resp))
```
Sobreescribe `txt_salida` directamente. Si el usuario tenía un prompt bueno y
la macro lo "mejora" mal, **se pierde el original**.

**Solución sugerida:**
Antes de sobreescribir, guardar la versión actual usando tu sistema de
versiones que ya existe (mencionas "hasta 30 versiones"). Sería algo como:

```python
def _cmd_scoring_auto_en_macro(self):
    actual = self.txt_salida.get("1.0", "end").strip()
    if not actual or len(actual) < 20:
        return self.set_estado("⚠️ Genera un prompt primero para scoring.", "#e67e22")

    # NUEVO: guardar versión antes de modificar
    try:
        self._guardar_version_prompt(actual, motivo="Pre-scoring auto")
    except Exception:
        pass  # No bloquear si falla el guardado

    # ... resto igual
```

**Impacto:** Alto. Es la diferencia entre "macro fiable" y "macro que asusta".

---

### 2. Verificar si "Cacheo de system prompts" está realmente implementado

**Archivo:** `modules/core.py`

**Observación:**
En `cosas_modificadas.txt` mencionas "Cacheo system prompts (evita
recalcular)". Pero al revisar `core.py` solo veo cacheo de **info del
modelo** (`_cache_modelo_info`, `_cache_modelo_clave`).

Son cosas distintas:
- `_cache_modelo_info` = cachea la info que muestras en la UI (specs, ratios, etc.)
- "system prompts" = los prompts del sistema que se mandan al LLM en cada llamada

**Verificar:** ¿implementaste también el segundo? Si no, está pendiente.

**Si quieres añadirlo:**
Los system prompts vienen de `prompts.py`. La estrategia sería cachearlos
con clave compuesta (modo + plataforma + modelo + flags relevantes) en un
diccionario, y devolver del caché si la clave ya existe.

---

## 🟡 Prioridad MEDIA — UX y fiabilidad

### 3. Delay de 18s en macro de previsualizar — demasiado largo

**Archivo:** `modules/tools_workflow.py`
**Función:** `_ejecutar_macro()` (sección de delays)

**Problema:**
Un delay fijo de 18s es problemático:
- Si el worker termina en 3s, el usuario espera 15s innecesariamente
- Si tarda más de 18s (red lenta, modelo grande), la macro continúa antes de tiempo
- 18s sin feedback visual = usuario cancela pensando que está colgado

**Solución sugerida:**
Hacer la macro **espera al callback de finalización** en lugar de delay fijo:

```python
# En lugar de:
self.after(18000, _siguiente_paso)

# Mejor:
def _on_terminado():
    _siguiente_paso()
self._cmd_previsualizar(callback=_on_terminado)
```

Si modificarlo es complejo, al menos **muestra countdown visible** al
usuario: "⏳ Previsualizando... (15s restantes)" decreciente.

**Impacto:** Medio. La percepción de "app rápida" vs "app lenta".

---

### 4. `_cmd_idea_auto_en_macro` inserta ideas en orden inverso

**Archivo:** `modules/tools_workflow.py`
**Función:** `_cmd_idea_auto_en_macro()`

**Comportamiento actual:**
```python
self.after(0, lambda: self.txt_idea.insert("1.0", resp + "\n\n"))
```
Cada nueva idea generada se inserta **al principio del textarea**. Si la
macro genera 3 ideas seguidas:
- Idea 1 generada → aparece arriba
- Idea 2 generada → aparece encima de Idea 1
- Idea 3 generada → aparece encima de Idea 2

Lectura final: **3, 2, 1** (orden inverso al que se generaron).

**Solución sugerida:**
- Si quieres reemplazar la idea anterior con la nueva: usar `delete("1.0", "end")` antes del insert
- Si quieres acumular en orden: usar `insert("end", "\n\n" + resp)` (al final)

Verifica cuál es el comportamiento que esperas y ajústalo.

---

### 5. Tutorial en una sola ventana scrolleable — navegación por pasos sería mejor

**Archivo:** `modules/core.py`
**Función:** `_abrir_tutorial()` (línea ~2610)

**Estado actual:**
17 pasos en ventana única con scroll. Funciona para primer arranque pero
para usuarios que vuelven a consultarlo es engorroso buscar el paso concreto.

**Mejora sugerida (no urgente):**
Convertirlo en wizard con botones [< Anterior] [Siguiente >], contador
"Paso X/17", barra de progreso. La info por paso es la misma; solo cambia
la presentación.

**Impacto:** Bajo. Es mejora de pulido, no bloqueo.

---

## 🟢 Prioridad BAJA — Pulido futuro

### 6. Documentar las decisiones de UX raras

Cuando una macro tiene delay 18s en lugar de callbacks, es una decisión.
Pero si no está documentada, dentro de 3 meses (o tu yo del futuro)
mirando ese código no sabrá si:
- Es porque el worker SÍ tarda 18s realmente
- Es porque hay race conditions y se intenta evitar
- Es un valor mágico que alguien copió

**Sugerencia:** docstring corto explicando el "por qué", no el "qué":

```python
# 18s porque previsualizar invoca al worker de imágenes que en SeaArt
# tiene latencia P95 ~15s. Margen de 3s para procesamiento UI.
self.after(18000, _siguiente_paso)
```

---

### 7. Tests para las nuevas funciones auto de macros

Las 3 funciones nuevas (`_cmd_idea_auto_en_macro`, `_cmd_variacion_auto_en_macro`,
`_cmd_scoring_auto_en_macro`) no tienen tests. Son justo las que más
pueden romper en uso real (threading + LLM + UI update).

**Mínimo recomendable:**
- Test que verifica que `_cmd_scoring_auto_en_macro` NO sobreescribe si
  el prompt es vacío
- Test que verifica que el threading no bloquea el UI
- Test mock del worker que devuelve error → la macro debe seguir con
  set_estado en rojo, no caer

No urgente, pero te ahorrará tiempo en futuras refactorizaciones.

---

## 📋 Resumen de acciones recomendadas

| Prioridad | Cambio | Tiempo estimado |
|-----------|--------|----------------|
| 🔴 Alta | Guardar versión antes de scoring auto | 10 min |
| 🔴 Alta | Verificar si cacheo system prompts está hecho | 5 min |
| 🟡 Media | Callback en macro previsualizar (o countdown) | 30 min |
| 🟡 Media | Decidir orden de inserción en idea auto | 5 min |
| 🟢 Baja | Tutorial con navegación por pasos | 1-2h |
| 🟢 Baja | Comentarios explicando decisiones UX raras | 15 min |
| 🟢 Baja | Tests de las macros nuevas | 1-2h |

**Total tiempo si haces todo: ~5 horas**
**Total si haces solo lo crítico (🔴): 15 minutos**

---

## 💡 Recomendación final del revisor

**Antes de tocar nada:**

1. Hacer commit y tag v1.0.9 (esta versión vale la pena inmortalizar)
2. **Usar la app intensivamente 2-3 días**. Anota fricciones REALES, no
   especulaciones. Las observaciones de arriba son **hipótesis del
   revisor** mirando código — el uso real las confirma o descarta.
3. Solo entonces decidir qué arreglar.

**Sobre ElevenLabs:** ver decisión aparte (lo que comentamos en chat).
Mi recomendación: NO mezclarlo ahora con el flujo Suno/SeaArt sin pensar
bien las consecuencias arquitectónicas.
