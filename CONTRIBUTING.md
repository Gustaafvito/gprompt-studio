# Cómo contribuir

Gracias por pasarte. Esto lo mantiene una persona, así que lo más útil que
puedes hacer no es necesariamente escribir código.

## Lo que más ayuda, por orden

**1. Reportar un fallo con el log.** El log está en
`%USERPROFILE%\.arquitecto_prompts\logs\gprompt.log` y es lo que separa un
arreglo de una tarde adivinando. Hay
[plantilla](https://github.com/Gustaafvito/gprompt-studio/issues/new/choose)
que te lo pide.

**2. Decirme que la ficha de un modelo no cuadra.** El catálogo se pudre
solo: los proveedores retiran modelos y sacan otros cada pocas semanas. Si
generas con algo y sus reglas no son las que dice la app, quiero saberlo.

**3. Añadir modelos.** Si usas una plataforma que yo no toco, tú sabes de
sus modelos más que yo.

## Antes de escribir código

**Abre un issue primero** si es algo más que un arreglo pequeño. Puede que
esté a medio hacer, o que no encaje con hacia dónde va esto — mejor
saberlo antes de dedicarle una tarde.

```bash
git clone https://github.com/Gustaafvito/gprompt-studio.git
cd gprompt-studio
pip install -e ".[dev]"
pytest tests/ -q      # tienen que pasar todos antes de empezar
```

## Lo que se pide en un cambio

**Tests que expliquen el porqué, no solo el qué.** Aquí un test no
comprueba que una función devuelve 4: cuenta qué se rompió, cómo se
descubrió y qué pasaría si vuelve. Mira cualquiera de `tests/` y verás el
patrón — los docstrings son la mitad del valor.

```bash
pytest tests/ -q      # todo en verde
ruff check .          # sin avisos
```

**Las fichas de modelos se miden, no se copian.** Si añades un modelo, sus
reglas —prosa o tags, límite de caracteres, si acepta negativo, sampler—
salen de generar con él. La documentación de los proveedores se contradice
con la realidad más de lo que parece: de las once listas de modelos que
tenía este proyecto escritas desde documentación oficial, **las once
estaban podridas** cuando se comprobaron una a una con claves reales.

Si no puedes medir un dato, márcalo como `POR CONFIRMAR` en
`limitaciones`. Es mejor que inventarlo.

**El texto de la interfaz va bilingüe.** Cualquier cadena nueva que se vea
en pantalla necesita su traducción en `modules/i18n.py`. Hay un test que lo
vigila.

## Estructura, en corto

```
config.py           el catálogo y las plataformas
api_clients.py      los 13 proveedores de LLM
prompts.py          las reglas de redacción por modo y modelo
data/*.json         las fichas de los modelos, los estilos, el glosario
modules/            la interfaz y los servicios
tests/              1.337 candados
```

`docs/AGREGAR_MODELO.md` explica el proceso de dar de alta un modelo, y
`docs/BUILD.md` cómo se construye el ejecutable.

## Licencia

Al contribuir aceptas que tu aportación se publique bajo la
[licencia Apache 2.0](LICENSE) del proyecto.
