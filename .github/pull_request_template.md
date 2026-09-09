## Qué cambia

<!-- Una frase. Si hace falta más, probablemente sean dos PR. -->

## Por qué

<!-- El problema que resuelve. Si hay un issue, enlázalo: «Cierra #12». -->

## Cómo lo has comprobado

<!-- Qué probaste y qué salió. «Pasan los tests» no basta si el cambio se
     ve en la interfaz o depende de un proveedor: dilo. -->

- [ ] `pytest tests/ -q` en verde
- [ ] `ruff check .` limpio
- [ ] Si toca el catálogo de modelos, la ficha está **medida generando**, no
      copiada de la documentación
- [ ] Si añade texto en la interfaz, tiene su traducción al inglés en
      `modules/i18n.py`
