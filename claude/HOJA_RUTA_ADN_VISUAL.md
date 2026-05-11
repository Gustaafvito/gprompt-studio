# 🧬 Hoja de ruta — ADN Visual JSON

> Feature objetivo: análisis estructurado de imagen/vídeo → JSON con atributos
> reutilizables → conversión a prompts optimizados por plataforma.
> Estado: planificación. Sin implementar todavía.

---

## 📋 Resumen ejecutivo

**Qué resuelve:** El análisis actual devuelve un párrafo descriptivo monolítico
que no permite "reusar partes". El ADN Visual JSON estructura todos los
atributos visuales en categorías editables/bloqueables, permitiendo
variaciones controladas (mantener iluminación + cambiar sujeto, etc.).

**Diferenciador:** ninguna herramienta del mercado combina ADN JSON +
biblioteca guardada + bloqueo de atributos + exportación multi-plataforma.

**Tiempo total estimado:** 14-20 horas en 3 fases.

---

## 🔧 Pre-requisitos técnicos

### Visión LLM disponible

Tu app necesita acceso a un modelo con capacidad de visión. Opciones por
orden de recomendación:

| Proveedor | Coste | Calidad | Velocidad | Configuración |
|-----------|-------|---------|-----------|---------------|
| **Gemini** | Gratis (1500/día) | ⭐⭐⭐⭐⭐ | 3-5s | Crear cuenta Google AI Studio |
| **Ollama + LLaVA** | Gratis | ⭐⭐⭐ | 20-40s | Instalación local pesada |
| **OpenRouter** | ~$0.001/análisis | ⭐⭐⭐⭐ | 4-8s | Cuenta openrouter.ai |
| **Claude / GPT-4o** | De pago directo | ⭐⭐⭐⭐⭐ | 3-6s | API de pago |

**Recomendación:** empezar con Gemini gratis. Tu app YA tiene fallback
automático a Ollama si Gemini falla.

### Lo que NO sirve

❌ **DeepSeek** no procesa imágenes (solo texto). Aunque sea tu LLM por
defecto, el análisis SIEMPRE pasará por uno de los de arriba.

---

## 🎯 FASE 1 — ADN JSON básico (MVP)

**Tiempo estimado:** 4-6 horas
**Valor:** 80% del beneficio total

### 1.1 — Definir esquema JSON estructurado

Crear constante `ADN_SCHEMA` en `config.py`:

```python
ADN_SCHEMA_IMAGEN = {
    "sujeto": {
        "tipo": "",  # persona / objeto / animal / paisaje
        "genero": "",
        "edad_aprox": "",
        "etnia": "",
        "cabello": {"color": "", "largo": "", "estilo": ""},
        "ojos": {"color": "", "forma": ""},
        "ropa": {"prenda": "", "color": "", "material": ""},
        "pose": "",
        "expresion": "",
    },
    "escena": {
        "ubicacion": "",
        "interior_exterior": "",
        "elementos": [],
        "profundidad": "",
    },
    "iluminacion": {
        "tipo": "",  # natural / artificial / mixta
        "direccion": "",
        "intensidad": "",
        "hora_dia": "",
        "color_temperatura": "",
        "fuentes": [],
    },
    "camara": {
        "encuadre": "",  # primer plano / plano medio / plano general
        "angulo": "",
        "lente_simulada": "",
        "profundidad_campo": "",
        "distorsion": "",
    },
    "estilo": {
        "estetica": "",  # fotografía / pintura / 3D / anime / etc.
        "epoca": "",
        "tecnica": "",
        "paleta_dominante": [],  # array de 3-5 colores
    },
    "composicion": {
        "regla": "",  # tercios / simetría / diagonal / central
        "lineas_guia": "",
        "equilibrio": "",
    },
    "atmosfera": {
        "estado_animo": "",
        "energia": "",  # tranquila / dinámica / dramática
    },
    "tecnico": {
        "grano": "",
        "contraste": "",
        "saturacion": "",
        "postproceso": "",
    },
}

ADN_SCHEMA_VIDEO = {
    # Hereda todo lo de imagen y añade:
    **ADN_SCHEMA_IMAGEN,
    "movimiento": {
        "camara": "",  # estático / pan / tilt / dolly / handheld
        "sujeto": "",
        "velocidad": "",
    },
    "narrativa": {
        "duracion_estimada": "",
        "beats": [],  # array de hasta 3 momentos clave
        "transicion_inicial": "",
        "transicion_final": "",
    },
}
```

### 1.2 — System prompt para Vision LLM

Crear en `prompts.py` la función `get_adn_system_prompt(modo)`:

