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

# Property classes will be imported here as they are translated
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
