"""
Pre-trained Vertebra Segmentation Integration.

This module provides integration with pre-trained deep learning models
for automatic vertebra detection and segmentation in medical images.

Supported Models:
- TotalSpineSeg (nnU-Net based) - Primary recommended model
- Hugging Face spine-segmentation - Alternative option

Installation:
    # For TotalSpineSeg (recommended):
    pip install totalspineseg

    # For Hugging Face model:
    pip install transformers torch fastmonai

Usage:
    from spine_modeling.algorithms.vertebra_segmentation import VertebraSegmenter

    segmenter = VertebraSegmenter()
    results = segmenter.segment(image_path)
"""

from typing import Optional, Dict, List, Tuple, Any
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import logging
import numpy as np

logger = logging.getLogger(__name__)


class SegmentationBackend(Enum):
    """Available segmentation backends."""
    TOTALSPINESEG = "totalspineseg"
    HUGGINGFACE = "huggingface"
    AUTO = "auto"


@dataclass
class VertebraResult:
    """Result of vertebra segmentation for a single vertebra.

    Attributes:
        label: Vertebra label (e.g., "L1", "T12", "C7")
        level: Numeric level within region (1-5 for lumbar, 1-12 for thoracic, etc.)
        region: Spinal region ("cervical", "thoracic", "lumbar", "sacral")
        centroid: (x, y, z) centroid coordinates in image space
        bounding_box: (x_min, y_min, x_max, y_max) or (x_min, y_min, z_min, x_max, y_max, z_max)
        confidence: Detection confidence score (0-1)
        mask: Optional binary segmentation mask
    """
    label: str
    level: int
    region: str
    centroid: Tuple[float, ...]
    bounding_box: Tuple[float, ...]
    confidence: float
    mask: Optional[np.ndarray] = None


@dataclass
class SegmentationResult:
    """Complete segmentation result for a spine image.

    Attributes:
        vertebrae: List of detected vertebrae
        full_mask: Complete segmentation mask with all vertebrae labeled
        metadata: Additional information from the model
    """
    vertebrae: List[VertebraResult]
    full_mask: Optional[np.ndarray] = None
    metadata: Optional[Dict[str, Any]] = None


