"""Spinal realignment module for CT model alignment with EOS images.

This module provides functionality for computing optimal alignment transformations
to position CT-derived vertebral models within the EOS space coordinate system
and register them with 2D EOS radiograph projections.
"""

from typing import Tuple, List, Optional, Dict, TYPE_CHECKING
import numpy as np
from dataclasses import dataclass

if TYPE_CHECKING:
    import vtk
else:
    try:
        import vtk
    except ImportError:
        vtk = None

from spine_modeling.core.position import Position
from spine_modeling.imaging.eos_space import EosSpace


@dataclass
class Landmark3D:
    """Represents a 3D landmark point on a vertebral model.

    Attributes:
        name: Landmark identifier (e.g., "L3_superior_anterior")
        position: 3D coordinates in model space
        vertebra: Vertebra name (e.g., "L3")
    """
    name: str
    position: Position
    vertebra: str


@dataclass
class Landmark2D:
    """Represents a 2D landmark point on an EOS image.

    Attributes:
        name: Landmark identifier
        position: 2D coordinates in image space (pixels or meters)
        image_plane: Which image ("frontal" or "lateral")
    """
    name: str
    position: Tuple[float, float]
    image_plane: str


@dataclass
class TransformParameters:
    """Parameters for 3D transformation.

    Attributes:
        translation: XYZ translation in meters
        rotation: XYZ rotation in degrees (Euler angles)
        scale: Uniform scale factor
    """
    translation: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    rotation: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    scale: float = 1.0

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'translation': self.translation,
            'rotation': self.rotation,
            'scale': self.scale
        }


