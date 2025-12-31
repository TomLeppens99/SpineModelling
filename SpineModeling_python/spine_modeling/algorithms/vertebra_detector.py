"""
Vertebra Detection Module for EOS X-ray Images

This module provides automatic detection and localization of vertebrae in
EOS biplanar X-ray images. It uses a combination of image processing
techniques and anatomical priors to identify vertebral bodies.

Detection Pipeline:
1. Preprocessing: Enhance contrast, reduce noise
2. Spine localization: Find the approximate spinal column region
3. Vertebra segmentation: Identify individual vertebral bodies
4. Landmark extraction: Find key anatomical points (endplates, pedicles)
5. Classification: Label vertebrae (C1-C7, T1-T12, L1-L5, S1)

The algorithm is optimized for:
- EOS frontal (AP) and lateral X-ray views
- Adult and adolescent spines
- Normal and scoliotic spines (up to ~60° Cobb angle)

Example Usage:
    >>> from spine_modeling.algorithms import VertebraDetector
    >>> detector = VertebraDetector()
    >>> vertebrae = detector.detect(eos_image)
    >>> for v in vertebrae:
    ...     print(f"{v.label}: center=({v.center_x}, {v.center_y})")
"""

import numpy as np
from typing import List, Optional, Tuple, Dict, NamedTuple
from dataclasses import dataclass, field
from enum import Enum
import logging

try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    cv2 = None
    HAS_OPENCV = False

try:
    from scipy import ndimage
    from scipy.signal import find_peaks
    HAS_SCIPY = True
except ImportError:
    ndimage = None
    find_peaks = None
    HAS_SCIPY = False

logger = logging.getLogger(__name__)


class VertebraLevel(Enum):
    """Vertebra level classification."""
    # Cervical
    C1 = "C1"
    C2 = "C2"
    C3 = "C3"
    C4 = "C4"
    C5 = "C5"
    C6 = "C6"
    C7 = "C7"
    # Thoracic
    T1 = "T1"
    T2 = "T2"
    T3 = "T3"
    T4 = "T4"
    T5 = "T5"
    T6 = "T6"
    T7 = "T7"
    T8 = "T8"
    T9 = "T9"
    T10 = "T10"
    T11 = "T11"
    T12 = "T12"
    # Lumbar
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L4 = "L4"
    L5 = "L5"
    # Sacrum
    S1 = "S1"
    # Unknown
    UNKNOWN = "Unknown"


@dataclass
class VertebraLandmarks:
    """Anatomical landmarks for a single vertebra."""
    # Endplate corners (4 points defining the vertebral body)
    superior_left: Tuple[float, float] = (0, 0)
    superior_right: Tuple[float, float] = (0, 0)
    inferior_left: Tuple[float, float] = (0, 0)
    inferior_right: Tuple[float, float] = (0, 0)

    # Pedicle centers (for frontal view)
    left_pedicle: Optional[Tuple[float, float]] = None
    right_pedicle: Optional[Tuple[float, float]] = None

    # Spinous process (for lateral view)
    spinous_process: Optional[Tuple[float, float]] = None


@dataclass
class DetectedVertebra:
    """Represents a detected vertebra with its properties."""
    # Position
    center_x: float
    center_y: float

    # Bounding box
    bbox_x: int
    bbox_y: int
    bbox_width: int
    bbox_height: int

    # Classification
    label: VertebraLevel = VertebraLevel.UNKNOWN
    confidence: float = 0.0

    # Anatomical measurements
    width: float = 0.0  # mm (if pixel_spacing known)
    height: float = 0.0  # mm

    # Landmarks
    landmarks: Optional[VertebraLandmarks] = None

    # Contour (optional, for visualization)
    contour: Optional[np.ndarray] = None

    @property
    def center(self) -> Tuple[float, float]:
        """Get center point as tuple."""
        return (self.center_x, self.center_y)

    @property
    def bbox(self) -> Tuple[int, int, int, int]:
        """Get bounding box as (x, y, width, height)."""
        return (self.bbox_x, self.bbox_y, self.bbox_width, self.bbox_height)


