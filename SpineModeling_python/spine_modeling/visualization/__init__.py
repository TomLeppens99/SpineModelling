"""3D visualization and rendering.

This module provides VTK-based 3D rendering capabilities for OpenSim models,
including bodies, joints, muscles, markers, and interactive visualization.
"""

from .sim_model_visualization import SimModelVisualization

__all__ = ["SimModelVisualization"]
