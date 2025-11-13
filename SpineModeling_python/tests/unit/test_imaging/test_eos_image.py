"""
Unit tests for the EosImage class.

Tests cover DICOM reading, metadata extraction, and calibration parameter handling.
Uses mocking to simulate DICOM file reading without requiring actual DICOM files.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Try to import the module - it should work even if pydicom/numpy aren't installed
from spine_modeling.imaging.eos_image import EosImage


class TestEosImageCreation:
    """Test EosImage object creation and initialization."""

    def test_eos_image_creation(self):
        """Test basic EosImage creation."""
        eos_image = EosImage(directory="/path/to/image.dcm")
        assert eos_image.directory == "/path/to/image.dcm"
        assert eos_image.columns == 0
        assert eos_image.rows == 0
        assert eos_image.distance_source_to_isocenter == 0.0

    def test_eos_image_with_defaults(self):
        """Test that default values are set correctly."""
        eos_image = EosImage(directory="/test.dcm")
        assert eos_image.image_rotated is False
        assert eos_image.image_plane == ""
        assert eos_image.image_comments == ""
        assert eos_image.field_of_view_origin == 0
        assert eos_image.dicom_dataset is None
        assert eos_image.pixel_array is None

    def test_eos_image_str_representation(self):
        """Test string representation."""
        eos_image = EosImage(directory="/test.dcm")
        eos_image.columns = 1024
        eos_image.rows = 2048
        eos_image.image_plane = "AP"
        str_repr = str(eos_image)
        assert "/test.dcm" in str_repr
        assert "1024x2048" in str_repr
        assert "AP" in str_repr


@pytest.mark.skipif(
    not hasattr(EosImage, '__annotations__'),
    reason="Module not properly imported"
)
class TestEosImageDICOMReading:
    """Test DICOM reading functionality with mocking."""

    @patch('spine_modeling.imaging.eos_image.pydicom')
    @patch('spine_modeling.imaging.eos_image.Path')
    def test_read_image_success(self, mock_path, mock_pydicom):
        """Test successful DICOM image reading."""
        # Setup mocks
        mock_path.return_value.exists.return_value = True

        mock_dataset = Mock()
        mock_dataset.Rows = 2048
        mock_dataset.Columns = 1024
        mock_dataset.DistanceSourceToIsocenter = 1350.0  # mm
        mock_dataset.DistanceSourceToDetector = 2700.0  # mm
        mock_dataset.DistanceSourceToPatient = 1000.0  # mm
        mock_dataset.ImagerPixelSpacing = [0.143, 0.143]  # mm
        mock_dataset.PixelSpacing = [0.143, 0.143]  # mm
        mock_dataset.PatientOrientation = "AP"

        mock_pydicom.dcmread.return_value = mock_dataset

        # Test
        eos_image = EosImage(directory="/test.dcm")
        result = eos_image.read_image()

        assert result is True
        assert eos_image.rows == 2048
        assert eos_image.columns == 1024
        assert abs(eos_image.distance_source_to_isocenter - 1.35) < 1e-6
        assert abs(eos_image.distance_source_to_detector - 2.7) < 1e-6
        assert abs(eos_image.distance_source_to_patient - 1.0) < 1e-6
        assert eos_image.image_plane == "AP"

    @patch('spine_modeling.imaging.eos_image.pydicom')
    @patch('spine_modeling.imaging.eos_image.Path')
    def test_read_image_file_not_found(self, mock_path, mock_pydicom):
        """Test reading non-existent file raises FileNotFoundError."""
        mock_path.return_value.exists.return_value = False

        eos_image = EosImage(directory="/nonexistent.dcm")

        with pytest.raises(FileNotFoundError, match="File/Path cannot be found"):
            eos_image.read_image()

    @patch('spine_modeling.imaging.eos_image.pydicom', None)
    def test_read_image_without_pydicom(self):
        """Test that reading without pydicom raises ImportError."""
        eos_image = EosImage(directory="/test.dcm")

        with pytest.raises(ImportError, match="pydicom is required"):
            eos_image.read_image()

    @patch('spine_modeling.imaging.eos_image.pydicom')
    @patch('spine_modeling.imaging.eos_image.Path')
    def test_read_image_missing_required_tag(self, mock_path, mock_pydicom):
        """Test handling of missing required DICOM tags."""
        mock_path.return_value.exists.return_value = True

        # Create dataset missing required tags
        mock_dataset = Mock()
        mock_dataset.Rows = 2048
        mock_dataset.Columns = 1024
        # Missing DistanceSourceToIsocenter
        del mock_dataset.DistanceSourceToIsocenter

        mock_pydicom.dcmread.return_value = mock_dataset

        eos_image = EosImage(directory="/test.dcm")

        with pytest.raises(ValueError, match="Required DICOM tag missing"):
            eos_image.read_image()

    @patch('spine_modeling.imaging.eos_image.pydicom')
    @patch('spine_modeling.imaging.eos_image.Path')
    def test_read_image_calculates_dimensions(self, mock_path, mock_pydicom):
        """Test that physical dimensions are calculated correctly."""
        mock_path.return_value.exists.return_value = True

        mock_dataset = Mock()
        mock_dataset.Rows = 1000
        mock_dataset.Columns = 500
        mock_dataset.DistanceSourceToIsocenter = 1350.0
        mock_dataset.DistanceSourceToDetector = 2700.0
        mock_dataset.DistanceSourceToPatient = 1000.0
        mock_dataset.ImagerPixelSpacing = [0.2, 0.2]
        mock_dataset.PixelSpacing = [0.2, 0.2]  # mm
        mock_dataset.PatientOrientation = "LAT"

        mock_pydicom.dcmread.return_value = mock_dataset

        eos_image = EosImage(directory="/test.dcm")
        eos_image.read_image()

        # pixel_spacing_x = 0.2mm = 0.0002m
        # width = 500 * 0.0002 = 0.1m
        # height = 1000 * 0.0002 = 0.2m
        assert abs(eos_image.width - 0.1) < 1e-6
        assert abs(eos_image.height - 0.2) < 1e-6


class TestEosImageDetailedReading:
    """Test detailed DICOM tag reading functionality."""

    @patch('spine_modeling.imaging.eos_image.pydicom')
    @patch('spine_modeling.imaging.eos_image.Path')
    def test_read_image_tags_to_properties_success(self, mock_path, mock_pydicom):
        """Test successful detailed DICOM reading."""
        mock_path.return_value.exists.return_value = True

        mock_dataset = Mock()
        mock_dataset.Rows = 2048
        mock_dataset.Columns = 1024
        mock_dataset.DistanceSourceToIsocenter = 1350.0
        mock_dataset.DistanceSourceToDetector = 2700.0
        mock_dataset.DistanceSourceToPatient = 1000.0
        mock_dataset.ImagerPixelSpacing = [0.143, 0.143]
        mock_dataset.PixelSpacing = [0.143, 0.143]
        mock_dataset.PatientOrientation = "AP"
        mock_dataset.FieldOfViewOrigin = 0
        mock_dataset.ImageComments = "EOS Test Image"

        # Mock iteration for tag building
        mock_dataset.__iter__ = Mock(return_value=iter([]))

        mock_pydicom.dcmread.return_value = mock_dataset

        eos_image = EosImage(directory="/test.dcm")
        result = eos_image.read_image_tags_to_properties()

        assert result is True
        assert eos_image.image_comments == "EOS Test Image"
        assert eos_image.field_of_view_origin == 0

    @patch('spine_modeling.imaging.eos_image.pydicom')
    @patch('spine_modeling.imaging.eos_image.Path')
    def test_read_image_tags_calibration_error(self, mock_path, mock_pydicom):
        """Test error when calibration parameters are missing."""
        mock_path.return_value.exists.return_value = True

        mock_dataset = Mock()
        mock_dataset.Rows = 2048
        mock_dataset.Columns = 1024
        # Simulate missing calibration parameters
        mock_dataset.configure_mock(**{
            'DistanceSourceToIsocenter': Mock(side_effect=AttributeError)
        })

        mock_pydicom.dcmread.return_value = mock_dataset

        eos_image = EosImage(directory="/test.dcm")

        with pytest.raises(ValueError, match="Spatial calibration parameters"):
            eos_image.read_image_tags_to_properties()


class TestEosImageUtilityMethods:
    """Test utility methods of EosImage."""

    def test_get_calibration_summary(self):
        """Test getting calibration summary."""
        eos_image = EosImage(directory="/test.dcm")
        eos_image.distance_source_to_isocenter = 1.35
        eos_image.distance_source_to_detector = 2.7
        eos_image.distance_source_to_patient = 1.0
        eos_image.pixel_spacing_x = 0.000143
        eos_image.pixel_spacing_y = 0.000143
        eos_image.width = 0.146
        eos_image.height = 0.293

        summary = eos_image.get_calibration_summary()

        assert summary["source_to_isocenter"] == 1.35
        assert summary["source_to_detector"] == 2.7
        assert summary["source_to_patient"] == 1.0
        assert summary["pixel_spacing_x"] == 0.000143
        assert summary["pixel_spacing_y"] == 0.000143
        assert summary["image_width"] == 0.146
        assert summary["image_height"] == 0.293

    @patch('spine_modeling.imaging.eos_image.pydicom')
    def test_get_patient_name_with_dataset(self, mock_pydicom):
        """Test getting patient name from loaded dataset."""
        mock_dataset = Mock()
        mock_dataset.PatientName = "DOE^JOHN"

        eos_image = EosImage(directory="/test.dcm")
        eos_image.dicom_dataset = mock_dataset

        patient_name = eos_image.get_patient_name()
        assert patient_name == "DOE^JOHN"

    def test_get_patient_name_without_dataset(self):
        """Test getting patient name when no dataset loaded."""
        eos_image = EosImage(directory="/test.dcm")

        patient_name = eos_image.get_patient_name()
        assert patient_name == ""

    @patch('spine_modeling.imaging.eos_image.pydicom')
    def test_get_patient_name_missing_tag(self, mock_pydicom):
        """Test getting patient name when tag is missing."""
        mock_dataset = Mock(spec=[])  # No PatientName attribute

        eos_image = EosImage(directory="/test.dcm")
        eos_image.dicom_dataset = mock_dataset

        patient_name = eos_image.get_patient_name()
        assert patient_name == ""


class TestEosImagePixelArray:
    """Test pixel array loading functionality."""

    @patch('spine_modeling.imaging.eos_image.np')
    @patch('spine_modeling.imaging.eos_image.pydicom')
    def test_load_pixel_array_success(self, mock_pydicom, mock_np):
        """Test successful pixel array loading."""
        mock_dataset = Mock()
        mock_pixel_array = Mock()
        mock_dataset.pixel_array = mock_pixel_array

        eos_image = EosImage(directory="/test.dcm")
        eos_image.dicom_dataset = mock_dataset

        result = eos_image.load_pixel_array()

        assert result is mock_pixel_array
        assert eos_image.pixel_array is mock_pixel_array

    @patch('spine_modeling.imaging.eos_image.np', None)
    def test_load_pixel_array_without_numpy(self):
        """Test that loading without numpy raises ImportError."""
        eos_image = EosImage(directory="/test.dcm")

        with pytest.raises(ImportError, match="numpy is required"):
            eos_image.load_pixel_array()

    @patch('spine_modeling.imaging.eos_image.np')
    @patch('spine_modeling.imaging.eos_image.pydicom')
    def test_load_pixel_array_without_dataset(self, mock_pydicom, mock_np):
        """Test loading pixel array when dataset not loaded."""
        eos_image = EosImage(directory="/test.dcm")
        eos_image.dicom_dataset = None

        result = eos_image.load_pixel_array()

        assert result is None


class TestEosImageDICOMTags:
    """Test DICOM tag handling."""

    @patch('spine_modeling.imaging.eos_image.pydicom')
    def test_build_dicom_tags_dict(self, mock_pydicom):
        """Test building DICOM tags dictionary."""
        # Create mock DICOM elements
        mock_element1 = Mock()
        mock_element1.tag.group = 0x0010
        mock_element1.tag.element = 0x0010
        mock_element1.name = "PatientName"
        mock_element1.value = "DOE^JOHN"

        mock_element2 = Mock()
        mock_element2.tag.group = 0x0028
        mock_element2.tag.element = 0x0010
        mock_element2.name = "Rows"
        mock_element2.value = 2048

        mock_dataset = Mock()
        mock_dataset.__iter__ = Mock(return_value=iter([mock_element1, mock_element2]))

        eos_image = EosImage(directory="/test.dcm")
        eos_image.dicom_dataset = mock_dataset
        eos_image._build_dicom_tags_dict()

        assert len(eos_image.dicom_tags) == 2
        assert "0010,0010" in eos_image.dicom_tags
        assert eos_image.dicom_tags["0010,0010"]["name"] == "PatientName"
        assert eos_image.dicom_tags["0010,0010"]["value"] == "DOE^JOHN"

    @patch('spine_modeling.imaging.eos_image.pydicom')
    def test_get_dicom_tag_table(self, mock_pydicom):
        """Test getting DICOM tags as table data."""
        # Create mock DICOM elements
        mock_element = Mock()
        mock_element.tag.group = 0x0010
        mock_element.tag.element = 0x0010
        mock_element.name = "PatientName"
        mock_element.value = "DOE^JOHN"

        mock_dataset = Mock()
        mock_dataset.__iter__ = Mock(return_value=iter([mock_element]))

        eos_image = EosImage(directory="/test.dcm")
        eos_image.dicom_dataset = mock_dataset
        eos_image._build_dicom_tags_dict()

        table = eos_image.get_dicom_tag_table()

        assert len(table) == 1
        assert table[0]["group"] == "0010"
        assert table[0]["element"] == "0010"
        assert table[0]["description"] == "PatientName"
        assert table[0]["value"] == "DOE^JOHN"


class TestEosImageEdgeCases:
    """Test edge cases and special scenarios."""

    @patch('spine_modeling.imaging.eos_image.pydicom')
    @patch('spine_modeling.imaging.eos_image.Path')
    def test_read_image_without_patient_orientation(self, mock_path, mock_pydicom):
        """Test reading image without PatientOrientation tag."""
        mock_path.return_value.exists.return_value = True

        mock_dataset = Mock(spec=['Rows', 'Columns', 'DistanceSourceToIsocenter',
                                   'DistanceSourceToDetector', 'DistanceSourceToPatient',
                                   'ImagerPixelSpacing', 'PixelSpacing'])
        mock_dataset.Rows = 2048
        mock_dataset.Columns = 1024
        mock_dataset.DistanceSourceToIsocenter = 1350.0
        mock_dataset.DistanceSourceToDetector = 2700.0
        mock_dataset.DistanceSourceToPatient = 1000.0
        mock_dataset.ImagerPixelSpacing = [0.143, 0.143]
        mock_dataset.PixelSpacing = [0.143, 0.143]

        mock_pydicom.dcmread.return_value = mock_dataset

        eos_image = EosImage(directory="/test.dcm")
        eos_image.read_image()

        assert eos_image.image_plane == "UNKNOWN"

    def test_eos_image_modification(self):
        """Test that EosImage properties can be modified."""
        eos_image = EosImage(directory="/test.dcm")

        eos_image.columns = 1024
        eos_image.rows = 2048
        eos_image.distance_source_to_isocenter = 1.35
        eos_image.image_rotated = True

        assert eos_image.columns == 1024
        assert eos_image.rows == 2048
        assert eos_image.distance_source_to_isocenter == 1.35
        assert eos_image.image_rotated is True
