"""
Position module for 3D coordinate representation.

This module provides the Position class for representing 3D spatial coordinates
in the SpineModeling application. Used throughout the application for representing
points in 3D space, including anatomical landmarks, image coordinates, and
biomechanical model positions.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple
import math


@dataclass
class Position:
    """
    Represents a 3D position in space with X, Y, and Z coordinates.

    This class is used throughout the SpineModeling application to represent
    spatial coordinates for:
    - EOS X-ray source positions
    - Patient positioning in 3D space
    - Image plane origins
    - Anatomical landmark positions
    - Biomechanical model coordinates

    Attributes:
        x (float): X-coordinate in meters
        y (float): Y-coordinate in meters
        z (float): Z-coordinate in meters

    Examples:
        >>> pos = Position(1.0, 2.0, 3.0)
        >>> pos.x
        1.0
        >>> pos.distance_to(Position(0.0, 0.0, 0.0))
        3.7416573867739413
        >>> pos + Position(1.0, 1.0, 1.0)
        Position(x=2.0, y=3.0, z=4.0)
    """

    x: float
    y: float
    z: float

    def distance_to(self, other: Position) -> float:
        """
        Calculate Euclidean distance to another position.

        Args:
            other (Position): The target position

        Returns:
            float: The Euclidean distance between this position and the other

        Examples:
            >>> p1 = Position(0.0, 0.0, 0.0)
            >>> p2 = Position(3.0, 4.0, 0.0)
            >>> p1.distance_to(p2)
            5.0
        """
        dx = self.x - other.x
        dy = self.y - other.y
        dz = self.z - other.z
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    def __add__(self, other: Position) -> Position:
        """
        Add two positions component-wise.

        Args:
            other (Position): The position to add

        Returns:
            Position: A new position with summed coordinates

        Examples:
            >>> Position(1.0, 2.0, 3.0) + Position(4.0, 5.0, 6.0)
            Position(x=5.0, y=7.0, z=9.0)
        """
        return Position(self.x + other.x, self.y + other.y, self.z + other.z)

    def __sub__(self, other: Position) -> Position:
        """
        Subtract two positions component-wise.

        Args:
            other (Position): The position to subtract

        Returns:
            Position: A new position with subtracted coordinates

        Examples:
            >>> Position(5.0, 7.0, 9.0) - Position(1.0, 2.0, 3.0)
            Position(x=4.0, y=5.0, z=6.0)
        """
        return Position(self.x - other.x, self.y - other.y, self.z - other.z)

    def __mul__(self, scalar: float) -> Position:
        """
        Multiply position by a scalar.

        Args:
            scalar (float): The scalar multiplier

        Returns:
            Position: A new position with scaled coordinates

        Examples:
            >>> Position(1.0, 2.0, 3.0) * 2.0
            Position(x=2.0, y=4.0, z=6.0)
        """
        return Position(self.x * scalar, self.y * scalar, self.z * scalar)

    def __truediv__(self, scalar: float) -> Position:
        """
        Divide position by a scalar.

        Args:
            scalar (float): The scalar divisor

        Returns:
            Position: A new position with divided coordinates

        Raises:
            ZeroDivisionError: If scalar is zero

        Examples:
            >>> Position(2.0, 4.0, 6.0) / 2.0
            Position(x=1.0, y=2.0, z=3.0)
        """
        if scalar == 0:
            raise ZeroDivisionError("Cannot divide position by zero")
        return Position(self.x / scalar, self.y / scalar, self.z / scalar)

    def to_tuple(self) -> Tuple[float, float, float]:
        """
        Convert position to a tuple.

        Returns:
            Tuple[float, float, float]: (x, y, z) coordinates

        Examples:
            >>> Position(1.0, 2.0, 3.0).to_tuple()
            (1.0, 2.0, 3.0)
        """
        return (self.x, self.y, self.z)

    @classmethod
    def from_tuple(cls, coords: Tuple[float, float, float]) -> Position:
        """
        Create a Position from a tuple of coordinates.

        Args:
            coords (Tuple[float, float, float]): (x, y, z) coordinates

        Returns:
            Position: New position instance

        Examples:
            >>> Position.from_tuple((1.0, 2.0, 3.0))
            Position(x=1.0, y=2.0, z=3.0)
        """
        return cls(coords[0], coords[1], coords[2])

    def magnitude(self) -> float:
        """
        Calculate the magnitude (length) of the position vector from origin.

        Returns:
            float: The magnitude of the vector

        Examples:
            >>> Position(3.0, 4.0, 0.0).magnitude()
            5.0
        """
        return math.sqrt(self.x * self.x + self.y * self.y + self.z * self.z)

    def normalize(self) -> Position:
        """
        Return a normalized (unit length) version of this position vector.

        Returns:
            Position: A new position with magnitude 1.0

        Raises:
            ValueError: If the position is at the origin (zero magnitude)

        Examples:
            >>> pos = Position(3.0, 4.0, 0.0)
            >>> normalized = pos.normalize()
            >>> normalized.magnitude()
            1.0
        """
        mag = self.magnitude()
        if mag == 0:
            raise ValueError("Cannot normalize a zero-magnitude position")
        return self / mag
