"""
Unit tests for the EllipsePoint class and PointCollection.

Tests cover all methods, edge cases, and expected behaviors.
"""

import pytest
import math
from spine_modeling.core.ellipse_point import EllipsePoint, PointCollection


class TestEllipsePointCreation:
    """Test EllipsePoint object creation and initialization."""

    def test_point_creation(self):
        """Test basic point creation with float values."""
        point = EllipsePoint(10.5, 20.3)
        assert point.x == 10.5
        assert point.y == 20.3

    def test_point_creation_with_integers(self):
        """Test point creation with integer values."""
        point = EllipsePoint(10, 20)
        assert point.x == 10
        assert point.y == 20

    def test_point_creation_with_negative_values(self):
        """Test point creation with negative coordinates."""
        point = EllipsePoint(-5.0, -10.0)
        assert point.x == -5.0
        assert point.y == -10.0

    def test_point_creation_at_origin(self):
        """Test point creation at origin."""
        point = EllipsePoint(0.0, 0.0)
        assert point.x == 0.0
        assert point.y == 0.0

    def test_point_equality(self):
        """Test point equality comparison."""
        point1 = EllipsePoint(1.0, 2.0)
        point2 = EllipsePoint(1.0, 2.0)
        assert point1 == point2

    def test_point_inequality(self):
        """Test point inequality comparison."""
        point1 = EllipsePoint(1.0, 2.0)
        point2 = EllipsePoint(1.0, 3.0)
        assert point1 != point2


class TestEllipsePointDistance:
    """Test distance calculations between points."""

    def test_distance_to_same_point(self):
        """Test distance to itself is zero."""
        point = EllipsePoint(10.0, 20.0)
        assert point.distance_to(point) == 0.0

    def test_distance_to_origin(self):
        """Test distance calculation to origin."""
        point = EllipsePoint(3.0, 4.0)
        origin = EllipsePoint(0.0, 0.0)
        assert point.distance_to(origin) == 5.0

    def test_distance_2d_pythagorean(self):
        """Test 2D distance calculation."""
        point1 = EllipsePoint(0.0, 0.0)
        point2 = EllipsePoint(5.0, 12.0)
        expected = 13.0
        assert point1.distance_to(point2) == expected

    def test_distance_is_symmetric(self):
        """Test that distance from A to B equals distance from B to A."""
        point1 = EllipsePoint(1.0, 2.0)
        point2 = EllipsePoint(4.0, 6.0)
        assert point1.distance_to(point2) == point2.distance_to(point1)

    def test_distance_with_negative_coordinates(self):
        """Test distance calculation with negative coordinates."""
        point1 = EllipsePoint(-3.0, -4.0)
        point2 = EllipsePoint(0.0, 0.0)
        assert point1.distance_to(point2) == 5.0


class TestEllipsePointArithmetic:
    """Test arithmetic operations on points."""

    def test_addition(self):
        """Test point addition."""
        point1 = EllipsePoint(1.0, 2.0)
        point2 = EllipsePoint(3.0, 4.0)
        result = point1 + point2
        assert result == EllipsePoint(4.0, 6.0)

    def test_addition_with_zero(self):
        """Test addition with zero point."""
        point = EllipsePoint(5.0, 7.0)
        zero = EllipsePoint(0.0, 0.0)
        result = point + zero
        assert result == point

    def test_subtraction(self):
        """Test point subtraction."""
        point1 = EllipsePoint(5.0, 7.0)
        point2 = EllipsePoint(2.0, 3.0)
        result = point1 - point2
        assert result == EllipsePoint(3.0, 4.0)

    def test_subtraction_same_point(self):
        """Test subtracting point from itself gives zero."""
        point = EllipsePoint(5.0, 7.0)
        result = point - point
        assert result == EllipsePoint(0.0, 0.0)

    def test_multiplication_by_scalar(self):
        """Test multiplication by scalar."""
        point = EllipsePoint(2.0, 3.0)
        result = point * 2.0
        assert result == EllipsePoint(4.0, 6.0)

    def test_multiplication_by_zero(self):
        """Test multiplication by zero."""
        point = EllipsePoint(5.0, 7.0)
        result = point * 0.0
        assert result == EllipsePoint(0.0, 0.0)

    def test_division_by_scalar(self):
        """Test division by scalar."""
        point = EllipsePoint(4.0, 6.0)
        result = point / 2.0
        assert result == EllipsePoint(2.0, 3.0)

    def test_division_by_zero_raises_error(self):
        """Test that division by zero raises ZeroDivisionError."""
        point = EllipsePoint(1.0, 2.0)
        with pytest.raises(ZeroDivisionError, match="Cannot divide point by zero"):
            point / 0.0


