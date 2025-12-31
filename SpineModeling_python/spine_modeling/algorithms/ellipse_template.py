"""
Ellipse Template Module - Fixed-Size Ellipse Placement

This module provides template-based ellipse placement for EOS X-ray images.
Based on clinical insight that marker ellipses have standardized sizes:
- Cluster markers (M, R, L): 3mm diameter
- Single markers: 5mm diameter

This approach eliminates the need for eigenvalue-based fitting when marker
sizes are known, significantly speeding up the annotation workflow.

Usage:
    >>> template = EllipseTemplate(marker_type='cluster')  # 3mm
    >>> ellipse = template.place_at(center_x=100, center_y=200, eos_image=img)
    >>> # Returns ellipse parameters ready for visualization

    >>> # Automatic detection
    >>> detector = CircularMarkerDetector()
    >>> markers = detector.detect(eos_image)
    >>> for marker in markers:
    ...     print(f"Found marker at ({marker.x}, {marker.y})")
"""

import numpy as np
from typing import List, Tuple, Optional, NamedTuple
from dataclasses import dataclass, field
from enum import Enum
import logging

try:
    import cv2
    HAS_OPENCV = True
except ImportError:
    cv2 = None
    HAS_OPENCV = False

logger = logging.getLogger(__name__)


class MarkerType(Enum):
    """Types of markers with their standard diameters in mm."""
    CLUSTER = 3.0  # M, R, L markers (3mm diameter)
    SINGLE = 5.0   # Single markers (5mm diameter)
    CUSTOM = 0.0   # User-defined size


@dataclass
class EllipseParameters:
    """
    Represents ellipse parameters for visualization.

    Attributes:
        center_x: X coordinate of center (pixels)
        center_y: Y coordinate of center (pixels)
        semi_major: Semi-major axis length (pixels)
        semi_minor: Semi-minor axis length (pixels)
        angle: Rotation angle in degrees (0 for circular markers)
        diameter_mm: Physical diameter in millimeters
        marker_type: Type of marker (cluster/single/custom)
    """
    center_x: float
    center_y: float
    semi_major: float  # pixels
    semi_minor: float  # pixels
    angle: float = 0.0  # degrees
    diameter_mm: float = 0.0
    marker_type: MarkerType = MarkerType.SINGLE

    @property
    def is_circle(self) -> bool:
        """Check if ellipse is effectively a circle."""
        return abs(self.semi_major - self.semi_minor) < 0.01

    @property
    def diameter_pixels(self) -> float:
        """Get diameter in pixels (for circular markers)."""
        return 2 * max(self.semi_major, self.semi_minor)

    def to_coefficients(self) -> np.ndarray:
        """
        Convert to general conic coefficients [A, B, C, D, E, F].

        Compatible with existing EllipseFit output format.
        """
        cx, cy = self.center_x, self.center_y
        a, b = self.semi_major, self.semi_minor
        theta = np.radians(self.angle)

        cos_t = np.cos(theta)
        sin_t = np.sin(theta)

        # General conic: Ax² + Bxy + Cy² + Dx + Ey + F = 0
        A = (cos_t / a) ** 2 + (sin_t / b) ** 2
        B = 2 * cos_t * sin_t * (1 / a ** 2 - 1 / b ** 2)
        C = (sin_t / a) ** 2 + (cos_t / b) ** 2
        D = -2 * A * cx - B * cy
        E = -B * cx - 2 * C * cy
        F = A * cx ** 2 + B * cx * cy + C * cy ** 2 - 1

        return np.array([A, B, C, D, E, F])

    def get_contour_points(self, num_points: int = 64) -> np.ndarray:
        """
        Generate points along the ellipse contour for visualization.

        Args:
            num_points: Number of points to generate

        Returns:
            Array of shape (num_points, 2) with (x, y) coordinates
        """
        theta = np.linspace(0, 2 * np.pi, num_points, endpoint=False)
        angle_rad = np.radians(self.angle)

        # Parametric ellipse
        x = self.semi_major * np.cos(theta)
        y = self.semi_minor * np.sin(theta)

        # Rotate
        cos_a = np.cos(angle_rad)
        sin_a = np.sin(angle_rad)
        x_rot = x * cos_a - y * sin_a + self.center_x
        y_rot = x * sin_a + y * cos_a + self.center_y

        return np.column_stack([x_rot, y_rot])


