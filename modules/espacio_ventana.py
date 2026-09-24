"""El alto de la ventana principal: cuánto mide al abrir y quién cede espacio.

QUÉ PASABA (medido el 24-sep-2026 en 1920×1080 al 100 %)
La ventana se monta de arriba abajo con `pack`, y el «Resultado editable» es
lo último que se empaqueta. Cuando no cabe todo, Tk encoge primero lo último:
el resultado absorbía el déficit entero. A su tamaño por defecto (1382×897)
las franjas pedían 1092 px y el resultado, que pide 240, recibía 30: una
línea. Maximizada, 142.

Además, el tamaño inicial se calculaba con los píxeles REALES de la pantalla
y se pasaba a `CTk.geometry()`, que los multiplica por el escalado de
Windows. Con el escalado al 125 % —el de fábrica en muchos portátiles— la
ventana pedía 897 × 1,25 = 1121 px de alto en una pantalla de 1080.

Aquí, funciones puras para poder probarlas sin abrir ventanas:
  • `geometria_inicial()` — tamaño y posición al abrir, en unidades lógicas;
  • `repartir()` — cuánto ceden las pestañas y la idea para que el resultado
    conserve su alto;
  • `plegar_pestanas()` — si ni así cabe, las pestañas se pliegan a su tira
    de títulos (pulsar un título las despliega).
"""

# Las dos franjas elásticas por encima del resultado, en unidades lógicas.
PESTANAS_MAX = 230   # lo que tenían siempre
# Por debajo se corta el contenido visible de Ajustes Extra y de Negativos:
# medido, ninguno necesita más de ~195 con la cabecera de las pestañas.
PESTANAS_MIN = 195
IDEA_MAX = 90        # lo que tenía siempre
IDEA_MIN = 56        # tres líneas
# Por debajo de esto el resultado ya no sirve para leer un prompt (unas ocho
# líneas con su rótulo). Si desplegar las pestañas lo dejaría más bajo, se
# pliegan a su tira de títulos. Medido: sin plegar, con la ventana a 800 de
# alto el resultado se quedaba en 2 px, y a 760 desaparecía.
SALIDA_UTIL = 180
# Si ni con las pestañas plegadas llega a esto (ventanas de ~700 de alto o
# menos), la app lo dice una vez: la salida es maximizar o el Modo Focus.
SALIDA_MINIMA = 100

# Estimaciones de Windows en píxeles a escala 100 %; se multiplican por el
# escalado. La barra de tareas de Windows 11 mide 48; el marco de la
# ventana (título y bordes), unos 40.
_BARRA_TAREAS = 60
_MARCO = 40


def geometria_inicial(pantalla_w, pantalla_h, escala=1.0):
    """(ancho, alto, x, y) al abrir, en unidades LÓGICAS de CustomTkinter.

    `pantalla_w` y `pantalla_h` en píxeles reales, como los da
    `winfo_screenwidth()`. `escala` es el escalado de la ventana (1.25 al
    125 %). El resultado va directo a `CTk.geometry()`, que lo multiplica
    por esa escala: por eso se divide aquí.
    """
    escala = escala or 1.0
    util_h = max(pantalla_h - _BARRA_TAREAS * escala, 600)
    marco = _MARCO * escala

    if pantalla_w <= 1400:           # HD pequeñas (1366x768, 1280x720)
        ancho, alto = pantalla_w * 0.95, util_h * 0.92
    elif pantalla_w <= 1920:         # Full HD
        # Era 0,88: con la barra de tareas y el marco sobraban ~80 px que el
        # resultado necesita. Con 0,94 la ventana entera sigue cabiendo.
        ancho, alto = pantalla_w * 0.72, util_h * 0.94
    elif pantalla_w <= 2560:         # QHD / 2K
        ancho, alto = pantalla_w * 0.62, util_h * 0.82
    else:                            # 4K+
        ancho, alto = min(pantalla_w * 0.50, 1600 * escala), min(util_h * 0.78, 1200 * escala)

    # Que la ventana entera —con su marco— quepa encima de la barra de tareas.
    alto = min(alto, util_h - marco)

    # Mínimos sensatos, pero nunca más de lo que cabe: 620 lógicos al 125 %
    # son 775 px reales, más que una pantalla de 768.
    cabe_w = pantalla_w / escala
    cabe_h = (util_h - marco) / escala
    w = int(max(min(820, cabe_w), ancho / escala))
    h = int(max(min(620, cabe_h), alto / escala))
    x = max(0, int((pantalla_w - w * escala) / 2 / escala))
    y = max(0, int((util_h - h * escala - marco) / 2 / escala))
    return w, h, x, y


def plegar_pestanas(espacio, manual=None):
    """¿Van las pestañas plegadas a su tira de títulos?

    Lo que haya decidido el usuario manda (`manual` True o False). Si no ha
    decidido nada, se pliegan solo cuando desplegadas dejarían el resultado
    por debajo de lo útil.
    """
    if manual is not None:
        return bool(manual)
    return espacio - PESTANAS_MIN - IDEA_MIN < SALIDA_UTIL


def repartir(espacio, salida, plegadas=None):
    """Alto para (pestañas, idea) cuando las tres franjas comparten `espacio`.

    Todo en unidades lógicas. `salida` es lo que pide el marco del resultado.
    Primero el resultado; lo que sobre, a las pestañas y luego a la idea,
    cada una entre su mínimo y su máximo. Si no llega ni para los mínimos,
    se quedan en el mínimo y el resultado se lleva lo que quede.

    `plegadas` es el alto de la tira de títulos cuando las pestañas van
    plegadas: entonces miden eso y el resto se lo reparten idea y resultado.
    """
    resto = espacio - salida
    if plegadas is not None:
        pestanas = plegadas
        idea = min(IDEA_MAX, max(IDEA_MIN, resto - pestanas))
    else:
        # Ceden primero las pestañas: de 230 a 195 solo pierden hueco vacío
        # (medido), mientras que la idea pierde líneas a la vista.
        idea = min(IDEA_MAX, max(IDEA_MIN, resto - PESTANAS_MIN))
        pestanas = min(PESTANAS_MAX, max(PESTANAS_MIN, resto - idea))
    return int(pestanas), int(idea)