class TestEllipsePointConversion:
    """Test conversion methods for EllipsePoint."""

    def test_to_tuple(self):
        """Test conversion to tuple."""
        point = EllipsePoint(1.5, 2.5)
        result = point.to_tuple()
        assert result == (1.5, 2.5)
        assert isinstance(result, tuple)

    def test_from_tuple(self):
        """Test creation from tuple."""
        coords = (1.5, 2.5)
        point = EllipsePoint.from_tuple(coords)
        assert point == EllipsePoint(1.5, 2.5)

    def test_tuple_roundtrip(self):
        """Test that to_tuple and from_tuple are inverse operations."""
        original = EllipsePoint(10.5, 20.3)
        tuple_form = original.to_tuple()
        reconstructed = EllipsePoint.from_tuple(tuple_form)
        assert original == reconstructed


class TestEllipsePointMagnitude:
    """Test magnitude calculations."""

    def test_magnitude_zero(self):
        """Test magnitude of zero point."""
        point = EllipsePoint(0.0, 0.0)
        assert point.magnitude() == 0.0

    def test_magnitude_simple(self):
        """Test magnitude of simple point."""
        point = EllipsePoint(3.0, 4.0)
        assert point.magnitude() == 5.0

    def test_magnitude_negative_coordinates(self):
        """Test magnitude with negative coordinates."""
        point = EllipsePoint(-3.0, -4.0)
        assert point.magnitude() == 5.0


class TestPointCollectionCreation:
    """Test PointCollection creation and initialization."""

    def test_empty_collection(self):
        """Test creating empty collection."""
        collection = PointCollection()
        assert len(collection) == 0
        assert isinstance(collection, list)

    def test_collection_with_initial_points(self):
        """Test creating collection with initial points."""
        points = [EllipsePoint(1.0, 2.0), EllipsePoint(3.0, 4.0)]
        collection = PointCollection(points)
        assert len(collection) == 2
        assert collection[0] == points[0]
        assert collection[1] == points[1]

    def test_collection_append(self):
        """Test appending points to collection."""
        collection = PointCollection()
        collection.append(EllipsePoint(1.0, 2.0))
        collection.append(EllipsePoint(3.0, 4.0))
        assert len(collection) == 2

    def test_collection_extend(self):
        """Test extending collection with multiple points."""
        collection = PointCollection()
        points = [EllipsePoint(1.0, 2.0), EllipsePoint(3.0, 4.0)]
        collection.extend(points)
        assert len(collection) == 2


class TestPointCollectionCentroid:
    """Test centroid calculation for PointCollection."""

    def test_centroid_single_point(self):
        """Test centroid of single point."""
        collection = PointCollection([EllipsePoint(5.0, 7.0)])
        centroid = collection.centroid()
        assert centroid == EllipsePoint(5.0, 7.0)

    def test_centroid_two_points(self):
        """Test centroid of two points."""
        collection = PointCollection([
            EllipsePoint(0.0, 0.0),
            EllipsePoint(4.0, 6.0)
        ])
        centroid = collection.centroid()
        assert centroid == EllipsePoint(2.0, 3.0)

    def test_centroid_square(self):
        """Test centroid of square corners."""
        collection = PointCollection([
            EllipsePoint(0.0, 0.0),
            EllipsePoint(4.0, 0.0),
            EllipsePoint(4.0, 4.0),
            EllipsePoint(0.0, 4.0)
        ])
        centroid = collection.centroid()
        assert centroid == EllipsePoint(2.0, 2.0)

    def test_centroid_empty_raises_error(self):
        """Test that centroid of empty collection raises ValueError."""
        collection = PointCollection()
        with pytest.raises(ValueError, match="Cannot calculate centroid of empty collection"):
            collection.centroid()


class TestPointCollectionBounds:
    """Test bounding box calculation for PointCollection."""

    def test_bounds_single_point(self):
        """Test bounds of single point."""
        collection = PointCollection([EllipsePoint(5.0, 7.0)])
        bounds = collection.bounds()
        assert bounds == (5.0, 7.0, 5.0, 7.0)

    def test_bounds_two_points(self):
        """Test bounds of two points."""
        collection = PointCollection([
            EllipsePoint(1.0, 2.0),
            EllipsePoint(5.0, 8.0)
        ])
        bounds = collection.bounds()
        assert bounds == (1.0, 2.0, 5.0, 8.0)

    def test_bounds_multiple_points(self):
        """Test bounds of multiple points."""
        collection = PointCollection([
            EllipsePoint(1.0, 2.0),
            EllipsePoint(5.0, 8.0),
            EllipsePoint(3.0, 4.0),
            EllipsePoint(-1.0, 10.0)
        ])
        bounds = collection.bounds()
        assert bounds == (-1.0, 2.0, 5.0, 10.0)

    def test_bounds_empty_raises_error(self):
        """Test that bounds of empty collection raises ValueError."""
        collection = PointCollection()
        with pytest.raises(ValueError, match="Cannot calculate bounds of empty collection"):
            collection.bounds()