class EllipseTemplate:
    """
    Template-based ellipse placement with fixed sizes.

    For EOS X-ray markers with known physical sizes, this class provides
    instant ellipse placement without fitting - just click the center.

    Attributes:
        marker_type: Type of marker (determines size)
        diameter_mm: Physical diameter in millimeters

    Example:
        >>> template = EllipseTemplate(marker_type=MarkerType.CLUSTER)
        >>> ellipse = template.place_at(100, 200, pixel_spacing=0.000179)
        >>> print(f"Ellipse radius: {ellipse.semi_major:.1f} pixels")
    """

    # Standard marker sizes in mm
    CLUSTER_DIAMETER_MM = 3.0  # M, R, L markers
    SINGLE_DIAMETER_MM = 5.0   # Single markers

    def __init__(
        self,
        marker_type: MarkerType = MarkerType.SINGLE,
        custom_diameter_mm: Optional[float] = None
    ):
        """
        Initialize ellipse template.

        Args:
            marker_type: Type of marker (CLUSTER=3mm, SINGLE=5mm, CUSTOM)
            custom_diameter_mm: Custom diameter if marker_type is CUSTOM
        """
        self.marker_type = marker_type

        if marker_type == MarkerType.CUSTOM:
            if custom_diameter_mm is None:
                raise ValueError("custom_diameter_mm required for CUSTOM marker type")
            self.diameter_mm = custom_diameter_mm
        else:
            self.diameter_mm = marker_type.value

    def place_at(
        self,
        center_x: float,
        center_y: float,
        pixel_spacing: Optional[float] = None,
        eos_image: Optional[object] = None,
        angle: float = 0.0
    ) -> EllipseParameters:
        """
        Place a template ellipse at the specified center point.

        Args:
            center_x: X coordinate of center (pixels)
            center_y: Y coordinate of center (pixels)
            pixel_spacing: Pixel spacing in meters (from DICOM)
            eos_image: EosImage object (alternative to pixel_spacing)
            angle: Rotation angle in degrees (default 0 for circles)

        Returns:
            EllipseParameters with the placed ellipse

        Raises:
            ValueError: If neither pixel_spacing nor eos_image provided
        """
        # Get pixel spacing
        if pixel_spacing is None and eos_image is not None:
            pixel_spacing = eos_image.pixel_spacing_x  # meters

        if pixel_spacing is None:
            raise ValueError("Either pixel_spacing or eos_image must be provided")

        # Convert mm to pixels
        # pixel_spacing is in meters, diameter is in mm
        diameter_pixels = (self.diameter_mm / 1000.0) / pixel_spacing
        radius_pixels = diameter_pixels / 2.0

        logger.debug(
            f"Placing {self.marker_type.name} marker: "
            f"diameter={self.diameter_mm}mm -> {diameter_pixels:.1f}px "
            f"at ({center_x:.1f}, {center_y:.1f})"
        )

        return EllipseParameters(
            center_x=center_x,
            center_y=center_y,
            semi_major=radius_pixels,
            semi_minor=radius_pixels,  # Circular for standard markers
            angle=angle,
            diameter_mm=self.diameter_mm,
            marker_type=self.marker_type
        )

    @classmethod
    def for_cluster_marker(cls) -> 'EllipseTemplate':
        """Create template for cluster markers (M, R, L) - 3mm diameter."""
        return cls(marker_type=MarkerType.CLUSTER)

    @classmethod
    def for_single_marker(cls) -> 'EllipseTemplate':
        """Create template for single markers - 5mm diameter."""
        return cls(marker_type=MarkerType.SINGLE)

    @classmethod
    def with_custom_size(cls, diameter_mm: float) -> 'EllipseTemplate':
        """Create template with custom diameter."""
        return cls(marker_type=MarkerType.CUSTOM, custom_diameter_mm=diameter_mm)


@dataclass
class DetectedMarker:
    """Represents a detected circular marker in an image."""
    x: float  # Center X (pixels)
    y: float  # Center Y (pixels)
    radius: float  # Radius (pixels)
    confidence: float = 1.0  # Detection confidence (0-1)

    @property
    def diameter(self) -> float:
        """Get diameter in pixels."""
        return 2 * self.radius


