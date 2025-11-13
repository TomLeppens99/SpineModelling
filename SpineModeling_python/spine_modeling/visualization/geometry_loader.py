"""Geometry file loader for 3D models.

Loads various 3D geometry formats (STL, OBJ, VTP) and creates VTK poly data
for visualization in the spine modeling application.
"""

from typing import Optional, Tuple, TYPE_CHECKING
import os

if TYPE_CHECKING:
    import vtk
else:
    try:
        import vtk
    except ImportError:
        vtk = None


class GeometryLoader:
    """Handles loading of 3D geometry files in various formats."""

    SUPPORTED_FORMATS = {'.stl', '.obj', '.vtp'}

    def __init__(self):
        if vtk is None:
            raise ImportError("VTK is required for geometry loading")

    @staticmethod
    def is_supported_format(file_path: str) -> bool:
        """Check if the file format is supported.

        Args:
            file_path: Path to the geometry file

        Returns:
            True if format is supported, False otherwise
        """
        ext = os.path.splitext(file_path)[1].lower()
        return ext in GeometryLoader.SUPPORTED_FORMATS

    @staticmethod
    def load_geometry(file_path: str) -> Optional['vtk.vtkPolyData']:
        """Load geometry from file and return as vtkPolyData.

        Args:
            file_path: Path to the geometry file (.stl, .obj, or .vtp)

        Returns:
            vtkPolyData object or None if loading failed

        Raises:
            ValueError: If file format is not supported
            FileNotFoundError: If file does not exist
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Geometry file not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()

        if ext not in GeometryLoader.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported geometry format: {ext}. "
                f"Supported formats: {', '.join(GeometryLoader.SUPPORTED_FORMATS)}"
            )

        reader = GeometryLoader._create_reader(file_path, ext)
        if reader is None:
            return None

        reader.Update()
        return reader.GetOutput()

    @staticmethod
    def _create_reader(file_path: str, extension: str):
        """Create appropriate VTK reader for the file format.

        Args:
            file_path: Path to the geometry file
            extension: File extension (with dot)

        Returns:
            VTK reader object or None if format not supported
        """
        if extension == '.stl':
            reader = vtk.vtkSTLReader()
        elif extension == '.obj':
            reader = vtk.vtkOBJReader()
        elif extension == '.vtp':
            reader = vtk.vtkXMLPolyDataReader()
        else:
            return None

        reader.SetFileName(file_path)
        return reader

    @staticmethod
    def create_actor_from_polydata(
        polydata: 'vtk.vtkPolyData',
        color: Tuple[float, float, float] = (1.0, 1.0, 1.0),
        scale: Tuple[float, float, float] = (1.0, 1.0, 1.0),
        opacity: float = 1.0,
        add_axes: bool = False,
        axes_scale: float = 0.06
    ) -> 'vtk.vtkActor':
        """Create VTK actor from polydata with specified properties.

        Args:
            polydata: Input VTK polydata
            color: RGB color tuple (0-1 range)
            scale: XYZ scale factors
            opacity: Opacity (0-1)
            add_axes: Whether to add coordinate axes
            axes_scale: Scale factor for axes

        Returns:
            Configured vtkActor
        """
        # Create transform
        transform = vtk.vtkTransform()

        # Apply transform to polydata
        transform_filter = vtk.vtkTransformFilter()
        transform_filter.SetInputData(polydata)
        transform_filter.SetTransform(transform)

        # Optionally add axes
        if add_axes:
            axes = vtk.vtkAxes()
            axes.SetOrigin(0, 0, 0)
            axes.SetScaleFactor(axes_scale)

            append_filter = vtk.vtkAppendPolyData()
            append_filter.AddInputConnection(transform_filter.GetOutputPort())
            append_filter.AddInputConnection(axes.GetOutputPort())

            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(append_filter.GetOutputPort())
        else:
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(transform_filter.GetOutputPort())

        # Create actor
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        actor.GetProperty().SetColor(color[0], color[1], color[2])
        actor.GetProperty().SetOpacity(opacity)
        actor.SetScale(scale[0], scale[1], scale[2])

        return actor

    @staticmethod
    def load_and_create_actor(
        file_path: str,
        color: Tuple[float, float, float] = (1.0, 1.0, 1.0),
        scale: Tuple[float, float, float] = (1.0, 1.0, 1.0),
        opacity: float = 1.0,
        add_axes: bool = False,
        axes_scale: float = 0.06
    ) -> Tuple[Optional['vtk.vtkActor'], Optional['vtk.vtkPolyData']]:
        """Load geometry file and create VTK actor in one step.

        Args:
            file_path: Path to geometry file
            color: RGB color tuple (0-1 range)
            scale: XYZ scale factors
            opacity: Opacity (0-1)
            add_axes: Whether to add coordinate axes
            axes_scale: Scale factor for axes

        Returns:
            Tuple of (vtkActor, vtkPolyData) or (None, None) if loading failed
        """
        try:
            polydata = GeometryLoader.load_geometry(file_path)
            if polydata is None:
                return None, None

            actor = GeometryLoader.create_actor_from_polydata(
                polydata, color, scale, opacity, add_axes, axes_scale
            )

            return actor, polydata

        except (ValueError, FileNotFoundError) as e:
            print(f"Error loading geometry: {e}")
            return None, None


class CT3DModelLoader:
    """Specialized loader for CT-derived 3D vertebral models."""

    def __init__(self):
        self.geometry_loader = GeometryLoader()

    def load_vertebral_model(
        self,
        file_path: str,
        color: Tuple[float, float, float] = (0.9, 0.9, 0.7),  # Bone-like color
        opacity: float = 0.8
    ) -> Tuple[Optional['vtk.vtkActor'], Optional['vtk.vtkPolyData']]:
        """Load a vertebral model from CT scan.

        Args:
            file_path: Path to vertebral model file
            color: RGB color for the vertebra (default: bone color)
            opacity: Opacity (default: 0.8 for slight transparency)

        Returns:
            Tuple of (vtkActor, vtkPolyData) or (None, None) if failed
        """
        return self.geometry_loader.load_and_create_actor(
            file_path=file_path,
            color=color,
            scale=(1.0, 1.0, 1.0),  # No scaling by default
            opacity=opacity,
            add_axes=True,  # Add axes for orientation
            axes_scale=10.0  # Larger axes for vertebral models
        )

    def load_multiple_vertebrae(
        self,
        file_paths: list,
        base_color: Tuple[float, float, float] = (0.9, 0.9, 0.7)
    ) -> list:
        """Load multiple vertebral models.

        Args:
            file_paths: List of paths to vertebral model files
            base_color: Base RGB color for vertebrae

        Returns:
            List of tuples (actor, polydata, file_path) for successfully loaded models
        """
        loaded_models = []

        for file_path in file_paths:
            actor, polydata = self.load_vertebral_model(file_path, base_color)

            if actor is not None and polydata is not None:
                loaded_models.append((actor, polydata, file_path))
                print(f"Loaded: {os.path.basename(file_path)}")
            else:
                print(f"Failed to load: {os.path.basename(file_path)}")

        return loaded_models