```python
ADN_VISION_PROMPT = """
Eres un experto en análisis visual para prompt engineering de IA generativa.

Analiza la imagen y devuelve un JSON estructurado con TODOS los atributos
visuales relevantes. Sé EXTREMADAMENTE detallado.

CATEGORÍAS OBLIGATORIAS:
- sujeto: atributos físicos completos, ropa, pose, expresión
- escena: ubicación, elementos contextuales, profundidad
- iluminacion: tipo, dirección, intensidad, hora del día, temperatura color
- camara: encuadre, ángulo, lente simulada, profundidad de campo
- estilo: estética, época, técnica, paleta de 3-5 colores dominantes
- composicion: regla de tercios, líneas guía, equilibrio
- atmosfera: estado de ánimo, energía visual
- tecnico: grano, contraste, saturación, postproceso

REGLAS:
1. Responde SOLO con JSON válido. Sin texto antes ni después.
2. Sin markdown, sin ```json```, solo el objeto.
3. Si un campo no aplica o no se aprecia, déjalo como string vacío "".
4. Los arrays (elementos, paleta_dominante) deben tener entre 0 y 5 items.
5. Sé específico: "rubio platino con mechas doradas" mejor que "rubio".
6. Para paleta_dominante usa nombres específicos: "azul cobalto" no "azul".

EJEMPLO DE OUTPUT:
{
  "sujeto": { ... },
  "escena": { ... },
  ...
}
"""
```

Variante para vídeo: añade instrucciones sobre movimiento + narrativa.

### 1.3 — Worker de análisis ADN

En `workers.py` añadir método `analizar_adn(imagen_path, modo)`:

```python
def analizar_adn(self, imagen_path: str, modo: str = "imagen") -> dict:
    """
    Analiza imagen/vídeo y devuelve dict estructurado con todos los atributos.
    Usa la cadena de fallback: Gemini → Ollama → OpenRouter.

    Args:
        imagen_path: ruta a la imagen o frame extraído del vídeo
        modo: "imagen" o "video" — determina el schema

    Returns:
        dict con estructura ADN_SCHEMA (puede tener campos vacíos)

    Raises:
        VisionError si ningún proveedor de visión está disponible
    """
    system_prompt = get_adn_system_prompt(modo)
    raw_text = self.vision_chain.analizar(imagen_path, system_prompt)

    # Parsear JSON con tolerancia (a veces los LLMs añaden ```json wrap)
    try:
        # Limpiar wrappers comunes
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.split("```")[1]
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        cleaned = cleaned.strip()

        adn = json.loads(cleaned)

        # Validar estructura básica
        schema = ADN_SCHEMA_VIDEO if modo == "video" else ADN_SCHEMA_IMAGEN
        for key in schema:
            if key not in adn:
                adn[key] = schema[key]  # Rellenar campos faltantes

        return adn
    except json.JSONDecodeError as e:
        logger.error(f"ADN inválido del LLM: {e}\nRaw: {raw_text[:200]}")
        # Fallback: intentar segunda llamada con prompt más estricto
        raise VisionError(f"El LLM devolvió JSON inválido. Intenta otra imagen.")
```

### 1.4 — UI: botón "🧬 ADN Visual JSON"

En `tools_creative.py` (donde está el botón Vision actual) añadir:

```python
btn_adn = ctk.CTkButton(
    frame_botones,
    text="🧬 ADN Visual",
    width=130, height=32,
    fg_color="#7c3aed", hover_color="#6d28d9",
    command=self._cmd_adn_visual
)
CTkToolTip(btn_adn, message="Extrae ADN JSON estructurado: sujeto, iluminación, "
                            "cámara, estilo... para variaciones controladas")
```

### 1.5 — Ventana de resultado del ADN

Nuevo método `_cmd_adn_visual()` que:

1. Verifica que hay imagen cargada (si no → mensaje)
2. Lanza worker en thread
3. Muestra spinner "🧬 Extrayendo ADN visual..."
4. Cuando termina → abre ventana con el JSON

Layout de la ventana:

```
┌──────────────────────────────────────────────────┐
│  🧬 ADN Visual de la imagen                      │
├──────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────┐  │
│  │ {                                          │  │
│  │   "sujeto": {                              │  │
│  │     "tipo": "persona",                     │  │
│  │     "genero": "femenino",                  │  │
│  │     ...                                    │  │
│  │   },                                       │  │
│  │   ...                                      │  │
│  │ }                                          │  │
│  │                                            │  │
│  │ [Editor JSON con sintaxis coloreada]      │  │
│  └────────────────────────────────────────────┘  │
│                                                  │
│  [📋 Copiar JSON]  [🎯 Usar en prompt actual]   │
│  [💾 Guardar como ADN]  [🚪 Cerrar]             │
└──────────────────────────────────────────────────┘
```

### 1.6 — Conversión ADN → prompt natural

Función `adn_a_prompt(adn_dict, plataforma="seaart")`:

Recibe el JSON y devuelve un prompt en texto. Lógica básica:

```python
def adn_a_prompt(adn, plataforma="seaart"):
    """Convierte ADN JSON a prompt según plataforma."""
    if plataforma == "seaart":
        return _adn_a_tags_con_pesos(adn)
    elif plataforma == "midjourney":
        return _adn_a_natural_midjourney(adn)
    elif plataforma == "dalle":
        return _adn_a_natural_largo(adn)
    # ...
