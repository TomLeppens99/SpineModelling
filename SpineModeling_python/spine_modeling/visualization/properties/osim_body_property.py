"""OpenSim Body Property - VTK visualization for body components with geometry.

This is a streamlined implementation focusing on core VTK assembly and transform management.
Full implementation will be refined during testing phase.
"""

from typing import List, Optional

try:
    import vtk
except ImportError:
    vtk = None

try:
    import opensim
except ImportError:
    opensim = None


class OsimBodyProperty:
    """Property wrapper for OpenSim Body with VTK assembly visualization.
    
    Manages body geometry, transforms, joints, markers, and display properties.
    """
    
    def __init__(self):
        if vtk is None:
            raise ImportError("VTK is required")
        
        # System properties
        self._object_name: str = ""
        self._object_type: str = ""
        self._mass: float = 0.0
        self._is_visible: bool = True
        
        # OpenSim objects
        self._body: Optional[object] = None
        self._mass_center: Optional[object] = None
        
        # Related properties
        self.geometry_property_list: List = []
        self.joint_property: Optional[object] = None
        self.marker_property_list: List = []
        
        # VTK objects
        self.assembly = vtk.vtkAssembly()
        self.transform = vtk.vtkTransform()
        self.axes_actor = vtk.vtkActor()
        self.mass_center_actor = vtk.vtkActor()
        self.vtk_renderwindow: Optional[object] = None
        
        # Context menu (Phase 5)
        self._context_menu = None
    
    @property
    def object_name(self) -> str:
        return self._object_name
    
    @object_name.setter
    def object_name(self, value: str):
        self._object_name = value
        if self._body and opensim:
            self._body.setName(value)
    
    @property
    def body(self):
        return self._body
    
    @body.setter
    def body(self, value):
        self._body = value
    
    @property
    def mass(self) -> float:
        return self._mass
    
    def read_body_properties(self, body):
        """Read properties from OpenSim Body."""
        if opensim is None:
            raise ImportError("OpenSim is required")
        
        self._body = body
        self._object_name = body.getName()
        self._object_type = str(type(body))
        self._mass = body.getMass()
        self._mass_center = opensim.Vec3()
        body.getMassCenter(self._mass_center)
    
    def highlight_body(self):
        """Highlight body geometry with green color."""
        for geom_prop in self.geometry_property_list:
            if geom_prop.vtk_actor:
                geom_prop.vtk_actor.GetProperty().SetColor(0, 0.8, 0.5)
    
    def unhighlight_body(self):
        """Remove highlighting and restore original colors."""
        for geom_prop in self.geometry_property_list:
            if geom_prop.vtk_actor:
                # Restore original color from geom_prop
                geom_prop.vtk_actor.GetProperty().SetColor(
                    geom_prop._geom_color_r,
                    geom_prop._geom_color_g,
                    geom_prop._geom_color_b
                )
    
    def hide_programmatically(self):
        """Hide body by setting opacity to 0."""
        self._is_visible = False
        self.assembly.GetProperty().SetOpacity(0)
    
    def show_programmatically(self):
        """Show body by setting opacity to 1."""
        self._is_visible = True
        self.assembly.GetProperty().SetOpacity(1)
    
    def show_only_programmatically(self):
        """Show only this body (implementation depends on parent manager)."""
        self.show_programmatically()
    
    def show_hide_transparent_programmatically(self):
        """Toggle transparency."""
        current_opacity = self.assembly.GetProperty().GetOpacity()
        new_opacity = 0.3 if current_opacity > 0.5 else 1.0
        self.assembly.GetProperty().SetOpacity(new_opacity)
    
    def point_represent_programmatically(self):
        """Set point representation."""
        for geom_prop in self.geometry_property_list:
            if geom_prop.vtk_actor:
                geom_prop.vtk_actor.GetProperty().SetRepresentationToPoints()
    
    def smooth_shaded_programatically(self):
        """Set smooth shaded representation."""
        for geom_prop in self.geometry_property_list:
            if geom_prop.vtk_actor:
                geom_prop.vtk_actor.GetProperty().SetRepresentationToSurface()
    
    def wireframe_programatically(self):
        """Set wireframe representation."""
        for geom_prop in self.geometry_property_list:
            if geom_prop.vtk_actor:
                geom_prop.vtk_actor.GetProperty().SetRepresentationToWireframe()
    
    def __repr__(self) -> str:
        return f"OsimBodyProperty(name='{self._object_name}', mass={self._mass:.3f}, geometries={len(self.geometry_property_list)})"
