"""
ComfyUIWorkflowExporter: Exportador de prompts a workflows de ComfyUI.

Genera archivos .json que pueden ser arrastrados directamente a ComfyUI.
"""
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ComfyUIWorkflowExporter:
    """Exportador de prompts optimizados a workflows de ComfyUI."""

    @staticmethod
    def export_to_workflow(
        positive: str,
        negative: str = "",
        modelo: str = "flux",
        width: int = 1024,
        height: int = 1024,
        steps: int = 30,
        cfg: float = 3.5,
        sampler: str = "euler",
        seed: Optional[int] = None,
        loras: list = None,
        output_name: str = "prompt_export"
    ) -> Dict[str, Any]:
        """Genera un workflow JSON para ComfyUI.

        Args:
            positive: Prompt positivo
            negative: Prompt negativo
            modelo: Modelo base (flux, sd, etc.)
            width/height: Dimensiones de salida
            steps: Pasos de inferencia
            cfg: Guidance scale
            sampler: Sampler a usar
            seed: Semilla para reproducibilidad
            loras: Lista de diccionarios {nombre, peso}
            output_name: Nombre del archivo de salida

        Returns:
            Dict con el workflow listo para guardar como .json
        """
        workflow = {
            "last_node_id": 0,
            "last_link_id": 0,
            "nodes": [],
            "links": [],
            "version": 0.4
        }

        node_id = 1

        clip_loader = {
            "id": node_id,
            "type": "CLIPLoader",
            "pos": [100, 200],
            "size": [300, 80],
            "flags": {},
            "order": 0,
            "properties": {},
            "widgets_values": ["t5ixxl_fp8_safetensors.safetensors"]
        }
        workflow["nodes"].append(clip_loader)
        node_id += 1

        clip_node = {
            "id": node_id,
            "type": "CLIPTextEncode",
            "pos": [400, 200],
            "size": [400, 200],
            "flags": {},
            "order": 1,
            "properties": {},
            "widgets_values": [positive]
        }
        workflow["nodes"].append(clip_node)
        workflow["links"].append([node_id - 1, node_id, 0, 0, 1])
        node_id += 1

        neg_node = {
            "id": node_id,
            "type": "CLIPTextEncode",
            "pos": [400, 450],
            "size": [400, 200],
            "flags": {},
            "order": 2,
            "properties": {},
            "widgets_values": [negative or "worst quality, low quality"]
        }
        workflow["nodes"].append(neg_node)
        workflow["links"].append([node_id - 2, node_id, 0, 0, 2])
        neg_node_id = node_id
        node_id += 1

        model_node = {
            "id": node_id,
            "type": "DualCLIPLoader" if modelo.startswith("flux") else "CLIPLoader",
            "pos": [100, 400],
            "size": [300, 100],
            "flags": {},
            "order": 3,
            "properties": {},
            "widgets_values": [
                "flux1-dev.safetensors" if modelo.startswith("flux") else "sd_xl_base_1.0.safetensors",
                "t5ixxl_fp8_safetensors.safetensors"
            ] if modelo.startswith("flux") else ["t5xxl_fp8_e4m3fn.safetensors"]
        }
        workflow["nodes"].append(model_node)
        node_id += 1

        ksampler = {
            "id": node_id,
            "type": "KSampler",
            "pos": [700, 300],
            "size": [300, 200],
            "flags": {},
            "order": 4,
            "properties": {},
            "widgets_values": [
                seed or 42,
                "fixed",
                steps,
                cfg,
                sampler,
                "normal",
                1.0
            ]
        }
        workflow["nodes"].append(ksampler)
        for link_id in range(1, node_id):
            workflow["links"].append([link_id, node_id, 0, 0, link_id])
        node_id += 1

        vae_loader = {
            "id": node_id,
            "type": "VAELoader",
            "pos": [100, 600],
            "size": [300, 80],
            "flags": {},
            "order": 5,
            "properties": {},
            "widgets_values": ["flux_vae_t5xxl_fp8_safetensors.safetensors"]
        }
        workflow["nodes"].append(vae_loader)
        node_id += 1

        vae_decode = {
            "id": node_id,
            "type": "VAEDecode",
            "pos": [1000, 300],
            "size": [300, 100],
            "flags": {},
            "order": 6,
            "properties": {},
            "widgets_values": []
        }
        workflow["nodes"].append(vae_decode)
        node_id += 1

        save_node = {
            "id": node_id,
            "type": "SaveImage",
            "pos": [1300, 300],
            "size": [300, 300],
            "flags": {},
            "order": 7,
            "properties": {},
            "widgets_values": [output_name]
        }
        workflow["nodes"].append(save_node)

        workflow["last_node_id"] = node_id
        workflow["last_link_id"] = len(workflow["links"])

        return workflow

    @staticmethod
    def save_workflow(workflow: Dict, filepath: str) -> bool:
        """Guarda un workflow a un archivo JSON."""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(workflow, f, indent=2, ensure_ascii=False)
            logger.info(f"[ComfyUIExporter] Workflow guardado: {filepath}")
            return True
        except Exception as e:
            logger.error(f"[ComfyUIExporter] Error guardando workflow: {e}")
            return False

    @staticmethod
    def export_simple_sdxl(
        positive: str,
        negative: str = "",
        seed: Optional[int] = None,
        steps: int = 30,
        cfg: float = 7.0
    ) -> Dict[str, Any]:
        """Genera un workflow simplificado para SDXL."""
        return ComfyUIWorkflowExporter.export_to_workflow(
            positive=positive,
            negative=negative,
            modelo="sdxl",
            width=1024,
            height=1024,
            steps=steps,
            cfg=cfg,
            sampler="euler_a",
            seed=seed
        )

    @staticmethod
    def export_simple_flux(
        positive: str,
        negative: str = "",
        seed: Optional[int] = None,
        steps: int = 25,
        cfg: float = 1.0
    ) -> Dict[str, Any]:
        """Genera un workflow simplificado para Flux."""
        return ComfyUIWorkflowExporter.export_to_workflow(
            positive=positive,
            negative=negative,
            modelo="flux",
            width=1024,
            height=1024,
            steps=steps,
            cfg=cfg,
            sampler="euler",
            seed=seed
        )