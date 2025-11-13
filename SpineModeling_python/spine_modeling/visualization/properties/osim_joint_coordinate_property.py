"""
Joint coordinate property wrapper for OpenSim models.

This module provides a property class that wraps OpenSim Coordinate objects,
exposing joint coordinate properties for display in property grids.
"""

from typing import Optional

try:
    import opensim
except ImportError:
    opensim = None


class OsimJointCoordinateProperty:
    """
    Property wrapper for OpenSim Coordinate objects.
    
    This class encapsulates a joint coordinate (degree of freedom) in an
    OpenSim model, including its name, parent body, range of motion, default
    values, and constraints (clamped, locked).
    
    Attributes:
        object_name (str): Name of the coordinate
        object_type (str): Type of the coordinate object
        parent_body: OpenSim Body that owns this coordinate
        default_value (float): Default coordinate value
        default_speed (float): Default speed value
        range_max (float): Maximum range value
        range_min (float): Minimum range value
        is_clamped (bool): Whether coordinate is clamped to range
        is_locked (bool): Whether coordinate is locked
        coor_number (int): Coordinate number in joint
        coordinate: OpenSim Coordinate object
        axis: Motion axis (Vec3)
    
    Example:
        >>> coord_prop = OsimJointCoordinateProperty()
        >>> coord_prop.coordinate = joint.get_coordinates(0)
        >>> coord_prop.coor_number = 0
        >>> coord_prop.read_joint_coordinate()
        >>> print(f"{coord_prop.object_name}: {coord_prop.default_value}")
    """
    
    def __init__(self):
        """Initialize an empty joint coordinate property."""
        # OpenSim objects
        self._parent_body: Optional[object] = None  # opensim.Body
        self._coordinate: Optional[object] = None  # opensim.Coordinate
        self._axis: Optional[object] = None  # opensim.Vec3
        self._function: Optional[object] = None  # opensim.Function
        
        # System properties
        self._object_name: str = "WorldFrameFixed"
        self._object_type: str = ""
        self._default_speed: float = 0.0
        self._default_value: float = 0.0
        self._range_max: float = 0.0
        self._range_min: float = 0.0
        self._is_clamped: bool = False
        self._is_locked: bool = False
        self._coor_number: int = 0
    
    # Properties - Category: Joint Coordinate Properties
    
    @property
    def object_name(self) -> str:
        """Get the coordinate name (read-only)."""
        return self._object_name
    
    @object_name.setter
    def object_name(self, value: str):
        """Set the coordinate name."""
        self._object_name = value
    
    @property
    def object_type(self) -> str:
        """Get the object type (read-only)."""
        return self._object_type
    
    @object_type.setter
    def object_type(self, value: str):
        """Set the object type."""
        self._object_type = value
    
    @property
    def parent_body(self) -> Optional[object]:
        """Get the parent body (read-only)."""
        return self._parent_body
    
    @parent_body.setter
    def parent_body(self, value: object):
        """Set the parent body."""
        self._parent_body = value
    
    @property
    def default_value(self) -> float:
        """Get the default coordinate value (read-only)."""
        return self._default_value
    
    @default_value.setter
    def default_value(self, value: float):
        """Set the default value."""
        self._default_value = value
    
    @property
    def default_speed(self) -> float:
        """Get the default speed value."""
        return self._default_speed
    
    @default_speed.setter
    def default_speed(self, value: float):
        """Set the default speed."""
        self._default_speed = value
    
    @property
    def range_max(self) -> float:
        """Get the maximum range value."""
        return self._range_max
    
    @range_max.setter
    def range_max(self, value: float):
        """Set the maximum range."""
        self._range_max = value
    
    @property
    def range_min(self) -> float:
        """Get the minimum range value."""
        return self._range_min
    
    @range_min.setter
    def range_min(self, value: float):
        """Set the minimum range."""
        self._range_min = value
    
    @property
    def is_clamped(self) -> bool:
        """Get whether coordinate is clamped."""
        return self._is_clamped
    
    @is_clamped.setter
    def is_clamped(self, value: bool):
        """Set clamped status."""
        self._is_clamped = value
    
    @property
    def is_locked(self) -> bool:
        """Get whether coordinate is locked."""
        return self._is_locked
    
    @is_locked.setter
    def is_locked(self, value: bool):
        """Set locked status."""
        self._is_locked = value
    
    @property
    def coor_number(self) -> int:
        """Get the coordinate number in the joint (read-only)."""
        return self._coor_number
    
    @coor_number.setter
    def coor_number(self, value: int):
        """Set the coordinate number."""
        self._coor_number = value
    
    @property
    def coordinate(self) -> Optional[object]:
        """Get the OpenSim Coordinate object (not browsable in UI)."""
        return self._coordinate
    
    @coordinate.setter
    def coordinate(self, value: object):
        """Set the OpenSim Coordinate object."""
        self._coordinate = value
    
    @property
    def axis(self) -> Optional[object]:
        """Get the motion axis Vec3 (not browsable in UI)."""
        return self._axis
    
    @axis.setter
    def axis(self, value: object):
        """Set the motion axis."""
        self._axis = value
    
    @property
    def function(self) -> Optional[object]:
        """Get the transform function."""
        return self._function
    
    @function.setter
    def function(self, value: object):
        """Set the transform function."""
        self._function = value
    
    def read_joint_coordinate(self) -> None:
        """
        Read properties from the OpenSim Coordinate.
        
        Extracts all relevant properties from the coordinate object including
        name, parent body, type, default values, range, and constraint status.
        
        Raises:
            ImportError: If opensim package is not installed
            ValueError: If coordinate is not set
            
        Example:
            >>> coord_prop = OsimJointCoordinateProperty()
            >>> coord_prop.coordinate = model.getJointSet().get(0).get_coordinates(0)
            >>> coord_prop.coor_number = 0
            >>> coord_prop.read_joint_coordinate()
            >>> print(f"Range: [{coord_prop.range_min}, {coord_prop.range_max}]")
        """
        if opensim is None:
            raise ImportError(
                "OpenSim package is required but not installed. "
                "Install with: pip install opensim"
            )
        
        if self._coordinate is None:
            raise ValueError("Coordinate must be set before reading properties")
        
        self._object_name = self._coordinate.getName()
        self._parent_body = self._coordinate.getJoint().getParentBody()
        self._object_type = str(type(self._coordinate))
        self._default_value = self._coordinate.getDefaultValue()
        self._default_speed = self._coordinate.getDefaultSpeedValue()
        self._range_max = self._coordinate.getRangeMax()
        self._range_min = self._coordinate.getRangeMin()
        self._is_clamped = self._coordinate.get_clamped()
        self._is_locked = self._coordinate.get_locked()
        
        # Note: CustomJoint axis extraction commented out in original C# code
        # This would require additional type checking and casting:
        # if isinstance(self._coordinate.getJoint(), opensim.CustomJoint):
        #     if self._parent_body.toString() != "ground":
        #         cust_joint = self._coordinate.getJoint()
        #         sp_transform = cust_joint.getSpatialTransform()
        #         trans_axis = sp_transform.getTransformAxis(self._coor_number)
        #         self._axis = trans_axis.getAxis()
        #         self._function = trans_axis.getFunction()
    
    def __repr__(self) -> str:
        """Return string representation of the coordinate property."""
        return (
            f"OsimJointCoordinateProperty("
            f"name='{self._object_name}', "
            f"value={self._default_value:.3f}, "
            f"range=[{self._range_min:.3f}, {self._range_max:.3f}], "
            f"clamped={self._is_clamped}, "
            f"locked={self._is_locked})"
        )
