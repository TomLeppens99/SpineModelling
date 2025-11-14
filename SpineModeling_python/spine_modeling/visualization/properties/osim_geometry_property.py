"""OpenSim Geometry Property - VTK visualization for OpenSim DisplayGeometry.

Handles 3D geometry visualization including meshes, scale factors, colors, textures,
and opacity for OpenSim model geometry components.
"""

from typing import Optional
import os

try:
    import vtk
except ImportError:
    vtk = None

try:
    import opensim
except ImportError:
    opensim = None


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

    @property
    def geom_color_normalized(self):
        """Get normalized RGB color values (0.0-1.0) for VTK."""
        return (self._geom_color_r, self._geom_color_g, self._geom_color_b)
    
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
    
    def __repr__(self) -> str:
        return f"OsimGeometryProperty(name='{self._object_name}', file='{self._geometry_file}')"
