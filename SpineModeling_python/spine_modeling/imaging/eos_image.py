"""
EOS Image module for EOS X-ray medical image handling.

This module provides the EosImage class for loading and managing EOS X-ray images,
including DICOM metadata extraction, calibration parameters, and image properties
required for 3D reconstruction and biomechanical analysis.
"""

from __future__ import annotations
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from pathlib import Path
import logging

try:
    import pydicom
    from pydicom.dataset import Dataset
except ImportError:
    pydicom = None  # type: ignore
    Dataset = None  # type: ignore

try:
    import numpy as np
except ImportError:
    np = None  # type: ignore

logger = logging.getLogger(__name__)


@dataclass
class EosImage:
    """
    Represents an EOS X-ray medical image with calibration parameters.

    EOS imaging is a biplanar X-ray system that captures simultaneous frontal
    and lateral views with low radiation dose. This class encapsulates the
    image data and calibration parameters required for 3D reconstruction.

    Attributes:
        directory (str): Path to the DICOM file
        distance_source_to_isocenter (float): Distance from X-ray source to isocenter (meters)
        distance_source_to_detector (float): Distance from X-ray source to detector (meters)
        distance_source_to_patient (float): Distance from X-ray source to patient (meters)
        imager_pixel_spacing_x (float): Physical spacing of detector pixels in X (millimeters)
        imager_pixel_spacing_y (float): Physical spacing of detector pixels in Y (millimeters)
        pixel_spacing_x (float): Physical spacing of image pixels in X (meters)
        pixel_spacing_y (float): Physical spacing of image pixels in Y (meters)
        height (float): Physical height of image in meters
        width (float): Physical width of image in meters
        columns (int): Number of pixel columns in image
        rows (int): Number of pixel rows in image
        image_plane (str): Image plane orientation (e.g., "AP", "LAT")
        image_comments (str): DICOM image comments
        field_of_view_origin (int): Field of view origin indicator
        image_rotated (bool): Whether image has been rotated
        dicom_dataset (Optional[Dataset]): Loaded DICOM dataset
        pixel_array (Optional[np.ndarray]): Image pixel data array
        dicom_tags (Dict[str, Any]): Dictionary of DICOM tag values

    Examples:
        >>> eos_image = EosImage(directory="/path/to/image.dcm")
        >>> eos_image.read_image()
        >>> print(f"Image size: {eos_image.columns}x{eos_image.rows}")
        >>> print(f"Source distance: {eos_image.distance_source_to_isocenter}m")
    """

    directory: str
    distance_source_to_isocenter: float = 0.0
    distance_source_to_detector: float = 0.0
    distance_source_to_patient: float = 0.0
    imager_pixel_spacing_x: float = 0.0
    imager_pixel_spacing_y: float = 0.0
    pixel_spacing_x: float = 0.0
    pixel_spacing_y: float = 0.0
    height: float = 0.0
    width: float = 0.0
    columns: int = 0
    rows: int = 0
    image_plane: str = ""
    image_comments: str = ""
    field_of_view_origin: int = 0
    image_rotated: bool = False
    dicom_dataset: Optional[Dataset] = field(default=None, repr=False)
    pixel_array: Optional[np.ndarray] = field(default=None, repr=False)
    dicom_tags: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate dependencies are available."""
        if pydicom is None:
            logger.warning("pydicom not installed - DICOM reading will not work")
        if np is None:
            logger.warning("numpy not installed - pixel array operations will not work")

    def read_image(self) -> bool:
        """
        Read DICOM image and extract basic calibration parameters.

        This method loads the DICOM file and extracts essential metadata
        including image dimensions and EOS-specific calibration parameters.

        Returns:
            bool: True if successful, False otherwise

        Raises:
            FileNotFoundError: If DICOM file does not exist
            ImportError: If pydicom is not installed
            ValueError: If required DICOM tags are missing

        Examples:
            >>> eos_image = EosImage(directory="/path/to/eos.dcm")
            >>> success = eos_image.read_image()
            >>> if success:
            ...     print(f"Loaded image: {eos_image.columns}x{eos_image.rows}")
        """
        if pydicom is None:
            raise ImportError("pydicom is required for DICOM reading")

        # Check file exists
        if not Path(self.directory).exists():
            raise FileNotFoundError(
                f"File/Path cannot be found: {self.directory}. "
                "Check connection to network database."
            )

        try:
            # Read DICOM file
            self.dicom_dataset = pydicom.dcmread(self.directory)

            # Extract basic image dimensions
            self.rows = int(self.dicom_dataset.Rows)
            self.columns = int(self.dicom_dataset.Columns)

            # Extract EOS calibration parameters (convert mm to meters)
            self.distance_source_to_isocenter = (
                float(self.dicom_dataset.DistanceSourceToIsocenter) / 1000.0
            )
            self.distance_source_to_detector = (
                float(self.dicom_dataset.DistanceSourceToDetector) / 1000.0
            )
            self.distance_source_to_patient = (
                float(self.dicom_dataset.DistanceSourceToPatient) / 1000.0
            )

            # Extract pixel spacing (convert mm to meters for imager, mm to m for pixel)
            imager_spacing = self.dicom_dataset.ImagerPixelSpacing
            self.imager_pixel_spacing_x = float(imager_spacing[0]) * 1000.0
            # TODO: Support non-uniform resolution
            self.imager_pixel_spacing_y = self.imager_pixel_spacing_x

            pixel_spacing = self.dicom_dataset.PixelSpacing
            self.pixel_spacing_x = float(pixel_spacing[0]) / 1000.0
            # TODO: Support non-uniform resolution
            self.pixel_spacing_y = self.pixel_spacing_x

            # Extract image plane orientation
            if hasattr(self.dicom_dataset, "PatientOrientation"):
                self.image_plane = str(self.dicom_dataset.PatientOrientation)
            else:
                self.image_plane = "UNKNOWN"

            # Calculate physical dimensions
            self.height = self.pixel_spacing_y * self.rows
            self.width = self.pixel_spacing_x * self.columns

            return True

        except AttributeError as e:
            logger.error("Missing required DICOM tag: %s", e)
            raise ValueError(
                f"Required DICOM tag missing in file {self.directory}: {e}"
            ) from e
        except Exception as e:
            logger.error("Error reading DICOM file: %s", e)
            return False

    def read_image_tags_to_properties(self) -> bool:
        """
        Read all DICOM tags and populate properties with detailed metadata.

        This method performs a more comprehensive read of DICOM metadata,
        including optional tags and validation of calibration parameters.

        Returns:
            bool: True if successful, False otherwise

        Raises:
            FileNotFoundError: If DICOM file does not exist
            ImportError: If pydicom is not installed
            ValueError: If spatial calibration parameters cannot be extracted

        Examples:
            >>> eos_image = EosImage(directory="/path/to/eos.dcm")
            >>> success = eos_image.read_image_tags_to_properties()
            >>> if success:
            ...     print(f"Image comments: {eos_image.image_comments}")
        """
        if pydicom is None:
            raise ImportError("pydicom is required for DICOM reading")

        # Check file exists
        if not Path(self.directory).exists():
            raise FileNotFoundError(
                f"File/Path cannot be found: {self.directory}"
            )

        try:
            # Read DICOM file
            self.dicom_dataset = pydicom.dcmread(self.directory)

            # Build dictionary of all DICOM tags
            self._build_dicom_tags_dict()

            # Extract basic dimensions
            self.rows = int(self.dicom_dataset.Rows)
            self.columns = int(self.dicom_dataset.Columns)

            # Extract and validate spatial calibration parameters
            try:
                self.distance_source_to_isocenter = (
                    float(self.dicom_dataset.DistanceSourceToIsocenter) / 1000.0
                )
                self.distance_source_to_detector = (
                    float(self.dicom_dataset.DistanceSourceToDetector) / 1000.0
                )
                self.distance_source_to_patient = (
                    float(self.dicom_dataset.DistanceSourceToPatient) / 1000.0
                )
            except (AttributeError, ValueError) as e:
                raise ValueError(
                    "Spatial calibration parameters could not be extracted from the DICOM tags. "
                    "Please make sure you are working with the original EOS images. "
                    "Secondary captures can't be used for 3D purposes. "
                    "Close and re-open to try again with a different set of images."
                ) from e

            # Extract pixel spacing
            imager_spacing = self.dicom_dataset.ImagerPixelSpacing
            self.imager_pixel_spacing_x = float(imager_spacing[0]) * 1000.0
            # TODO: Support non-uniform resolution
            self.imager_pixel_spacing_y = self.imager_pixel_spacing_x

            pixel_spacing = self.dicom_dataset.PixelSpacing
            self.pixel_spacing_x = float(pixel_spacing[0]) / 1000.0
            # TODO: Support non-uniform resolution
            self.pixel_spacing_y = self.pixel_spacing_x

            # Extract image orientation
            if hasattr(self.dicom_dataset, "PatientOrientation"):
                self.image_plane = str(self.dicom_dataset.PatientOrientation)
            else:
                self.image_plane = "UNKNOWN"

            # Calculate physical dimensions
            self.height = self.pixel_spacing_y * self.rows
            self.width = self.pixel_spacing_x * self.columns

            # Extract optional metadata
            if hasattr(self.dicom_dataset, "FieldOfViewOrigin"):
                self.field_of_view_origin = int(self.dicom_dataset.FieldOfViewOrigin)

            if hasattr(self.dicom_dataset, "ImageComments"):
                self.image_comments = str(self.dicom_dataset.ImageComments)

            return True

        except Exception as e:
            logger.error("Error reading DICOM tags: %s", e)
            return False

    def _build_dicom_tags_dict(self) -> None:
        """
        Build a dictionary of all DICOM tags in the dataset.

        This internal method extracts all DICOM tags and stores them in
        a structured dictionary for easy access and display.
        """
        if self.dicom_dataset is None:
            return

        self.dicom_tags.clear()

        for element in self.dicom_dataset:
            try:
                tag_group = f"{element.tag.group:04X}"
                tag_element = f"{element.tag.element:04X}"
                tag_name = element.name if hasattr(element, "name") else "Unknown"
                tag_value = element.value

                self.dicom_tags[f"{tag_group},{tag_element}"] = {
                    "group": tag_group,
                    "element": tag_element,
                    "name": tag_name,
                    "value": tag_value,
                }
            except Exception as e:
                logger.warning("Could not process DICOM tag %s: %s", element.tag, e)

    def get_dicom_tag_table(self) -> list:
        """
        Get DICOM tags formatted as a list of dictionaries for table display.

        Returns:
            list: List of dictionaries with keys: group, element, description, value

        Examples:
            >>> eos_image = EosImage(directory="/path/to/eos.dcm")
            >>> eos_image.read_image_tags_to_properties()
            >>> tags = eos_image.get_dicom_tag_table()
            >>> for tag in tags[:3]:  # Show first 3 tags
            ...     print(f"{tag['group']},{tag['element']}: {tag['value']}")
        """
        if not self.dicom_tags:
            self._build_dicom_tags_dict()

        table_data = []
        for tag_info in self.dicom_tags.values():
            table_data.append({
                "group": tag_info["group"],
                "element": tag_info["element"],
                "description": tag_info["name"],
                "value": str(tag_info["value"])
            })

        return table_data

    def load_pixel_array(self) -> Optional[np.ndarray]:
        """
        Load pixel data from DICOM file as numpy array.

        Returns:
            Optional[np.ndarray]: Pixel array if successful, None otherwise

        Raises:
            ImportError: If numpy or pydicom is not installed

        Examples:
            >>> eos_image = EosImage(directory="/path/to/eos.dcm")
            >>> eos_image.read_image()
            >>> pixels = eos_image.load_pixel_array()
            >>> if pixels is not None:
            ...     print(f"Pixel array shape: {pixels.shape}")
        """
        if np is None:
            raise ImportError("numpy is required for pixel array operations")
        if pydicom is None:
            raise ImportError("pydicom is required for DICOM reading")

        if self.dicom_dataset is None:
            logger.warning("DICOM dataset not loaded. Call read_image() first.")
            return None

        try:
            self.pixel_array = self.dicom_dataset.pixel_array
            return self.pixel_array
        except Exception as e:
            logger.error("Error loading pixel array: %s", e)
            return None

    def get_patient_name(self) -> str:
        """
        Get patient name from DICOM metadata.

        Returns:
            str: Patient name or empty string if not available

        Examples:
            >>> eos_image = EosImage(directory="/path/to/eos.dcm")
            >>> eos_image.read_image()
            >>> patient_name = eos_image.get_patient_name()
        """
        if self.dicom_dataset is None:
            return ""

        if hasattr(self.dicom_dataset, "PatientName"):
            return str(self.dicom_dataset.PatientName)

        return ""

    def get_calibration_summary(self) -> Dict[str, float]:
        """
        Get a summary of calibration parameters.

        Returns:
            Dict[str, float]: Dictionary of calibration parameters

        Examples:
            >>> eos_image = EosImage(directory="/path/to/eos.dcm")
            >>> eos_image.read_image()
            >>> calibration = eos_image.get_calibration_summary()
            >>> print(f"Source to detector: {calibration['source_to_detector']}m")
        """
        return {
            "source_to_isocenter": self.distance_source_to_isocenter,
            "source_to_detector": self.distance_source_to_detector,
            "source_to_patient": self.distance_source_to_patient,
            "pixel_spacing_x": self.pixel_spacing_x,
            "pixel_spacing_y": self.pixel_spacing_y,
            "image_width": self.width,
            "image_height": self.height,
        }

    def __str__(self) -> str:
        """String representation of EosImage."""
        return (
            f"EosImage(directory='{self.directory}', "
            f"size={self.columns}x{self.rows}, "
            f"plane='{self.image_plane}')"
        )
