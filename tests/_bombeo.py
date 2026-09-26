"""Dejar correr los eventos de Tk un rato, sin poder colgarse.

EL CUELGUE (encontrado el 24-sep-2026 con la bitácora de cuelgues)
Los tests «bombeaban» así:

    root.after(ms, root.quit)
    root.mainloop()

y se quedaban colgados de vez en cuando, siempre en ese `mainloop()`. Tres
volcados distintos, los tres igual. La causa: la PRIMERA vez que se llama a
`CTk.mainloop()`, CustomTkinter hace un `update()` para pintar la barra de
título de Windows antes de arrancar el bucle de verdad. Si para entonces el
temporizador del `quit` ya ha vencido —porque construir la ventana tardó más
que `ms`—, el `quit` se ejecuta dentro de ese `update()`. Y `_tkinter` pone a
cero la marca de salida al empezar el bucle: el `quit` se pierde y el bucle
no termina nunca.

Reproducido a propósito en tests/test_bombeo.py: con el temporizador
vencido, el patrón viejo no vuelve.

Por eso se cuelga «a veces» y más con la máquina cargada: depende de si la
construcción tarda más o menos que la espera.

EL ARREGLO
Bombear con `update()` durante el tiempo pedido. `update()` atiende los
temporizadores que van venciendo, que es lo único que buscaban los tests, y
no depende de ningún `quit`.
"""
import time


def bombear(widget, ms=120):
    """Atiende eventos y temporizadores de Tk durante `ms` milisegundos."""
    fin = time.monotonic() + ms / 1000
    while True:
        widget.update()
        if time.monotonic() >= fin:
            return
        time.sleep(0.01)
