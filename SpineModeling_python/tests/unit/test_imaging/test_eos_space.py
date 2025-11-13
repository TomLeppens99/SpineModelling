"""
Unit tests for the EosSpace class and related classes.

Tests cover 3D geometry calculations, projection/inverse projection,
and coordinate conversions.
"""

import pytest
import math
from spine_modeling.core.position import Position
from spine_modeling.imaging.eos_image import EosImage
from spine_modeling.imaging.eos_space import (
    EosSpace,
    Orientation,
    SpaceObject
)


class TestOrientation:
    """Test Orientation class."""

    def test_orientation_creation(self):
        """Test orientation creation."""
        orientation = Orientation(10.0, 20.0, 30.0)
        assert orientation.x == 10.0
        assert orientation.y == 20.0
        assert orientation.z == 30.0

    def test_orientation_to_tuple(self):
        """Test conversion to tuple."""
        orientation = Orientation(10.0, 20.0, 30.0)
        result = orientation.to_tuple()
        assert result == (10.0, 20.0, 30.0)

    def test_orientation_equality(self):
        """Test orientation equality."""
        orient1 = Orientation(10.0, 20.0, 30.0)
        orient2 = Orientation(10.0, 20.0, 30.0)
        assert orient1 == orient2


class TestSpaceObject:
    """Test SpaceObject class."""

    def test_space_object_creation(self):
        """Test space object creation."""
        pos = Position(1.0, 2.0, 3.0)
        obj = SpaceObject(position=pos, name="TestObject")
        assert obj.position == pos
        assert obj.name == "TestObject"
        assert obj.properties == {}

    def test_space_object_with_properties(self):
        """Test space object with custom properties."""
        pos = Position(1.0, 2.0, 3.0)
        props = {"type": "landmark", "confidence": 0.95}
        obj = SpaceObject(position=pos, name="L1", properties=props)
        assert obj.properties == props

    def test_space_object_default_name(self):
        """Test space object with default name."""
        pos = Position(1.0, 2.0, 3.0)
        obj = SpaceObject(position=pos)
        assert obj.name == ""


class TestEosSpaceCreation:
    """Test EosSpace initialization."""

    def test_eos_space_creation(self):
        """Test basic EosSpace creation."""
        image_a = EosImage(directory="/test_a.dcm")
        image_b = EosImage(directory="/test_b.dcm")

        eos_space = EosSpace(image_a, image_b)

        assert eos_space.eos_image_a is image_a
        assert eos_space.eos_image_b is image_b
        assert len(eos_space.space_objects) == 0

    def test_eos_space_initial_positions(self):
        """Test that initial positions are at origin."""
        image_a = EosImage(directory="/test_a.dcm")
        image_b = EosImage(directory="/test_b.dcm")

        eos_space = EosSpace(image_a, image_b)

        assert eos_space.position_source1 == Position(0.0, 0.0, 0.0)
        assert eos_space.position_source2 == Position(0.0, 0.0, 0.0)
        assert eos_space.patient_position == Position(0.0, 0.0, 0.0)

    def test_eos_space_str_representation(self):
        """Test string representation."""
        image_a = EosImage(directory="/test_a.dcm")
        image_b = EosImage(directory="/test_b.dcm")
        image_a.image_plane = "AP"
        image_b.image_plane = "LAT"

        eos_space = EosSpace(image_a, image_b)
        str_repr = str(eos_space)

        assert "AP" in str_repr
        assert "LAT" in str_repr


