"""
PreviewService: Servicio para previsualización de prompts via Pollinations.ai.

Extraído de app.py para desacoplar la lógica de red de la UI.
"""
import io
import logging

import requests
from PIL import Image

logger = logging.getLogger(__name__)


class PreviewService:
    """Servicio para generar previsualizaciones de prompts."""

    POLLINATIONS_URL = "https://image.pollinations.ai/prompt/{prompt_encoded}"

    @staticmethod
    def generate_preview(prompt: str, width: int = 512, height: int = 512,
                        seed: int = None, model: str = "flux") -> Image.Image | None:
        """Genera una imagen de preview usando Pollinations.ai.

        Args:
            prompt: Texto del prompt a previsualizar
            width: Ancho de la imagen (default 512)
            height: Alto de la imagen (default 512)
            seed: Semilla opcional para reproducibilidad
            model: Modelo a usar (flux, turbo, etc.)

        Returns:
            PIL.Image o None si falla
        """
        try:
            from urllib.parse import quote

            prompt_trunc = prompt[:800]
            encoded = quote(prompt_trunc)

            params = f"?width={width}&height={height}&model={model}"
            if seed is not None:
                params += f"&seed={seed}"

            url = f"https://image.pollinations.ai/prompt/{encoded}{params}"

            logger.debug(f"[PreviewService] Fetching: {url[:100]}...")

            response = requests.get(url, timeout=30, stream=True)
            response.raise_for_status()

            image_data = response.content
            img = Image.open(io.BytesIO(image_data))

            return img

        except requests.Timeout:
            logger.warning("[PreviewService] Timeout al obtener preview")
            return None
        except requests.RequestException as e:
            logger.warning(f"[PreviewService] Request error: {e}")
            return None
        except Exception as e:
            logger.error(f"[PreviewService] Error general: {e}")
            return None

    @staticmethod
    def save_preview(img: Image.Image, path: str) -> bool:
        """Guarda una imagen de preview a disco."""
        try:
            img.save(path)
            return True
        except Exception as e:
            logger.error(f"[PreviewService] Error guardando preview: {e}")
            return False

    @staticmethod
    def get_preview_thumbnail(img: Image.Image, size: int = 200) -> Image.Image:
        """Genera un thumbnail de la imagen."""
        try:
            img.thumbnail((size, size), Image.Resampling.LANCZOS)
            return img
        except Exception:
            return img
