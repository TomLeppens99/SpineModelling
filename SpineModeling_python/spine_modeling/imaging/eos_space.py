"""
EOS Space module for 3D coordinate reconstruction from dual X-ray images.

This module provides classes for managing 3D spatial reconstruction from
biplanar EOS X-ray images, including calibration geometry, coordinate
transformations, and projection/inverse projection methods.
"""

from __future__ import annotations
from typing import Tuple, List, Optional
from dataclasses import dataclass
import math
import logging

from spine_modeling.core.position import Position
from spine_modeling.imaging.eos_image import EosImage

logger = logging.getLogger(__name__)


@dataclass
class Orientation:
    """
    Represents 3D orientation using Euler angles.

    Attributes:
        x (float): Rotation around X-axis in degrees
        y (float): Rotation around Y-axis in degrees
        z (float): Rotation around Z-axis in degrees

    Examples:
        >>> orientation = Orientation(0, 180, 0)
        >>> orientation.x
        0
    """

    x: float
    y: float
    z: float

    def to_tuple(self) -> Tuple[float, float, float]:
        """
        Convert orientation to tuple.

        Returns:
            Tuple[float, float, float]: (x, y, z) angles in degrees
        """
        return (self.x, self.y, self.z)


@dataclass
class SpaceObject:
    """
    Represents a 3D object in EOS space.

    This class is a placeholder for objects that exist in the 3D EOS
    reconstruction space, such as anatomical landmarks or measurement points.

    Attributes:
        position (Position): 3D position of the object
        name (str): Name/identifier of the object
        properties (dict): Additional properties of the object

    Examples:
        >>> obj = SpaceObject(Position(1.0, 2.0, 3.0), name="Landmark1")
        >>> obj.position.x
        1.0
    """

    position: Position
    name: str = ""
    properties: dict = None

    def __post_init__(self):
        """Initialize properties dictionary if not provided."""
        if self.properties is None:
            self.properties = {}


