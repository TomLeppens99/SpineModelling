"""
Hierarchical grouping element for OpenSim model components.

This module provides a grouping class that manages collections of body and
force properties, enabling group-level visibility and display operations.
"""

from typing import List, Optional

try:
    import vtk
except ImportError:
    vtk = None


class OsimGroupElement:
    """
    Hierarchical group for managing OpenSim model visualization properties.
    
    This class groups related body and force properties together, allowing
    batch operations on visibility, highlighting, and rendering representation.
    Groups can contain multiple OsimBodyProperty and OsimForceProperty objects.
    
    Attributes:
        group_name (str): Name of the group
        osim_body_property_list (List): List of OsimBodyProperty objects
        osim_force_property_list (List): List of OsimForceProperty objects
        vtk_renderwindow (vtkRenderWindow): VTK render window for rendering
        is_visible (bool): Group visibility status
    
    Example:
        >>> group = OsimGroupElement()
        >>> group.group_name = "Left Leg"
        >>> group.osim_body_property_list.append(femur_prop)
        >>> group.osim_body_property_list.append(tibia_prop)
        >>> group.highlight_body()
    
    Note:
        UI context menu functionality is provided in the UI layer (Phase 5).
        This class focuses on core grouping and visibility management.
    """
    
    def __init__(self):
        """Initialize an empty group element."""
        if vtk is None:
            raise ImportError(
                "VTK package is required but not installed. "
                "Install with: pip install vtk"
            )
        
        self._is_visible: bool = True
        self._group_name: str = ""
        self._vtk_renderwindow: Optional[object] = None  # vtkRenderWindow
        self._osim_body_property_list: List = []  # List[OsimBodyProperty]
        self._osim_force_property_list: List = []  # List[OsimForceProperty]
        
        # UI context menu will be added in Phase 5 (PyQt5 QMenu)
        self._context_menu = None
    
    @property
    def group_name(self) -> str:
        """Get or set the group name."""
        return self._group_name
    
    @group_name.setter
    def group_name(self, value: str):
        """Set the group name."""
        self._group_name = value
    
    @property
    def is_visible(self) -> bool:
        """Get the group visibility status."""
        return self._is_visible
    
    @is_visible.setter
    def is_visible(self, value: bool):
        """Set the group visibility status."""
        self._is_visible = value
    
    @property
    def context_menu(self):
        """Get the context menu (UI layer, Phase 5)."""
        return self._context_menu
    
    @context_menu.setter
    def context_menu(self, value):
        """Set the context menu."""
        self._context_menu = value
    
    @property
    def osim_body_property_list(self) -> List:
        """Get the list of body properties in this group."""
        return self._osim_body_property_list
    
    @osim_body_property_list.setter
    def osim_body_property_list(self, value: List):
        """Set the body property list."""
        self._osim_body_property_list = value
    
    @property
    def osim_force_property_list(self) -> List:
        """Get the list of force properties in this group."""
        return self._osim_force_property_list
    
    @osim_force_property_list.setter
    def osim_force_property_list(self, value: List):
        """Set the force property list."""
        self._osim_force_property_list = value
    
    @property
    def vtk_renderwindow(self) -> Optional[object]:
        """Get the VTK render window."""
        return self._vtk_renderwindow
    
    @vtk_renderwindow.setter
    def vtk_renderwindow(self, value: object):
        """Set the VTK render window."""
        self._vtk_renderwindow = value
    
    # Methods for group operations
    
    def highlight_body(self) -> None:
        """
        Highlight all bodies in this group.
        
        Iterates through all body properties and applies highlighting.
        Useful for visual feedback during selection or interaction.
        
        Example:
            >>> group.highlight_body()
            >>> render_window.Render()
        """
        for body_prop in self._osim_body_property_list:
            body_prop.vtk_renderwindow = self.vtk_renderwindow
            body_prop.highlight_body()
    
    def unhighlight_body(self) -> None:
        """
        Remove highlighting from all bodies in this group.
        
        Iterates through all body properties and removes highlighting.
        
        Example:
            >>> group.unhighlight_body()
            >>> render_window.Render()
        """
        for body_prop in self._osim_body_property_list:
            body_prop.vtk_renderwindow = self.vtk_renderwindow
            body_prop.unhighlight_body()
    
    def hide(self) -> None:
        """
        Hide all bodies in this group.
        
        Makes all body properties in the group invisible.
        
        Example:
            >>> group.hide()
            >>> render_window.Render()
        """
        for body_prop in self._osim_body_property_list:
            body_prop.vtk_renderwindow = self.vtk_renderwindow
            body_prop.hide_programmatically()
        self._is_visible = False
    
    def show(self) -> None:
        """
        Show all bodies in this group.
        
        Makes all body properties in the group visible.
        
        Example:
            >>> group.show()
            >>> render_window.Render()
        """
        for body_prop in self._osim_body_property_list:
            body_prop.vtk_renderwindow = self.vtk_renderwindow
            body_prop.show_programmatically()
        self._is_visible = True
    
    def show_only(self) -> None:
        """
        Show only this group (hide all others).
        
        This would typically be coordinated by the parent visualization
        manager that has access to all groups.
        
        Example:
            >>> group.show_only()
            >>> render_window.Render()
        """
        for body_prop in self._osim_body_property_list:
            body_prop.vtk_renderwindow = self.vtk_renderwindow
            body_prop.show_only_programmatically()
        self._is_visible = True
    
    def toggle_transparent(self) -> None:
        """
        Toggle transparency for all bodies in group.
        
        Switches between opaque and transparent rendering for
        bodies in the group.
        
        Example:
            >>> group.toggle_transparent()
            >>> render_window.Render()
        """
        for body_prop in self._osim_body_property_list:
            body_prop.show_hide_transparent_programmatically()
    
    def set_point_representation(self) -> None:
        """
        Set point representation for all bodies in group.
        
        Changes rendering mode to point cloud representation.
        
        Example:
            >>> group.set_point_representation()
            >>> render_window.Render()
        """
        for body_prop in self._osim_body_property_list:
            body_prop.vtk_renderwindow = self.vtk_renderwindow
            body_prop.point_represent_programmatically()
    
    def set_smooth_shaded(self) -> None:
        """
        Set smooth shaded representation for all bodies in group.
        
        Changes rendering mode to smooth shading (default).
        
        Example:
            >>> group.set_smooth_shaded()
            >>> render_window.Render()
        """
        for body_prop in self._osim_body_property_list:
            body_prop.vtk_renderwindow = self.vtk_renderwindow
            body_prop.smooth_shaded_programatically()
    
    def set_wireframe(self) -> None:
        """
        Set wireframe representation for all bodies in group.
        
        Changes rendering mode to wireframe.
        
        Example:
            >>> group.set_wireframe()
            >>> render_window.Render()
        """
        for body_prop in self._osim_body_property_list:
            body_prop.vtk_renderwindow = self.vtk_renderwindow
            body_prop.wireframe_programatically()
    
    def __repr__(self) -> str:
        """Return string representation of the group."""
        return (
            f"OsimGroupElement("
            f"name='{self._group_name}', "
            f"bodies={len(self._osim_body_property_list)}, "
            f"forces={len(self._osim_force_property_list)}, "
            f"visible={self._is_visible})"
        )
    
    def __len__(self) -> int:
        """Return total number of properties in group."""
        return len(self._osim_body_property_list) + len(self._osim_force_property_list)
