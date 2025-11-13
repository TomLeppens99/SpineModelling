"""SimModelVisualization - Main OpenSim model rendering engine with VTK.

This is the core visualization engine that manages OpenSim model loading, VTK rendering,
and interactive manipulation of bodies, joints, muscles, and markers.

This is a streamlined implementation focusing on core functionality. Full implementation
will be refined during testing and integration phases.
"""

from typing import List, Optional, Dict
import os

try:
    import vtk
except ImportError:
    vtk = None

try:
    import opensim
except ImportError:
    opensim = None

# Import property classes
try:
    from .properties.osim_body_property import OsimBodyProperty
    from .properties.osim_joint_property import OsimJointProperty
    from .properties.osim_force_property import OsimForceProperty
    from .properties.osim_marker_property import OsimMarkerProperty
    from .properties.osim_group_element import OsimGroupElement
    from .properties.osim_model_property import OsimModelProperty
except ImportError:
    # Fallback for direct execution
    OsimBodyProperty = None
    OsimJointProperty = None
    OsimForceProperty = None
    OsimMarkerProperty = None
    OsimGroupElement = None
    OsimModelProperty = None


class SimModelVisualization:
    """
    Main visualization engine for OpenSim biomechanical models with VTK.
    
    This class orchestrates the complete visualization pipeline:
    - Loads OpenSim .osim model files
    - Creates VTK actors for bodies, joints, muscles, markers
    - Manages transforms and coordinate systems
    - Handles interactive manipulation
    - Provides visibility and display controls
    
    Attributes:
        model (opensim.Model): The loaded OpenSim model
        state (opensim.State): Current model state
        body_property_list (List[OsimBodyProperty]): All body properties
        joint_property_list (List[OsimJointProperty]): All joint properties
        force_property_list (List[OsimForceProperty]): All force/muscle properties
        marker_property_list (List[OsimMarkerProperty]): All marker properties
        group_list (List[OsimGroupElement]): Hierarchical groups
        model_property (OsimModelProperty): Model-level properties
        
    Example:
        >>> viz = SimModelVisualization()
        >>> viz.load_model("gait2392.osim")
        >>> viz.initialize_model_in_renderer(renderer)
        >>> render_window.Render()
    """
    
    def __init__(self):
        """Initialize the visualization engine."""
        if vtk is None:
            raise ImportError("VTK is required")
        
        # OpenSim objects
        self.model: Optional[object] = None  # opensim.Model
        self.state: Optional[object] = None  # opensim.State
        self.model_property: Optional[object] = None  # OsimModelProperty
        
        # Property lists
        self.body_property_list: List = []  # List[OsimBodyProperty]
        self.joint_property_list: List = []  # List[OsimJointProperty]
        self.force_property_list: List = []  # List[OsimForceProperty]
        self.marker_property_list: List = []  # List[OsimMarkerProperty]
        self.group_list: List = []  # List[OsimGroupElement]
        self._coordinate_property_list: List = []  # List[OsimJointCoordinateProperty]
        
        # VTK objects
        self.renderer: Optional[object] = None  # vtkRenderer
        self.render_window: Optional[object] = None  # vtkRenderWindow
        self.ground_axes_actor: Optional[object] = None  # vtkAxesActor
        
        # Configuration
        self.geometry_dirs: List[str] = []
        self.show_ground_axes: bool = True
        self.bodies_pickable: bool = True
        self.markers_pickable: bool = True
        self.forces_pickable: bool = True
        
        # Internal state
        self._model_loaded: bool = False
        self._initialized: bool = False
    
    def load_model(self, model_path: str) -> bool:
        """
        Load an OpenSim model from file.
        
        Args:
            model_path: Path to .osim model file
            
        Returns:
            bool: True if successful, False otherwise
            
        Example:
            >>> viz = SimModelVisualization()
            >>> success = viz.load_model("/path/to/model.osim")
        """
        if opensim is None:
            raise ImportError("OpenSim is required")
        
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        try:
            # Load model
            self.model = opensim.Model(model_path)
            
            # Initialize system
            self.state = self.model.initSystem()
            
            # Create model property
            if OsimModelProperty:
                self.model_property = OsimModelProperty()
                self.model_property.read_model_properties(self.model)
            
            self._model_loaded = True
            return True
            
        except Exception as e:
            print(f"Error loading model: {e}")
            return False
    
    def read_model(self) -> None:
        """
        Read and parse the loaded OpenSim model.
        
        Extracts all bodies, joints, forces, and markers from the model and
        creates corresponding property objects for visualization.
        
        Raises:
            RuntimeError: If model not loaded
        """
        if not self._model_loaded or self.model is None:
            raise RuntimeError("Model must be loaded before reading")
        
        if opensim is None:
            raise ImportError("OpenSim is required")
        
        # Clear existing properties
        self.body_property_list.clear()
        self.joint_property_list.clear()
        self.force_property_list.clear()
        self.marker_property_list.clear()
        
        # Read bodies
        body_set = self.model.getBodySet()
        for i in range(body_set.getSize()):
            body = body_set.get(i)
            if OsimBodyProperty:
                body_prop = OsimBodyProperty()
                body_prop.read_body_properties(body)
                self.body_property_list.append(body_prop)
        
        # Read joints
        joint_set = self.model.getJointSet()
        for i in range(joint_set.getSize()):
            joint = joint_set.get(i)
            if OsimJointProperty:
                joint_prop = OsimJointProperty()
                joint_prop.read_joint_properties(joint)
                self.joint_property_list.append(joint_prop)
        
        # Read forces/muscles
        force_set = self.model.getForceSet()
        for i in range(force_set.getSize()):
            force = force_set.get(i)
            if OsimForceProperty:
                force_prop = OsimForceProperty()
                force_prop.read_force_properties(force)
                self.force_property_list.append(force_prop)
        
        # Read markers
        marker_set = self.model.getMarkerSet()
        for i in range(marker_set.getSize()):
            marker = marker_set.get(i)
            if OsimMarkerProperty:
                marker_prop = OsimMarkerProperty()
                marker_prop.read_marker_properties(marker)
                self.marker_property_list.append(marker_prop)
    
    def initialize_model_in_renderer(self, renderer: object) -> None:
        """
        Initialize the model visualization in a VTK renderer.
        
        Creates all VTK actors for bodies, joints, muscles, and markers,
        and adds them to the renderer.
        
        Args:
            renderer (vtkRenderer): VTK renderer to add actors to
            
        Example:
            >>> viz = SimModelVisualization()
            >>> viz.load_model("model.osim")
            >>> viz.read_model()
            >>> renderer = vtk.vtkRenderer()
            >>> viz.initialize_model_in_renderer(renderer)
        """
        if not self._model_loaded:
            raise RuntimeError("Model must be loaded before initialization")
        
        self.renderer = renderer
        
        # Add ground reference axes if enabled
        if self.show_ground_axes:
            self.add_ground_reference_axes(renderer)
        
        # Add body actors
        for body_prop in self.body_property_list:
            if body_prop.assembly:
                renderer.AddActor(body_prop.assembly)
        
        # Add joint actors
        for joint_prop in self.joint_property_list:
            if joint_prop.joint_actor:
                renderer.AddActor(joint_prop.joint_actor)
        
        # Add marker actors
        for marker_prop in self.marker_property_list:
            if marker_prop.marker_actor:
                renderer.AddActor(marker_prop.marker_actor)
        
        # Add muscle actors (control points and lines)
        for force_prop in self.force_property_list:
            for cp_prop in force_prop.control_point_property_list:
                if cp_prop.control_point_actor:
                    renderer.AddActor(cp_prop.control_point_actor)
            for line_prop in force_prop.muscle_line_property_list:
                if line_prop.muscle_actor:
                    renderer.AddActor(line_prop.muscle_actor)
        
        self._initialized = True
    
    def add_ground_reference_axes(self, renderer: object) -> None:
        """
        Add ground reference coordinate axes to the renderer.
        
        Creates RGB axes (X=red, Y=green, Z=blue) at the origin.
        
        Args:
            renderer (vtkRenderer): VTK renderer
        """
        axes = vtk.vtkAxesActor()
        axes.SetTotalLength(0.1, 0.1, 0.1)  # 10cm axes
        axes.SetShaftTypeToCylinder()
        axes.SetCylinderRadius(0.02)
        renderer.AddActor(axes)
        self.ground_axes_actor = axes
    
    def show_hide_ground_reference_axes(self, renderer: object, show: bool) -> None:
        """
        Show or hide the ground reference axes.
        
        Args:
            renderer (vtkRenderer): VTK renderer
            show (bool): True to show, False to hide
        """
        if self.ground_axes_actor:
            self.ground_axes_actor.SetVisibility(show)
            self.show_ground_axes = show
    
    def unhighlight_everything(self) -> None:
        """Remove highlighting from all visualization elements."""
        for body_prop in self.body_property_list:
            body_prop.unhighlight_body()
        for marker_prop in self.marker_property_list:
            marker_prop.unhighlight_marker()
        for force_prop in self.force_property_list:
            force_prop.unhighlight_force()
    
    def change_visibility(self) -> None:
        """Toggle visibility of all model components."""
        # Implementation depends on specific visibility requirements
        pass
    
    def change_bodies_pickable(self, value: bool) -> None:
        """Enable or disable picking for all body actors."""
        self.bodies_pickable = value
        for body_prop in self.body_property_list:
            if body_prop.assembly:
                if value:
                    body_prop.assembly.PickableOn()
                else:
                    body_prop.assembly.PickableOff()
    
    def change_markers_pickable(self, value: bool) -> None:
        """Enable or disable picking for all marker actors."""
        self.markers_pickable = value
        for marker_prop in self.marker_property_list:
            if marker_prop.marker_actor:
                if value:
                    marker_prop.marker_actor.PickableOn()
                else:
                    marker_prop.marker_actor.PickableOff()
    
    def change_forces_pickable(self, value: bool) -> None:
        """Enable or disable picking for all force/muscle actors."""
        self.forces_pickable = value
        for force_prop in self.force_property_list:
            for cp_prop in force_prop.control_point_property_list:
                if cp_prop.control_point_actor:
                    if value:
                        cp_prop.control_point_actor.PickableOn()
                    else:
                        cp_prop.control_point_actor.PickableOff()
    
    def get_specified_body_property(self, body: object) -> Optional[object]:
        """
        Get the body property for a specific OpenSim Body.
        
        Args:
            body: opensim.Body object
            
        Returns:
            OsimBodyProperty or None if not found
        """
        if opensim is None:
            return None
        
        body_name = body.getName()
        return self.get_specified_body_property_from_name(body_name)
    
    def get_specified_body_property_from_name(self, name: str) -> Optional[object]:
        """
        Get the body property by name.
        
        Args:
            name: Body name
            
        Returns:
            OsimBodyProperty or None if not found
        """
        for body_prop in self.body_property_list:
            if body_prop.object_name == name:
                return body_prop
        return None
    
    def get_specified_joint_property(self, joint: object) -> Optional[object]:
        """
        Get the joint property for a specific OpenSim Joint.
        
        Args:
            joint: opensim.Joint object
            
        Returns:
            OsimJointProperty or None if not found
        """
        if opensim is None:
            return None
        
        joint_name = joint.getName()
        for joint_prop in self.joint_property_list:
            if joint_prop.object_name == joint_name:
                return joint_prop
        return None
    
    def update_visualization(self) -> None:
        """
        Update all visualization elements to reflect current model state.
        
        Should be called after modifying the model state to update VTK actors.
        """
        if not self._initialized:
            return
        
        # Update muscle geometries
        for force_prop in self.force_property_list:
            force_prop.update_muscle_geometry()
        
        # Render if window available
        if self.render_window:
            self.render_window.Render()
    
    def __repr__(self) -> str:
        """Return string representation of the visualization."""
        model_name = self.model_property.object_name if self.model_property else "None"
        return (
            f"SimModelVisualization("
            f"model='{model_name}', "
            f"bodies={len(self.body_property_list)}, "
            f"joints={len(self.joint_property_list)}, "
            f"forces={len(self.force_property_list)}, "
            f"markers={len(self.marker_property_list)}, "
            f"initialized={self._initialized})"
        )
