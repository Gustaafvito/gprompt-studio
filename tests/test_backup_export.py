"""Tests de BackupExportService — completitud del backup.

Regresión del fix de sesión 20: `paletas` (7ª colección del store) se quedaba
fuera del backup. Este test asegura que TODAS las colecciones de archivo del
store viajan en el backup, para que no se vuelva a olvidar ninguna al añadir
colecciones nuevas.
"""
from types import SimpleNamespace

from modules.backup_export import BackupExportService

# Colecciones de archivo que DataStore gestiona (deben estar todas en el backup)
COLECCIONES_STORE = [
    "historial", "favoritos", "estrellas",
    "personajes", "loras", "plantillas", "paletas",
]


def _fake_app():
    store = SimpleNamespace(
        **{c: [{"x": i}] for i, c in enumerate(COLECCIONES_STORE)},
        cargar_preferencias=lambda: {"tema": "dark"},
    )
    return SimpleNamespace(store=store)


def test_backup_incluye_todas_las_colecciones():
    svc = BackupExportService(_fake_app())
    backup = svc._construir_backup()
    for col in COLECCIONES_STORE:
        assert col in backup, f"el backup omite la colección '{col}'"
    assert "preferencias" in backup


def test_backup_incluye_paletas_concretamente():
    """Guard explícito del bug que se arregló: paletas presentes."""
    svc = BackupExportService(_fake_app())
    backup = svc._construir_backup()
    assert "paletas" in backup
    assert backup["paletas"] == [{"x": 6}]
