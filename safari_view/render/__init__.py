"""
SafariView Rendering Pipeline and Modes.
"""

from safari_view.render.mode_800 import Mode800Transformer
from safari_view.render.mode_2600 import Mode2600Transformer
from safari_view.render.mode_st import ModeSTTransformer, NativeTransformer
from safari_view.render.pipeline import Pipeline, RenderContext, RenderMode

__all__ = [
    "Pipeline",
    "RenderContext",
    "RenderMode",
    "Mode2600Transformer",
    "Mode800Transformer",
    "ModeSTTransformer",
    "NativeTransformer",
]


def create_pipeline() -> Pipeline:
    """Create a default rendering pipeline."""
    transformers = {
        RenderMode.MODE_2600: Mode2600Transformer(),
        RenderMode.MODE_800: Mode800Transformer(),
        RenderMode.MODE_ST: ModeSTTransformer(),
        RenderMode.NATIVE: NativeTransformer(),
    }
    return Pipeline(transformers)