class TestPointCollectionArrayConversion:
    """Test array conversion methods for PointCollection."""

    def test_to_arrays_empty(self):
        """Test converting empty collection to arrays."""
        collection = PointCollection()
        x_coords, y_coords = collection.to_arrays()
        assert x_coords == []
        assert y_coords == []

    def test_to_arrays_single_point(self):
        """Test converting single point to arrays."""
        collection = PointCollection([EllipsePoint(1.0, 2.0)])
        x_coords, y_coords = collection.to_arrays()
        assert x_coords == [1.0]
        assert y_coords == [2.0]

    def test_to_arrays_multiple_points(self):
        """Test converting multiple points to arrays."""
        collection = PointCollection([
            EllipsePoint(1.0, 2.0),
            EllipsePoint(3.0, 4.0),
            EllipsePoint(5.0, 6.0)
        ])
        x_coords, y_coords = collection.to_arrays()
        assert x_coords == [1.0, 3.0, 5.0]
        assert y_coords == [2.0, 4.0, 6.0]

    def test_from_arrays_empty(self):
        """Test creating collection from empty arrays."""
        collection = PointCollection.from_arrays([], [])
        assert len(collection) == 0

    def test_from_arrays_single_point(self):
        """Test creating collection from single point arrays."""
        collection = PointCollection.from_arrays([1.0], [2.0])
        assert len(collection) == 1
        assert collection[0] == EllipsePoint(1.0, 2.0)

    def test_from_arrays_multiple_points(self):
        """Test creating collection from multiple point arrays."""
        x = [1.0, 3.0, 5.0]
        y = [2.0, 4.0, 6.0]
        collection = PointCollection.from_arrays(x, y)
        assert len(collection) == 3
        assert collection[0] == EllipsePoint(1.0, 2.0)
        assert collection[1] == EllipsePoint(3.0, 4.0)
        assert collection[2] == EllipsePoint(5.0, 6.0)

    def test_from_arrays_mismatched_length_raises_error(self):
        """Test that mismatched array lengths raise ValueError."""
        x = [1.0, 2.0, 3.0]
        y = [4.0, 5.0]
        with pytest.raises(ValueError, match="X and Y coordinate arrays must have same length"):
            PointCollection.from_arrays(x, y)

    def test_array_roundtrip(self):
        """Test that to_arrays and from_arrays are inverse operations."""
        original = PointCollection([
            EllipsePoint(1.5, 2.5),
            EllipsePoint(3.7, 4.9),
            EllipsePoint(5.1, 6.3)
        ])
        x_coords, y_coords = original.to_arrays()
        reconstructed = PointCollection.from_arrays(x_coords, y_coords)
        assert len(original) == len(reconstructed)
        for orig, recon in zip(original, reconstructed):
            assert orig == recon


class TestPointCollectionEdgeCases:
    """Test edge cases and special scenarios for PointCollection."""

    def test_collection_is_iterable(self):
        """Test that collection can be iterated."""
        points = [EllipsePoint(i, i*2) for i in range(5)]
        collection = PointCollection(points)
        count = 0
        for point in collection:
            assert isinstance(point, EllipsePoint)
            count += 1
        assert count == 5

    def test_collection_indexing(self):
        """Test that collection supports indexing."""
        collection = PointCollection([
            EllipsePoint(1.0, 2.0),
            EllipsePoint(3.0, 4.0)
        ])
        assert collection[0] == EllipsePoint(1.0, 2.0)
        assert collection[1] == EllipsePoint(3.0, 4.0)
        assert collection[-1] == EllipsePoint(3.0, 4.0)

    def test_collection_slicing(self):
        """Test that collection supports slicing."""
        collection = PointCollection([
            EllipsePoint(i, i*2) for i in range(10)
        ])
        sliced = collection[2:5]
        assert len(sliced) == 3
        assert sliced[0] == EllipsePoint(2, 4)

    def test_collection_remove(self):
        """Test removing points from collection."""
        point = EllipsePoint(3.0, 4.0)
        collection = PointCollection([
            EllipsePoint(1.0, 2.0),
            point,
            EllipsePoint(5.0, 6.0)
        ])
        collection.remove(point)
        assert len(collection) == 2
        assert point not in collection

    def test_collection_clear(self):
        """Test clearing collection."""
        collection = PointCollection([
            EllipsePoint(1.0, 2.0),
            EllipsePoint(3.0, 4.0)
        ])
        collection.clear()
        assert len(collection) == 0
