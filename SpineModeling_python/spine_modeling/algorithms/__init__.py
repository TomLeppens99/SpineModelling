"""Core algorithms for biomechanical analysis.

This module contains key algorithms including ellipse fitting,
template-based ellipse placement, automatic marker detection,
vertebra segmentation, coordinate transformations, and biomechanical calculations.
"""

from .ellipse_fit import EllipseFit, fit_ellipse_to_points
from .ellipse_template import (
    EllipseTemplate,
    EllipseParameters,
    MarkerType,
    CircularMarkerDetector,
    EllipsePlacementManager,
    DetectedMarker,
)
from .vertebra_segmentation import (
    VertebraSegmenter,
    VertebraResult,
    SegmentationResult,
    SegmentationBackend,
    segment_vertebrae,
)

__all__ = [
    # Ellipse fitting (eigenvalue-based)
    'EllipseFit',
    'fit_ellipse_to_points',
    # Template-based placement (fixed sizes)
    'EllipseTemplate',
    'EllipseParameters',
    'MarkerType',
    # Automatic marker detection
    'CircularMarkerDetector',
    'DetectedMarker',
    # Ellipse workflow manager
    'EllipsePlacementManager',
    # Vertebra segmentation (pre-trained models)
    'VertebraSegmenter',
    'VertebraResult',
    'SegmentationResult',
    'SegmentationBackend',
    'segment_vertebrae',
]