class RealignmentCalculator:
    """Calculates optimal transformation for vertebral model realignment.

    This class provides methods to compute the best fit transformation to align
    a 3D CT-derived vertebral model with the EOS imaging space using landmark-based
    registration or iterative projection matching.
    """

    def __init__(self, eos_space: EosSpace):
        """Initialize realignment calculator.

        Args:
            eos_space: EosSpace instance with calibration
        """
        self.eos_space = eos_space
        self.landmarks_3d: List[Landmark3D] = []
        self.landmarks_2d: List[Landmark2D] = []

    def add_3d_landmark(self, landmark: Landmark3D):
        """Add a 3D landmark from the vertebral model.

        Args:
            landmark: 3D landmark to add
        """
        self.landmarks_3d.append(landmark)

    def add_2d_landmark(self, landmark: Landmark2D):
        """Add a 2D landmark from EOS image.

        Args:
            landmark: 2D landmark to add
        """
        self.landmarks_2d.append(landmark)

    def clear_landmarks(self):
        """Clear all landmarks."""
        self.landmarks_3d.clear()
        self.landmarks_2d.clear()

    def estimate_initial_position(
        self,
        vertebra_level: str
    ) -> TransformParameters:
        """Estimate initial position for a vertebra based on typical anatomy.

        Args:
            vertebra_level: Vertebra name (e.g., "L3", "L4")

        Returns:
            Initial transform parameters
        """
        # Typical vertebral body heights (meters) from literature
        vertebra_heights = {
            'L1': 0.028,
            'L2': 0.029,
            'L3': 0.030,
            'L4': 0.031,
            'L5': 0.032,
            'T12': 0.025,
        }

        # Typical vertical positions relative to patient position
        # (approximate lumbar spine positioning)
        vertical_offsets = {
            'L1': 0.15,
            'L2': 0.12,
            'L3': 0.09,
            'L4': 0.06,
            'L5': 0.03,
            'T12': 0.18,
        }

        # Get patient position from EOS space
        patient_pos = self.eos_space.patient_position

        # Estimate initial position
        y_offset = vertical_offsets.get(vertebra_level, 0.1)

        # Place at patient position with appropriate vertical offset
        translation = (
            patient_pos.x,
            patient_pos.y + y_offset,
            patient_pos.z
        )

        # Default rotation (no rotation from EOS space alignment)
        rotation = (0.0, 0.0, 0.0)

        # Scale from mm (typical CT data) to meters (EOS space)
        scale = 0.001

        return TransformParameters(translation, rotation, scale)

    def compute_landmark_based_transform(
        self,
        use_least_squares: bool = True
    ) -> Optional[TransformParameters]:
        """Compute transformation using landmark correspondences.

        Uses paired 3D-2D landmarks to compute optimal transformation that
        minimizes reprojection error.

        Args:
            use_least_squares: If True, use least squares fitting

        Returns:
            Computed transform parameters or None if insufficient landmarks
        """
        if len(self.landmarks_3d) < 3 or len(self.landmarks_2d) < 4:
            print("Insufficient landmarks. Need at least 3 3D and 4 2D landmarks.")
            return None

        # Match landmarks by name
        matched_pairs = self._match_landmarks()

        if len(matched_pairs) < 3:
            print("Insufficient matched landmark pairs.")
            return None

        # Extract 3D and 2D points
        points_3d = np.array([pair[0] for pair in matched_pairs])
        points_2d_frontal = np.array([pair[1] for pair in matched_pairs if pair[2] == 'frontal'])
        points_2d_lateral = np.array([pair[1] for pair in matched_pairs if pair[2] == 'lateral'])

        # Compute transformation using iterative optimization
        # For now, return estimated position (simplified approach)
        # Full implementation would use scipy.optimize or similar

        # Compute centroid of 3D points
        centroid_3d = np.mean(points_3d, axis=0)

        # Estimate translation as difference from patient position
        translation = (
            centroid_3d[0],
            centroid_3d[1],
            centroid_3d[2]
        )

        return TransformParameters(translation=translation, scale=0.001)

    def _match_landmarks(self) -> List[Tuple[Tuple[float, float, float], Tuple[float, float], str]]:
        """Match 3D and 2D landmarks by name.

        Returns:
            List of (3d_point, 2d_point, image_plane) tuples
        """
        matched = []

        for lm_3d in self.landmarks_3d:
            for lm_2d in self.landmarks_2d:
                if lm_3d.name == lm_2d.name:
                    point_3d = (lm_3d.position.x, lm_3d.position.y, lm_3d.position.z)
                    matched.append((point_3d, lm_2d.position, lm_2d.image_plane))

        return matched

    def compute_projection_error(
        self,
        polydata: 'vtk.vtkPolyData',
        transform: TransformParameters,
        target_contours_frontal: Optional['vtk.vtkPolyData'] = None,
        target_contours_lateral: Optional['vtk.vtkPolyData'] = None
    ) -> float:
        """Compute projection error between transformed model and target contours.

        Args:
            polydata: 3D model to project
            transform: Current transformation
            target_contours_frontal: Target contours on frontal image
            target_contours_lateral: Target contours on lateral image

        Returns:
            Projection error (lower is better)
        """
        # This would compute the distance between projected model edges
        # and manually traced contours on the EOS images
        # For now, return placeholder
        return 0.0

    def optimize_transform(
        self,
        polydata: 'vtk.vtkPolyData',
        initial_transform: TransformParameters,
        target_contours_frontal: Optional['vtk.vtkPolyData'] = None,
        target_contours_lateral: Optional['vtk.vtkPolyData'] = None,
        max_iterations: int = 100,
        tolerance: float = 1e-4
    ) -> TransformParameters:
        """Optimize transformation to minimize projection error.

        Args:
            polydata: 3D vertebral model
            initial_transform: Starting transformation
            target_contours_frontal: Target contours on frontal view
            target_contours_lateral: Target contours on lateral view
            max_iterations: Maximum optimization iterations
            tolerance: Convergence tolerance

        Returns:
            Optimized transformation parameters
        """
        # This would use scipy.optimize.minimize or similar to find
        # the transformation that minimizes projection error
        # For now, return initial transform
        return initial_transform


