"""Filas de botones que no esconden nada cuando la ventana se estrecha.

QUÉ PASABA (medido el 24-sep-2026 en 1920×1080 al 100 %)
La botonera y la cabecera se montan con `pack(side="left")`. Cuando no
caben, Tk no avisa: encoge los últimos hasta dejarlos en nada. A su tamaño
por defecto (1382 de ancho):
  • la segunda fila de la botonera pedía 1630 px de botones de ancho fijo;
    «Preview» quedaba en 34 px y Reset, Última, Setup y Cargar setup no se
    veían en absoluto;
  • de los 8 menús de la cabecera, «UI» quedaba en 37 px y «Workflow» no
    aparecía. El modo compacto saltaba por debajo de 1180, una cifra de
    cuando eran 7 menús.

Aquí:
  • `ancho_boton()` — el ancho de un botón según su texto, nunca mayor que
    el que tenía; la mayoría llevaban 20-30 px de aire a cada lado;
  • `repartir_en_filas()` — en qué línea va cada grupo, función pura;
  • `FilaFluida` — el contenedor que lo aplica: lo que no cabe baja a la
    línea siguiente, entero, en vez de desaparecer.
"""
import customtkinter as ctk

# Aire a los dos lados del texto dentro del botón.
MARGEN_TEXTO = 24


def ancho_boton(fuente, texto, maximo):
    """Ancho para que `texto` quepa con aire, sin pasar del `maximo` de antes.

    Los botones de solo icono (los de 40 o menos) se quedan como estaban:
    miden lo mismo con cualquier texto y encogerlos los haría difíciles de
    pulsar.
    """
    if maximo <= 40:
        return maximo
    return min(maximo, fuente.measure(texto) + MARGEN_TEXTO)


def repartir_en_filas(anchos, disponible, hueco=0):
    """Número de línea (0, 1, …) de cada pieza, en orden y sin partir ninguna.

    Entre dos piezas de la misma línea va `hueco` (el separador). Una pieza
    más ancha que `disponible` va sola en su línea: no hay nada mejor que
    hacer con ella.
    """
    lineas, linea, usado = [], 0, 0
    for ancho in anchos:
        if usado and usado + hueco + ancho > disponible:
            linea += 1
            usado = 0
        usado = ancho if not usado else usado + hueco + ancho
        lineas.append(linea)
    return lineas


def cabe_completo(disponible, anchos, hueco=0):
    """¿Caben todas las piezas en una sola línea?"""
    if not anchos:
        return True
    return sum(anchos) + hueco * (len(anchos) - 1) <= disponible


class FilaFluida(ctk.CTkFrame):
    """Piezas de izquierda a derecha; la que no cabe baja a la línea siguiente.

    Cada pieza se crea con `nueva_pieza()` y se rellena por dentro. Entre dos
    piezas de la misma línea va un separador vertical; la primera de cada
    línea lo oculta, para que ninguna línea empiece con una raya suelta.
    """

    def __init__(self, master, color_separador, **kwargs):
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(master, **kwargs)
        self._color_separador = color_separador
        self._piezas = []        # (unidad, separador o None, cuerpo)
        self._lineas = []
        self._reparto = None
        self.bind("<Configure>", self._recolocar, add="+")

    def nueva_pieza(self, con_separador=True):
        """Devuelve el marco donde meter los botones de la pieza."""
        unidad = ctk.CTkFrame(self, fg_color="transparent")
        separador = None
        if con_separador:
            separador = ctk.CTkFrame(unidad, fg_color="transparent", width=14, height=32)
            separador.pack_propagate(False)
            ctk.CTkFrame(separador, fg_color=self._color_separador,
                         width=1, height=22).place(relx=0.5, rely=0.5, anchor="center")
        cuerpo = ctk.CTkFrame(unidad, fg_color="transparent")
        cuerpo.pack(side="left")
        self._piezas.append((unidad, separador, cuerpo))
        self._reparto = None
        self.after_idle(self._recolocar)
        return cuerpo

    def lineas(self):
        """Cuántas líneas ocupa ahora mismo (para los tests)."""
        return 1 + max(self._reparto or [0])

    def _hueco(self):
        # El separador (14) más su margen (2 a cada lado), en píxeles reales.
        return int(18 * ctk.ScalingTracker.get_widget_scaling(self))

    def _recolocar(self, _evento=None):
        try:
            if not self.winfo_exists() or not self._piezas:
                return
            disponible = self.winfo_width()
            anchos = [cuerpo.winfo_reqwidth() for _u, _s, cuerpo in self._piezas]
            if disponible <= 1:
                # Aún sin mapear: todo en una línea hasta saber cuánto hay.
                reparto = [0] * len(anchos)
            else:
                reparto = repartir_en_filas(anchos, disponible, self._hueco())
            if reparto == self._reparto:
                return
            self._reparto = reparto
            self._aplicar(reparto)
        except Exception:
            # Una ventana que se cierra a mitad de un <Configure>.
            pass

    def _aplicar(self, reparto):
        necesarias = 1 + max(reparto)
        while len(self._lineas) < necesarias:
            linea = ctk.CTkFrame(self, fg_color="transparent")
            self._lineas.append(linea)
        for i, linea in enumerate(self._lineas):
            if i < necesarias:
                linea.pack(side="top", fill="x", pady=(0, 3) if i < necesarias - 1 else 0)
            else:
                linea.pack_forget()
        anterior = None
        for (unidad, separador, cuerpo), num in zip(self._piezas, reparto):
            unidad.pack_forget()
            if separador is not None:
                if num == anterior:
                    separador.pack(side="left", padx=2, before=cuerpo)
                else:
                    separador.pack_forget()
            # Abajo: así los botones de una pieza sin título quedan a la
            # altura de los de las piezas que lo llevan.
            unidad.pack(in_=self._lineas[num], side="left", anchor="s")
            # Las líneas se crean después que algunas piezas; sin esto las
            # taparían, porque Tk apila a los hermanos por orden de creación.
            unidad.lift()
            anterior = num