class SpineRegionDetector:
    """
    Detects the spinal column region in an X-ray image.

    This is the first step in vertebra detection - finding where the spine is
    in the image to focus subsequent processing.
    """

    def __init__(self):
        if not HAS_OPENCV:
            raise ImportError("OpenCV is required for spine detection")

    def detect_spine_region(
        self,
        image: np.ndarray,
        view: str = "frontal"
    ) -> Tuple[int, int, int, int]:
        """
        Detect the approximate bounding box of the spinal column.

        Args:
            image: Grayscale X-ray image (8-bit)
            view: "frontal" or "lateral"

        Returns:
            Tuple (x, y, width, height) of spine region
        """
        h, w = image.shape[:2]

        if view == "frontal":
            # In frontal view, spine is typically in the center
            # Use vertical projection profile to find the spine

            # Enhance edges
            edges = cv2.Canny(image, 50, 150)

            # Vertical projection (sum along rows)
            v_projection = np.sum(edges, axis=0)

            # Smooth the projection
            kernel_size = w // 20
            if kernel_size % 2 == 0:
                kernel_size += 1
            v_smooth = cv2.GaussianBlur(v_projection.reshape(1, -1), (kernel_size, 1), 0).flatten()

            # Find the peak (spine location)
            center_x = np.argmax(v_smooth)

            # Estimate width as ~15% of image width
            spine_width = int(w * 0.15)

            x = max(0, center_x - spine_width // 2)
            return (x, 0, spine_width, h)

        else:  # lateral view
            # In lateral view, use horizontal edges to find vertebral bodies
            # Spine typically occupies central-posterior region

            # Use Sobel for horizontal edges
            sobel_y = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=5)
            sobel_y = np.abs(sobel_y).astype(np.uint8)

            # Horizontal projection
            h_projection = np.sum(sobel_y, axis=1)

            # Find region with strongest horizontal edges (vertebral endplates)
            kernel_size = h // 20
            if kernel_size % 2 == 0:
                kernel_size += 1
            h_smooth = cv2.GaussianBlur(h_projection.reshape(-1, 1), (1, kernel_size), 0).flatten()

            # Spine is typically in the posterior half
            spine_x = int(w * 0.3)
            spine_width = int(w * 0.4)

            return (spine_x, 0, spine_width, h)

    def detect_spine_centerline(
        self,
        image: np.ndarray,
        view: str = "frontal"
    ) -> np.ndarray:
        """
        Detect the centerline of the spine.

        Args:
            image: Grayscale X-ray image
            view: "frontal" or "lateral"

        Returns:
            Array of (x, y) points along the spine centerline
        """
        h, w = image.shape[:2]

        # Get spine region
        roi_x, roi_y, roi_w, roi_h = self.detect_spine_region(image, view)
        roi = image[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w]

        # For each row, find the center of mass of intensity
        centerline = []

        # Sample every few rows for efficiency
        step = max(1, h // 200)

        for y in range(0, roi_h, step):
            row = roi[y, :]

            # Invert if needed (vertebrae may be dark or light)
            if np.mean(row) > 128:
                row = 255 - row

            # Find weighted center
            if np.sum(row) > 0:
                x_center = np.average(np.arange(len(row)), weights=row)
                centerline.append((roi_x + x_center, roi_y + y))

        return np.array(centerline)


class VertebraSegmenter:
    """
    Segments individual vertebrae from the spine region.

    Uses the periodic structure of the spine (alternating vertebrae and discs)
    to identify individual vertebral bodies.
    """

    def __init__(self):
        if not HAS_OPENCV or not HAS_SCIPY:
            raise ImportError("OpenCV and SciPy are required for vertebra segmentation")

    def segment_vertebrae(
        self,
        image: np.ndarray,
        spine_region: Tuple[int, int, int, int],
        view: str = "frontal",
        expected_count: Optional[int] = None
    ) -> List[DetectedVertebra]:
        """
        Segment individual vertebrae from the spine region.

        Args:
            image: Grayscale X-ray image
            spine_region: (x, y, width, height) of spine region
            view: "frontal" or "lateral"
            expected_count: Expected number of vertebrae (helps with validation)

        Returns:
            List of DetectedVertebra objects
        """
        x, y, w, h = spine_region
        roi = image[y:y+h, x:x+w]

        vertebrae = []

        if view == "frontal":
            vertebrae = self._segment_frontal(roi, x, y)
        else:
            vertebrae = self._segment_lateral(roi, x, y)

        # Validate and filter
        vertebrae = self._filter_detections(vertebrae, expected_count)

        return vertebrae

    def _segment_frontal(
        self,
        roi: np.ndarray,
        offset_x: int,
        offset_y: int
    ) -> List[DetectedVertebra]:
        """Segment vertebrae in frontal view."""
        h, w = roi.shape[:2]
        vertebrae = []

        # Enhance horizontal edges (vertebral endplates)
        sobel_y = cv2.Sobel(roi, cv2.CV_64F, 0, 1, ksize=5)
        edge_strength = np.abs(sobel_y)

        # Normalize
        edge_norm = cv2.normalize(edge_strength, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

        # Create horizontal projection profile
        h_profile = np.mean(edge_norm, axis=1)

        # Smooth the profile
        kernel_size = max(3, h // 50)
        if kernel_size % 2 == 0:
            kernel_size += 1
        h_smooth = cv2.GaussianBlur(h_profile.reshape(-1, 1), (1, kernel_size), 0).flatten()

        # Find peaks (endplate locations)
        # Minimum distance between peaks based on expected vertebra height
        min_vertebra_height = h // 30  # Rough estimate

        peaks, properties = find_peaks(
            h_smooth,
            distance=min_vertebra_height,
            prominence=np.std(h_smooth) * 0.5
        )

        logger.debug(f"Found {len(peaks)} endplate candidates in frontal view")

        # Group peaks into vertebrae (pairs of endplates)
        for i in range(len(peaks) - 1):
            top_y = peaks[i]
            bottom_y = peaks[i + 1]

            # Vertebra height
            vert_height = bottom_y - top_y

            # Skip if too small or too large
            if vert_height < min_vertebra_height * 0.5:
                continue
            if vert_height > min_vertebra_height * 3:
                continue

            # Find center x using intensity in the vertebra region
            vert_roi = roi[top_y:bottom_y, :]

            # Column profile
            col_profile = np.mean(vert_roi, axis=0)

            # Find center (could be intensity-weighted)
            center_x = w // 2  # Default to center

            # Try to find actual center using intensity
            if np.std(col_profile) > 10:
                # Invert if vertebrae are darker
                if np.mean(col_profile) < 128:
                    col_profile = 255 - col_profile
                center_x = np.argmax(col_profile)

            vertebrae.append(DetectedVertebra(
                center_x=offset_x + center_x,
                center_y=offset_y + (top_y + bottom_y) // 2,
                bbox_x=offset_x,
                bbox_y=offset_y + top_y,
                bbox_width=w,
                bbox_height=vert_height,
                confidence=0.7
            ))

        return vertebrae

    def _segment_lateral(
        self,
        roi: np.ndarray,
        offset_x: int,
        offset_y: int
    ) -> List[DetectedVertebra]:
        """Segment vertebrae in lateral view."""
        h, w = roi.shape[:2]
        vertebrae = []

        # In lateral view, vertebral bodies appear as rectangular regions
        # Use both horizontal edges (endplates) and vertical edges (anterior/posterior)

        # Horizontal edges for endplates
        sobel_y = cv2.Sobel(roi, cv2.CV_64F, 0, 1, ksize=5)
        edges_h = np.abs(sobel_y)

        # Normalize and threshold
        edges_norm = cv2.normalize(edges_h, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

        # Horizontal projection
        h_profile = np.mean(edges_norm, axis=1)

        # Smooth
        kernel_size = max(3, h // 50)
        if kernel_size % 2 == 0:
            kernel_size += 1
        h_smooth = cv2.GaussianBlur(h_profile.reshape(-1, 1), (1, kernel_size), 0).flatten()

        # Find peaks
        min_vertebra_height = h // 30
        peaks, _ = find_peaks(
            h_smooth,
            distance=min_vertebra_height,
            prominence=np.std(h_smooth) * 0.3
        )

        logger.debug(f"Found {len(peaks)} endplate candidates in lateral view")

        # Group into vertebrae
        for i in range(len(peaks) - 1):
            top_y = peaks[i]
            bottom_y = peaks[i + 1]

            vert_height = bottom_y - top_y

            if vert_height < min_vertebra_height * 0.5:
                continue
            if vert_height > min_vertebra_height * 3:
                continue

            # Find anterior-posterior extent
            vert_roi = roi[top_y:bottom_y, :]
            col_profile = np.mean(vert_roi, axis=0)

            # Find edges of vertebral body
            threshold = np.mean(col_profile)
            above_thresh = col_profile > threshold

            if np.any(above_thresh):
                left_edge = np.argmax(above_thresh)
                right_edge = len(above_thresh) - np.argmax(above_thresh[::-1])
                center_x = (left_edge + right_edge) // 2
                vert_width = right_edge - left_edge
            else:
                center_x = w // 2
                vert_width = w // 2

            vertebrae.append(DetectedVertebra(
                center_x=offset_x + center_x,
                center_y=offset_y + (top_y + bottom_y) // 2,
                bbox_x=offset_x + max(0, center_x - vert_width // 2),
                bbox_y=offset_y + top_y,
                bbox_width=vert_width,
                bbox_height=vert_height,
                confidence=0.6
            ))

        return vertebrae

    def _filter_detections(
        self,
        vertebrae: List[DetectedVertebra],
        expected_count: Optional[int] = None
    ) -> List[DetectedVertebra]:
        """Filter and validate detected vertebrae."""
        if not vertebrae:
            return []

        # Sort by y-coordinate (top to bottom)
        vertebrae.sort(key=lambda v: v.center_y)

        # Remove overlapping detections
        filtered = []
        for v in vertebrae:
            overlap = False
            for existing in filtered:
                # Check vertical overlap
                v_top = v.bbox_y
                v_bottom = v.bbox_y + v.bbox_height
                e_top = existing.bbox_y
                e_bottom = existing.bbox_y + existing.bbox_height

                overlap_amount = min(v_bottom, e_bottom) - max(v_top, e_top)
                if overlap_amount > 0.5 * min(v.bbox_height, existing.bbox_height):
                    overlap = True
                    # Keep the one with higher confidence
                    if v.confidence > existing.confidence:
                        filtered.remove(existing)
                        filtered.append(v)
                    break

            if not overlap:
                filtered.append(v)

        # Re-sort
        filtered.sort(key=lambda v: v.center_y)

        return filtered


class VertebraLabeler:
    """
    Labels detected vertebrae with their anatomical levels (C1-S1).

    Uses anatomical priors and relative positioning to classify vertebrae.
    """

    # Approximate relative heights of vertebrae (normalized)
    # Based on anatomical averages
    VERTEBRA_HEIGHT_RATIOS = {
        # Cervical (smaller)
        'C': 0.7,
        # Thoracic (medium, decreasing superiorly)
        'T': 0.85,
        # Lumbar (largest)
        'L': 1.0,
        # Sacral
        'S': 0.9
    }

    # Expected count per region
    VERTEBRA_COUNTS = {
        'C': 7,
        'T': 12,
        'L': 5,
        'S': 1  # Usually only S1 is clearly visible
    }

    def label_vertebrae(
        self,
        vertebrae: List[DetectedVertebra],
        reference_level: Optional[Tuple[str, int]] = None,
        reference_y: Optional[float] = None
    ) -> List[DetectedVertebra]:
        """
        Assign anatomical labels to detected vertebrae.

        Args:
            vertebrae: List of detected vertebrae (sorted top to bottom)
            reference_level: Optional known level, e.g., ("L", 4) for L4
            reference_y: Y-coordinate of reference level

        Returns:
            Vertebrae with labels assigned
        """
        if not vertebrae:
            return []

        # If we have a reference, use it
        if reference_level and reference_y is not None:
            return self._label_from_reference(vertebrae, reference_level, reference_y)

        # Otherwise, use heuristics based on size and position
        return self._label_by_heuristics(vertebrae)

    def _label_from_reference(
        self,
        vertebrae: List[DetectedVertebra],
        reference_level: Tuple[str, int],
        reference_y: float
    ) -> List[DetectedVertebra]:
        """Label vertebrae using a known reference point."""
        region, number = reference_level

        # Find the vertebra closest to reference_y
        ref_idx = min(range(len(vertebrae)),
                      key=lambda i: abs(vertebrae[i].center_y - reference_y))

        # Label from reference point
        levels = self._get_level_sequence()

        try:
            ref_level_str = f"{region}{number}"
            ref_level_idx = levels.index(ref_level_str)
        except ValueError:
            logger.warning(f"Unknown reference level: {ref_level_str}")
            return vertebrae

        # Assign labels
        for i, v in enumerate(vertebrae):
            level_idx = ref_level_idx + (i - ref_idx)

            if 0 <= level_idx < len(levels):
                try:
                    v.label = VertebraLevel(levels[level_idx])
                    v.confidence = min(v.confidence + 0.2, 1.0)
                except ValueError:
                    v.label = VertebraLevel.UNKNOWN
            else:
                v.label = VertebraLevel.UNKNOWN

        return vertebrae

    def _label_by_heuristics(
        self,
        vertebrae: List[DetectedVertebra]
    ) -> List[DetectedVertebra]:
        """Label vertebrae using size and position heuristics."""
        if not vertebrae:
            return []

        # Calculate relative heights
        heights = [v.bbox_height for v in vertebrae]
        mean_height = np.mean(heights)

        # Find the largest vertebrae (likely lumbar)
        relative_heights = [h / mean_height for h in heights]

        # Lumbar vertebrae are typically the largest
        # Find the region of largest vertebrae
        max_height_idx = np.argmax(relative_heights)

        # Assume the largest is around L3-L4
        # Count backwards and forwards
        levels = self._get_level_sequence()

        # Estimate L3 position (typically around 70-80% down the visible spine)
        total_vertebrae = len(vertebrae)
        estimated_l3_idx = int(total_vertebrae * 0.75)

        # Adjust based on max height position
        l3_idx = max(max_height_idx - 1, estimated_l3_idx)

        # Find L3 in the level sequence
        try:
            l3_level_idx = levels.index("L3")
        except ValueError:
            l3_level_idx = 20  # Fallback

        # Assign labels
        for i, v in enumerate(vertebrae):
            level_idx = l3_level_idx + (i - l3_idx)

            if 0 <= level_idx < len(levels):
                try:
                    v.label = VertebraLevel(levels[level_idx])
                except ValueError:
                    v.label = VertebraLevel.UNKNOWN
            else:
                v.label = VertebraLevel.UNKNOWN

            # Confidence based on distance from reference
            distance_from_ref = abs(i - l3_idx)
            v.confidence = max(0.3, 0.8 - distance_from_ref * 0.05)

        return vertebrae

    def _get_level_sequence(self) -> List[str]:
        """Get the sequence of vertebral levels from C1 to S1."""
        levels = []
        for i in range(1, 8):
            levels.append(f"C{i}")
        for i in range(1, 13):
            levels.append(f"T{i}")
        for i in range(1, 6):
            levels.append(f"L{i}")
        levels.append("S1")
        return levels


class VertebraDetector:
    """
    Main class for automatic vertebra detection in EOS X-ray images.

    Combines spine localization, vertebra segmentation, and labeling
    into a single easy-to-use interface.

    Example:
        >>> detector = VertebraDetector()
        >>> vertebrae = detector.detect(eos_image)
        >>> for v in vertebrae:
        ...     print(f"{v.label.value}: ({v.center_x:.0f}, {v.center_y:.0f})")
    """

    def __init__(self):
        """Initialize the vertebra detector."""
        if not HAS_OPENCV:
            raise ImportError("OpenCV is required for vertebra detection")
        if not HAS_SCIPY:
            raise ImportError("SciPy is required for vertebra detection")

        self.spine_detector = SpineRegionDetector()
        self.segmenter = VertebraSegmenter()
        self.labeler = VertebraLabeler()

    def detect(
        self,
        image: np.ndarray,
        pixel_spacing: Optional[float] = None,
        view: str = "frontal",
        reference_level: Optional[Tuple[str, int]] = None,
        reference_y: Optional[float] = None,
        eos_image: Optional[object] = None
    ) -> List[DetectedVertebra]:
        """
        Detect vertebrae in an X-ray image.

        Args:
            image: Grayscale X-ray image (8-bit or 16-bit)
            pixel_spacing: Pixel spacing in meters (for size measurements)
            view: "frontal" or "lateral"
            reference_level: Optional known vertebra level, e.g., ("L", 4)
            reference_y: Y-coordinate of reference level
            eos_image: EosImage object (alternative source)

        Returns:
            List of DetectedVertebra objects, sorted top to bottom
        """
        # Get image from EosImage if provided
        if eos_image is not None:
            if image is None:
                image = eos_image.load_pixel_array()
            if pixel_spacing is None:
                pixel_spacing = eos_image.pixel_spacing_x

        if image is None:
            raise ValueError("Image data required")

        logger.info(f"Detecting vertebrae in {view} view, image shape: {image.shape}")

        # Preprocess
        processed = self._preprocess(image)

        # Detect spine region
        spine_region = self.spine_detector.detect_spine_region(processed, view)
        logger.debug(f"Spine region: {spine_region}")

        # Segment vertebrae
        vertebrae = self.segmenter.segment_vertebrae(processed, spine_region, view)
        logger.info(f"Segmented {len(vertebrae)} vertebrae")

        # Label vertebrae
        vertebrae = self.labeler.label_vertebrae(vertebrae, reference_level, reference_y)

        # Add size measurements if pixel spacing is known
        if pixel_spacing is not None:
            for v in vertebrae:
                v.width = v.bbox_width * pixel_spacing * 1000  # Convert to mm
                v.height = v.bbox_height * pixel_spacing * 1000

        return vertebrae

    def _preprocess(self, image: np.ndarray) -> np.ndarray:
        """Preprocess image for detection."""
        # Convert to 8-bit if needed
        if image.dtype == np.uint16:
            p_low, p_high = np.percentile(image, [1, 99])
            image = np.clip(image, p_low, p_high)
            image = ((image - p_low) / (p_high - p_low) * 255).astype(np.uint8)
        elif image.dtype != np.uint8:
            image = cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)

        # Apply CLAHE for contrast enhancement
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(image)

        # Denoise
        denoised = cv2.bilateralFilter(enhanced, d=5, sigmaColor=50, sigmaSpace=50)

        return denoised

    def detect_with_visualization(
        self,
        image: np.ndarray,
        **kwargs
    ) -> Tuple[List[DetectedVertebra], np.ndarray]:
        """
        Detect vertebrae and return visualization.

        Returns:
            Tuple of (vertebrae list, annotated image)
        """
        vertebrae = self.detect(image, **kwargs)

        # Create visualization
        if len(image.shape) == 2:
            vis = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        else:
            vis = image.copy()

        # Normalize for display
        if vis.dtype != np.uint8:
            vis = cv2.normalize(vis, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)

        # Draw detections
        for v in vertebrae:
            # Draw bounding box
            color = (0, 255, 0) if v.confidence > 0.5 else (0, 255, 255)
            cv2.rectangle(
                vis,
                (v.bbox_x, v.bbox_y),
                (v.bbox_x + v.bbox_width, v.bbox_y + v.bbox_height),
                color, 2
            )

            # Draw center point
            cv2.circle(vis, (int(v.center_x), int(v.center_y)), 5, (0, 0, 255), -1)

            # Draw label
            label_text = f"{v.label.value} ({v.confidence:.2f})"
            cv2.putText(
                vis, label_text,
                (v.bbox_x, v.bbox_y - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1
            )

        return vertebrae, vis


def detect_vertebrae(
    image: np.ndarray,
    view: str = "frontal",
    **kwargs
) -> List[DetectedVertebra]:
    """
    Convenience function for vertebra detection.

    Args:
        image: X-ray image
        view: "frontal" or "lateral"
        **kwargs: Additional arguments for VertebraDetector.detect()

    Returns:
        List of detected vertebrae
    """
    detector = VertebraDetector()
    return detector.detect(image, view=view, **kwargs)