class EosSpace:
    """
    Manages 3D spatial reconstruction from biplanar EOS X-ray images.

    This class handles the geometric setup of the EOS imaging system,
    including X-ray source positions, image plane orientations, and
    patient positioning. It provides methods for projecting 3D points
    onto 2D image planes and performing inverse projection (triangulation)
    from dual 2D views to 3D space.

    The EOS system uses two orthogonal X-ray sources to capture simultaneous
    frontal and lateral views, enabling 3D reconstruction with precise
    calibration parameters.

    Attributes:
        eos_image_a (EosImage): First EOS image (typically frontal/AP view)
        eos_image_b (EosImage): Second EOS image (typically lateral view)
        position_source1 (Position): 3D position of first X-ray source
        position_source2 (Position): 3D position of second X-ray source
        patient_position (Position): 3D position of patient in EOS space
        position_origin_image1 (Position): Origin position of first image plane
        position_origin_image2 (Position): Origin position of second image plane
        orientation_image1 (Orientation): Orientation of first image plane
        orientation_image2 (Orientation): Orientation of second image plane
        space_objects (List[SpaceObject]): List of 3D objects in the space

    Examples:
        >>> image_a = EosImage(directory="/path/to/frontal.dcm")
        >>> image_b = EosImage(directory="/path/to/lateral.dcm")
        >>> eos_space = EosSpace(image_a, image_b)
        >>> eos_space.calculate_eos_space()
        >>> x_proj, z_proj = eos_space.project(0.1, 0.2)
    """

    def __init__(self, eos_image_a: EosImage, eos_image_b: EosImage):
        """
        Initialize EosSpace with two EOS images.

        Args:
            eos_image_a (EosImage): First EOS image (frontal view)
            eos_image_b (EosImage): Second EOS image (lateral view)
        """
        self.eos_image_a = eos_image_a
        self.eos_image_b = eos_image_b

        # Initialize positions (will be calculated)
        self.position_source1 = Position(0.0, 0.0, 0.0)
        self.position_source2 = Position(0.0, 0.0, 0.0)
        self.patient_position = Position(0.0, 0.0, 0.0)
        self.position_origin_image1 = Position(0.0, 0.0, 0.0)
        self.position_origin_image2 = Position(0.0, 0.0, 0.0)

        # Initialize orientations (will be calculated)
        self.orientation_image1 = Orientation(0.0, 0.0, 0.0)
        self.orientation_image2 = Orientation(0.0, 0.0, 0.0)

        # Space objects list
        self.space_objects: List[SpaceObject] = []

    def calculate_eos_space(self) -> None:
        """
        Calculate 3D geometry of EOS imaging system.

        This method computes the positions of X-ray sources, image plane origins,
        and patient position based on the calibration parameters from the two
        EOS images. The coordinate system is centered at the isocenter.

        The calculation assumes:
        - Isocenter at origin (0, 0, 0)
        - Source 1 (frontal) positioned on negative Z-axis
        - Source 2 (lateral) positioned on negative X-axis
        - Patient positioned between sources and isocenter

        Note: Image orientations are currently hardcoded and should be automated
        in future versions (TODO from original C# code).

        Examples:
            >>> eos_space = EosSpace(image_a, image_b)
            >>> eos_space.calculate_eos_space()
            >>> print(f"Source 1 position: {eos_space.position_source1}")
        """
        # Calculate X-ray source positions
        # Source 1 (frontal view): on negative Z-axis at distance from isocenter
        self.position_source1 = Position(
            0.0,
            0.0,
            -self.eos_image_a.distance_source_to_isocenter
        )

        # Source 2 (lateral view): on negative X-axis at distance from isocenter
        self.position_source2 = Position(
            -self.eos_image_b.distance_source_to_isocenter,
            0.0,
            0.0
        )

        # Calculate patient position (between sources and isocenter)
        self.patient_position = Position(
            -(self.eos_image_b.distance_source_to_isocenter -
              self.eos_image_b.distance_source_to_patient),
            0.0,
            -(self.eos_image_a.distance_source_to_isocenter -
              self.eos_image_a.distance_source_to_patient)
        )

        # Calculate image plane origin positions
        # Image 1 (frontal): centered in X, at detector distance on positive Z
        self.position_origin_image1 = Position(
            self.eos_image_a.width / 2.0,
            0.0,
            (self.eos_image_a.distance_source_to_detector -
             self.eos_image_a.distance_source_to_isocenter)
        )

        # Image 2 (lateral): at detector distance on positive X, centered in Z
        self.position_origin_image2 = Position(
            (self.eos_image_b.distance_source_to_detector -
             self.eos_image_b.distance_source_to_isocenter),
            0.0,
            -self.eos_image_b.width / 2.0
        )

        # Set image plane orientations
        # Frontal image: rotated 180° around Y-axis
        self.orientation_image1 = Orientation(0, 180, 0)

        # Lateral image: rotated 270° around Y-axis
        # TODO: Automate image orientation detection
        self.orientation_image2 = Orientation(0, 270, 0)

    def project(self, x_real: float, z_real: float) -> Tuple[float, float]:
        """
        Project 3D coordinates onto 2D image planes.

        Given a 3D point in EOS space (with known x and z coordinates),
        project it onto the two image planes to find where it would appear
        in the images.

        This uses perspective projection based on the source-to-isocenter
        distances and the 3D position of the point.

        Args:
            x_real (float): Real X-coordinate in 3D space (meters)
            z_real (float): Real Z-coordinate in 3D space (meters)

        Returns:
            Tuple[float, float]: (x_projection, z_projection) coordinates
                x_projection: Projected X coordinate on frontal image
                z_projection: Projected Z coordinate on lateral image

        Examples:
            >>> eos_space = EosSpace(image_a, image_b)
            >>> eos_space.calculate_eos_space()
            >>> x_proj, z_proj = eos_space.project(0.1, 0.2)
        """
        # Project onto frontal image (x coordinate)
        x_proj = (
            (x_real / (self.eos_image_a.distance_source_to_isocenter + z_real)) *
            self.eos_image_a.distance_source_to_isocenter
        )

        # Project onto lateral image (z coordinate)
        z_proj = (
            (z_real / (self.eos_image_b.distance_source_to_isocenter + x_real)) *
            self.eos_image_b.distance_source_to_isocenter
        )

        return (x_proj, z_proj)

    def inverse_project(self, x_proj: float, z_proj: float) -> Tuple[float, float]:
        """
        Inverse project from 2D image coordinates to 3D space (triangulation).

        Given projection coordinates on both image planes, calculate the
        real 3D position by triangulating from the two X-ray sources.

        This solves the inverse projection problem by finding the intersection
        of the two projection rays from the sources through the image points.

        Args:
            x_proj (float): Projected X coordinate on frontal image (meters)
            z_proj (float): Projected Z coordinate on lateral image (meters)

        Returns:
            Tuple[float, float]: (x_real, z_real) 3D coordinates in meters

        Examples:
            >>> eos_space = EosSpace(image_a, image_b)
            >>> eos_space.calculate_eos_space()
            >>> x_real, z_real = eos_space.inverse_project(0.05, 0.08)
        """
        # Calculate ray slopes from sources through projection points
        # Frontal ray (from source 1 through x_proj)
        slope_frontal = (
            (0 - (-self.eos_image_a.distance_source_to_isocenter)) /
            (x_proj - 0)
        )

        # Lateral ray (from source 2 through z_proj)
        slope_lateral = (
            (-z_proj - 0) /
            (0 - self.eos_image_b.distance_source_to_isocenter)
        )

        # Find intersection point (triangulation)
        x_real = (
            (-slope_lateral * self.eos_image_b.distance_source_to_isocenter) -
            (-self.eos_image_a.distance_source_to_isocenter)
        ) / (slope_frontal - slope_lateral)

        z_real = slope_frontal * x_real + (-self.eos_image_a.distance_source_to_isocenter)

        return (x_real, z_real)

    def convert_pixel_to_meters(
        self,
        pixel_value: int,
        pixel_spacing: Optional[float] = None,
        image_label: Optional[str] = None
    ) -> float:
        """
        Convert pixel coordinates to physical distance in meters.

        Args:
            pixel_value (int): Pixel coordinate value
            pixel_spacing (Optional[float]): Pixel spacing in meters.
                If None, image_label must be provided.
            image_label (Optional[str]): Image label ("A" or "B") to use
                its pixel spacing. Ignored if pixel_spacing is provided.

        Returns:
            float: Physical distance in meters

        Raises:
            ValueError: If neither pixel_spacing nor valid image_label is provided

        Examples:
            >>> eos_space = EosSpace(image_a, image_b)
            >>> meters = eos_space.convert_pixel_to_meters(100, pixel_spacing=0.000143)
            >>> meters_a = eos_space.convert_pixel_to_meters(100, image_label="A")
        """
        if pixel_spacing is not None:
            return float(pixel_value) * pixel_spacing

        if image_label == "A":
            return float(pixel_value) * self.eos_image_a.pixel_spacing_x
        elif image_label == "B":
            return float(pixel_value) * self.eos_image_b.pixel_spacing_x
        else:
            raise ValueError(
                "Either pixel_spacing or valid image_label ('A' or 'B') must be provided"
            )

    def convert_meters_to_pixels(
        self,
        meters: float,
        pixel_spacing: float
    ) -> int:
        """
        Convert physical distance in meters to pixel coordinates.

        Args:
            meters (float): Physical distance in meters
            pixel_spacing (float): Pixel spacing in meters

        Returns:
            int: Pixel coordinate value (rounded)

        Examples:
            >>> eos_space = EosSpace(image_a, image_b)
            >>> pixels = eos_space.convert_meters_to_pixels(0.0143, 0.000143)
            >>> pixels
            100
        """
        return round(meters / pixel_spacing)

    def add_space_object(self, space_object: SpaceObject) -> None:
        """
        Add a 3D object to the space.

        Args:
            space_object (SpaceObject): Object to add

        Examples:
            >>> eos_space = EosSpace(image_a, image_b)
            >>> landmark = SpaceObject(Position(0.1, 0.2, 0.3), name="L1")
            >>> eos_space.add_space_object(landmark)
        """
        self.space_objects.append(space_object)

    def remove_space_object(self, space_object: SpaceObject) -> bool:
        """
        Remove a 3D object from the space.

        Args:
            space_object (SpaceObject): Object to remove

        Returns:
            bool: True if object was removed, False if not found

        Examples:
            >>> eos_space = EosSpace(image_a, image_b)
            >>> landmark = SpaceObject(Position(0.1, 0.2, 0.3), name="L1")
            >>> eos_space.add_space_object(landmark)
            >>> eos_space.remove_space_object(landmark)
            True
        """
        try:
            self.space_objects.remove(space_object)
            return True
        except ValueError:
            return False

    def clear_space_objects(self) -> None:
        """
        Remove all 3D objects from the space.

        Examples:
            >>> eos_space = EosSpace(image_a, image_b)
            >>> eos_space.clear_space_objects()
            >>> len(eos_space.space_objects)
            0
        """
        self.space_objects.clear()

    def get_geometry_summary(self) -> dict:
        """
        Get a summary of the EOS space geometry.

        Returns:
            dict: Dictionary containing key geometric parameters

        Examples:
            >>> eos_space = EosSpace(image_a, image_b)
            >>> eos_space.calculate_eos_space()
            >>> summary = eos_space.get_geometry_summary()
            >>> summary["source1"]
            Position(x=0.0, y=0.0, z=-1.35)
        """
        return {
            "source1": self.position_source1,
            "source2": self.position_source2,
            "patient": self.patient_position,
            "image1_origin": self.position_origin_image1,
            "image2_origin": self.position_origin_image2,
            "image1_orientation": self.orientation_image1,
            "image2_orientation": self.orientation_image2,
            "num_objects": len(self.space_objects),
        }

    def __str__(self) -> str:
        """String representation of EosSpace."""
        return (
            f"EosSpace(images=({self.eos_image_a.image_plane}, "
            f"{self.eos_image_b.image_plane}), "
            f"objects={len(self.space_objects)})"
        )