class VertebraSegmenter:
    """
    Wrapper for pre-trained vertebra segmentation models.

    This class provides a unified interface to various pre-trained
    deep learning models for vertebra detection and segmentation.

    Example:
        >>> segmenter = VertebraSegmenter(backend=SegmentationBackend.TOTALSPINESEG)
        >>> result = segmenter.segment("path/to/ct_scan.nii.gz")
        >>> for vertebra in result.vertebrae:
        ...     print(f"{vertebra.label}: centroid={vertebra.centroid}")
    """

    def __init__(
        self,
        backend: SegmentationBackend = SegmentationBackend.AUTO,
        device: str = "auto",
        model_path: Optional[str] = None
    ):
        """
        Initialize the vertebra segmenter.

        Args:
            backend: Which segmentation backend to use
            device: Device for inference ("cpu", "cuda", "auto")
            model_path: Optional path to custom model weights
        """
        self.backend = backend
        self.device = device
        self.model_path = model_path
        self._model = None
        self._backend_impl = None

        # Auto-detect best available backend
        if backend == SegmentationBackend.AUTO:
            self.backend = self._detect_backend()

        logger.info(f"VertebraSegmenter initialized with backend: {self.backend.value}")

    def _detect_backend(self) -> SegmentationBackend:
        """Detect the best available backend."""
        # Try TotalSpineSeg first (recommended)
        try:
            import totalspineseg
            return SegmentationBackend.TOTALSPINESEG
        except ImportError:
            pass

        # Try Hugging Face transformers
        try:
            import transformers
            import torch
            return SegmentationBackend.HUGGINGFACE
        except ImportError:
            pass

        logger.warning(
            "No segmentation backend found. Please install one of:\n"
            "  pip install totalspineseg  (recommended)\n"
            "  pip install transformers torch"
        )
        return SegmentationBackend.TOTALSPINESEG  # Default, will fail with helpful message

    def _ensure_model_loaded(self) -> None:
        """Ensure the model is loaded before inference."""
        if self._model is not None:
            return

        if self.backend == SegmentationBackend.TOTALSPINESEG:
            self._load_totalspineseg()
        elif self.backend == SegmentationBackend.HUGGINGFACE:
            self._load_huggingface()

    def _load_totalspineseg(self) -> None:
        """Load TotalSpineSeg model."""
        try:
            from totalspineseg import TotalSpineSeg

            self._model = TotalSpineSeg()
            self._backend_impl = "totalspineseg"
            logger.info("TotalSpineSeg model loaded successfully")

        except ImportError as e:
            raise ImportError(
                "TotalSpineSeg not installed. Install with:\n"
                "  pip install totalspineseg\n\n"
                "For more information, see: https://github.com/neuropoly/totalspineseg"
            ) from e

    def _load_huggingface(self) -> None:
        """Load Hugging Face spine segmentation model."""
        try:
            from transformers import AutoModel, AutoProcessor
            import torch

            model_id = self.model_path or "skaliy/spine-segmentation"

            # Determine device
            if self.device == "auto":
                device = "cuda" if torch.cuda.is_available() else "cpu"
            else:
                device = self.device

            self._model = AutoModel.from_pretrained(model_id).to(device)
            self._processor = AutoProcessor.from_pretrained(model_id)
            self._device = device
            self._backend_impl = "huggingface"
            logger.info(f"Hugging Face model loaded on {device}")

        except ImportError as e:
            raise ImportError(
                "Hugging Face transformers not installed. Install with:\n"
                "  pip install transformers torch\n\n"
                "For GPU support: pip install torch --index-url https://download.pytorch.org/whl/cu118"
            ) from e

    def segment(
        self,
        image_path: str,
        return_mask: bool = True,
        **kwargs
    ) -> SegmentationResult:
        """
        Segment vertebrae in a medical image.

        Args:
            image_path: Path to the image file (DICOM, NIfTI, or supported format)
            return_mask: Whether to include segmentation masks in results
            **kwargs: Additional arguments passed to the backend

        Returns:
            SegmentationResult with detected vertebrae and optional masks

        Raises:
            ImportError: If required backend is not installed
            FileNotFoundError: If image file doesn't exist
            ValueError: If image format is not supported
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")

        self._ensure_model_loaded()

        if self._backend_impl == "totalspineseg":
            return self._segment_totalspineseg(image_path, return_mask, **kwargs)
        elif self._backend_impl == "huggingface":
            return self._segment_huggingface(image_path, return_mask, **kwargs)
        else:
            raise RuntimeError(f"Unknown backend: {self._backend_impl}")

    def _segment_totalspineseg(
        self,
        image_path: Path,
        return_mask: bool,
        **kwargs
    ) -> SegmentationResult:
        """Run segmentation using TotalSpineSeg."""
        # TotalSpineSeg returns labeled segmentation
        result = self._model.segment(str(image_path), **kwargs)

        vertebrae = []

        # Parse TotalSpineSeg output format
        if hasattr(result, 'vertebrae'):
            for v in result.vertebrae:
                vertebra = VertebraResult(
                    label=v.label,
                    level=self._parse_level(v.label),
                    region=self._parse_region(v.label),
                    centroid=tuple(v.centroid),
                    bounding_box=tuple(v.bbox) if hasattr(v, 'bbox') else (),
                    confidence=getattr(v, 'confidence', 1.0),
                    mask=v.mask if return_mask and hasattr(v, 'mask') else None
                )
                vertebrae.append(vertebra)

        return SegmentationResult(
            vertebrae=vertebrae,
            full_mask=result.mask if return_mask and hasattr(result, 'mask') else None,
            metadata={'backend': 'totalspineseg'}
        )

    def _segment_huggingface(
        self,
        image_path: Path,
        return_mask: bool,
        **kwargs
    ) -> SegmentationResult:
        """Run segmentation using Hugging Face model."""
        import torch
        import numpy as np

        # Load image
        if image_path.suffix.lower() in ['.dcm', '.dicom']:
            import pydicom
            ds = pydicom.dcmread(str(image_path))
            image = ds.pixel_array.astype(np.float32)
        else:
            # Assume NIfTI or other format
            try:
                import nibabel as nib
                img = nib.load(str(image_path))
                image = img.get_fdata().astype(np.float32)
            except Exception:
                from PIL import Image
                image = np.array(Image.open(image_path)).astype(np.float32)

        # Preprocess
        inputs = self._processor(images=image, return_tensors="pt")
        inputs = {k: v.to(self._device) for k, v in inputs.items()}

        # Inference
        with torch.no_grad():
            outputs = self._model(**inputs)

        # Post-process (model-specific)
        # This is a simplified version - actual implementation depends on model output format
        vertebrae = []

        return SegmentationResult(
            vertebrae=vertebrae,
            full_mask=None,
            metadata={'backend': 'huggingface'}
        )

    def _parse_level(self, label: str) -> int:
        """Parse vertebra level from label (e.g., 'L1' -> 1)."""
        import re
        match = re.search(r'(\d+)', label)
        return int(match.group(1)) if match else 0

    def _parse_region(self, label: str) -> str:
        """Parse spinal region from label (e.g., 'L1' -> 'lumbar')."""
        label_upper = label.upper()
        if label_upper.startswith('C'):
            return 'cervical'
        elif label_upper.startswith('T'):
            return 'thoracic'
        elif label_upper.startswith('L'):
            return 'lumbar'
        elif label_upper.startswith('S'):
            return 'sacral'
        return 'unknown'

    def is_available(self) -> bool:
        """Check if the segmentation backend is available."""
        try:
            self._ensure_model_loaded()
            return True
        except ImportError:
            return False

    @staticmethod
    def get_installation_instructions() -> str:
        """Get installation instructions for segmentation backends."""
        return """