```

**MVP:** solo SeaArt al principio. Las otras plataformas en Fase 3.

### 1.7 — Tests críticos

- Test: ADN_SCHEMA_IMAGEN tiene todas las claves esperadas
- Test: parseo JSON tolerante a ```json wrap
- Test: campos faltantes se rellenan con strings vacíos
- Test mock: `analizar_adn` con LLM que devuelve JSON válido
- Test mock: `analizar_adn` con LLM que devuelve JSON malformado → VisionError
- Test: `adn_a_prompt` con ADN vacío no peta

---

## 🎨 FASE 2 — Editor visual del ADN

**Tiempo estimado:** 6-8 horas adicionales
**Pre-requisito:** Fase 1 terminada y testeada con 10+ imágenes reales

### 2.1 — UI con paneles por categoría

Reemplazar editor JSON crudo por interfaz estructurada:

```
┌─ 🧑 Sujeto ───────────────────────[🔒]─┐
│  Tipo:    [persona ▾]                  │
│  Género:  [femenino ▾]                 │
│  Edad:    [25-30 ▾]                    │
│  Cabello: rubio platino [editar]      │
│  [+ Añadir atributo]                   │
└────────────────────────────────────────┘

┌─ 🌅 Iluminación ──────────────────[🔓]─┐
│  Tipo:    [natural lateral ▾]          │
│  Hora:    [golden hour ▾]              │
│  Intens.: [suave ▾]                    │
└────────────────────────────────────────┘
```

Cada bloque tiene candado 🔒/🔓 que marca si se "preserva" al generar
variaciones.

### 2.2 — Sistema de bloqueo

```python
class ADNEditor:
    def __init__(self, adn_dict):
        self.adn = adn_dict
        self.bloqueado = {key: False for key in adn_dict}

    def toggle_bloqueo(self, categoria):
        self.bloqueado[categoria] = not self.bloqueado[categoria]

    def generar_variacion_prompt(self, cambios_usuario):
        """Devuelve nuevo ADN: bloqueados intactos, no-bloqueados re-imaginados."""
        nuevo = copy.deepcopy(self.adn)
        for categoria, nuevo_valor in cambios_usuario.items():
            if not self.bloqueado.get(categoria, False):
                nuevo[categoria] = nuevo_valor
        return nuevo
```

### 2.3 — Biblioteca de ADNs guardados

Nueva entidad en `persistence.py`: `adns_guardados.json`.

Estructura:
```python
{
    "id": "adn_1",
    "nombre": "Retrato golden hour analógico",
    "creado": "2026-05-09T10:30:00",
    "imagen_origen": "ruta/a/imagen.jpg",
    "thumbnail_base64": "...",  # 64x64 para preview
    "adn": { ... },
    "tags": ["retrato", "golden hour", "analógico"],
    "veces_usado": 3,
}
```

Botón en menú UI: **"🧬 Biblioteca ADN"** → ventana con grid de
thumbnails + búsqueda + filtros por tag.

### 2.4 — Modal "Aplicar ADN a prompt actual"

Cuando seleccionas un ADN de la biblioteca:

```
┌──────────────────────────────────────────┐
│  Aplicar ADN: "Retrato golden hour..."  │
├──────────────────────────────────────────┤
│  ☑ Sujeto                                │
│  ☐ Escena                                │
│  ☑ Iluminación  ← solo si quieres esto  │
│  ☐ Cámara                                │
│  ☑ Estilo                                │
│  ☐ Composición                           │
│                                          │
│  [✅ Aplicar selección]  [Cancelar]      │
└──────────────────────────────────────────┘
```

---

## 🌐 FASE 3 — Multi-plataforma

**Tiempo estimado:** 4-6 horas adicionales
**Pre-requisito:** Fases 1 + 2 estables

### 3.1 — Conversores por plataforma

Implementar en `prompts.py` funciones específicas:

- `adn_a_seaart(adn)` → tags con pesos `(palabra:1.2)`
- `adn_a_midjourney(adn)` → natural + parámetros `--ar --style raw`
- `adn_a_dalle(adn)` → descripción natural larga
- `adn_a_flux(adn)` → estructura técnica formal
- `adn_a_kling_video(adn)` → JSON específico de Kling
- `adn_a_seedance(adn)` → formato SeaArt video