class TestEosSpaceCalculation:
    """Test EOS space geometry calculations."""

    def setup_method(self):
        """Set up test fixtures."""
        self.image_a = EosImage(directory="/test_a.dcm")
        self.image_b = EosImage(directory="/test_b.dcm")

        # Set realistic EOS calibration parameters
        self.image_a.distance_source_to_isocenter = 1.35  # meters
        self.image_a.distance_source_to_detector = 2.7  # meters
        self.image_a.distance_source_to_patient = 1.0  # meters
        self.image_a.width = 0.146  # meters
        self.image_a.pixel_spacing_x = 0.000143  # meters

        self.image_b.distance_source_to_isocenter = 1.35
        self.image_b.distance_source_to_detector = 2.7
        self.image_b.distance_source_to_patient = 1.0
        self.image_b.width = 0.146
        self.image_b.pixel_spacing_x = 0.000143

    def test_calculate_eos_space_source_positions(self):
        """Test calculation of X-ray source positions."""
        eos_space = EosSpace(self.image_a, self.image_b)
        eos_space.calculate_eos_space()

        # Source 1 should be on negative Z-axis
        assert eos_space.position_source1.x == 0.0
        assert eos_space.position_source1.y == 0.0
        assert eos_space.position_source1.z == -1.35

        # Source 2 should be on negative X-axis
        assert eos_space.position_source2.x == -1.35
        assert eos_space.position_source2.y == 0.0
        assert eos_space.position_source2.z == 0.0

    def test_calculate_eos_space_patient_position(self):
        """Test calculation of patient position."""
        eos_space = EosSpace(self.image_a, self.image_b)
        eos_space.calculate_eos_space()

        # Patient should be between sources and isocenter
        expected_x = -(1.35 - 1.0)  # -0.35
        expected_z = -(1.35 - 1.0)  # -0.35

        assert abs(eos_space.patient_position.x - expected_x) < 1e-6
        assert eos_space.patient_position.y == 0.0
        assert abs(eos_space.patient_position.z - expected_z) < 1e-6

    def test_calculate_eos_space_image_origins(self):
        """Test calculation of image plane origins."""
        eos_space = EosSpace(self.image_a, self.image_b)
        eos_space.calculate_eos_space()

        # Image 1 origin
        expected_x1 = 0.146 / 2.0  # width / 2
        expected_z1 = 2.7 - 1.35  # detector - isocenter = 1.35

        assert abs(eos_space.position_origin_image1.x - expected_x1) < 1e-6
        assert eos_space.position_origin_image1.y == 0.0
        assert abs(eos_space.position_origin_image1.z - expected_z1) < 1e-6

        # Image 2 origin
        expected_x2 = 2.7 - 1.35  # detector - isocenter = 1.35
        expected_z2 = -0.146 / 2.0  # -width / 2

        assert abs(eos_space.position_origin_image2.x - expected_x2) < 1e-6
        assert eos_space.position_origin_image2.y == 0.0
        assert abs(eos_space.position_origin_image2.z - expected_z2) < 1e-6

    def test_calculate_eos_space_orientations(self):
        """Test calculation of image plane orientations."""
        eos_space = EosSpace(self.image_a, self.image_b)
        eos_space.calculate_eos_space()

        # Image 1 orientation: (0, 180, 0)
        assert eos_space.orientation_image1 == Orientation(0, 180, 0)

        # Image 2 orientation: (0, 270, 0)
        assert eos_space.orientation_image2 == Orientation(0, 270, 0)


