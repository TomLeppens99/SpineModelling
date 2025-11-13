"""3D to 2D projection system for vertebral models onto EOS images.

This module provides functionality to project 3D CT-derived vertebral models
onto 2D EOS X-ray images using perspective projection based on EOS calibration
parameters.
"""

from typing import Tuple, List, Optional, TYPE_CHECKING
import numpy as np

if TYPE_CHECKING:
    import vtk
else:
    try:
        import vtk
    except ImportError:
        vtk = None

from spine_modeling.imaging.eos_space import EosSpace
from spine_modeling.core.position import Position


class Projection3D:
    """Handles 3D-to-2D projection of vertebral models onto EOS images.

    This class takes a 3D vertebral model (VTK polydata) and projects it onto
    the two 2D EOS image planes (frontal and lateral) using perspective projection
    based on the EOS calibration parameters.
    """

    def __init__(self, eos_space: EosSpace):
        """Initialize the projection system.

        Args:
            eos_space: EosSpace instance with calibration parameters
        """
        if vtk is None:
            raise ImportError("VTK is required for 3D projection")

        self.eos_space = eos_space
        self.eos_space.calculate_eos_space()  # Ensure geometry is calculated

    def project_point_to_images(
        self,
        point_3d: Tuple[float, float, float]
    ) -> Tuple[Tuple[float, float], Tuple[float, float]]:
        """Project a single 3D point onto both 2D image planes.

        Args:
            point_3d: 3D point as (x, y, z) tuple in meters

        Returns:
            Tuple containing:
                - (x_frontal, y_frontal): Coordinates on frontal image
                - (x_lateral, y_lateral): Coordinates on lateral image
        """
        x, y, z = point_3d

        # Project XZ coordinates using EosSpace
        x_proj, z_proj = self.eos_space.project(x, z)

        # For frontal image: x_proj is horizontal, y is vertical (preserved)
        frontal_coords = (x_proj, y)

        # For lateral image: z_proj is horizontal, y is vertical (preserved)
        lateral_coords = (z_proj, y)

        return frontal_coords, lateral_coords

    def project_polydata(
        self,
        polydata: 'vtk.vtkPolyData'
    ) -> Tuple['vtk.vtkPolyData', 'vtk.vtkPolyData']:
        """Project entire VTK polydata onto both 2D image planes.

        Args:
            polydata: Input 3D polydata (vertebral model)

        Returns:
            Tuple of (frontal_polydata, lateral_polydata)
        """
        if polydata is None or polydata.GetNumberOfPoints() == 0:
            return None, None

        # Get all points from the 3D polydata
        num_points = polydata.GetNumberOfPoints()

        # Create output polydata for each view
        frontal_polydata = vtk.vtkPolyData()
        lateral_polydata = vtk.vtkPolyData()

        frontal_points = vtk.vtkPoints()
        lateral_points = vtk.vtkPoints()

        # Project each point
        for i in range(num_points):
            point_3d = polydata.GetPoint(i)

            frontal_coords, lateral_coords = self.project_point_to_images(point_3d)

            # Add projected points (set Z=0 for 2D)
            frontal_points.InsertNextPoint(frontal_coords[0], frontal_coords[1], 0)
            lateral_points.InsertNextPoint(lateral_coords[0], lateral_coords[1], 0)

        frontal_polydata.SetPoints(frontal_points)
        lateral_polydata.SetPoints(lateral_points)

        # Copy cell connectivity from original polydata
        frontal_polydata.SetPolys(polydata.GetPolys())
        lateral_polydata.SetPolys(polydata.GetPolys())

        return frontal_polydata, lateral_polydata

    def create_silhouette_from_polydata(
        self,
        polydata: 'vtk.vtkPolyData',
        view: str = 'frontal'
    ) -> 'vtk.vtkPolyData':
        """Create 2D silhouette (outline) of 3D model for a specific view.

        Args:
            polydata: Input 3D polydata
            view: View to project to ('frontal' or 'lateral')

        Returns:
            Silhouette polydata with edge representation
        """
        # Project the polydata
        frontal_poly, lateral_poly = self.project_polydata(polydata)

        if view == 'frontal':
            projected = frontal_poly
        else:
            projected = lateral_poly

        if projected is None:
            return None

        # Extract edges for silhouette
        edge_extractor = vtk.vtkFeatureEdges()
        edge_extractor.SetInputData(projected)
        edge_extractor.BoundaryEdgesOn()
        edge_extractor.FeatureEdgesOff()
        edge_extractor.ManifoldEdgesOff()
        edge_extractor.NonManifoldEdgesOff()
        edge_extractor.Update()

        return edge_extractor.GetOutput()

    def create_projection_actors(
        self,
        polydata: 'vtk.vtkPolyData',
        color_frontal: Tuple[float, float, float] = (1.0, 0.0, 0.0),
        color_lateral: Tuple[float, float, float] = (0.0, 0.0, 1.0),
        opacity: float = 0.3,
        line_width: float = 2.0
    ) -> Tuple['vtk.vtkActor', 'vtk.vtkActor']:
        """Create VTK actors for projected model on both views.

        Args:
            polydata: Input 3D polydata
            color_frontal: RGB color for frontal projection
            color_lateral: RGB color for lateral projection
            opacity: Opacity for the projections
            line_width: Line width for silhouette edges

        Returns:
            Tuple of (frontal_actor, lateral_actor)
        """
        frontal_poly, lateral_poly = self.project_polydata(polydata)

        if frontal_poly is None or lateral_poly is None:
            return None, None

        # Create frontal actor
        frontal_mapper = vtk.vtkPolyDataMapper()
        frontal_mapper.SetInputData(frontal_poly)

        frontal_actor = vtk.vtkActor()
        frontal_actor.SetMapper(frontal_mapper)
        frontal_actor.GetProperty().SetColor(color_frontal)
        frontal_actor.GetProperty().SetOpacity(opacity)
        frontal_actor.GetProperty().SetRepresentationToWireframe()
        frontal_actor.GetProperty().SetLineWidth(line_width)

        # Create lateral actor
        lateral_mapper = vtk.vtkPolyDataMapper()
        lateral_mapper.SetInputData(lateral_poly)

        lateral_actor = vtk.vtkActor()
        lateral_actor.SetMapper(lateral_mapper)
        lateral_actor.GetProperty().SetColor(color_lateral)
        lateral_actor.GetProperty().SetOpacity(opacity)
        lateral_actor.GetProperty().SetRepresentationToWireframe()
        lateral_actor.GetProperty().SetLineWidth(line_width)

        return frontal_actor, lateral_actor

    def transform_model_to_eos_space(
        self,
        polydata: 'vtk.vtkPolyData',
        translation: Tuple[float, float, float] = (0, 0, 0),
        rotation: Tuple[float, float, float] = (0, 0, 0),
        scale: float = 1.0
    ) -> 'vtk.vtkPolyData':
        """Transform 3D model to align with EOS space coordinates.

        Args:
            polydata: Input polydata
            translation: XYZ translation in meters
            rotation: XYZ rotation in degrees
            scale: Uniform scale factor

        Returns:
            Transformed polydata
        """
        # Create transform
        transform = vtk.vtkTransform()
        transform.Translate(translation)
        transform.RotateX(rotation[0])
        transform.RotateY(rotation[1])
        transform.RotateZ(rotation[2])
        transform.Scale(scale, scale, scale)

        # Apply transform
        transform_filter = vtk.vtkTransformPolyDataFilter()
        transform_filter.SetInputData(polydata)
        transform_filter.SetTransform(transform)
        transform_filter.Update()

        return transform_filter.GetOutput()

    def convert_projection_to_pixels(
        self,
        projection_coords: Tuple[float, float],
        image_label: str
    ) -> Tuple[int, int]:
        """Convert projection coordinates from meters to pixel coordinates.

        Args:
            projection_coords: (x, y) coordinates in meters
            image_label: "A" for frontal, "B" for lateral

        Returns:
            Tuple of (x_pixel, y_pixel)
        """
        x_meters, y_meters = projection_coords

        if image_label == "A":
            pixel_spacing_x = self.eos_space.eos_image_a.pixel_spacing_x
            pixel_spacing_y = self.eos_space.eos_image_a.pixel_spacing_y

            # Convert from EOS space origin to image pixel coordinates
            x_pixel = self.eos_space.convert_meters_to_pixels(
                x_meters + self.eos_space.eos_image_a.width / 2,
                pixel_spacing_x
            )
            y_pixel = self.eos_space.convert_meters_to_pixels(y_meters, pixel_spacing_y)

        elif image_label == "B":
            pixel_spacing_x = self.eos_space.eos_image_b.pixel_spacing_x
            pixel_spacing_y = self.eos_space.eos_image_b.pixel_spacing_y

            # Convert from EOS space origin to image pixel coordinates
            x_pixel = self.eos_space.convert_meters_to_pixels(
                x_meters + self.eos_space.eos_image_b.width / 2,
                pixel_spacing_x
            )
            y_pixel = self.eos_space.convert_meters_to_pixels(y_meters, pixel_spacing_y)

        else:
            raise ValueError(f"Invalid image_label: {image_label}. Use 'A' or 'B'")

        return (x_pixel, y_pixel)

    def get_projected_bounds(
        self,
        polydata: 'vtk.vtkPolyData',
        view: str = 'frontal'
    ) -> Tuple[float, float, float, float]:
        """Get bounding box of projected model.

        Args:
            polydata: Input 3D polydata
            view: View to project to ('frontal' or 'lateral')

        Returns:
            Tuple of (x_min, x_max, y_min, y_max) in meters
        """
        frontal_poly, lateral_poly = self.project_polydata(polydata)

        if view == 'frontal':
            projected = frontal_poly
        else:
            projected = lateral_poly

        if projected is None:
            return (0, 0, 0, 0)

        bounds = projected.GetBounds()
        return (bounds[0], bounds[1], bounds[2], bounds[3])


