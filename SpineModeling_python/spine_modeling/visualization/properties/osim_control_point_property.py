"""
Muscle control point property for OpenSim models.

This module provides a property class for muscle path points (origin, insertion,
via points) with VTK sphere visualization and transform management.
"""

from typing import Optional

try:
    import vtk
except ImportError:
    vtk = None

try:
    import opensim
except ImportError:
    opensim = None


class OsimControlPointProperty:
    """
    Property class for muscle control points in OpenSim models.
    
    This class wraps an OpenSim PathPoint (muscle attachment or via point)
    and creates a VTK sphere actor for visualization. It manages the 3D
    position relative to the parent body and provides transform operations
    for coordinate system conversions.
    
    Attributes:
        path_point: OpenSim PathPoint object
        is_origin (bool): True if this is muscle origin
        is_insertion (bool): True if this is muscle insertion
        is_via_point (bool): True if this is a via point
        nb_via_point (int): Number of via points
        cp_number (int): Order number in muscle bundle
        object_name (str): Name of the control point
        body_name (str): Name of the parent SimBody
        X (float): X offset relative to body
        Y (float): Y offset relative to body
        Z (float): Z offset relative to body
        control_point_actor (vtkActor): VTK sphere actor
        control_point_transform (vtkTransform): Transform for positioning
        control_point_actor_radius (float): Sphere radius (default 0.0017)
        osim_force_property: Parent OsimForceProperty
        parent_body_prop: Parent OsimBodyProperty
    
    Example:
        >>> cp_prop = OsimControlPointProperty()
        >>> cp_prop.path_point = muscle.getGeometryPath().getPathPointSet().get(0)
        >>> cp_prop.is_origin = True
        >>> cp_prop.make_control_point_actor()
        >>> renderer.AddActor(cp_prop.control_point_actor)
    """
    
    def __init__(self):
        """Initialize a muscle control point property."""
        if vtk is None:
            raise ImportError(
                "VTK package is required but not installed. "
                "Install with: pip install vtk"
            )
        
        # OpenSim objects
        self.path_point: Optional[object] = None  # opensim.PathPoint
        self.is_origin: bool = False
        self.is_insertion: bool = False
        self.is_via_point: bool = False
        self.nb_via_point: int = 0
        
        # Parent properties
        self.osim_force_property: Optional[object] = None  # OsimForceProperty
        self.parent_body_prop: Optional[object] = None  # OsimBodyProperty
        
        # Internal properties
        self._position: Optional[list] = None
        self._control_point_actor_radius: float = 0.0017
        self._cp_number: int = 0
        self._r_offset: Optional[object] = None  # opensim.Vec3
        
        # VTK objects
        self._vtk_render_window: Optional[object] = None
        self._render_window_image1: Optional[object] = None
        self._render_window_image2: Optional[object] = None
        self.control_point_transform = vtk.vtkTransform()
        self._control_point_actor = vtk.vtkActor()
    
    # Properties - Category: Muscle controlpoint Properties
    
    @property
    def cp_number(self) -> int:
        """Get the order number of control point in muscle bundle."""
        return self._cp_number
    
    @cp_number.setter
    def cp_number(self, value: int):
        """Set the control point number."""
        self._cp_number = value
    
    @property
    def object_name(self) -> str:
        """Get or set the control point name."""
        if self.path_point is None:
            return ""
        return self.path_point.getName()
    
    @object_name.setter
    def object_name(self, value: str):
        """Set the control point name in OpenSim model."""
        if self.path_point is not None:
            self.path_point.setName(value)
    
    @property
    def body_name(self) -> str:
        """Get the parent SimBody name (read-only)."""
        if self.path_point is None:
            return ""
        return self.path_point.getBodyName()
    
    @property
    def X(self) -> float:
        """Get or set X offset relative to body."""
        if self._r_offset is None:
            return 0.0
        return self._r_offset.get(0)
    
    @X.setter
    def X(self, value: float):
        """Set X offset."""
        if self._r_offset is not None:
            self._r_offset.set(0, value)
    
    @property
    def Y(self) -> float:
        """Get or set Y offset relative to body."""
        if self._r_offset is None:
            return 0.0
        return self._r_offset.get(1)
    
    @Y.setter
    def Y(self, value: float):
        """Set Y offset."""
        if self._r_offset is not None:
            self._r_offset.set(1, value)
    
    @property
    def Z(self) -> float:
        """Get or set Z offset relative to body."""
        if self._r_offset is None:
            return 0.0
        return self._r_offset.get(2)
    
    @Z.setter
    def Z(self, value: float):
        """Set Z offset."""
        if self._r_offset is not None:
            self._r_offset.set(2, value)
    
    @property
    def r_offset(self) -> Optional[object]:
        """Get the offset Vec3 (not browsable in UI)."""
        return self._r_offset
    
    @r_offset.setter
    def r_offset(self, value: object):
        """Set the offset Vec3."""
        self._r_offset = value
    
    @property
    def control_point_actor_radius(self) -> float:
        """Get or set the control point actor radius."""
        return self._control_point_actor_radius
    
    @control_point_actor_radius.setter
    def control_point_actor_radius(self, value: float):
        """Set the control point actor radius."""
        self._control_point_actor_radius = value
    
    @property
    def control_point_actor(self) -> object:
        """Get the VTK actor for the control point."""
        return self._control_point_actor
    
    @control_point_actor.setter
    def control_point_actor(self, value: object):
        """Set the control point actor."""
        self._control_point_actor = value
    
    @property
    def position(self) -> list:
        """Get or set the 3D position of the control point."""
        return list(self._control_point_actor.GetPosition())
    
    @position.setter
    def position(self, value: list):
        """Set the 3D position."""
        if len(value) >= 3:
            self._control_point_actor.SetPosition(value[0], value[1], value[2])
    
    def make_control_point_actor(self) -> None:
        """
        Create the VTK sphere actor for the control point.
        
        Creates a sphere source, configures the mapper and actor, and sets
        up the transform. The sphere is colored red and made non-pickable.
        
        Raises:
            ValueError: If path_point is not set
            
        Example:
            >>> cp_prop = OsimControlPointProperty()
            >>> cp_prop.path_point = muscle.getGeometryPath().getPathPointSet().get(0)
            >>> cp_prop.make_control_point_actor()
        """
        if self.path_point is None:
            raise ValueError("path_point must be set before creating actor")
        
        # Get location offset from OpenSim
        self._r_offset = self.path_point.getLocation()
        
        # Create sphere source
        sphere = vtk.vtkSphereSource()
        sphere.SetRadius(self._control_point_actor_radius)
        
        # Create mapper
        sphere_mapper = vtk.vtkPolyDataMapper()
        sphere_mapper.SetInputConnection(sphere.GetOutputPort())
        
        # Get body name (for potential debugging)
        _ = self.path_point.getBody().getName()
        
        # Configure actor
        self._control_point_actor.SetMapper(sphere_mapper)
        self._control_point_actor.PickableOff()
        self._control_point_actor.GetProperty().SetColor(1, 0, 0)  # Red
        self._control_point_actor.SetUserTransform(self.control_point_transform)
    
    def scale_control_point_actor(self, value: float) -> None:
        """
        Scale the control point actor by a factor.
        
        Args:
            value: Scale factor
            
        Example:
            >>> cp_prop.scale_control_point_actor(1.5)  # 50% larger
        """
        self._control_point_actor.SetScale(value)
    
    def get_relative_vtk_transform(
        self,
        child_transform: object,
        parent_transform: object
    ) -> object:
        """
        Compute relative transform between child and parent coordinate systems.
        
        Calculates the transform that represents child_transform in the
        coordinate system of parent_transform.
        
        Args:
            child_transform (vtkTransform): Child coordinate system
            parent_transform (vtkTransform): Parent coordinate system
            
        Returns:
            vtkTransform: Relative transform from parent to child
            
        Example:
            >>> rel_trans = cp_prop.get_relative_vtk_transform(
            ...     cp_prop.control_point_transform,
            ...     cp_prop.parent_body_prop.transform
            ... )
        """
        relative_transform = vtk.vtkTransform()
        child_transform_copy = vtk.vtkTransform()
        child_transform_copy.DeepCopy(child_transform)
        
        # Get inverse of parent transform
        inverse_matrix = vtk.vtkMatrix4x4()
        parent_transform.GetInverse(inverse_matrix)
        
        # Apply inverse to child transform
        child_transform_copy.PostMultiply()
        child_transform_copy.Concatenate(inverse_matrix)
        
        relative_transform = child_transform_copy
        return relative_transform
    
    def update_cp_in_model(self, state: object, transform: object) -> None:
        """
        Update the control point location in the OpenSim model.
        
        Computes the relative position of the control point with respect to
        the parent body and updates the OpenSim PathPoint location. This is
        used when the user interactively moves a control point.
        
        Args:
            state: OpenSim State object
            transform (vtkTransform): New transform (currently unused in logic)
            
        Raises:
            ValueError: If parent_body_prop is not set
            ImportError: If opensim package is not installed
            
        Example:
            >>> cp_prop.update_cp_in_model(model_state, new_transform)
        """
        if opensim is None:
            raise ImportError(
                "OpenSim package is required but not installed. "
                "Install with: pip install opensim"
            )
        
        if self.parent_body_prop is None:
            raise ValueError("parent_body_prop must be set")
        
        # Get relative transform from parent body
        d = self.get_relative_vtk_transform(
            self.control_point_transform,
            self.parent_body_prop.transform
        )
        pos = d.GetPosition()
        
        # Create new location Vec3
        new_loc = opensim.Vec3()
        new_loc.set(0, pos[0])
        new_loc.set(1, pos[1])
        new_loc.set(2, pos[2])
        
        # Update OpenSim model
        self.path_point.setLocation(state, new_loc)
        self.path_point.update(state)
        self.parent_body_prop.body.updateDisplayer(state)
    
    def __repr__(self) -> str:
        """Return string representation of the control point property."""
        point_type = (
            "origin" if self.is_origin
            else "insertion" if self.is_insertion
            else "via_point" if self.is_via_point
            else "unknown"
        )
        return (
            f"OsimControlPointProperty("
            f"name='{self.object_name}', "
            f"body='{self.body_name}', "
            f"type={point_type}, "
            f"pos=[{self.X:.3f}, {self.Y:.3f}, {self.Z:.3f}])"
        )
