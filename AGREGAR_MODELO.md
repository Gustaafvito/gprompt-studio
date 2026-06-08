# 📋 Guía: Agregar / Auditar Modelos

Plantilla y checklist para añadir un modelo nuevo (o auditar uno
existente) al catálogo de G-Prompt Studio. Mantén este archivo
actualizado cuando descubras patrones nuevos.

---

## 🎯 Antes de empezar

Cosas que necesitas tener a mano del modelo:

- [ ] **Nombre exacto** como aparece en la plataforma (ej. "Z Image Turbo")
- [ ] **Plataforma** (SeaArt / ComfyUI / Magnific / API / etc.)
- [ ] **Tipo** (imagen / vídeo / audio)
- [ ] **Familia** (Flux / SDXL / Z-Image / Veo / Suno / etc.)
- [ ] **Rating oficial** de la plataforma (si lo expone)
- [ ] **max_chars positive** (mide con un prompt largo, ver más abajo)
- [ ] **max_chars negative** (si admite y es distinto del positive)
- [ ] **¿`is_natural` o tag-based?** (¿usa lenguaje natural o tags con
      comas y pesos?)
- [ ] **Ratios disponibles** en la plataforma
- [ ] **Pasos recomendados** (8, 20, 28-50, etc.)
- [ ] **CFG recomendado** (1.0, 3-5, 7, etc.)
- [ ] **Sampler recomendado** (Euler, DPM++, etc.) — solo si la
      plataforma lo expone
- [ ] **Descripción/best_for** (1-2 frases con lo que destaca)
- [ ] **Prompt de ejemplo** real que sepas que funciona bien

---

## 📝 Plantilla del spec (copia y rellena)

### Para `data/model_specs_imagen.json`

```json
"NOMBRE_DEL_MODELO": {
  "nota": 4.5,
  "has_negative": true,
  "is_natural": false,
  "ratios": [
    "1:1", "9:16", "16:9", "2:3", "3:2", "3:4", "4:3", "4:5", "5:4"
  ],
  "max_chars": 2000,
  "max_chars_negative": 2000,
  "modos_gen": ["Estándar", "Calidad"],
  "max_imagenes": 4,
  "best_for": "Una o dos frases con lo que destaca el modelo (tipo de imagen, velocidad, calidad, especialidad).",
  "prompt_formula": "Resumen de cómo construir prompt para este modelo (orden de campos, pesos, formato).",
  "prompt_ejemplo": "Un ejemplo real que sabes que funciona bien.",
  "sampler_recomendado": "Euler",
  "pasos": 20,
  "cfg": 1.0,
  "coste_energia": "28 (Calidad) — gratis VIP",
  "limitaciones": "Cualquier limitación importante: pesos no soportados, sin negative, modelo Turbo puro, etc."
}
```

### Para `data/model_specs_video.json`

```json
"NOMBRE_DEL_MODELO_VIDEO": {
  "nota": 4.5,
  "has_negative": true,
  "has_audio": true,
  "audio_desc": "SFX + BGM integrados (toggles Efecto de sonido / Agregar BGM)",
  "duraciones": ["5s", "10s"],
  "ratios": ["9:16", "16:9", "1:1"],
  "max_chars": 1500,
  "modos_gen": ["Estándar", "Calidad"],
  "best_for": "Especialidad: cinematográfico, anime, foto-realista, etc.",
  "prompt_formula": "Subject + action + camera control + style. Notas específicas del modelo.",
  "prompt_ejemplo": "Ejemplo real corto que funcione.",
  "limitaciones": "Sin negative / máx 5s / cosas similares."
}
```

### Para `data/model_specs_audio.json`

```json
"NOMBRE_DEL_MODELO_AUDIO": {
  "nota": 4.5,
  "usa_tags_estructurales": true,
  "duracion_max_min": 4,
  "best_for": "Tipos de música/voz para los que destaca.",
  "instrumental": true,
  "voz_disponible": true,
  "idiomas_letra": ["en", "es", "ja", "zh"],
  "prompt_formula": "Cómo se estructura el prompt para este modelo.",
  "prompt_ejemplo": "Ejemplo real."
}
```

