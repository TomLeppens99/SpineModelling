"""
Unit tests for the Position class.

Tests cover all methods, edge cases, and expected behaviors of the Position class.
"""

import pytest
import math
from spine_modeling.core.position import Position


class TestPositionCreation:
    """Test Position object creation and initialization."""

    def test_position_creation(self):
        """Test basic position creation with float values."""
        pos = Position(1.0, 2.0, 3.0)
        assert pos.x == 1.0
        assert pos.y == 2.0
        assert pos.z == 3.0

    def test_position_creation_with_integers(self):
        """Test position creation with integer values."""
        pos = Position(1, 2, 3)
        assert pos.x == 1
        assert pos.y == 2
        assert pos.z == 3

    def test_position_creation_with_negative_values(self):
        """Test position creation with negative coordinates."""
        pos = Position(-1.0, -2.0, -3.0)
        assert pos.x == -1.0
        assert pos.y == -2.0
        assert pos.z == -3.0

    def test_position_creation_with_zero(self):
        """Test position creation at origin."""
        pos = Position(0.0, 0.0, 0.0)
        assert pos.x == 0.0
        assert pos.y == 0.0
        assert pos.z == 0.0

    def test_position_equality(self):
        """Test position equality comparison."""
        pos1 = Position(1.0, 2.0, 3.0)
        pos2 = Position(1.0, 2.0, 3.0)
        assert pos1 == pos2

    def test_position_inequality(self):
        """Test position inequality comparison."""
        pos1 = Position(1.0, 2.0, 3.0)
        pos2 = Position(1.0, 2.0, 4.0)
        assert pos1 != pos2


class TestPositionDistance:
    """Test distance calculations between positions."""

    def test_distance_to_same_position(self):
        """Test distance to itself is zero."""
        pos = Position(1.0, 2.0, 3.0)
        assert pos.distance_to(pos) == 0.0

    def test_distance_to_origin(self):
        """Test distance calculation to origin."""
        pos = Position(3.0, 4.0, 0.0)
        origin = Position(0.0, 0.0, 0.0)
        assert pos.distance_to(origin) == 5.0

    def test_distance_3d_pythagorean(self):
        """Test 3D distance calculation."""
        pos1 = Position(0.0, 0.0, 0.0)
        pos2 = Position(1.0, 2.0, 2.0)
        expected = math.sqrt(1.0 + 4.0 + 4.0)  # sqrt(9) = 3
        assert pos1.distance_to(pos2) == expected

    def test_distance_is_symmetric(self):
        """Test that distance from A to B equals distance from B to A."""
        pos1 = Position(1.0, 2.0, 3.0)
        pos2 = Position(4.0, 5.0, 6.0)
        assert pos1.distance_to(pos2) == pos2.distance_to(pos1)

    def test_distance_with_negative_coordinates(self):
        """Test distance calculation with negative coordinates."""
        pos1 = Position(-1.0, -2.0, -3.0)
        pos2 = Position(1.0, 2.0, 3.0)
        expected = math.sqrt(4.0 + 16.0 + 36.0)  # sqrt(56)
        assert abs(pos1.distance_to(pos2) - expected) < 1e-10


class TestPositionArithmetic:
    """Test arithmetic operations on positions."""

    def test_addition(self):
        """Test position addition."""
        pos1 = Position(1.0, 2.0, 3.0)
        pos2 = Position(4.0, 5.0, 6.0)
        result = pos1 + pos2
        assert result == Position(5.0, 7.0, 9.0)

    def test_addition_with_zero(self):
        """Test addition with zero position."""
        pos = Position(1.0, 2.0, 3.0)
        zero = Position(0.0, 0.0, 0.0)
        result = pos + zero
        assert result == pos

    def test_addition_with_negative(self):
        """Test addition with negative values."""
        pos1 = Position(5.0, 3.0, 2.0)
        pos2 = Position(-2.0, -1.0, -1.0)
        result = pos1 + pos2
        assert result == Position(3.0, 2.0, 1.0)

    def test_subtraction(self):
        """Test position subtraction."""
        pos1 = Position(5.0, 7.0, 9.0)
        pos2 = Position(1.0, 2.0, 3.0)
        result = pos1 - pos2
        assert result == Position(4.0, 5.0, 6.0)

    def test_subtraction_same_position(self):
        """Test subtracting position from itself gives zero."""
        pos = Position(1.0, 2.0, 3.0)
        result = pos - pos
        assert result == Position(0.0, 0.0, 0.0)

    def test_multiplication_by_scalar(self):
        """Test multiplication by scalar."""
        pos = Position(1.0, 2.0, 3.0)
        result = pos * 2.0
        assert result == Position(2.0, 4.0, 6.0)

    def test_multiplication_by_zero(self):
        """Test multiplication by zero."""
        pos = Position(1.0, 2.0, 3.0)
        result = pos * 0.0
        assert result == Position(0.0, 0.0, 0.0)

    def test_multiplication_by_negative(self):
        """Test multiplication by negative scalar."""
        pos = Position(1.0, 2.0, 3.0)
        result = pos * -2.0
        assert result == Position(-2.0, -4.0, -6.0)

    def test_division_by_scalar(self):
        """Test division by scalar."""
        pos = Position(2.0, 4.0, 6.0)
        result = pos / 2.0
        assert result == Position(1.0, 2.0, 3.0)

    def test_division_by_one(self):
        """Test division by one returns same position."""
        pos = Position(1.0, 2.0, 3.0)
        result = pos / 1.0
        assert result == pos

    def test_division_by_zero_raises_error(self):
        """Test that division by zero raises ZeroDivisionError."""
        pos = Position(1.0, 2.0, 3.0)
        with pytest.raises(ZeroDivisionError, match="Cannot divide position by zero"):
            pos / 0.0


