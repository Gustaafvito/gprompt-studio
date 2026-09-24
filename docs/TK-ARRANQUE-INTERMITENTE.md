# Los 62 errores de setup de Tk (24-sep-2026)

Registro de lo observado, lo demostrado y lo que **sigue pendiente**. Las
trazas están copiadas literales porque son la única prueba que hay: el fallo
es intermitente y tardó 18 tiradas completas de la suite en aparecer.

## El síntoma

`python -m pytest -q` falla de vez en cuando con **exactamente 62 errores**
de setup, empezando siempre en:

```
tests/test_cortometraje_desde_referencias.py::TestElBotonDelPanel::test_el_boton_existe_con_su_traduccion
```

## Lo que NO es

Parecía una cascada: «empieza en `TestElBotonDelPanel` y contagia a todo lo
que abre ventana después», con la fixture `panel` de ese fichero como
sospechosa (crea un `VisualStudio` por test sobre un root compartido y deja
`after` pendientes al destruirlo).

Eso está **descartado**, y por medida, no por opinión:

- **Los `after` huérfanos no hacen daño.** `tkinter.Misc.destroy()` llama a
  `deletecommand` sobre los `after` pendientes del widget, así que quedan
  neutralizados a nivel de Tcl. Una sonda que creó y destruyó 20 paneles con
  `report_callback_exception` enganchado cazó **0** excepciones.
- **No es agotamiento de handles.** 120 paneles llegan a 392 GDI y 144 USER,
  contra un límite de 10 000. (Hay una fuga real de ~3 GDI por panel, pero
  es demasiado pequeña para importar.)
- **No es una cascada.** 62 es **exactamente** el número de tests que
  dependen de la fixture de sesión `tk_root`, y `TestElBotonDelPanel` es
  simplemente el PRIMERO de esos 62 en orden de colección.

Inyectando un fallo en `ctk.CTk()` se reproduce el síntoma entero en 1,47 s:

```
======================== 82 passed, 62 errors in 1.47s ========================
```

pytest **cachea** la excepción de una fixture de sesión y la relanza en cada
test que la pida: es **un** fallo contado 62 veces.

## Lo que sí es

Falla la creación del intérprete de Tcl. Las dos veces que se capturó, el
mensaje fue **distinto**:

### Traza 1 — no se pudo leer el fichero

```
_tkinter.TclError: Can't find a usable init.tcl in the following directories:
    {C:\Users\gusta\AppData\Local\Programs\Python\Python310\tcl\tcl8.6}

C:/Users/.../tcl/tcl8.6/init.tcl: couldn't read file ".../init.tcl": No error
couldn't read file ".../tcl8.6/init.tcl": No error
    while executing
"source C:/Users/.../tcl/tcl8.6/init.tcl"
```

`No error` es **errno 0**. El fichero está intacto y se lee bien después. Es
más: en esa misma tirada, otro intérprete del mismo proceso había leído ese
fichero sin problema segundos antes.

### Traza 2 — se cargó a medias

```
_tkinter.TclError: invalid command name "tcl_findLibrary"
```

`tcl_findLibrary` es un proc que define **ese mismo** `init.tcl`. Misma
avería, vista por el otro lado.

Las dos tienen la misma hoja de traza:

```
  File ".../lib/tkinter/__init__.py", line 2299, in __init__
    self.tk = _tkinter.create(screenName, baseName, className, ...)
```

## Lo que NO está demostrado

**No se sabe qué impide leer la instalación de Tcl.** Hay indicios de que es
transitorio (el fichero está en su sitio, se lee antes y después, y otro
intérprete del mismo proceso lo leyó bien), pero la causa de fondo sigue sin
identificar.

Durante la investigación se apuntó a un antivirus y a otras sesiones de
Claude ejecutando tests en paralelo. **Ninguna de las dos cosas se midió**, y
la segunda resultó ser falsa: los procesos de pytest «ajenos» eran bucles de
medición propios que habían quedado huérfanos. Esas atribuciones se han
retirado del código y no deben darse por buenas.

Tampoco está medida la tasa real: las tiradas se solaparon con esos bucles
huérfanos, así que los porcentajes de esa sesión no valen.

## Lo que arregla el cambio, y lo que no

`tests/_arranque_tk.py` reintenta el arranque del intérprete (4 intentos,
espera creciente).

**Arregla** los arranques que fallan con excepción. Comprobado inyectando las
dos trazas reales: con un fallo la tirada se recupera y deja un
`RuntimeWarning` visible; con fallo persistente sigue reventando y deja el
log. Se vio además actuar **en real** una vez, salvando la tirada.

**NO arregla el cuelgue.** También se observó una tirada **bloqueada 22
minutos** en este mismo punto (45 s de CPU en 22 minutos de reloj: esperando
E/S, no girando). Un reintento no puede rescatar algo que no vuelve. Para eso
está el cortafuegos de tiempo de `conftest.py`, que vuelca la pila y **aborta**
—volcar sin abortar deja el proceso colgado igual—. Eso convierte el cuelgue
en una traza legible; **el cuelgue en sí sigue abierto**.

## Dónde mirar cuando vuelva a pasar

| Fichero | Qué guarda |
| --- | --- |
| `~/.arquitecto_prompts/tk_root_fallido.log` | Por qué no se pudo crear el root: versiones, `_default_root` y la traza completa. |
| `~/.arquitecto_prompts/tests_colgados.log` | La pila de un test que se pasó del límite, con su nodeid. |

El límite por test son 300 s, ajustable con `GPROMPT_LIMITE_TEST` (0 lo
desactiva).

## Los tres intérpretes por proceso

Cada proceso de pytest arranca **tres** intérpretes de Tcl, y los tres leen
el mismo `init.tcl`:

| # | Dónde | Protegido |
| --- | --- | --- |
| 1 | `tk_disponible()`, `tests/conftest.py` | sí |
| 2 | `ArquitectoApp()`, `tests/test_barrido_ui.py` | sí |
| 3 | `tk_root()`, `tests/conftest.py` | sí |

El 2 importa porque `ArquitectoApp` hereda de `ctk.CTk`: si le toca a ese, el
síntoma no son 62 errores sino los 24 de `test_barrido_ui`. Por eso el filtro
mira la **traza** y no el mensaje —un `TclError` de cualquier widget de la app
no puede provocar que se repita su inicialización entera cuatro veces—.