class VertebralModelProjector:
    """High-level interface for projecting vertebral models onto EOS images."""

    def __init__(self, eos_space: EosSpace):
        """Initialize vertebral model projector.

        Args:
            eos_space: EosSpace instance with calibration
        """
        self.projection_3d = Projection3D(eos_space)
        self.loaded_models = []  # List of (name, polydata, transform)

    def add_vertebral_model(
        self,
        name: str,
        polydata: 'vtk.vtkPolyData',
        initial_position: Tuple[float, float, float] = (0, 0, 0),
        initial_rotation: Tuple[float, float, float] = (0, 0, 0),
        scale: float = 0.001  # Default: mm to meters conversion
    ):
        """Add a vertebral model to be projected.

        Args:
            name: Name identifier for the model (e.g., "L3")
            polydata: VTK polydata of the vertebra
            initial_position: Initial XYZ position in meters
            initial_rotation: Initial XYZ rotation in degrees
            scale: Scale factor (default converts mm to meters)
        """
        # Transform to EOS space
        transformed = self.projection_3d.transform_model_to_eos_space(
            polydata,
            translation=initial_position,
            rotation=initial_rotation,
            scale=scale
        )

        self.loaded_models.append({
            'name': name,
            'polydata_original': polydata,
            'polydata_transformed': transformed,
            'position': initial_position,
            'rotation': initial_rotation,
            'scale': scale
        })

    def update_model_transform(
        self,
        name: str,
        position: Optional[Tuple[float, float, float]] = None,
        rotation: Optional[Tuple[float, float, float]] = None,
        scale: Optional[float] = None
    ):
        """Update transformation of a loaded model.

        Args:
            name: Name of the model to update
            position: New position (None to keep current)
            rotation: New rotation (None to keep current)
            scale: New scale (None to keep current)
        """
        for model in self.loaded_models:
            if model['name'] == name:
                # Update stored parameters
                if position is not None:
                    model['position'] = position
                if rotation is not None:
                    model['rotation'] = rotation
                if scale is not None:
                    model['scale'] = scale

                # Re-transform
                model['polydata_transformed'] = self.projection_3d.transform_model_to_eos_space(
                    model['polydata_original'],
                    translation=model['position'],
                    rotation=model['rotation'],
                    scale=model['scale']
                )
                break

    def get_all_projection_actors(
        self,
        color_frontal: Tuple[float, float, float] = (1.0, 0.0, 0.0),
        color_lateral: Tuple[float, float, float] = (0.0, 0.0, 1.0),
        opacity: float = 0.3
    ) -> List[Tuple[str, 'vtk.vtkActor', 'vtk.vtkActor']]:
        """Get projection actors for all loaded models.

        Args:
            color_frontal: RGB color for frontal projections
            color_lateral: RGB color for lateral projections
            opacity: Opacity for projections

        Returns:
            List of (name, frontal_actor, lateral_actor) tuples
        """
        actors = []

        for model in self.loaded_models:
            frontal_actor, lateral_actor = self.projection_3d.create_projection_actors(
                model['polydata_transformed'],
                color_frontal=color_frontal,
                color_lateral=color_lateral,
                opacity=opacity
            )

            if frontal_actor and lateral_actor:
                actors.append((model['name'], frontal_actor, lateral_actor))

        return actors

    def clear_all_models(self):
        """Remove all loaded models."""
        self.loaded_models.clear()

    def get_model_count(self) -> int:
        """Get number of loaded models."""
        return len(self.loaded_models)

    def get_model_names(self) -> List[str]:
        """Get names of all loaded models."""
        return [model['name'] for model in self.loaded_models]
