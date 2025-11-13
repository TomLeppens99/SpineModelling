"""
Marker property wrapper for OpenSim models.

This module provides a property class for OpenSim Marker objects with VTK
sphere visualization and position management.

Note: The original C# class name was "OsimMakerProperty" (typo), but this
      Python version uses the correct name "OsimMarkerProperty".
"""

from typing import Optional, Tuple

try:
    import vtk
except ImportError:
    vtk = None

try:
    import opensim
except ImportError:
    opensim = None

# Import Position from core module
try:
    from spine_modeling.core.position import Position
except ImportError:
    Position = None


class OsimMarkerProperty:
    """
    Property wrapper for OpenSim Marker objects with VTK visualization.
    
    This class encapsulates an OpenSim Marker (anatomical landmark) with
    a VTK sphere actor for visualization. Markers can be fixed to bodies
    or movable, and have configurable color and visibility.
    
    Attributes:
        object_name (str): Marker name from protocol
        object_type (str): Type of marker object
        reference_body (str): Body to which marker is linked
        is_fixed (bool): Whether marker is fixed to body
        is_visible (bool): Marker visibility status
        marker_color (tuple): RGB color (0-255 range)
        abs_position (Position): Absolute position (ground frame)
        r_offset (Vec3): Relative offset from body
        marker (Marker): OpenSim Marker object
        marker_actor (vtkActor): VTK sphere actor
        marker_transform (vtkTransform): Transform for positioning
        parent_body_prop (OsimBodyProperty): Parent body property
        reference_body_object (Body): OpenSim Body object
    
    Example:
        >>> marker_prop = OsimMarkerProperty()
        >>> marker_prop.marker = model.getMarkerSet().get("LASIS")
        >>> marker_prop.read_marker_properties(marker_prop.marker)
        >>> renderer.AddActor(marker_prop.marker_actor)
    """
    
    def __init__(self):
        """Initialize a marker property with default purple color."""
        if vtk is None:
            raise ImportError(
                "VTK package is required but not installed. "
                "Install with: pip install vtk"
            )
        
        # System properties
        self._object_name: str = ""
        self._object_type: str = ""
        self._reference_body: str = ""
        self._is_fixed: bool = False
        self._is_visible: bool = True
        self._color_r: float = 0.82
        self._color_g: float = 0.37
        self._color_b: float = 0.93  # Default purple
        self._marker_color: Tuple[int, int, int] = (209, 94, 237)  # RGB 0-255
        
        # Position (uses Position class from core module)
        if Position is not None:
            self._abs_position = Position(0, 0, 0)
        else:
            self._abs_position = None
        
        # Parent properties
        self.parent_body_prop: Optional[object] = None  # OsimBodyProperty
        
        # OpenSim objects
        self.reference_body_object: Optional[object] = None  # opensim.Body
        self._r_offset: Optional[object] = None  # opensim.Vec3
        self._marker: Optional[object] = None  # opensim.Marker
        
        # VTK objects
        self._marker_actor = vtk.vtkActor()
        self._vtk_renderwindow: Optional[object] = None
        self._opace_assembly = vtk.vtkAssembly()
        self.marker_transform = vtk.vtkTransform()
        
        # UI context menu (to be added in Phase 5)
        self._context_menu = None
    
    # Properties - Category: Marker Properties
    
    @property
    def object_name(self) -> str:
        """Get or set the marker name."""
        return self._object_name
    
    @object_name.setter
    def object_name(self, value: str):
        """Set marker name and update OpenSim marker."""
        self._object_name = value
        if self._marker is not None:
            self._marker.setName(value)
    
    @property
    def object_type(self) -> str:
        """Get the object type (read-only)."""
        return self._object_type
    
    @object_type.setter
    def object_type(self, value: str):
        """Set the object type."""
        self._object_type = value
    
    @property
    def is_fixed(self) -> bool:
        """Get or set whether marker is fixed to body."""
        return self._is_fixed
    
    @is_fixed.setter
    def is_fixed(self, value: bool):
        """Set fixed status and update OpenSim marker."""
        self._is_fixed = value
        if self._marker is not None:
            self._marker.setFixed(value)
    
    @property
    def reference_body(self) -> str:
        """Get the reference body name."""
        return self._reference_body
    
    @reference_body.setter
    def reference_body(self, value: str):
        """Set the reference body name."""
        self._reference_body = value
    
    @property
    def marker_color(self) -> Tuple[int, int, int]:
        """Get or set marker color (RGB 0-255)."""
        return self._marker_color
    
    @marker_color.setter
    def marker_color(self, value: Tuple[int, int, int]):
        """Set marker color and update actor."""
        self._marker_color = value
        self._color_r = value[0] / 255.0
        self._color_g = value[1] / 255.0
        self._color_b = value[2] / 255.0
        self.update_marker_color()
    
    @property
    def is_visible(self) -> bool:
        """Get or set marker visibility."""
        return self._is_visible
    
    @is_visible.setter
    def is_visible(self, value: bool):
        """Set visibility and update actor."""
        self._is_visible = value
        self.modify_visible()
    
    @property
    def abs_position(self):
        """Get or set absolute position (ground frame)."""
        return self._abs_position
    
    @abs_position.setter
    def abs_position(self, value):
        """Set absolute position."""
        self._abs_position = value
    
    @property
    def abs_position_text(self) -> str:
        """Get absolute position as text."""
        if self._abs_position is not None:
            return str(self._abs_position)
        return "(0, 0, 0)"
    
    @property
    def abs_position_x(self) -> str:
        """Get X component of absolute position."""
        if self._abs_position is not None:
            return str(self._abs_position.x)
        return "0"
    
    @property
    def abs_position_y(self) -> str:
        """Get Y component of absolute position."""
        if self._abs_position is not None:
            return str(self._abs_position.y)
        return "0"
    
    @property
    def abs_position_z(self) -> str:
        """Get Z component of absolute position."""
        if self._abs_position is not None:
            return str(self._abs_position.z)
        return "0"
    
    @property
    def r_offset_text(self) -> str:
        """Get relative offset as text."""
        if self._r_offset is not None:
            return self._r_offset.toString()
        return "(0, 0, 0)"
    
    @property
    def r_offset(self):
        """Get or set relative offset (body frame)."""
        if self._marker is not None and self._r_offset is not None:
            self._marker.getOffset(self._r_offset)
        return self._r_offset
    
    @r_offset.setter
    def r_offset(self, value):
        """Set relative offset."""
        self._r_offset = value
    
    @property
    def marker(self):
        """Get the OpenSim Marker object."""
        return self._marker
    
    @marker.setter
    def marker(self, value):
        """Set the OpenSim Marker object."""
        self._marker = value
    
    @property
    def marker_actor(self) -> object:
        """Get the VTK actor for the marker."""
        return self._marker_actor
    
    @marker_actor.setter
    def marker_actor(self, value: object):
        """Set the marker actor."""
        self._marker_actor = value
    
    @property
    def context_menu(self):
        """Get the context menu (UI layer)."""
        return self._context_menu
    
    @context_menu.setter
    def context_menu(self, value):
        """Set the context menu."""
        self._context_menu = value
    
    @property
    def color_r(self) -> float:
        """Get red color component (0-1)."""
        return self._color_r
    
    @color_r.setter
    def color_r(self, value: float):
        """Set red component."""
        self._color_r = value
    
    @property
    def color_g(self) -> float:
        """Get green color component (0-1)."""
        return self._color_g
    
    @color_g.setter
    def color_g(self, value: float):
        """Set green component."""
        self._color_g = value
    
    @property
    def color_b(self) -> float:
        """Get blue color component (0-1)."""
        return self._color_b
    
    @color_b.setter
    def color_b(self, value: float):
        """Set blue component."""
        self._color_b = value
    
    @property
    def vtk_renderwindow(self) -> Optional[object]:
        """Get the VTK render window."""
        return self._vtk_renderwindow
    
    @vtk_renderwindow.setter
    def vtk_renderwindow(self, value: object):
        """Set the VTK render window."""
        self._vtk_renderwindow = value
    
    # Methods
    
    def read_marker_properties(self, marker: object) -> None:
        """
        Read properties from an OpenSim Marker.
        
        Extracts marker properties including name, fixed status, reference
        body, offset, and type.
        
        Args:
            marker: An opensim.Marker instance
            
        Example:
            >>> marker_prop = OsimMarkerProperty()
            >>> marker = model.getMarkerSet().get("LASIS")
            >>> marker_prop.read_marker_properties(marker)
        """
        if opensim is None:
            raise ImportError(
                "OpenSim package is required but not installed. "
                "Install with: pip install opensim"
            )
        
        self._marker = marker
        self._object_name = marker.getName()
        self._is_fixed = marker.getFixed()
        self._reference_body = marker.getBody().getName()
        
        # Get offset
        if self._r_offset is None:
            self._r_offset = opensim.Vec3()
        marker.getOffset(self._r_offset)
        
        self._object_type = str(type(marker))
    
    def modify_visible(self) -> None:
        """
        Update actor visibility based on is_visible flag.
        
        Shows or hides the marker actor and enables/disables picking.
        """
        if self._is_visible:
            self.show()
        else:
            self.hide()
    
    def highlight_marker(self) -> None:
        """
        Highlight the marker with green color.
        
        Used for visual feedback during selection or interaction.
        
        Example:
            >>> marker_prop.highlight_marker()
            >>> render_window.Render()
        """
        self._marker_actor.GetProperty().SetColor(0, 0.8, 0.5)
    
    def unhighlight_marker(self) -> None:
        """
        Remove highlighting and restore original color.
        
        Example:
            >>> marker_prop.unhighlight_marker()
            >>> render_window.Render()
        """
        self._marker_actor.GetProperty().SetColor(
            self._color_r, self._color_g, self._color_b
        )
    
    def update_marker_color(self) -> None:
        """
        Update the VTK actor color from current color properties.
        
        Example:
            >>> marker_prop.marker_color = (255, 0, 0)  # Red
        """
        self._marker_actor.GetProperty().SetColor(
            self._color_r, self._color_g, self._color_b
        )
    
    def hide(self) -> None:
        """
        Hide the marker actor.
        
        Sets opacity to 0 and disables picking.
        
        Example:
            >>> marker_prop.hide()
            >>> render_window.Render()
        """
        self._is_visible = False
        self._marker_actor.GetProperty().SetOpacity(0)
        self._marker_actor.PickableOff()
    
    def show(self) -> None:
        """
        Show the marker actor.
        
        Sets opacity to 1 and enables picking.
        
        Example:
            >>> marker_prop.show()
            >>> render_window.Render()
        """
        self._is_visible = True
        self._marker_actor.GetProperty().SetOpacity(1)
        self._marker_actor.PickableOn()
    
    def __repr__(self) -> str:
        """Return string representation of the marker property."""
        return (
            f"OsimMarkerProperty("
            f"name='{self._object_name}', "
            f"body='{self._reference_body}', "
            f"fixed={self._is_fixed}, "
            f"visible={self._is_visible})"
        )
