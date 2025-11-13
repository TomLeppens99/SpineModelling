"""
Ellipse Point module for 2D point representation in ellipse fitting.

This module provides the EllipsePoint class for representing 2D points used
in ellipse fitting algorithms. These points are typically extracted from image
annotations and used to fit ellipses to anatomical features.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple
import math


@dataclass
class EllipsePoint:
    """
    Represents a 2D point used in ellipse fitting algorithms.

    This class is used for storing points that will be fit to an ellipse,
    typically from user annotations on medical images marking anatomical
    features like vertebral bodies or endplates.

    Attributes:
        x (float): X-coordinate in image pixel space
        y (float): Y-coordinate in image pixel space

    Examples:
        >>> point = EllipsePoint(10.5, 20.3)
        >>> point.x
        10.5
        >>> point.distance_to(EllipsePoint(0.0, 0.0))
        22.846584517431523
    """

    x: float
    y: float

    def distance_to(self, other: EllipsePoint) -> float:
        """
        Calculate Euclidean distance to another point.

        Args:
            other (EllipsePoint): The target point

        Returns:
            float: The Euclidean distance between this point and the other

        Examples:
            >>> p1 = EllipsePoint(0.0, 0.0)
            >>> p2 = EllipsePoint(3.0, 4.0)
            >>> p1.distance_to(p2)
            5.0
        """
        dx = self.x - other.x
        dy = self.y - other.y
        return math.sqrt(dx * dx + dy * dy)

    def __add__(self, other: EllipsePoint) -> EllipsePoint:
        """
        Add two points component-wise.

        Args:
            other (EllipsePoint): The point to add

        Returns:
            EllipsePoint: A new point with summed coordinates

        Examples:
            >>> EllipsePoint(1.0, 2.0) + EllipsePoint(3.0, 4.0)
            EllipsePoint(x=4.0, y=6.0)
        """
        return EllipsePoint(self.x + other.x, self.y + other.y)

    def __sub__(self, other: EllipsePoint) -> EllipsePoint:
        """
        Subtract two points component-wise.

        Args:
            other (EllipsePoint): The point to subtract

        Returns:
            EllipsePoint: A new point with subtracted coordinates

        Examples:
            >>> EllipsePoint(5.0, 7.0) - EllipsePoint(1.0, 2.0)
            EllipsePoint(x=4.0, y=5.0)
        """
        return EllipsePoint(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> EllipsePoint:
        """
        Multiply point by a scalar.

        Args:
            scalar (float): The scalar multiplier

        Returns:
            EllipsePoint: A new point with scaled coordinates

        Examples:
            >>> EllipsePoint(2.0, 3.0) * 2.0
            EllipsePoint(x=4.0, y=6.0)
        """
        return EllipsePoint(self.x * scalar, self.y * scalar)

    def __truediv__(self, scalar: float) -> EllipsePoint:
        """
        Divide point by a scalar.

        Args:
            scalar (float): The scalar divisor

        Returns:
            EllipsePoint: A new point with divided coordinates

        Raises:
            ZeroDivisionError: If scalar is zero

        Examples:
            >>> EllipsePoint(4.0, 6.0) / 2.0
            EllipsePoint(x=2.0, y=3.0)
        """
        if scalar == 0:
            raise ZeroDivisionError("Cannot divide point by zero")
        return EllipsePoint(self.x / scalar, self.y / scalar)

    def to_tuple(self) -> Tuple[float, float]:
        """
        Convert point to a tuple.

        Returns:
            Tuple[float, float]: (x, y) coordinates

        Examples:
            >>> EllipsePoint(1.5, 2.5).to_tuple()
            (1.5, 2.5)
        """
        return (self.x, self.y)

    @classmethod
    def from_tuple(cls, coords: Tuple[float, float]) -> EllipsePoint:
        """
        Create an EllipsePoint from a tuple of coordinates.

        Args:
            coords (Tuple[float, float]): (x, y) coordinates

        Returns:
            EllipsePoint: New point instance

        Examples:
            >>> EllipsePoint.from_tuple((1.5, 2.5))
            EllipsePoint(x=1.5, y=2.5)
        """
        return cls(coords[0], coords[1])

    def magnitude(self) -> float:
        """
        Calculate the magnitude (length) of the point vector from origin.

        Returns:
            float: The magnitude of the vector

        Examples:
            >>> EllipsePoint(3.0, 4.0).magnitude()
            5.0
        """
        return math.sqrt(self.x * self.x + self.y * self.y)


class PointCollection(list):
    """
    A collection of EllipsePoint objects with additional utility methods.

    This class extends Python's built-in list to provide specialized
    functionality for managing collections of points used in ellipse fitting.
    It maintains type safety and provides convenience methods for common
    operations.

    Examples:
        >>> collection = PointCollection()
        >>> collection.append(EllipsePoint(1.0, 2.0))
        >>> collection.append(EllipsePoint(3.0, 4.0))
        >>> len(collection)
        2
        >>> centroid = collection.centroid()
        >>> centroid.x
        2.0
    """

    def __init__(self, points: List[EllipsePoint] = None):
        """
        Initialize a PointCollection.

        Args:
            points (List[EllipsePoint], optional): Initial points to add
        """
        super().__init__()
        if points:
            self.extend(points)

    def centroid(self) -> EllipsePoint:
        """
        Calculate the centroid (center of mass) of all points.

        Returns:
            EllipsePoint: The centroid of all points in the collection

        Raises:
            ValueError: If the collection is empty

        Examples:
            >>> collection = PointCollection([
            ...     EllipsePoint(0.0, 0.0),
            ...     EllipsePoint(4.0, 0.0),
            ...     EllipsePoint(4.0, 4.0),
            ...     EllipsePoint(0.0, 4.0)
            ... ])
            >>> centroid = collection.centroid()
            >>> centroid.x, centroid.y
            (2.0, 2.0)
        """
        if not self:
            raise ValueError("Cannot calculate centroid of empty collection")

        sum_x = sum(point.x for point in self)
        sum_y = sum(point.y for point in self)
        count = len(self)

        return EllipsePoint(sum_x / count, sum_y / count)

    def bounds(self) -> Tuple[float, float, float, float]:
        """
        Calculate the bounding box of all points.

        Returns:
            Tuple[float, float, float, float]: (min_x, min_y, max_x, max_y)

        Raises:
            ValueError: If the collection is empty

        Examples:
            >>> collection = PointCollection([
            ...     EllipsePoint(1.0, 2.0),
            ...     EllipsePoint(5.0, 8.0),
            ...     EllipsePoint(3.0, 4.0)
            ... ])
            >>> collection.bounds()
            (1.0, 2.0, 5.0, 8.0)
        """
        if not self:
            raise ValueError("Cannot calculate bounds of empty collection")

        min_x = min(point.x for point in self)
        max_x = max(point.x for point in self)
        min_y = min(point.y for point in self)
        max_y = max(point.y for point in self)

        return (min_x, min_y, max_x, max_y)

    def to_arrays(self) -> Tuple[List[float], List[float]]:
        """
        Convert collection to separate X and Y coordinate arrays.

        Useful for interfacing with numerical libraries that expect
        separate arrays for x and y coordinates.

        Returns:
            Tuple[List[float], List[float]]: (x_coords, y_coords)

        Examples:
            >>> collection = PointCollection([
            ...     EllipsePoint(1.0, 2.0),
            ...     EllipsePoint(3.0, 4.0)
            ... ])
            >>> x_coords, y_coords = collection.to_arrays()
            >>> x_coords
            [1.0, 3.0]
            >>> y_coords
            [2.0, 4.0]
        """
        x_coords = [point.x for point in self]
        y_coords = [point.y for point in self]
        return (x_coords, y_coords)

    @classmethod
    def from_arrays(cls, x_coords: List[float], y_coords: List[float]) -> PointCollection:
        """
        Create a PointCollection from separate X and Y coordinate arrays.

        Args:
            x_coords (List[float]): X coordinates
            y_coords (List[float]): Y coordinates

        Returns:
            PointCollection: New collection with points from arrays

        Raises:
            ValueError: If arrays have different lengths

        Examples:
            >>> x = [1.0, 2.0, 3.0]
            >>> y = [4.0, 5.0, 6.0]
            >>> collection = PointCollection.from_arrays(x, y)
            >>> len(collection)
            3
        """
        if len(x_coords) != len(y_coords):
            raise ValueError("X and Y coordinate arrays must have same length")

        points = [EllipsePoint(x, y) for x, y in zip(x_coords, y_coords)]
        return cls(points)
