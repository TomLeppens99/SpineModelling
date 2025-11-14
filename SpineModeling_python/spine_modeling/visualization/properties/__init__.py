"""
Property classes for OpenSim model visualization with VTK.

This package contains property classes that encapsulate OpenSim objects (bodies,
joints, muscles, markers, etc.) with VTK visualization actors. Each property class
manages both the OpenSim biomechanical model component and its corresponding VTK
rendering representation.

Classes:
    OsimModelProperty: Model-level properties and settings
    OsimBodyProperty: Body visualization with VTK actors
    OsimJointProperty: Joint visualization with lines
    OsimForceProperty: Muscle/force visualization
    OsimGeometryProperty: Geometry shapes (spheres, cylinders, etc.)
    OsimMarkerProperty: Marker sphere visualization
    OsimControlPointProperty: Muscle control point visualization
    OsimJointCoordinateProperty: Joint coordinate visualization
    OsimMuscleActuatorLineProperty: Muscle line rendering
    OsimGroupElement: Hierarchical grouping for model elements
"""

from .osim_model_property import OsimModelProperty
from .osim_body_property import OsimBodyProperty
from .osim_joint_property import OsimJointProperty
from .osim_force_property import OsimForceProperty
from .osim_geometry_property import OsimGeometryProperty
from .osim_marker_property import OsimMarkerProperty
from .osim_control_point_property import OsimControlPointProperty
from .osim_joint_coordinate_property import OsimJointCoordinateProperty
from .osim_muscle_actuator_line_property import OsimMuscleActuatorLineProperty
from .osim_group_element import OsimGroupElement

__all__ = [
    "OsimModelProperty",
    "OsimBodyProperty",
    "OsimJointProperty",
    "OsimForceProperty",
    "OsimGeometryProperty",
    "OsimMarkerProperty",
    "OsimControlPointProperty",
    "OsimJointCoordinateProperty",
    "OsimMuscleActuatorLineProperty",
    "OsimGroupElement",
]
