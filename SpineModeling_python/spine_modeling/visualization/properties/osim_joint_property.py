"""OpenSim Joint Property - VTK visualization for joints between bodies."""

from typing import Optional, List

try:
    import vtk
except ImportError:
    vtk = None

try:
    import opensim
except ImportError:
    opensim = None


class OsimJointProperty:
    """Property wrapper for OpenSim Joint with VTK sphere/line visualization."""
    
    def __init__(self):
        if vtk is None:
            raise ImportError("VTK is required")
        
        # System properties
        self._object_name: str = "WorldFrameFixed"
        self._object_type: str = ""
        self._has_joint: bool = False
        
        # Parent properties
        self.osim_body_prop: Optional[object] = None
        self.osim_parent_body_prop: Optional[object] = None
        self.sim_model_visualization: Optional[object] = None
        
        # OpenSim objects
        self._parent_body: Optional[object] = None
        self._child_body: Optional[object] = None
        self._joint: Optional[object] = None
        self._location_in_parent: Optional[object] = None
        self._location_in_child: Optional[object] = None
        self._orientation_in_parent: Optional[object] = None
        self._orientation_in_child: Optional[object] = None
        self.osim_joint_coordinate_property_list: List = []
        
        # VTK objects
        self._vtk_transform = vtk.vtkTransform()
        self._assembly = vtk.vtkAssembly()
        self._joint_actor = vtk.vtkActor()
        self.axes_actor = vtk.vtkActor()
        self.sphere_mapper = vtk.vtkPolyDataMapper()
        self.sphere = vtk.vtkSphereSource()
        self._vtk_renderwindow: Optional[object] = None
        self.renderer: Optional[object] = None
    
    @property
    def object_name(self) -> str:
        return self._object_name
    
    @object_name.setter
    def object_name(self, value: str):
        self._object_name = value
    
    @property
    def joint_actor(self):
        return self._joint_actor
    
    @property
    def joint(self):
        return self._joint
    
    @joint.setter
    def joint(self, value):
        self._joint = value
    
    @property
    def parent_body(self):
        return self._parent_body
    
    @parent_body.setter
    def parent_body(self, value):
        self._parent_body = value
    
    @property
    def child_body(self):
        return self._child_body
    
    @child_body.setter
    def child_body(self, value):
        self._child_body = value
    
    def read_joint_properties(self, joint):
        """Read properties from OpenSim Joint."""
        if opensim is None:
            raise ImportError("OpenSim is required")
        
        self._joint = joint
        self._object_name = joint.getName()
        self._object_type = str(type(joint))
        self._parent_body = joint.getParentBody()
        self._child_body = joint.getBody()
        
        # Get locations and orientations
        self._location_in_parent = opensim.Vec3()
        joint.getLocationInParent(self._location_in_parent)
        
        self._location_in_child = opensim.Vec3()
        joint.getLocationInChild(self._location_in_child)
        
        self._orientation_in_parent = opensim.Vec3()
        joint.getOrientationInParent(self._orientation_in_parent)
        
        self._orientation_in_child = opensim.Vec3()
        joint.getOrientationInChild(self._orientation_in_child)
        
        self._has_joint = True
    
    def make_joint_actor(self, radius: float = 0.005):
        """Create VTK sphere actor for joint visualization."""
        self.sphere.SetRadius(radius)
        self.sphere_mapper.SetInputConnection(self.sphere.GetOutputPort())
        self._joint_actor.SetMapper(self.sphere_mapper)
        self._joint_actor.GetProperty().SetColor(1, 0, 0)  # Red
        self._joint_actor.SetUserTransform(self._vtk_transform)
    
    def __repr__(self) -> str:
        parent_name = self._parent_body.getName() if self._parent_body else "None"
        child_name = self._child_body.getName() if self._child_body else "None"
        return f"OsimJointProperty(name='{self._object_name}', parent='{parent_name}', child='{child_name}')"