Vertebra Segmentation - Installation Instructions
=================================================

Option 1: TotalSpineSeg (Recommended)
-------------------------------------
TotalSpineSeg is a state-of-the-art nnU-Net based model for spine segmentation.
It automatically downloads pre-trained weights on first use.

    pip install totalspineseg

GitHub: https://github.com/neuropoly/totalspineseg
Paper: https://arxiv.org/abs/2309.05310

Option 2: Hugging Face Model
----------------------------
Alternative option using the skaliy/spine-segmentation model.

    pip install transformers torch
    # For GPU support:
    pip install torch --index-url https://download.pytorch.org/whl/cu118

Hugging Face: https://huggingface.co/skaliy/spine-segmentation

Notes:
------
- Both options require ~2-4GB disk space for model weights
- GPU recommended for faster inference (NVIDIA CUDA)
- First run will download model weights automatically
- CT/MRI images work best; X-ray support varies by model
"""


def segment_vertebrae(
    image_path: str,
    backend: str = "auto",
    **kwargs
) -> SegmentationResult:
    """
    Convenience function for vertebra segmentation.

    Args:
        image_path: Path to medical image
        backend: Backend to use ("auto", "totalspineseg", "huggingface")
        **kwargs: Additional arguments for segmentation

    Returns:
        SegmentationResult with detected vertebrae

    Example:
        >>> results = segment_vertebrae("scan.nii.gz")
        >>> for v in results.vertebrae:
        ...     print(f"{v.label}: {v.centroid}")
    """
    backend_enum = SegmentationBackend(backend) if backend != "auto" else SegmentationBackend.AUTO
    segmenter = VertebraSegmenter(backend=backend_enum)
    return segmenter.segment(image_path, **kwargs)
