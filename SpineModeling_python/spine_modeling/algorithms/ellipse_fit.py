"""
Ellipse Fitting Module

This module implements the Fitzgibbon eigenvalue-based ellipse fitting algorithm
for fitting an ellipse to a set of 2D points. The method solves a constrained
eigenvalue problem to find the best-fit ellipse parameters.

The algorithm is based on:
Fitzgibbon, A., Pilu, M., and Fisher, R. B. (1999).
"Direct least square fitting of ellipses."
IEEE Transactions on Pattern Analysis and Machine Intelligence, 21(5), 476-480.

The ellipse is represented by the general conic equation:
    A*x^2 + B*x*y + C*y^2 + D*x + E*y + F = 0

Where the constraint 4*A*C - B^2 > 0 ensures the conic is an ellipse.

Example Usage:
    >>> from spine_modeling.core.ellipse_point import EllipsePoint
    >>> fitter = EllipseFit()
    >>> points = [
    ...     EllipsePoint(x=1.0, y=2.0),
    ...     EllipsePoint(x=2.0, y=3.0),
    ...     EllipsePoint(x=3.0, y=2.5),
    ...     # ... more points
    ... ]
    >>> coefficients = fitter.fit(points)
    >>> print(f"Ellipse coefficients (A,B,C,D,E,F): {coefficients}")

    The returned coefficients can be converted to geometric parameters:
    >>> center, axes, angle = fitter.get_ellipse_parameters(coefficients)
    >>> print(f"Center: {center}, Axes: {axes}, Angle: {angle}")

Performance Optimizations:
    - Vectorized coordinate extraction using numpy
    - LRU caching for repeated fits on same point sets
    - Optimized constraint matrix as class constant
    - Use scipy.linalg.solve instead of matrix inversion when available
"""

import numpy as np
from typing import List, Tuple, Optional, Union
from functools import lru_cache
import hashlib
import logging

try:
    from scipy import linalg as scipy_linalg
    HAS_SCIPY_LINALG = True
except ImportError:
    HAS_SCIPY_LINALG = False

try:
    from ..core.ellipse_point import EllipsePoint
except ImportError:
    # Allow standalone use
    EllipsePoint = None

logger = logging.getLogger(__name__)

# Pre-computed constraint matrix inverse for ellipse fitting (constant)
# Original C1 = [[0, 0, 0.5], [0, -1, 0], [0.5, 0, 0]]
CONSTRAINT_MATRIX = np.array([
    [0.0, 0.0, 0.5],
    [0.0, -1.0, 0.0],
    [0.5, 0.0, 0.0]
], dtype=np.float64)