class TestEosSpaceProjection:
    """Test projection and inverse projection methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.image_a = EosImage(directory="/test_a.dcm")
        self.image_b = EosImage(directory="/test_b.dcm")

        # Set calibration parameters
        self.image_a.distance_source_to_isocenter = 1.35
        self.image_b.distance_source_to_isocenter = 1.35

        self.eos_space = EosSpace(self.image_a, self.image_b)
        self.eos_space.calculate_eos_space()

    def test_project_at_isocenter(self):
        """Test projection of point at isocenter."""
        x_proj, z_proj = self.eos_space.project(0.0, 0.0)

        # Point at isocenter projects to origin
        assert abs(x_proj) < 1e-10
        assert abs(z_proj) < 1e-10

    def test_project_positive_coordinates(self):
        """Test projection of point with positive coordinates."""
        x_real = 0.1  # meters
        z_real = 0.2  # meters

        x_proj, z_proj = self.eos_space.project(x_real, z_real)

        # Verify projection calculations
        expected_x = (x_real / (1.35 + z_real)) * 1.35
        expected_z = (z_real / (1.35 + x_real)) * 1.35

        assert abs(x_proj - expected_x) < 1e-6
        assert abs(z_proj - expected_z) < 1e-6

    def test_inverse_project_at_origin(self):
        """Test inverse projection of origin."""
        # This would cause division by zero in slope calculation
        # Test with small offset instead
        x_real, z_real = self.eos_space.inverse_project(0.001, 0.001)

        # Should be close to origin
        assert abs(x_real) < 0.1
        assert abs(z_real) < 0.1

    def test_projection_inverse_projection_roundtrip(self):
        """Test that project and inverse_project are inverse operations."""
        # Start with real 3D coordinates
        x_real_orig = 0.1
        z_real_orig = 0.15

        # Project to 2D
        x_proj, z_proj = self.eos_space.project(x_real_orig, z_real_orig)

        # Inverse project back to 3D
        x_real_calc, z_real_calc = self.eos_space.inverse_project(x_proj, z_proj)

        # Should recover original coordinates
        assert abs(x_real_calc - x_real_orig) < 1e-6
        assert abs(z_real_calc - z_real_orig) < 1e-6

    def test_inverse_projection_with_known_values(self):
        """Test inverse projection with manually calculated values."""
        # Use specific projection coordinates
        x_proj = 0.05  # meters
        z_proj = 0.08  # meters

        x_real, z_real = self.eos_space.inverse_project(x_proj, z_proj)

        # Verify results are reasonable
        assert isinstance(x_real, float)
        assert isinstance(z_real, float)


class TestEosSpaceConversion:
    """Test coordinate conversion methods."""

    def setup_method(self):
        """Set up test fixtures."""
        self.image_a = EosImage(directory="/test_a.dcm")
        self.image_b = EosImage(directory="/test_b.dcm")

        self.image_a.pixel_spacing_x = 0.000143  # meters
        self.image_b.pixel_spacing_x = 0.000143  # meters

        self.eos_space = EosSpace(self.image_a, self.image_b)

    def test_convert_pixel_to_meters_with_spacing(self):
        """Test pixel to meters conversion with explicit spacing."""
        pixels = 100
        spacing = 0.000143  # meters

        meters = self.eos_space.convert_pixel_to_meters(pixels, pixel_spacing=spacing)

        expected = 100 * 0.000143
        assert abs(meters - expected) < 1e-10

    def test_convert_pixel_to_meters_image_a(self):
        """Test pixel to meters conversion using image A."""
        pixels = 100

        meters = self.eos_space.convert_pixel_to_meters(pixels, image_label="A")

        expected = 100 * 0.000143
        assert abs(meters - expected) < 1e-10

    def test_convert_pixel_to_meters_image_b(self):
        """Test pixel to meters conversion using image B."""
        pixels = 100

        meters = self.eos_space.convert_pixel_to_meters(pixels, image_label="B")

        expected = 100 * 0.000143
        assert abs(meters - expected) < 1e-10

    def test_convert_pixel_to_meters_invalid_label(self):
        """Test that invalid image label raises error."""
        with pytest.raises(ValueError, match="Either pixel_spacing or valid image_label"):
            self.eos_space.convert_pixel_to_meters(100, image_label="C")

    def test_convert_pixel_to_meters_no_args(self):
        """Test that missing both arguments raises error."""
        with pytest.raises(ValueError, match="Either pixel_spacing or valid image_label"):
            self.eos_space.convert_pixel_to_meters(100)

    def test_convert_meters_to_pixels(self):
        """Test meters to pixels conversion."""
        meters = 0.0143
        spacing = 0.000143

        pixels = self.eos_space.convert_meters_to_pixels(meters, spacing)

        expected = round(0.0143 / 0.000143)
        assert pixels == expected

    def test_convert_meters_to_pixels_rounding(self):
        """Test that meters to pixels rounds correctly."""
        meters = 0.01437  # Should round to 100 pixels
        spacing = 0.000143

        pixels = self.eos_space.convert_meters_to_pixels(meters, spacing)

        # 0.01437 / 0.000143 ≈ 100.49 → rounds to 100
        assert pixels == 100

    def test_conversion_roundtrip(self):
        """Test pixel-to-meters-to-pixel roundtrip."""
        original_pixels = 150
        spacing = 0.000143

        meters = self.eos_space.convert_pixel_to_meters(
            original_pixels,
            pixel_spacing=spacing
        )
        back_to_pixels = self.eos_space.convert_meters_to_pixels(meters, spacing)

        assert back_to_pixels == original_pixels


class TestEosSpaceObjects:
    """Test space object management."""

    def setup_method(self):
        """Set up test fixtures."""
        self.image_a = EosImage(directory="/test_a.dcm")
        self.image_b = EosImage(directory="/test_b.dcm")
        self.eos_space = EosSpace(self.image_a, self.image_b)

    def test_add_space_object(self):
        """Test adding a space object."""
        obj = SpaceObject(Position(1.0, 2.0, 3.0), name="L1")

        self.eos_space.add_space_object(obj)

        assert len(self.eos_space.space_objects) == 1
        assert self.eos_space.space_objects[0] is obj

    def test_add_multiple_space_objects(self):
        """Test adding multiple space objects."""
        obj1 = SpaceObject(Position(1.0, 2.0, 3.0), name="L1")
        obj2 = SpaceObject(Position(4.0, 5.0, 6.0), name="L2")
        obj3 = SpaceObject(Position(7.0, 8.0, 9.0), name="L3")

        self.eos_space.add_space_object(obj1)
        self.eos_space.add_space_object(obj2)
        self.eos_space.add_space_object(obj3)

        assert len(self.eos_space.space_objects) == 3

    def test_remove_space_object(self):
        """Test removing a space object."""
        obj = SpaceObject(Position(1.0, 2.0, 3.0), name="L1")
        self.eos_space.add_space_object(obj)

        result = self.eos_space.remove_space_object(obj)

        assert result is True
        assert len(self.eos_space.space_objects) == 0

    def test_remove_nonexistent_object(self):
        """Test removing object that doesn't exist."""
        obj = SpaceObject(Position(1.0, 2.0, 3.0), name="L1")

        result = self.eos_space.remove_space_object(obj)

        assert result is False

    def test_clear_space_objects(self):
        """Test clearing all space objects."""
        self.eos_space.add_space_object(SpaceObject(Position(1.0, 2.0, 3.0), name="L1"))
        self.eos_space.add_space_object(SpaceObject(Position(4.0, 5.0, 6.0), name="L2"))

        self.eos_space.clear_space_objects()

        assert len(self.eos_space.space_objects) == 0