class InteractiveAlignmentTool:
    """Interactive tool for manual adjustment of vertebral model alignment.

    Provides methods for incremental adjustment of position and rotation
    with real-time visualization updates.
    """

    def __init__(self, eos_space: EosSpace):
        """Initialize interactive alignment tool.

        Args:
            eos_space: EosSpace instance
        """
        self.eos_space = eos_space
        self.current_transforms: Dict[str, TransformParameters] = {}

    def set_model_transform(self, model_name: str, transform: TransformParameters):
        """Set transformation for a model.

        Args:
            model_name: Model identifier
            transform: Transform parameters
        """
        self.current_transforms[model_name] = transform

    def get_model_transform(self, model_name: str) -> Optional[TransformParameters]:
        """Get current transformation for a model.

        Args:
            model_name: Model identifier

        Returns:
            Transform parameters or None if not set
        """
        return self.current_transforms.get(model_name)

    def translate_model(
        self,
        model_name: str,
        delta_x: float = 0.0,
        delta_y: float = 0.0,
        delta_z: float = 0.0
    ) -> TransformParameters:
        """Translate model by specified amounts.

        Args:
            model_name: Model to translate
            delta_x: Translation in X (meters)
            delta_y: Translation in Y (meters)
            delta_z: Translation in Z (meters)

        Returns:
            Updated transform parameters
        """
        current = self.get_model_transform(model_name)
        if current is None:
            current = TransformParameters()

        new_translation = (
            current.translation[0] + delta_x,
            current.translation[1] + delta_y,
            current.translation[2] + delta_z
        )

        updated = TransformParameters(
            translation=new_translation,
            rotation=current.rotation,
            scale=current.scale
        )

        self.current_transforms[model_name] = updated
        return updated

    def rotate_model(
        self,
        model_name: str,
        delta_rx: float = 0.0,
        delta_ry: float = 0.0,
        delta_rz: float = 0.0
    ) -> TransformParameters:
        """Rotate model by specified angles.

        Args:
            model_name: Model to rotate
            delta_rx: Rotation around X (degrees)
            delta_ry: Rotation around Y (degrees)
            delta_rz: Rotation around Z (degrees)

        Returns:
            Updated transform parameters
        """
        current = self.get_model_transform(model_name)
        if current is None:
            current = TransformParameters()

        new_rotation = (
            current.rotation[0] + delta_rx,
            current.rotation[1] + delta_ry,
            current.rotation[2] + delta_rz
        )

        updated = TransformParameters(
            translation=current.translation,
            rotation=new_rotation,
            scale=current.scale
        )

        self.current_transforms[model_name] = updated
        return updated

    def scale_model(
        self,
        model_name: str,
        scale_factor: float
    ) -> TransformParameters:
        """Set scale factor for model.

        Args:
            model_name: Model to scale
            scale_factor: New scale factor

        Returns:
            Updated transform parameters
        """
        current = self.get_model_transform(model_name)
        if current is None:
            current = TransformParameters()

        updated = TransformParameters(
            translation=current.translation,
            rotation=current.rotation,
            scale=scale_factor
        )

        self.current_transforms[model_name] = updated
        return updated

    def reset_transform(self, model_name: str) -> TransformParameters:
        """Reset model transformation to identity.

        Args:
            model_name: Model to reset

        Returns:
            Reset transform parameters
        """
        default = TransformParameters()
        self.current_transforms[model_name] = default
        return default

    def save_transforms(self, file_path: str):
        """Save all transformations to file.

        Args:
            file_path: Path to save transforms
        """
        import json

        data = {
            name: transform.to_dict()
            for name, transform in self.current_transforms.items()
        }

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

    def load_transforms(self, file_path: str):
        """Load transformations from file.

        Args:
            file_path: Path to load transforms from
        """
        import json

        with open(file_path, 'r') as f:
            data = json.load(f)

        self.current_transforms = {
            name: TransformParameters(**params)
            for name, params in data.items()
        }