---

## 🔍 Tabla de campos: qué significan y son críticos

### Campos críticos (afectan al comportamiento de la app)

| Campo | Qué hace si está mal | Ejemplo |
|---|---|---|
| **`has_negative`** | Si es `false`, la app elimina el NEGATIVE del output | `true` para Z-Image, `false` para Nano Banana |
| **`is_natural`** | Si es `true`, la app usa lenguaje natural; si no, tags con pesos | `true` Z-Image-Base, `false` Z Image Turbo |
| **`max_chars`** | Cortador de seguridad: recorta el POSITIVE si excede | `2000` |
| **`max_chars_negative`** | Cortador específico del NEGATIVE. Si omites, usa `max_chars` | Omitir salvo que difiera |
| **`formato_bloques`** | Activa plantilla narrativa especial. Solo `"z_image"` por ahora | Solo Z-Image-Base |
| **`no_weights`** | Si es `true`, la app elimina pesos numéricos `(tag:1.2)` | Turbo puro en ComfyUI |
| **`ratios`** | Lista de ratios disponibles del modelo en la UI | `["1:1","9:16",...]` |

### Campos informativos (van al tooltip / dashboard / ayuda al LLM)

| Campo | Qué hace |
|---|---|
| `nota` | Rating del modelo en la UI |
| `best_for` | Tooltip + system prompt al LLM |
| `prompt_formula` | Hint al LLM sobre cómo estructurar el prompt |
| `prompt_ejemplo` | Few-shot example al LLM |
| `sampler_recomendado` | Solo informativo |
| `pasos`, `cfg`, `clip_skip` | Informativo (algunos modelos los respetan) |
| `coste_energia` | Tooltip de coste |
| `modos_gen` | Modos disponibles (Estándar, Calidad, Turbo) |
| `max_imagenes` | Cantidad por generación |
| `limitaciones` | Tooltip de "ojo con esto" |

---

## 🧪 Cómo medir `max_chars` real

La forma fiable de saber el límite es probar empíricamente:

1. Genera un prompt **largo y único** (~2000-3000 chars) con etiquetas
   reconocibles al final para saber dónde corta.
2. Pégalo en la plataforma.
3. Genera y mira qué parte del prompt ignoró.
4. Si la plataforma muestra un contador de caracteres antes de generar,
   úsalo (más fiable).

**Tip:** Pídeme a mí un prompt de la longitud que quieras y te lo
genero (`"Pásame un prompt de 2500 chars con tags reconocibles al
final"`).

**Importante:** Verifica también el límite del **NEGATIVE**. A
veces es el mismo, a veces más bajo (raro). Si difiere, declara
`max_chars_negative` en el spec.

---

## 📂 Sitios a actualizar al añadir un modelo

Para que el modelo aparezca y funcione en TODA la app, hay que
tocar estos sitios:

### 1. JSON de specs (obligatorio)

`data/model_specs_imagen.json` (o `_video.json` / `_audio.json`)

Añadir la entrada con la plantilla de arriba.

### 2. `config.py` — combo de selección (obligatorio)

Imagen: dentro de `MODELOS_IMAGEN` busca la familia correspondiente:

```python
("── Familia Z-Image ──", sorted([
    "Z Image Turbo",
    "Z-Image-Base",
    "TU_MODELO_NUEVO",   # ← añadir aquí
])),
```

Vídeo: `MOTORES_VIDEO` (suelen ir agrupados por familia).
Audio: `MODELOS_AUDIO`.

### 3. `config.py` — fórmulas de composición (opcional)

`FORMULAS_COMPOSICION` agrupa modelos por tipo de generación
(fotorrealismo_sd, retrato_sd, anime, etc.). Si tu modelo encaja
en alguna fórmula, añádelo allí:

```python
"fotorrealismo_sd": {
    "modelos": ["Z Image Turbo", "TU_MODELO_NUEVO", ...],
    ...
},
```

### 4. Smoke test + tests (obligatorio)

```bash
python -c "import app; print('OK')"
python -m pytest tests/ -q
```

### 5. Commit con mensaje claro

```
feat(specs): añadir [NOMBRE_MODELO] a familia [FAMILIA]

  • nota: 4.X
  • max_chars: XXXX
  • Especial: ...
```

---

## 🚦 Checklist final antes de commit

- [ ] Spec completo y validado en el JSON correspondiente
- [ ] `has_negative` reflexionado (¿la plataforma lo expone?)
- [ ] `is_natural` correcto (¿prompt narrativo o tags?)
- [ ] `max_chars` medido empíricamente (no estimado)
- [ ] `max_chars_negative` declarado solo si difiere de `max_chars`
- [ ] Modelo añadido al combo en `config.py`
- [ ] Modelo añadido a fórmulas relevantes si aplica
- [ ] `python -c "import app; print('OK')"` pasa
- [ ] `python -m pytest tests/ -q` verde
- [ ] Commit con prefijo `feat(specs):` o `fix(specs):`

---

## 📚 Ejemplos ya validados

### Z Image Turbo (SeaArt, familia Z-Image)
Tag-based con pesos SD tradicional. 8 NFEs ultra-rápido.
Ver `data/model_specs_imagen.json` → `"Z Image Turbo"`.

### Z-Image-Base (SeaArt, familia Z-Image)
HÍBRIDO: preámbulo de quality tags + bloques narrativos en
lenguaje natural. `formato_bloques: "z_image"` activa una
plantilla especial con bloques `[Subject & Composition]` etc.
Ver `data/model_specs_imagen.json` → `"Z-Image-Base"`.

### SeaArt Film Video (SeaArt, vídeo)
Cinematográfico con SFX + BGM integrados. `has_audio: true`.
Ver `data/model_specs_video.json` → `"SeaArt Film Video"`.

---

## 🔧 Comandos rápidos

```bash
# Listar todos los modelos imagen agrupados por familia
python -c "
import json, sys
from collections import defaultdict
sys.stdout.reconfigure(encoding='utf-8')
d = json.load(open('data/model_specs_imagen.json', encoding='utf-8'))
print(f'Total: {len(d)} modelos')
"

# Ver spec completo de UN modelo
python -c "
import json, sys
sys.stdout.reconfigure(encoding='utf-8')
d = json.load(open('data/model_specs_imagen.json', encoding='utf-8'))
print(json.dumps(d['NOMBRE_DEL_MODELO'], indent=2, ensure_ascii=False))
"

# Buscar modelos con un campo específico
python -c "
import json, sys
sys.stdout.reconfigure(encoding='utf-8')
d = json.load(open('data/model_specs_imagen.json', encoding='utf-8'))
for n, s in d.items():
    if s.get('has_negative') is False:
        print(n)
"
```

---

## 📊 Estado actual del catálogo (sesión 16)

| Categoría | Familia | Modelos | Auditado |
|---|---|---:|:---:|
| Imagen | Z-Image (SeaArt) | 2 | ✅ |
| Imagen | Z-Image (otros) | 3 | ⏳ |
| Imagen | Flux | 17 | ⏳ |
| Imagen | Illustrious | 10 | ⏳ |
| Imagen | SDXL | 6 | ⏳ |
| Imagen | Midjourney | 5 | ⏳ |
| Imagen | Otros | 75 | ⏳ |
| Vídeo | SeaArt | 2 | ✅ (1 de 2) |
| Vídeo | Resto | 13 | ⏳ |
| Audio | Todos | 10 | ⏳ |

Total: 118 imagen + 15 vídeo + 10 audio. **3 modelos auditados** al
cierre de la sesión 16.

---

*Este archivo es vivo. Actualízalo cuando descubras un patrón nuevo
de modelo, un campo que falte, o una manera mejor de medir
caracteres.*
