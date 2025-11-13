"""OpenSim Force Property - VTK visualization for muscles and actuators.

Streamlined implementation focusing on core muscle path visualization with control points.
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


class OsimForceProperty:
    """Property wrapper for OpenSim Force (muscle/actuator) with VTK path visualization.
    
    Manages muscle geometry paths, control points, and line actors connecting them.
    """
    
    def __init__(self):
        if vtk is None:
            raise ImportError("VTK is required")
        
        # System properties
        self._object_name: str = ""
        self._object_type: str = ""
        self._max_isometric_force: float = 0.0
        self._optimal_fiber_length: float = 0.0
        self._tendon_slack_length: float = 0.0
        self._pennation_angle: float = 0.0
        self._is_visible: bool = True
        self._color_r: float = 1.0
        self._color_g: float = 0.01
        self._color_b: float = 0.0
        
        # OpenSim objects
        self._force: Optional[object] = None  # opensim.Muscle or Force
        self._geometry_path: Optional[object] = None
        
        # Control points and lines
        self.control_point_property_list: List = []
        self.muscle_line_property_list: List = []
        
        # VTK objects
        self.assembly = vtk.vtkAssembly()
        self.vtk_renderwindow: Optional[object] = None
        
        # Context menu (Phase 5)
        self._context_menu = None
    
    @property
    def object_name(self) -> str:
        return self._object_name
    
    @object_name.setter
    def object_name(self, value: str):
        self._object_name = value
        if self._force and opensim:
            self._force.setName(value)
    
    @property
    def force(self):
        return self._force
    
    @force.setter
    def force(self, value):
        self._force = value
    
    @property
    def max_isometric_force(self) -> float:
        return self._max_isometric_force
    
    def read_force_properties(self, force):
        """Read properties from OpenSim Force/Muscle."""
        if opensim is None:
            raise ImportError("OpenSim is required")
        
        self._force = force
        self._object_name = force.getName()
        self._object_type = str(type(force))
        
        # Try to read muscle-specific properties
        try:
            if hasattr(force, 'getMaxIsometricForce'):
                self._max_isometric_force = force.getMaxIsometricForce()
            if hasattr(force, 'getOptimalFiberLength'):
                self._optimal_fiber_length = force.getOptimalFiberLength()
            if hasattr(force, 'getTendonSlackLength'):
                self._tendon_slack_length = force.getTendonSlackLength()
            if hasattr(force, 'getPennationAngleAtOptimalFiberLength'):
                self._pennation_angle = force.getPennationAngleAtOptimalFiberLength()
        except:
            pass
        
        # Get geometry path
        if hasattr(force, 'getGeometryPath'):
            self._geometry_path = force.getGeometryPath()
    
    def highlight_force(self):
        """Highlight muscle with green color."""
        for cp_prop in self.control_point_property_list:
            if cp_prop.control_point_actor:
                cp_prop.control_point_actor.GetProperty().SetColor(0, 0.8, 0.5)
        for line_prop in self.muscle_line_property_list:
            if line_prop.muscle_actor:
                line_prop.muscle_actor.GetProperty().SetColor(0, 0.8, 0.5)
    
    def unhighlight_force(self):
        """Remove highlighting and restore original colors."""
        for cp_prop in self.control_point_property_list:
            if cp_prop.control_point_actor:
                cp_prop.control_point_actor.GetProperty().SetColor(1, 0, 0)
        for line_prop in self.muscle_line_property_list:
            if line_prop.muscle_actor:
                line_prop.muscle_actor.GetProperty().SetColor(
                    line_prop.color_r, line_prop.color_g, line_prop.color_b
                )
    
    def hide_programmatically(self):
        """Hide muscle by setting opacity to 0."""
        self._is_visible = False
        for cp_prop in self.control_point_property_list:
            if cp_prop.control_point_actor:
                cp_prop.control_point_actor.GetProperty().SetOpacity(0)
        for line_prop in self.muscle_line_property_list:
            if line_prop.muscle_actor:
                line_prop.muscle_actor.GetProperty().SetOpacity(0)
    
    def show_programmatically(self):
        """Show muscle by setting opacity to 1."""
        self._is_visible = True
        for cp_prop in self.control_point_property_list:
            if cp_prop.control_point_actor:
                cp_prop.control_point_actor.GetProperty().SetOpacity(1)
        for line_prop in self.muscle_line_property_list:
            if line_prop.muscle_actor:
                line_prop.muscle_actor.GetProperty().SetOpacity(1)
    
    def update_muscle_geometry(self):
        """Update muscle line actors with current control point positions."""
        for line_prop in self.muscle_line_property_list:
            line_prop.update_muscle_line_actor()
    
    def __repr__(self) -> str:
        return (f"OsimForceProperty(name='{self._object_name}', "
                f"max_force={self._max_isometric_force:.1f}, "
                f"control_points={len(self.control_point_property_list)})")