class CircularMarkerDetector:
    """
    Automatic detection of circular markers in EOS X-ray images.

    Optimized for detecting radiopaque markers (typically metal beads) in
    EOS biplanar X-ray images. Uses multiple detection methods:
    1. Hough Circle Transform for well-defined circles
    2. Blob detection for varying contrast markers
    3. Adaptive thresholding for low-contrast regions

    The detector is specifically tuned for:
    - High dynamic range DICOM images (16-bit)
    - Metal markers that appear as bright spots on X-rays
    - Cluster markers (3mm) and single markers (5mm)

    Example:
        >>> detector = CircularMarkerDetector(sensitivity=0.7)
        >>> markers = detector.detect(pixel_array, pixel_spacing=0.000179)
        >>> for marker in markers:
        ...     print(f"Marker at ({marker.x}, {marker.y}), r={marker.radius}")
    """

    def __init__(
        self,
        min_radius_mm: float = 1.0,
        max_radius_mm: float = 4.0,
        sensitivity: float = 0.5
    ):
        """
        Initialize marker detector.

        Args:
            min_radius_mm: Minimum marker radius in mm (default: 1.0)
            max_radius_mm: Maximum marker radius in mm (default: 4.0)
            sensitivity: Detection sensitivity 0-1 (default: 0.5)
                        Higher values detect more markers but may include false positives
        """
        if not HAS_OPENCV:
            raise ImportError("OpenCV (cv2) is required for marker detection")

        self.min_radius_mm = min_radius_mm
        self.max_radius_mm = max_radius_mm
        self.sensitivity = np.clip(sensitivity, 0.1, 1.0)

    def _preprocess_xray(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess X-ray image for marker detection.

        Applies contrast enhancement and noise reduction optimized for
        detecting metal markers in EOS X-ray images.

        Args:
            image: Input grayscale image (8-bit or 16-bit)

        Returns:
            Preprocessed 8-bit image
        """
        # Convert to 8-bit if needed
        if image.dtype == np.uint16:
            # Use histogram-based normalization for DICOM images
            # This preserves marker visibility better than simple scaling
            p_low, p_high = np.percentile(image, [1, 99])
            image_clipped = np.clip(image, p_low, p_high)
            gray = ((image_clipped - p_low) / (p_high - p_low) * 255).astype(np.uint8)
        elif image.dtype != np.uint8:
            gray = cv2.normalize(image, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
        else:
            gray = image.copy()

        # Apply CLAHE (Contrast Limited Adaptive Histogram Equalization)
        # This enhances local contrast, making markers more visible
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        # Denoise while preserving edges (markers have sharp edges)
        denoised = cv2.bilateralFilter(enhanced, d=5, sigmaColor=50, sigmaSpace=50)

        return denoised

    def detect(
        self,
        image: np.ndarray,
        pixel_spacing: Optional[float] = None,
        eos_image: Optional[object] = None,
        use_preprocessing: bool = True
    ) -> List[DetectedMarker]:
        """
        Detect circular markers in an image.

        Args:
            image: Grayscale image array (8-bit, 16-bit, or color)
            pixel_spacing: Pixel spacing in meters (e.g., 0.000179 for 0.179mm)
            eos_image: EosImage object (alternative source for image and spacing)
            use_preprocessing: Apply X-ray specific preprocessing (default: True)

        Returns:
            List of DetectedMarker objects sorted by confidence (highest first)
        """
        # Get image and pixel spacing
        if eos_image is not None:
            if image is None:
                image = eos_image.load_pixel_array()
            if pixel_spacing is None:
                pixel_spacing = eos_image.pixel_spacing_x

        if image is None:
            raise ValueError("Image data required")

        logger.debug(f"Detecting markers: image shape={image.shape}, dtype={image.dtype}")

        # Convert to grayscale if needed
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image

        # Apply preprocessing for X-ray images
        if use_preprocessing:
            processed = self._preprocess_xray(gray)
        else:
            if gray.dtype != np.uint8:
                processed = cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX, dtype=cv2.CV_8U)
            else:
                processed = gray.copy()

        # Calculate radius range in pixels
        if pixel_spacing is not None:
            min_radius_px = int((self.min_radius_mm / 1000.0) / pixel_spacing)
            max_radius_px = int((self.max_radius_mm / 1000.0) / pixel_spacing)
            logger.debug(f"Radius range: {min_radius_px}-{max_radius_px} pixels "
                        f"({self.min_radius_mm}-{self.max_radius_mm} mm)")
        else:
            # Default pixel-based range if no spacing available
            min_radius_px = 5
            max_radius_px = 50

        # Ensure valid range
        min_radius_px = max(1, min_radius_px)
        max_radius_px = max(min_radius_px + 1, max_radius_px)

        markers = []

        # Method 1: Hough Circle Transform on preprocessed image
        hough_markers = self._detect_hough_circles(
            processed, min_radius_px, max_radius_px
        )
        markers.extend(hough_markers)
        logger.debug(f"Hough detection found {len(hough_markers)} markers")

        # Method 2: Blob Detection (complementary) on preprocessed image
        blob_markers = self._detect_blobs(
            processed, min_radius_px, max_radius_px
        )
        logger.debug(f"Blob detection found {len(blob_markers)} markers")

        # Method 3: Bright spot detection for metal markers
        bright_markers = self._detect_bright_spots(
            processed, min_radius_px, max_radius_px
        )
        logger.debug(f"Bright spot detection found {len(bright_markers)} markers")

        # Merge results, removing duplicates
        markers = self._merge_detections(markers, blob_markers)
        markers = self._merge_detections(markers, bright_markers)

        logger.info(f"Total detected: {len(markers)} circular markers")
        return markers

    def _detect_hough_circles(
        self,
        gray: np.ndarray,
        min_radius: int,
        max_radius: int
    ) -> List[DetectedMarker]:
        """Detect circles using Hough Circle Transform."""
        markers = []

        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (9, 9), 2)

        # Hough Circle parameters based on sensitivity
        param1 = int(100 * (1 - self.sensitivity * 0.5))  # Canny edge threshold
        param2 = int(50 * (1 - self.sensitivity * 0.5))   # Circle detection threshold

        circles = cv2.HoughCircles(
            blurred,
            cv2.HOUGH_GRADIENT,
            dp=1,
            minDist=min_radius * 2,
            param1=max(50, param1),
            param2=max(20, param2),
            minRadius=min_radius,
            maxRadius=max_radius
        )

        if circles is not None:
            circles = np.uint16(np.around(circles))
            for circle in circles[0, :]:
                x, y, r = circle
                markers.append(DetectedMarker(
                    x=float(x),
                    y=float(y),
                    radius=float(r),
                    confidence=0.8  # Hough circles are generally reliable
                ))

        return markers

    def _detect_blobs(
        self,
        gray: np.ndarray,
        min_radius: int,
        max_radius: int
    ) -> List[DetectedMarker]:
        """Detect circular blobs using SimpleBlobDetector."""
        markers = []

        # Configure blob detector
        params = cv2.SimpleBlobDetector_Params()

        # Filter by area
        min_area = np.pi * min_radius ** 2
        max_area = np.pi * max_radius ** 2
        params.filterByArea = True
        params.minArea = min_area
        params.maxArea = max_area

        # Filter by circularity (we want circles)
        params.filterByCircularity = True
        params.minCircularity = 0.7

        # Filter by convexity
        params.filterByConvexity = True
        params.minConvexity = 0.8

        # Filter by inertia (circular objects have inertia ratio ~1)
        params.filterByInertia = True
        params.minInertiaRatio = 0.5

        # Create detector
        detector = cv2.SimpleBlobDetector_create(params)

        # Detect blobs (invert image if markers are bright)
        keypoints = detector.detect(gray)

        # Also try inverted image
        inverted = cv2.bitwise_not(gray)
        keypoints_inv = detector.detect(inverted)
        keypoints.extend(keypoints_inv)

        for kp in keypoints:
            markers.append(DetectedMarker(
                x=kp.pt[0],
                y=kp.pt[1],
                radius=kp.size / 2,
                confidence=0.6  # Blob detection is less precise
            ))

        return markers

    def _detect_bright_spots(
        self,
        gray: np.ndarray,
        min_radius: int,
        max_radius: int
    ) -> List[DetectedMarker]:
        """
        Detect bright circular spots (metal markers in X-rays).

        Metal markers appear as bright spots on X-ray images due to their
        high radiodensity. This method uses thresholding and contour analysis
        to find circular bright regions.

        Args:
            gray: Preprocessed grayscale image
            min_radius: Minimum radius in pixels
            max_radius: Maximum radius in pixels

        Returns:
            List of DetectedMarker objects
        """
        markers = []

        # Calculate adaptive threshold based on sensitivity
        # Higher sensitivity = lower threshold = more detections
        threshold_percentile = 95 - (self.sensitivity * 20)  # 75-95 percentile

        # Find bright regions using percentile-based threshold
        threshold_value = np.percentile(gray, threshold_percentile)
        _, binary = cv2.threshold(gray, int(threshold_value), 255, cv2.THRESH_BINARY)

        # Morphological operations to clean up
        kernel_size = max(3, min_radius // 2)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)

        # Find contours
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for contour in contours:
            # Filter by area
            area = cv2.contourArea(contour)
            min_area = np.pi * min_radius ** 2
            max_area = np.pi * max_radius ** 2

            if area < min_area * 0.5 or area > max_area * 2:
                continue

            # Check circularity
            perimeter = cv2.arcLength(contour, True)
            if perimeter == 0:
                continue

            circularity = 4 * np.pi * area / (perimeter ** 2)
            if circularity < 0.6:  # Must be fairly circular
                continue

            # Get enclosing circle
            (x, y), radius = cv2.minEnclosingCircle(contour)

            # Check radius bounds
            if radius < min_radius * 0.7 or radius > max_radius * 1.3:
                continue

            # Calculate confidence based on circularity
            confidence = min(0.9, circularity * 0.9)

            markers.append(DetectedMarker(
                x=float(x),
                y=float(y),
                radius=float(radius),
                confidence=confidence
            ))

        return markers

    def _merge_detections(
        self,
        markers1: List[DetectedMarker],
        markers2: List[DetectedMarker],
        distance_threshold: float = 10.0
    ) -> List[DetectedMarker]:
        """Merge detections from multiple methods, removing duplicates."""
        all_markers = markers1.copy()

        for m2 in markers2:
            is_duplicate = False
            for m1 in all_markers:
                dist = np.sqrt((m1.x - m2.x) ** 2 + (m1.y - m2.y) ** 2)
                if dist < distance_threshold:
                    # Keep the one with higher confidence
                    if m2.confidence > m1.confidence:
                        all_markers.remove(m1)
                        all_markers.append(m2)
                    is_duplicate = True
                    break

            if not is_duplicate:
                all_markers.append(m2)

        # Sort by confidence (highest first)
        all_markers.sort(key=lambda m: m.confidence, reverse=True)
        return all_markers


class EllipsePlacementManager:
    """
    Manages ellipse placement workflow with templates and detection.

    Provides a unified interface for:
    1. Manual click-to-place with templates
    2. Automatic marker detection
    3. Manual adjustment of placed ellipses

    Example:
        >>> manager = EllipsePlacementManager(eos_image)
        >>>
        >>> # Click to place cluster marker
        >>> ellipse = manager.place_cluster_marker(x=100, y=200)
        >>>
        >>> # Or auto-detect all markers
        >>> detected = manager.auto_detect_markers()
        >>>
        >>> # Adjust if needed
        >>> manager.adjust_ellipse(ellipse, new_x=105, new_y=202)
    """

    def __init__(self, eos_image: object):
        """
        Initialize placement manager.

        Args:
            eos_image: EosImage object with calibration parameters
        """
        self.eos_image = eos_image
        self.pixel_spacing = eos_image.pixel_spacing_x

        # Templates
        self._cluster_template = EllipseTemplate.for_cluster_marker()
        self._single_template = EllipseTemplate.for_single_marker()

        # Placed ellipses
        self.ellipses: List[EllipseParameters] = []

        # Detector (lazy initialization)
        self._detector: Optional[CircularMarkerDetector] = None

    def place_cluster_marker(self, x: float, y: float) -> EllipseParameters:
        """
        Place a cluster marker (3mm) at the specified position.

        Args:
            x: Center X coordinate (pixels)
            y: Center Y coordinate (pixels)

        Returns:
            EllipseParameters for the placed marker
        """
        ellipse = self._cluster_template.place_at(
            x, y, pixel_spacing=self.pixel_spacing
        )
        self.ellipses.append(ellipse)
        logger.debug(f"Placed cluster marker at ({x:.1f}, {y:.1f})")
        return ellipse

    def place_single_marker(self, x: float, y: float) -> EllipseParameters:
        """
        Place a single marker (5mm) at the specified position.

        Args:
            x: Center X coordinate (pixels)
            y: Center Y coordinate (pixels)

        Returns:
            EllipseParameters for the placed marker
        """
        ellipse = self._single_template.place_at(
            x, y, pixel_spacing=self.pixel_spacing
        )
        self.ellipses.append(ellipse)
        logger.debug(f"Placed single marker at ({x:.1f}, {y:.1f})")
        return ellipse

    def place_custom_marker(
        self,
        x: float,
        y: float,
        diameter_mm: float
    ) -> EllipseParameters:
        """
        Place a custom-sized marker.

        Args:
            x: Center X coordinate (pixels)
            y: Center Y coordinate (pixels)
            diameter_mm: Marker diameter in millimeters

        Returns:
            EllipseParameters for the placed marker
        """
        template = EllipseTemplate.with_custom_size(diameter_mm)
        ellipse = template.place_at(x, y, pixel_spacing=self.pixel_spacing)
        self.ellipses.append(ellipse)
        return ellipse

    def auto_detect_markers(
        self,
        image: Optional[np.ndarray] = None
    ) -> List[EllipseParameters]:
        """
        Automatically detect circular markers in the image.

        Args:
            image: Optional image array (uses eos_image pixel array if not provided)

        Returns:
            List of EllipseParameters for detected markers
        """
        if not HAS_OPENCV:
            logger.warning("OpenCV not available for automatic detection")
            return []

        # Initialize detector if needed
        if self._detector is None:
            self._detector = CircularMarkerDetector(
                min_radius_mm=1.0,
                max_radius_mm=4.0,
                sensitivity=0.5
            )

        # Get image
        if image is None:
            image = self.eos_image.load_pixel_array()

        # Detect markers
        detected = self._detector.detect(
            image,
            pixel_spacing=self.pixel_spacing
        )

        # Convert to EllipseParameters
        ellipses = []
        for marker in detected:
            # Classify by size
            diameter_mm = (marker.radius * 2 * self.pixel_spacing) * 1000

            if diameter_mm < 4.0:
                marker_type = MarkerType.CLUSTER
            else:
                marker_type = MarkerType.SINGLE

            ellipse = EllipseParameters(
                center_x=marker.x,
                center_y=marker.y,
                semi_major=marker.radius,
                semi_minor=marker.radius,
                angle=0.0,
                diameter_mm=diameter_mm,
                marker_type=marker_type
            )
            ellipses.append(ellipse)
            self.ellipses.append(ellipse)

        logger.info(f"Auto-detected {len(ellipses)} markers")
        return ellipses

    def adjust_ellipse(
        self,
        ellipse: EllipseParameters,
        new_x: Optional[float] = None,
        new_y: Optional[float] = None,
        new_angle: Optional[float] = None,
        new_semi_major: Optional[float] = None,
        new_semi_minor: Optional[float] = None
    ) -> EllipseParameters:
        """
        Adjust an existing ellipse's parameters.

        Args:
            ellipse: The ellipse to adjust
            new_x: New center X (optional)
            new_y: New center Y (optional)
            new_angle: New rotation angle (optional)
            new_semi_major: New semi-major axis (optional)
            new_semi_minor: New semi-minor axis (optional)

        Returns:
            The adjusted ellipse (same object, modified in place)
        """
        if new_x is not None:
            ellipse.center_x = new_x
        if new_y is not None:
            ellipse.center_y = new_y
        if new_angle is not None:
            ellipse.angle = new_angle
        if new_semi_major is not None:
            ellipse.semi_major = new_semi_major
        if new_semi_minor is not None:
            ellipse.semi_minor = new_semi_minor

        return ellipse

    def remove_ellipse(self, ellipse: EllipseParameters) -> bool:
        """
        Remove an ellipse from the managed list.

        Args:
            ellipse: The ellipse to remove

        Returns:
            True if removed, False if not found
        """
        try:
            self.ellipses.remove(ellipse)
            return True
        except ValueError:
            return False

    def clear_all(self) -> int:
        """
        Remove all placed ellipses.

        Returns:
            Number of ellipses removed
        """
        count = len(self.ellipses)
        self.ellipses.clear()
        return count

    def get_ellipse_at(
        self,
        x: float,
        y: float,
        tolerance: float = 5.0
    ) -> Optional[EllipseParameters]:
        """
        Get ellipse at or near a point (for selection).

        Args:
            x: X coordinate
            y: Y coordinate
            tolerance: Distance tolerance in pixels

        Returns:
            EllipseParameters if found, None otherwise
        """
        for ellipse in self.ellipses:
            dist = np.sqrt(
                (ellipse.center_x - x) ** 2 +
                (ellipse.center_y - y) ** 2
            )
            if dist <= tolerance + ellipse.semi_major:
                return ellipse
        return None