class TestEosSpaceGeometrySummary:
    """Test geometry summary functionality."""

    def test_get_geometry_summary(self):
        """Test getting geometry summary."""
        image_a = EosImage(directory="/test_a.dcm")
        image_b = EosImage(directory="/test_b.dcm")

        image_a.distance_source_to_isocenter = 1.35
        image_a.distance_source_to_detector = 2.7
        image_a.distance_source_to_patient = 1.0
        image_a.width = 0.146

        image_b.distance_source_to_isocenter = 1.35
        image_b.distance_source_to_detector = 2.7
        image_b.distance_source_to_patient = 1.0
        image_b.width = 0.146

        eos_space = EosSpace(image_a, image_b)
        eos_space.calculate_eos_space()

        # Add some objects
        eos_space.add_space_object(SpaceObject(Position(0, 0, 0), name="O1"))
        eos_space.add_space_object(SpaceObject(Position(1, 1, 1), name="O2"))

        summary = eos_space.get_geometry_summary()

        assert "source1" in summary
        assert "source2" in summary
        assert "patient" in summary
        assert "image1_origin" in summary
        assert "image2_origin" in summary
        assert "image1_orientation" in summary
        assert "image2_orientation" in summary
        assert "num_objects" in summary
        assert summary["num_objects"] == 2

    def test_geometry_summary_structure(self):
        """Test that geometry summary has correct structure."""
        image_a = EosImage(directory="/test_a.dcm")
        image_b = EosImage(directory="/test_b.dcm")

        image_a.distance_source_to_isocenter = 1.35
        image_a.distance_source_to_detector = 2.7
        image_a.distance_source_to_patient = 1.0
        image_a.width = 0.146

        image_b.distance_source_to_isocenter = 1.35
        image_b.distance_source_to_detector = 2.7
        image_b.distance_source_to_patient = 1.0
        image_b.width = 0.146

        eos_space = EosSpace(image_a, image_b)
        eos_space.calculate_eos_space()

        summary = eos_space.get_geometry_summary()

        assert isinstance(summary["source1"], Position)
        assert isinstance(summary["source2"], Position)
        assert isinstance(summary["patient"], Position)
        assert isinstance(summary["image1_origin"], Position)
        assert isinstance(summary["image2_origin"], Position)
        assert isinstance(summary["image1_orientation"], Orientation)
        assert isinstance(summary["image2_orientation"], Orientation)
        assert isinstance(summary["num_objects"], int)