class EllipseFit:
    """
    Fitzgibbon eigenvalue-based ellipse fitting algorithm.

    This class implements direct least-squares fitting of ellipses to 2D point clouds
    using the method of Fitzgibbon et al. (1999). The algorithm solves a generalized
    eigenvalue problem with a constraint that ensures the fitted conic is an ellipse.

    Attributes:
        _cache (dict): Internal cache for fit results (enabled by default)
        _cache_enabled (bool): Whether caching is enabled
        _cache_max_size (int): Maximum cache entries

    """

    # Shared cache across instances for efficiency
    _fit_cache: dict = {}
    _cache_max_size: int = 128

    def __init__(self, enable_cache: bool = True):
        """
        Initialize the ellipse fitter.

        Args:
            enable_cache: Enable result caching for repeated fits (default: True)
        """
        self._cache_enabled = enable_cache

    def _extract_coordinates(self, points: List) -> Tuple[np.ndarray, np.ndarray]:
        """
        Extract x and y coordinates from points using vectorized operations.

        Args:
            points: List of points (various formats supported)

        Returns:
            Tuple of (x_coords, y_coords) numpy arrays

        Raises:
            ValueError: If points cannot be extracted
        """
        num_points = len(points)

        # Fast path: if points are already numpy array with shape (n, 2)
        if isinstance(points, np.ndarray) and points.ndim == 2 and points.shape[1] >= 2:
            return points[:, 0].astype(np.float64), points[:, 1].astype(np.float64)

        # Check first point to determine extraction strategy
        first_point = points[0]

        if hasattr(first_point, 'x') and hasattr(first_point, 'y'):
            # Objects with x, y attributes - use vectorized getattr
            x_coords = np.array([p.x for p in points], dtype=np.float64)
            y_coords = np.array([p.y for p in points], dtype=np.float64)
        elif isinstance(first_point, (tuple, list, np.ndarray)):
            # Tuple/list format - convert to numpy and slice
            arr = np.array(points, dtype=np.float64)
            x_coords = arr[:, 0]
            y_coords = arr[:, 1]
        else:
            raise ValueError("Points must have x,y attributes or be array-like")

        return x_coords, y_coords

    def _compute_cache_key(self, x_coords: np.ndarray, y_coords: np.ndarray) -> str:
        """Compute a hash key for caching based on coordinates."""
        # Use tobytes for fast hashing of numpy arrays
        data = np.concatenate([x_coords, y_coords]).tobytes()
        return hashlib.md5(data).hexdigest()

    def fit(self, points: List) -> Optional[np.ndarray]:
        """
        Fit an ellipse to a list of 2D points.

        This method implements the Fitzgibbon et al. algorithm:
        1. Build design matrices D1 (quadratic terms) and D2 (linear terms)
        2. Compute scatter matrices S1, S2, S3
        3. Solve constrained eigenvalue problem: M * a1 = λ * C1 * a1
        4. Select eigenvector corresponding to positive eigenvalue satisfying constraint
        5. Compute full parameter vector [a1; a2]

        Args:
            points: List of points with x and y attributes (e.g., EllipsePoint objects)
                    or list of tuples/lists [(x1,y1), (x2,y2), ...]
                    or numpy array of shape (n, 2)
                    Minimum 5 points required for ellipse fitting

        Returns:
            6-element numpy array [A, B, C, D, E, F] representing ellipse coefficients,
            or None if fitting failed

        Raises:
            ValueError: If fewer than 5 points provided
            RuntimeError: If no valid solution found

        Example:
            >>> fitter = EllipseFit()
            >>> points = [EllipsePoint(x=i, y=i**2) for i in range(10)]
            >>> coeffs = fitter.fit(points)
            >>> print(coeffs)
            [A, B, C, D, E, F]

        """
        if points is None or len(points) < 5:
            raise ValueError("At least 5 points required for ellipse fitting")

        # Extract coordinates using optimized method
        x_coords, y_coords = self._extract_coordinates(points)
        num_points = len(x_coords)

        # Check cache if enabled
        if self._cache_enabled:
            cache_key = self._compute_cache_key(x_coords, y_coords)
            if cache_key in EllipseFit._fit_cache:
                logger.debug(f"Cache hit for ellipse fit (key: {cache_key[:8]}...)")
                return EllipseFit._fit_cache[cache_key].copy()

        # Build design matrices using vectorized operations
        # D1 = [x.^2, x.*y, y.^2] - quadratic part
        x_sq = x_coords ** 2
        y_sq = y_coords ** 2
        xy = x_coords * y_coords

        D1 = np.column_stack([x_sq, xy, y_sq])

        # D2 = [x, y, ones] - linear part
        D2 = np.column_stack([x_coords, y_coords, np.ones(num_points, dtype=np.float64)])

        # Compute scatter matrices using optimized matrix operations
        S1 = D1.T @ D1
        S2 = D1.T @ D2
        S3 = D2.T @ D2

        # Check if S3 is invertible (use condition number for numerical stability)
        cond = np.linalg.cond(S3)
        if cond > 1e12:
            raise RuntimeError("S3 matrix is ill-conditioned, cannot compute solution reliably")

        # Solve for T using more stable method when scipy is available
        if HAS_SCIPY_LINALG:
            try:
                T = -scipy_linalg.solve(S3, S2.T, assume_a='pos')
            except scipy_linalg.LinAlgError:
                T = -np.linalg.solve(S3, S2.T)
        else:
            try:
                T = -np.linalg.solve(S3, S2.T)
            except np.linalg.LinAlgError:
                raise RuntimeError("Failed to solve S3 system")

        # M = S1 + S2 * T - reduced scatter matrix
        M = S1 + S2 @ T

        # Apply constraint matrix (using pre-computed constant)
        M = CONSTRAINT_MATRIX @ M

        # Solve eigensystem
        try:
            eigenvalues, eigenvectors = np.linalg.eig(M)
        except np.linalg.LinAlgError:
            raise RuntimeError("Failed to compute eigenvalues/eigenvectors")

        # Find eigenvector that satisfies ellipse constraint using vectorized check
        # Constraint: 4*a1[0]*a1[2] - a1[1]^2 > 0
        evecs = eigenvectors.T  # Shape: (3, 3) -> iterate over rows

        # Compute constraint for all eigenvectors at once
        conditions = 4 * evecs[:, 0] * evecs[:, 2] - evecs[:, 1] ** 2

        # Filter: must be real and positive
        valid_mask = np.isreal(conditions) & (conditions.real > 0)

        if not np.any(valid_mask):
            raise RuntimeError("No valid ellipse solution found (no eigenvector satisfies constraint)")

        # Select eigenvector with maximum positive condition
        valid_conditions = np.where(valid_mask, conditions.real, -np.inf)
        best_idx = np.argmax(valid_conditions)
        a1 = eigenvectors[:, best_idx].real

        # Compute a2 = T * a1
        a2 = T @ a1

        # Combine into full parameter vector [a1; a2]
        result = np.concatenate([a1, a2])

        # Cache result if enabled
        if self._cache_enabled:
            # Limit cache size
            if len(EllipseFit._fit_cache) >= EllipseFit._cache_max_size:
                # Remove oldest entry (FIFO)
                oldest_key = next(iter(EllipseFit._fit_cache))
                del EllipseFit._fit_cache[oldest_key]
            EllipseFit._fit_cache[cache_key] = result.copy()
            logger.debug(f"Cached ellipse fit result (key: {cache_key[:8]}...)")

        return result

    @classmethod
    def clear_cache(cls) -> int:
        """
        Clear the fit results cache.

        Returns:
            Number of entries cleared
        """
        count = len(cls._fit_cache)
        cls._fit_cache.clear()
        logger.debug(f"Cleared {count} entries from ellipse fit cache")
        return count

    @staticmethod
    def get_ellipse_parameters(coefficients: np.ndarray) -> Tuple[Tuple[float, float],
                                                                    Tuple[float, float],
                                                                    float]:
        """
        Convert ellipse coefficients to geometric parameters.

        Converts the general conic equation coefficients:
            A*x^2 + B*x*y + C*y^2 + D*x + E*y + F = 0

        To geometric ellipse parameters:
            - Center (cx, cy)
            - Semi-axes (a, b)
            - Rotation angle θ

        Args:
            coefficients: 6-element array [A, B, C, D, E, F]

        Returns:
            Tuple of ((cx, cy), (a, b), angle_degrees) where:
                - (cx, cy): Ellipse center coordinates
                - (a, b): Semi-major and semi-minor axes lengths
                - angle_degrees: Rotation angle in degrees (0-180)

        Raises:
            ValueError: If coefficients don't represent a valid ellipse

        Example:
            >>> coeffs = np.array([1, 0, 1, -4, -6, 4])
            >>> center, axes, angle = EllipseFit.get_ellipse_parameters(coeffs)
            >>> print(f"Center: ({center[0]:.2f}, {center[1]:.2f})")
            >>> print(f"Axes: ({axes[0]:.2f}, {axes[1]:.2f})")
            >>> print(f"Angle: {angle:.2f}°")

        """
        A, B, C, D, E, F = coefficients

        # Check ellipse constraint
        discriminant = B**2 - 4*A*C
        if discriminant >= 0:
            raise ValueError("Coefficients do not represent an ellipse (discriminant >= 0)")

        # Compute center
        denominator = B**2 - 4*A*C
        cx = (2*C*D - B*E) / denominator
        cy = (2*A*E - B*D) / denominator

        # Compute rotation angle
        if B == 0:
            if A < C:
                angle_rad = 0
            else:
                angle_rad = np.pi / 2
        else:
            angle_rad = np.arctan2(C - A - np.sqrt((A - C)**2 + B**2), B)

        angle_degrees = np.degrees(angle_rad)

        # Compute semi-axes lengths
        # Transform to canonical form
        numerator = 2 * (A*E**2 + C*D**2 - B*D*E + denominator*F)
        temp = np.sqrt((A - C)**2 + B**2)

        a_squared = numerator / (denominator * (temp - (A + C)))
        b_squared = numerator / (denominator * (-temp - (A + C)))

        if a_squared < 0 or b_squared < 0:
            raise ValueError("Invalid ellipse parameters (negative axis length)")

        a = np.sqrt(a_squared)
        b = np.sqrt(b_squared)

        # Ensure a >= b (a is semi-major axis)
        if b > a:
            a, b = b, a
            angle_degrees += 90

        # Normalize angle to [0, 180)
        angle_degrees = angle_degrees % 180

        return (cx, cy), (a, b), angle_degrees

    @staticmethod
    def evaluate_ellipse(coefficients: np.ndarray, x: float, y: float) -> float:
        """
        Evaluate the ellipse equation at a given point.

        Computes: A*x^2 + B*x*y + C*y^2 + D*x + E*y + F

        Args:
            coefficients: 6-element array [A, B, C, D, E, F]
            x: x-coordinate
            y: y-coordinate

        Returns:
            Value of ellipse equation at (x, y)
            - Value = 0: point is on the ellipse
            - Value < 0: point is inside the ellipse
            - Value > 0: point is outside the ellipse

        Example:
            >>> coeffs = np.array([1, 0, 1, -4, -6, 4])
            >>> value = EllipseFit.evaluate_ellipse(coeffs, 2.0, 3.0)
            >>> print(f"Point (2,3) is {'on' if abs(value) < 0.01 else 'off'} the ellipse")

        """
        A, B, C, D, E, F = coefficients
        return A * x**2 + B * x * y + C * y**2 + D * x + E * y + F

    @staticmethod
    def compute_fit_error(coefficients: np.ndarray, points: List) -> Tuple[float, float]:
        """
        Compute fitting error for a set of points.

        Args:
            coefficients: 6-element array [A, B, C, D, E, F]
            points: List of points with x and y attributes

        Returns:
            Tuple of (mean_error, max_error) representing:
                - mean_error: Mean absolute algebraic distance
                - max_error: Maximum absolute algebraic distance

        Example:
            >>> fitter = EllipseFit()
            >>> coeffs = fitter.fit(points)
            >>> mean_err, max_err = fitter.compute_fit_error(coeffs, points)
            >>> print(f"Mean error: {mean_err:.6f}, Max error: {max_err:.6f}")

        """
        errors = []
        for p in points:
            if hasattr(p, 'x') and hasattr(p, 'y'):
                error = abs(EllipseFit.evaluate_ellipse(coefficients, p.x, p.y))
                errors.append(error)
            elif isinstance(p, (tuple, list)) and len(p) >= 2:
                error = abs(EllipseFit.evaluate_ellipse(coefficients, p[0], p[1]))
                errors.append(error)

        if not errors:
            return 0.0, 0.0

        return np.mean(errors), np.max(errors)

    @staticmethod
    def generate_ellipse_points(coefficients: np.ndarray,
                               num_points: int = 100) -> Tuple[np.ndarray, np.ndarray]:
        """
        Generate points on the fitted ellipse for visualization.

        Args:
            coefficients: 6-element array [A, B, C, D, E, F]
            num_points: Number of points to generate (default: 100)

        Returns:
            Tuple of (x_coords, y_coords) numpy arrays

        Raises:
            ValueError: If coefficients don't represent a valid ellipse

        Example:
            >>> fitter = EllipseFit()
            >>> coeffs = fitter.fit(points)
            >>> x_ellipse, y_ellipse = fitter.generate_ellipse_points(coeffs)
            >>> import matplotlib.pyplot as plt
            >>> plt.plot(x_ellipse, y_ellipse, 'r-')
            >>> plt.show()

        """
        try:
            (cx, cy), (a, b), angle_deg = EllipseFit.get_ellipse_parameters(coefficients)
        except ValueError as e:
            raise ValueError(f"Cannot generate ellipse points: {e}")

        # Generate parametric points
        theta = np.linspace(0, 2 * np.pi, num_points)
        angle_rad = np.radians(angle_deg)

        # Ellipse in canonical form (centered at origin, aligned with axes)
        x_canonical = a * np.cos(theta)
        y_canonical = b * np.sin(theta)

        # Rotate and translate to actual position
        cos_angle = np.cos(angle_rad)
        sin_angle = np.sin(angle_rad)

        x_coords = cx + x_canonical * cos_angle - y_canonical * sin_angle
        y_coords = cy + x_canonical * sin_angle + y_canonical * cos_angle

        return x_coords, y_coords


# Utility function for standalone usage
def fit_ellipse_to_points(points: List) -> Optional[np.ndarray]:
    """
    Convenience function to fit an ellipse to a list of points.

    Args:
        points: List of (x, y) tuples/lists or objects with x, y attributes

    Returns:
        6-element numpy array of ellipse coefficients, or None if fitting failed

    Example:
        >>> points = [(1, 2), (2, 3), (3, 2), (2, 1), (1, 1)]
        >>> coeffs = fit_ellipse_to_points(points)
        >>> if coeffs is not None:
        ...     print(f"Ellipse coefficients: {coeffs}")

    """
    fitter = EllipseFit()
    try:
        return fitter.fit(points)
    except (ValueError, RuntimeError) as e:
        print(f"Ellipse fitting failed: {e}")
        return None