### 3.2 — UI: Exportar a plataforma

Dropdown en la ventana de ADN:

```
Exportar como: [SeaArt ▾]  [📋 Copiar prompt resultante]
```

### 3.3 — Preview comparativo

Botón **"Ver en todas las plataformas"** → ventana con tabs:

```
┌─[SeaArt]─[Midjourney]─[DALL-E]─[Flux]─┐
│                                        │
│  (masterpiece:1.3), 1woman, blonde     │
│  platinum hair, 85mm lens, golden     │
│  hour, (analog film:1.2), 35mm grain  │
│                                        │
│  [📋 Copiar]                           │
└────────────────────────────────────────┘
```

---

## 🔍 Validación de calidad

Criterios para considerar la feature "lista":

### Fase 1 — Lista cuando:
- ✅ 10 imágenes diversas analizadas devuelven JSON válido
- ✅ El JSON es **reutilizable**: con 1 cambio se nota la diferencia
  manteniendo el resto
- ✅ Fallback a Ollama funciona si Gemini falla
- ✅ Tests verdes

### Fase 2 — Lista cuando:
- ✅ Editor visual permite tocar cada campo sin perder los demás
- ✅ Bloqueo de categorías funciona en variaciones
- ✅ Biblioteca guarda/carga sin pérdida de datos

### Fase 3 — Lista cuando:
- ✅ 5 plataformas dan prompts útiles desde el mismo ADN
- ✅ Las diferencias entre plataformas son **reales**, no cosméticas

---

## ⚠️ Riesgos identificados

### R1: Calidad inconsistente del Vision LLM
**Mitigación:** prompt con ejemplo de output esperado + retry con prompt
más estricto si JSON sale malformado.

### R2: Ollama LLaVA puede dar análisis pobres
**Mitigación:** marcar al usuario qué proveedor se usó. "ADN extraído con
LLaVA local (calidad limitada)". Sugerir Gemini para mejor calidad.

### R3: Schema demasiado rígido para casos atípicos
**Mitigación:** todos los campos string vacíos por defecto. El LLM solo
rellena lo que ve. Mejor un campo vacío que forzar inventar.

### R4: Coste si se usa Claude/GPT-4o de pago
**Mitigación:** análisis batch desactivado por defecto. Aviso visible
del coste estimado antes de cada análisis si el LLM activo es de pago.

### R5: Privacidad de imágenes subidas
**Mitigación:** Gemini conserva imágenes según política Google. Recomendar
Ollama para contenido sensible. Documentar en README/Tutorial.

---

## 📅 Plan de ejecución sugerido

| Sesión | Duración | Objetivo |
|--------|----------|----------|
| Sesión 1 | 2h | Diseño schema + system prompt + tests sin UI |
| Sesión 2 | 2h | Worker + parsing tolerante + tests integración |
| Sesión 3 | 2h | UI básica: botón + ventana resultado + acciones |
| **Pausa** | 2-3 días | Usar con imágenes reales, ajustar prompt si JSON pobre |
| Sesión 4 | 3h | Editor visual estructurado (Fase 2.1-2.2) |
| Sesión 5 | 3h | Biblioteca de ADNs guardados (Fase 2.3-2.4) |
| **Pausa** | 2-3 días | Usar la biblioteca, verificar UX |
| Sesión 6 | 3h | Conversores multi-plataforma (Fase 3) |
| Sesión 7 | 2h | UI exportar + preview comparativo |

**Total:** 17 horas de desarrollo + tiempo de validación entre fases.

---

## 💡 Decisión recomendada

1. **NO empezar hasta hacer commit + tag v1.0.9** de lo que ya tienes
2. **NO empezar sin tener API key de Gemini funcionando** (es gratis,
   5 minutos crearla en https://aistudio.google.com)
3. **SÍ empezar con Fase 1 únicamente**. Es donde está el 80% del valor.
   Si después de Fase 1 ves que la feature no se usa, no inviertes
   más tiempo en Fases 2/3.

---

## 🎯 ¿Cómo conseguir API key de Gemini?

1. Ve a https://aistudio.google.com
2. Inicia sesión con tu cuenta Google
3. Botón "Get API key" arriba a la derecha
4. "Create API key in new project" → te genera la clave
5. Copia esa clave y pégala en tu app (ya tienes el campo en Preferencias o `.env`)
6. La variable se llama `GEMINI_API_KEY` en tu `.env`

**Coste:** 0 € hasta 1500 análisis/día (más que de sobra para uso personal).
