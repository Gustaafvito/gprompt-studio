"""Capturas para el README, el release y la web.

La app se arranca de verdad y se rellena con un prompt REAL escrito a mano
(no se llama a ningun LLM: no hace falta gastar tokens para una captura, y
asi el resultado es reproducible). La geometria se pide a Tk
(winfo_rootx/rooty/width/height) y se recorta con PIL, que es mas fiable que
adivinar el rectangulo de la ventana.

Se corre con mainloop() y las capturas se disparan con after(), porque una
ventana Tk no acaba de pintarse hasta que el bucle de eventos gira: con
update() sola salen widgets a medio dibujar.
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass
import logging

logging.disable(logging.WARNING)

from PIL import ImageGrab

DEST = Path(__file__).resolve().parent.parent / "docs" / "capturas"
DEST.mkdir(parents=True, exist_ok=True)

IDEA = ("una herrera trabajando el acero al rojo vivo en su taller, "
        "chispas suspendidas en el aire, luz de fragua contra la penumbra")

PROMPT = """POSITIVE:
A weathered blacksmith woman shaping glowing orange steel on an anvil inside
a dim stone workshop, sparks frozen mid-air around her hands, deep shadows
carving out the forge behind her, warm rim light on her sweat-streaked face
and leather apron, shot on 85mm at f/2.0, shallow depth of field, fine film
grain, muted earth palette with incandescent highlights.

NEGATIVE:
blurry, low quality, deformed hands, extra fingers, cartoon, anime, 3D
render, plastic skin, oversaturated, flat lighting, text, watermark,
signature, cloned face

--- AJUSTES RECOMENDADOS ---
Sampler: DPM++ 2M Karras · Pasos: 30 · CFG: 5.5 · Ratio: 3:2
Refuerzo: manos y rostro (inpaint tras la primera pasada)"""


def capturar(widget, nombre, espera=0.35):
    """Recorta la ventana y guarda el PNG."""
    widget.update_idletasks()
    time.sleep(espera)          # que el compositor de Windows termine
    x, y = widget.winfo_rootx(), widget.winfo_rooty()
    w, h = widget.winfo_width(), widget.winfo_height()
    img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
    destino = DEST / nombre
    img.save(destino, "PNG", optimize=True)
    kb = destino.stat().st_size / 1024
    print(f"  {nombre:<28} {img.width}x{img.height}  {kb:.0f} KB")
    return destino


def main():
    from app import ArquitectoApp

    app = ArquitectoApp()
    app.geometry("1400x1000+40+6")
    # Sin esto, cualquier ventana ajena (paso una de Chrome) se cuela por
    # delante y el recorte captura el escritorio del autor, no la app.
    app.attributes("-topmost", True)
    app.lift()
    app.update()

    pasos = []

    def paso1():
        # 1) Pantalla principal CON contenido: una app vacia no vende nada.
        try:
            app.txt_idea.delete("1.0", "end")
            app.txt_idea.insert("1.0", IDEA)
        except Exception as e:
            print("  ! idea:", e)
        # Elegir un modelo que luzca lo recien anadido.
        try:
            app.combo_modelo_imagen.set("GPT Image 2.5 Sunburst")
            app.events._on_modelo_imagen_cambio()
        except Exception as e:
            print("  ! modelo:", e)
        try:
            for serv in vars(app).values():
                if hasattr(serv, "actualizar_salida"):
                    serv.actualizar_salida(PROMPT)
                    break
            else:
                app.txt_salida.delete("1.0", "end")
                app.txt_salida.insert("1.0", PROMPT)
        except Exception as e:
            print("  ! salida:", e)
        app.update()
        pasos.append(capturar(app, "01-pantalla-principal.png"))
        app.after(400, paso2)

    def paso2():
        # 2) El desplegable de modelos abierto: es LA prueba de que hay
        #    catalogo de verdad, agrupado por familias. Es un Toplevel
        #    aparte, pero cae dentro del area de la ventana, asi que el
        #    mismo recorte lo pilla.
        try:
            app.combo_modelo_imagen._open_dropdown_menu()
        except Exception as e:
            print("  ! desplegable:", e)
        app.update()
        pasos.append(capturar(app, "02-catalogo-modelos.png", 0.6))
        app.after(500, paso3)

    def paso3():
        # 3) La paleta de comandos (Ctrl+K). Segun el propio LEEME es "el
        #    mejor atajo de la app": ensena de un golpe TODO lo que hace
        #    sin fotografiar ocho menus.
        try:
            app.combo_modelo_imagen._open_dropdown_menu()   # toggle: cierra
        except Exception as e:
            print("  ! cerrar desplegable:", e)
        app.update()
        antes = set(map(id, app.winfo_children()))
        try:
            from modules.command_palette import abrir_command_palette
            abrir_command_palette(app)
        except Exception as e:
            print("  ! paleta:", e)
        app.update()
        # La paleta es un Toplevel propio: se captura SU rectangulo, no el
        # de la ventana principal, o sale recortada o tapada.
        pal = None
        for w in app.winfo_children():
            if id(w) not in antes and w.winfo_class() == "Toplevel":
                pal = w
        if pal is not None:
            try:
                pal.attributes("-topmost", True)
                pal.lift()
            except Exception:
                pass
            # Se recorta la VENTANA PRINCIPAL, no la paleta: flotando sola
            # es un menu sin contexto, y encima de la app se entiende que
            # es un buscador de herramientas dentro del programa.
            pasos.append(capturar(app, "03-paleta-comandos.png", 0.6))
        else:
            print("  ! no localizo la ventana de la paleta")
        app.after(500, fin)

    def fin():
        print("\ncapturas en", DEST)
        try:
            app.destroy()
        except Exception:
            pass

    app.after(1200, paso1)      # margen para que arranque del todo
    app.mainloop()


if __name__ == "__main__":
    main()
