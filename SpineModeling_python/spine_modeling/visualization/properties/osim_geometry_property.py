"""OpenSim Geometry Property - VTK visualization for OpenSim DisplayGeometry.

Handles 3D geometry visualization including meshes, scale factors, colors, textures,
and opacity for OpenSim model geometry components.
"""

from typing import Optional, Tuple, TYPE_CHECKING
import os

if TYPE_CHECKING:
    import vtk
    import opensim
else:
    try:
        import vtk
    except ImportError:
        vtk = None

    try:
        import opensim
    except ImportError:
        opensim = None

from ..geometry_loader import GeometryLoader


class OsimGeometryProperty:
    """Property wrapper for OpenSim DisplayGeometry with VTK actors."""
    
    def __init__(self):
        if vtk is None:
            raise ImportError("VTK is required")
        
        # System properties
        self._object_name: str = ""
        self._object_type: str = ""
        self._geometry_file: str = ""
        self._geometry_dir_and_file: str = ""
        self._extension: str = ""
        self._texture_file: str = ""
        self._geom_color_r: float = 1.0
        self._geom_color_g: float = 1.0
        self._geom_color_b: float = 1.0
        self._opacity: float = 1.0
        self._display_preference: int = 4
        self._loaded_from_database: bool = False
        self._index_number_of_geometry: int = 0
        self.dlt_polydata_has_been_made: bool = False
        
        # OpenSim objects
        self._display_geometry: Optional[object] = None
        self._transform: Optional[object] = None
        self._geom_scale_factors: Optional[object] = None
        self.model: Optional[object] = None
        
        # VTK objects
        self._vtk_actor = vtk.vtkActor()
        self._vtk_actor1 = vtk.vtkActor()
        self._vtk_actor2 = vtk.vtkActor()
        self._vtk_polydata = vtk.vtkPolyData()
        self._vtk_polydata_dlt = vtk.vtkPolyData()
    
    @property
    def object_name(self) -> str:
        return self._object_name
    
    @object_name.setter
    def object_name(self, value: str):
        self._object_name = value
    
    @property
    def vtk_actor(self):
        return self._vtk_actor
    
    @property
    def display_geometry(self):
        return self._display_geometry
    
    @display_geometry.setter
    def display_geometry(self, value):
        self._display_geometry = value
        if self.model:
            self.model.updDisplayer()
    
    @property
    def opacity(self) -> float:
        return self._opacity
    
    @opacity.setter
    def opacity(self, value: float):
        self._opacity = value
        if self._display_geometry and opensim:
            self._display_geometry.setOpacity(value)
        if self._vtk_actor:
            self._vtk_actor.GetProperty().SetOpacity(value)
    
    @property
    def geom_color(self):
        return (int(self._geom_color_r * 255), 
                int(self._geom_color_g * 255), 
                int(self._geom_color_b * 255))
    
    @geom_color.setter
    def geom_color(self, value):
        r, g, b = value
        self._geom_color_r = r / 255.0
        self._geom_color_g = g / 255.0
        self._geom_color_b = b / 255.0
        if self._vtk_actor:
            self._vtk_actor.GetProperty().SetColor(
                self._geom_color_r, self._geom_color_g, self._geom_color_b
            )
    
    def read_geometry_properties(self, display_geom, model):
        """Read properties from OpenSim DisplayGeometry."""
        if opensim is None:
            raise ImportError("OpenSim is required")
        
        self._display_geometry = display_geom
        self.model = model
        self._geometry_file = display_geom.getGeometryFile()
        self._opacity = display_geom.getOpacity()
        
        # Get scale factors
        self._geom_scale_factors = opensim.Vec3()
        display_geom.getScaleFactors(self._geom_scale_factors)
        
        # Get transform
        self._transform = display_geom.getTransform()
        
        # Parse file info
        self._geometry_dir_and_file = self._geometry_file
        self._extension = os.path.splitext(self._geometry_file)[1]
        self._object_name = os.path.basename(self._geometry_file)
        self._object_type = str(type(display_geom))
    
    def make_vtk_actor(
        self,
        add_axes: bool = True,
        axes_scale: float = 0.06
    ) -> bool:
        """Create VTK actor from geometry file.

        Loads geometry from file and creates a VTK actor with proper scaling,
        coloring, and optional coordinate axes.

        Args:
            add_axes: Whether to add coordinate axes to the visualization
            axes_scale: Scale factor for coordinate axes

        Returns:
            True if actor was created successfully, False otherwise
        """
        if not self._geometry_dir_and_file:
            print("Error: No geometry file specified")
            return False

        if not os.path.exists(self._geometry_dir_and_file):
            print(f"Error: Geometry file not found: {self._geometry_dir_and_file}")
            return False

        # Check if format is supported
        if not GeometryLoader.is_supported_format(self._geometry_dir_and_file):
            print(
                f"Error: Only geometry files of type VTP, STL or OBJ can be read. "
                f"Got: {self._extension}"
            )
            return False

        try:
            # Load geometry
            polydata = GeometryLoader.load_geometry(self._geometry_dir_and_file)
            if polydata is None:
                return False

            self._vtk_polydata = polydata

            # Get scale factors
            if self._geom_scale_factors and opensim:
                scale_x = self._geom_scale_factors.get(0)
                scale_y = self._geom_scale_factors.get(1)
                scale_z = self._geom_scale_factors.get(2)
            else:
                scale_x = scale_y = scale_z = 1.0

            # Create transform
            transform = vtk.vtkTransform()
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

            # Create and configure actor
            self._vtk_actor = vtk.vtkActor()
            self._vtk_actor.SetMapper(mapper)
            self._vtk_actor.GetProperty().SetColor(
                self._geom_color_r, self._geom_color_g, self._geom_color_b
            )
            self._vtk_actor.SetScale(scale_x, scale_y, scale_z)

            return True

        except Exception as e:
            print(f"Error creating VTK actor: {e}")
            return False

    def make_2d_actors(self) -> bool:
        """Create 2D projection actors for dual EOS views.

        Creates two vtkActor objects (_vtk_actor1 and _vtk_actor2) for
        projecting 3D geometry onto 2D EOS images.

        Returns:
            True if actors were created successfully, False otherwise
        """
        if self._vtk_polydata.GetNumberOfPoints() == 0 and not self.dlt_polydata_has_been_made:
            print("Error: No polydata available. Call make_vtk_actor() first.")
            return False

        try:
            # Choose appropriate polydata source
            if self.dlt_polydata_has_been_made:
                source_polydata = self._vtk_polydata_dlt
            else:
                source_polydata = self._vtk_polydata

            # Create transform filter
            transform = vtk.vtkTransform()
            transform_filter = vtk.vtkTransformFilter()
            transform_filter.SetInputData(source_polydata)
            transform_filter.SetTransform(transform)

            # Create append filter
            append_filter = vtk.vtkAppendPolyData()
            append_filter.AddInputConnection(transform_filter.GetOutputPort())

            # Create mapper
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(append_filter.GetOutputPort())

            # Get scale factors
            if self._geom_scale_factors and opensim:
                scale_x = self._geom_scale_factors.get(0)
                scale_y = self._geom_scale_factors.get(1)
                scale_z = self._geom_scale_factors.get(2)
            else:
                scale_x = scale_y = scale_z = 1.0

            # Configure actor1 (for first EOS view)
            if not self.dlt_polydata_has_been_made:
                self._vtk_actor1.SetMapper(mapper)
                self._vtk_actor1.GetMapper().Update()
                self._vtk_actor1.GetMapper().Modified()
                self._vtk_actor1.GetProperty().SetOpacity(0.1)
                self._vtk_actor1.GetProperty().SetColor(1, 0, 0)  # Red
                self._vtk_actor1.SetScale(scale_x, scale_y, scale_z)
            else:
                # Update existing mapper
                self._vtk_actor1.GetMapper().SetInputConnection(
                    append_filter.GetOutputPort()
                )

            return True

        except Exception as e:
            print(f"Error creating 2D actors: {e}")
            return False

    def set_geometry_file(self, file_path: str) -> bool:
        """Set geometry file path and update extension info.

        Args:
            file_path: Full path to geometry file

        Returns:
            True if file exists and is supported format
        """
        if not os.path.exists(file_path):
            print(f"Error: File not found: {file_path}")
            return False

        if not GeometryLoader.is_supported_format(file_path):
            ext = os.path.splitext(file_path)[1]
            print(f"Error: Unsupported format: {ext}")
            return False

        self._geometry_dir_and_file = file_path
        self._geometry_file = os.path.basename(file_path)
        self._extension = os.path.splitext(file_path)[1].lower()
        self._object_name = self._geometry_file

        return True

    def get_vtk_transform(self) -> Optional['vtk.vtkTransform']:
        """Get the VTK transform from the actor.

        Returns:
            vtkTransform object or None if no transform is set
        """
        if self._vtk_actor:
            return self._vtk_actor.GetUserTransform()
        return None

    def set_vtk_transform(self, transform: 'vtk.vtkTransform'):
        """Set VTK transform on the actor.

        Args:
            transform: vtkTransform to apply to the actor
        """
        if self._vtk_actor:
            self._vtk_actor.SetUserTransform(transform)

    @property
    def geometry_file(self) -> str:
        """Get geometry file name."""
        return self._geometry_file

    @property
    def geometry_dir_and_file(self) -> str:
        """Get full geometry file path."""
        return self._geometry_dir_and_file

    @property
    def extension(self) -> str:
        """Get file extension."""
        return self._extension

    @property
    def loaded_from_database(self) -> bool:
        """Check if loaded from database."""
        return self._loaded_from_database

    @loaded_from_database.setter
    def loaded_from_database(self, value: bool):
        self._loaded_from_database = value

    @property
    def index_number_of_geometry(self) -> int:
        """Get geometry index number."""
        return self._index_number_of_geometry

    @index_number_of_geometry.setter
    def index_number_of_geometry(self, value: int):
        self._index_number_of_geometry = value

    @property
    def vtk_polydata(self) -> 'vtk.vtkPolyData':
        """Get the underlying VTK polydata."""
        return self._vtk_polydata

    @property
    def vtk_actor1(self) -> 'vtk.vtkActor':
        """Get the first 2D projection actor."""
        return self._vtk_actor1

    @property
    def vtk_actor2(self) -> 'vtk.vtkActor':
        """Get the second 2D projection actor."""
        return self._vtk_actor2

    def __repr__(self) -> str:
        return f"OsimGeometryProperty(name='{self._object_name}', file='{self._geometry_file}')"