class TestPositionConversion:
    """Test conversion methods for Position."""

    def test_to_tuple(self):
        """Test conversion to tuple."""
        pos = Position(1.0, 2.0, 3.0)
        result = pos.to_tuple()
        assert result == (1.0, 2.0, 3.0)
        assert isinstance(result, tuple)

    def test_from_tuple(self):
        """Test creation from tuple."""
        coords = (1.0, 2.0, 3.0)
        pos = Position.from_tuple(coords)
        assert pos == Position(1.0, 2.0, 3.0)

    def test_from_tuple_with_integers(self):
        """Test creation from tuple with integers."""
        coords = (1, 2, 3)
        pos = Position.from_tuple(coords)
        assert pos == Position(1, 2, 3)

    def test_tuple_roundtrip(self):
        """Test that to_tuple and from_tuple are inverse operations."""
        original = Position(1.5, 2.5, 3.5)
        tuple_form = original.to_tuple()
        reconstructed = Position.from_tuple(tuple_form)
        assert original == reconstructed


class TestPositionMagnitude:
    """Test magnitude and normalization methods."""

    def test_magnitude_zero(self):
        """Test magnitude of zero position."""
        pos = Position(0.0, 0.0, 0.0)
        assert pos.magnitude() == 0.0

    def test_magnitude_simple(self):
        """Test magnitude of simple position."""
        pos = Position(3.0, 4.0, 0.0)
        assert pos.magnitude() == 5.0

    def test_magnitude_3d(self):
        """Test magnitude in 3D."""
        pos = Position(1.0, 2.0, 2.0)
        expected = math.sqrt(1.0 + 4.0 + 4.0)  # sqrt(9) = 3
        assert pos.magnitude() == expected

    def test_magnitude_negative_coordinates(self):
        """Test magnitude with negative coordinates."""
        pos = Position(-3.0, -4.0, 0.0)
        assert pos.magnitude() == 5.0

    def test_normalize_simple(self):
        """Test normalization of simple vector."""
        pos = Position(3.0, 4.0, 0.0)
        normalized = pos.normalize()
        assert abs(normalized.magnitude() - 1.0) < 1e-10

    def test_normalize_preserves_direction(self):
        """Test that normalization preserves direction."""
        pos = Position(3.0, 4.0, 0.0)
        normalized = pos.normalize()
        # Check that normalized is parallel to original
        assert abs(normalized.x / pos.x - normalized.y / pos.y) < 1e-10

    def test_normalize_components(self):
        """Test normalized vector components."""
        pos = Position(3.0, 4.0, 0.0)
        normalized = pos.normalize()
        assert abs(normalized.x - 0.6) < 1e-10
        assert abs(normalized.y - 0.8) < 1e-10
        assert abs(normalized.z - 0.0) < 1e-10

    def test_normalize_zero_raises_error(self):
        """Test that normalizing zero position raises ValueError."""
        pos = Position(0.0, 0.0, 0.0)
        with pytest.raises(ValueError, match="Cannot normalize a zero-magnitude position"):
            pos.normalize()

    def test_normalize_idempotent(self):
        """Test that normalizing a unit vector returns a unit vector."""
        pos = Position(1.0, 0.0, 0.0)
        normalized = pos.normalize()
        assert normalized.magnitude() == 1.0
        double_normalized = normalized.normalize()
        assert abs(double_normalized.magnitude() - 1.0) < 1e-10


class TestPositionEdgeCases:
    """Test edge cases and special scenarios."""

    def test_very_large_values(self):
        """Test position with very large coordinate values."""
        pos = Position(1e10, 2e10, 3e10)
        assert pos.x == 1e10
        assert pos.y == 2e10
        assert pos.z == 3e10

    def test_very_small_values(self):
        """Test position with very small coordinate values."""
        pos = Position(1e-10, 2e-10, 3e-10)
        assert pos.x == 1e-10
        assert pos.y == 2e-10
        assert pos.z == 3e-10

    def test_mixed_sign_coordinates(self):
        """Test position with mixed positive and negative coordinates."""
        pos = Position(-1.0, 2.0, -3.0)
        assert pos.x == -1.0
        assert pos.y == 2.0
        assert pos.z == -3.0

    def test_chain_operations(self):
        """Test chaining multiple operations."""
        pos1 = Position(1.0, 2.0, 3.0)
        pos2 = Position(2.0, 3.0, 4.0)
        result = (pos1 + pos2) * 2.0 - pos1
        expected = Position(5.0, 8.0, 11.0)
        assert result == expected


class TestPositionStringRepresentation:
    """Test string representation of Position."""

    def test_repr(self):
        """Test __repr__ output."""
        pos = Position(1.0, 2.0, 3.0)
        repr_str = repr(pos)
        assert "Position" in repr_str
        assert "1.0" in repr_str
        assert "2.0" in repr_str
        assert "3.0" in repr_str

    def test_repr_eval_roundtrip(self):
        """Test that repr can be used to recreate object."""
        pos = Position(1.5, 2.5, 3.5)
        repr_str = repr(pos)
        # Note: Using eval in tests is acceptable for testing repr
        reconstructed = eval(repr_str)  # noqa: S307
        assert pos == reconstructed
