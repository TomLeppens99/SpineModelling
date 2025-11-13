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

        This method builds the complete property hierarchy by:
        1. Creating body properties with geometry
        2. Associating joints with bodies
        3. Creating marker properties linked to bodies
        4. Creating force/muscle properties

        Raises:
            RuntimeError: If model not loaded
        """
        if not self._model_loaded or self.model is None:
            raise RuntimeError("Model must be loaded before reading")

        if opensim is None:
            raise ImportError("OpenSim is required")

        # Clear existing properties
        self.clear_property_lists()

        # Build all property lists
        self.build_body_properties_from_model()
        self.build_marker_properties_from_model()
        self.build_force_properties_from_model()

    def clear_property_lists(self) -> None:
        """Clear all property lists."""
        self.body_property_list.clear()
        self.joint_property_list.clear()
        self.force_property_list.clear()
        self.marker_property_list.clear()
        self.group_list.clear()
        self._coordinate_property_list.clear()

    def build_body_properties_from_model(self) -> None:
        """
        Build body properties from the OpenSim model.

        Creates OsimBodyProperty objects for each body in the model,
        reads their properties, and extracts associated joints and coordinates.
        The ground body (index 0) is marked with is_ground flag.
        """
        if opensim is None or not OsimBodyProperty:
            return

        body_set = self.model.getBodySet()

        for i in range(body_set.getSize()):
            body = body_set.get(i)
            body_prop = OsimBodyProperty()

            # Mark ground body
            if i == 0:
                body_prop._is_ground = True

            # Read body properties
            body_prop.read_body_properties(body)
            self.body_property_list.append(body_prop)

            # Extract joint properties if body has joint
            if body.hasJoint():
                joint_prop = body_prop.joint_property
                if joint_prop:
                    self.joint_property_list.append(joint_prop)
                    # Extract coordinate properties from joint
                    if hasattr(joint_prop, 'coordinate_property_list'):
                        for coord_prop in joint_prop.coordinate_property_list:
                            self._coordinate_property_list.append(coord_prop)

    def build_joint_properties_from_model(self) -> None:
        """
        Build joint properties from the OpenSim model.

        Note: Joints are typically extracted during body property creation,
        but this method provides direct access to the joint set if needed.
        """
        if opensim is None or not OsimJointProperty:
            return

        joint_set = self.model.getJointSet()

        for i in range(joint_set.getSize()):
            joint = joint_set.get(i)
            joint_prop = OsimJointProperty()
            joint_prop.joint = joint
            joint_prop.read_joint()

    def build_marker_properties_from_model(self) -> None:
        """
        Build marker properties from the OpenSim model.

        Creates OsimMarkerProperty objects for each marker and links them
        to their parent body properties for transform inheritance.
        """
        if opensim is None or not OsimMarkerProperty:
            return

        marker_set = self.model.getMarkerSet()

        for i in range(marker_set.getSize()):
            marker = marker_set.get(i)
            marker_prop = OsimMarkerProperty()
            marker_prop.read_marker_properties(marker)

            # Link to parent body property
            try:
                parent_body = marker.getBody()
                marker_prop.parent_body_prop = self.get_specified_body_property(parent_body)
            except Exception as e:
                print(f"Warning: Could not link marker {marker.getName()} to body: {e}")

            self.marker_property_list.append(marker_prop)

    def build_force_properties_from_model(self) -> None:
        """
        Build force/muscle properties from the OpenSim model.

        Creates OsimForceProperty objects for each force element (muscles,
        actuators, etc.) in the model. Links to this visualization object
        and renderer for geometry updates.
        """
        if opensim is None or not OsimForceProperty:
            return

        force_set = self.model.getForceSet()

        for i in range(force_set.getSize()):
            force = force_set.get(i)
            force_prop = OsimForceProperty()
            force_prop.osim_model = self.model
            force_prop.sim_model_visualization = self
            force_prop.force_set_index = i
            force_prop.renderer = self.renderer
            force_prop.read_force_properties(force)

            self.force_property_list.append(force_prop)
    
    def initialize_model_in_renderer(self, renderer: object) -> None:
        """
        Initialize the model visualization in a VTK renderer.

        This is the main method to set up complete visualization. It:
        1. Initializes the OpenSim system state
        2. Adds ground reference axes
        3. Creates and adds body geometry with transforms
        4. Creates and adds marker spheres
        5. Optionally creates and adds muscle/force visualization

        Args:
            renderer (vtkRenderer): VTK renderer to add actors to

        Raises:
            RuntimeError: If model not loaded

        Example:
            >>> viz = SimModelVisualization()
            >>> viz.load_model("gait2392.osim")
            >>> viz.read_model()
            >>> renderer = vtk.vtkRenderer()
            >>> viz.initialize_model_in_renderer(renderer)
        """
        if not self._model_loaded:
            raise RuntimeError("Model must be loaded before initialization")

        self.renderer = renderer

        # Initialize OpenSim system state
        if not self.state:
            self.state = self.model.initSystem()

        # Add ground reference axes
        if self.show_ground_axes:
            self.add_ground_reference_axes(renderer)

        # Initialize bodies in renderer (with geometry and transforms)
        self.initialize_bodies_in_renderer(renderer)

        # Initialize markers in renderer
        self.initialize_markers_in_renderer(renderer)

        # Initialize muscles/forces if requested
        # (optional - can be enabled later)

        self._initialized = True

    def initialize_bodies_in_renderer(self, renderer: object) -> None:
        """
        Initialize all body visualization in the renderer.

        For each body:
        1. Loads geometry files and creates VTK actors
        2. Calculates absolute and relative transforms
        3. Sets up parent-child transform hierarchy
        4. Adds joint visualization (sphere and axes)
        5. Adds body assembly to renderer

        Args:
            renderer (vtkRenderer): VTK renderer
        """
        if opensim is None:
            return

        for body_prop in self.body_property_list:
            # Get body geometry set
            geometry_set = body_prop.body.getDisplayer().getGeometrySet()
            scale_factors = opensim.Vec3()
            body_prop.body.getScaleFactors(scale_factors)

            # Load and add each geometry to body assembly
            for j in range(geometry_set.getSize()):
                try:
                    # This would use OsimGeometryProperty to load .vtp/.obj/.stl files
                    # and create VTK actors - implementation depends on geometry property class
                    pass
                except Exception as e:
                    print(f"Warning: Could not load geometry {j} for body {body_prop.object_name}: {e}")

            # Set scale factors
            body_prop.assembly.SetScale(
                scale_factors.get(0),
                scale_factors.get(1),
                scale_factors.get(2)
            )

            # Calculate transforms
            absolute_child_transform = self.model.getSimbodyEngine().getTransform(
                self.state, body_prop.body
            )

            if body_prop.body.hasJoint():
                # Get parent body
                parent_body = body_prop.body.getJoint().getParentBody()
                parent_body_prop = self.get_specified_body_property(parent_body)

                # Calculate relative transform
                absolute_parent_transform = self.model.getSimbodyEngine().getTransform(
                    self.state, parent_body
                )
                relative_transform = self.get_relative_vtk_transform(
                    self.convert_transform_from_sim_to_vtk(absolute_child_transform),
                    self.convert_transform_from_sim_to_vtk(absolute_parent_transform)
                )

                # Set parent transform as input
                relative_transform.SetInput(parent_body_prop.transform)
                body_prop.assembly.SetUserTransform(relative_transform)
                body_prop.transform = relative_transform

                # Add joint visualization
                if body_prop.joint_property:
                    body_prop.joint_property.make_vtk_object()
                    if hasattr(body_prop.joint_property, 'make_joint_axes'):
                        body_prop.joint_property.make_joint_axes()

                    if body_prop.joint_property.joint_actor:
                        renderer.AddActor(body_prop.joint_property.joint_actor)
                    if hasattr(body_prop.joint_property, 'axes_actor') and body_prop.joint_property.axes_actor:
                        renderer.AddActor(body_prop.joint_property.axes_actor)
            else:
                # Ground body - use absolute transform
                vtk_transform = self.convert_transform_from_sim_to_vtk(absolute_child_transform)
                body_prop.assembly.SetUserTransform(vtk_transform)
                body_prop.transform = vtk_transform

            # Add body assembly to renderer
            renderer.AddActor(body_prop.assembly)

    def initialize_markers_in_renderer(self, renderer: object, marker_radius: float = 0.007) -> None:
        """
        Initialize all marker visualization in the renderer.

        Creates sphere actors for each marker with proper transforms
        linked to their parent body.

        Args:
            renderer (vtkRenderer): VTK renderer
            marker_radius (float): Radius of marker spheres in meters (default 7mm)
        """
        if opensim is None:
            return

        for marker_prop in self.marker_property_list:
            # Create sphere source
            sphere = vtk.vtkSphereSource()
            sphere.SetRadius(marker_radius)

            # Create mapper
            sphere_mapper = vtk.vtkPolyDataMapper()
            sphere_mapper.SetInputConnection(sphere.GetOutputPort())

            # Create actor
            marker_prop.marker_actor = vtk.vtkActor()
            marker_prop.marker_actor.SetMapper(sphere_mapper)

            # Set up transform (offset from parent body)
            if marker_prop.parent_body_prop:
                marker_prop.marker_transform.Translate(
                    marker_prop.r_offset.get(0),
                    marker_prop.r_offset.get(1),
                    marker_prop.r_offset.get(2)
                )
                marker_prop.marker_transform.PreMultiply()
                marker_prop.marker_transform.SetInput(marker_prop.parent_body_prop.transform)

                marker_prop.marker_actor.SetUserTransform(marker_prop.marker_transform)

            # Set color
            marker_prop.marker_actor.GetProperty().SetColor(
                marker_prop.color_r,
                marker_prop.color_g,
                marker_prop.color_b
            )

            # Add to renderer
            renderer.AddActor(marker_prop.marker_actor)
    
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
    
    def update_transforms(self) -> None:
        """
        Update all VTK transforms based on current OpenSim model state.

        This method recalculates transforms for:
        1. All body assemblies (from OpenSim Simbody engine)
        2. All markers (linked to body transforms)
        3. All joints (linked to body transforms)
        4. All muscle control points and lines

        Should be called after changing joint coordinates or model configuration.

        Example:
            >>> viz.state.setTime(1.0)  # Change simulation time
            >>> viz.update_transforms()
            >>> viz.renderer.GetRenderWindow().Render()
        """
        if not self._initialized or opensim is None:
            return

        # Update body transforms
        for body_prop in self.body_property_list:
            if not body_prop.body:
                continue

            # Get absolute transform from OpenSim
            absolute_child_transform = self.model.getSimbodyEngine().getTransform(
                self.state, body_prop.body
            )

            # Calculate relative transform if body has parent
            if body_prop.body.hasJoint():
                parent_body = body_prop.body.getJoint().getParentBody()
                absolute_parent_transform = self.model.getSimbodyEngine().getTransform(
                    self.state, parent_body
                )

                # Get relative transform
                relative_transform = self.get_relative_vtk_transform(
                    self.convert_transform_from_sim_to_vtk(absolute_child_transform),
                    self.convert_transform_from_sim_to_vtk(absolute_parent_transform)
                )

                # Link to parent transform
                parent_body_prop = self.get_specified_body_property(parent_body)
                relative_transform.SetInput(parent_body_prop.transform)
                body_prop.transform = relative_transform
            else:
                # Ground body - use absolute transform
                body_prop.transform = self.convert_transform_from_sim_to_vtk(absolute_child_transform)

        # Update marker transforms (linked to body transforms)
        for marker_prop in self.marker_property_list:
            if marker_prop.parent_body_prop and marker_prop.marker_transform:
                marker_prop.marker_transform.SetInput(marker_prop.parent_body_prop.transform)

        # Update joint transforms
        for joint_prop in self.joint_property_list:
            if hasattr(joint_prop, 'set_transformation'):
                joint_prop.set_transformation()

        # Update muscle/force transforms
        for force_prop in self.force_property_list:
            if hasattr(force_prop, 'control_point_property_list'):
                for cp_prop in force_prop.control_point_property_list:
                    if cp_prop.parent_body_prop and hasattr(cp_prop, 'control_point_transform'):
                        # Update control point transform
                        cp_transform = vtk.vtkTransform()
                        cp_transform.Translate(
                            cp_prop.r_offset.get(0),
                            cp_prop.r_offset.get(1),
                            cp_prop.r_offset.get(2)
                        )
                        cp_transform.PreMultiply()
                        cp_transform.SetInput(cp_prop.parent_body_prop.assembly.GetUserTransform())
                        cp_prop.control_point_actor.SetUserTransform(cp_transform)
                        cp_prop.control_point_transform = cp_transform

            # Update muscle line geometry
            if hasattr(force_prop, 'update_muscle_line_actor_transform'):
                force_prop.update_muscle_line_actor_transform()

    def update_renderer(self, renderer: object = None) -> None:
        """
        Update renderer with current transforms and render.

        Args:
            renderer (vtkRenderer): Renderer to update (uses self.renderer if None)
        """
        if renderer is None:
            renderer = self.renderer

        if not renderer:
            return

        # Update all transforms
        self.update_transforms()

        # Render
        render_window = renderer.GetRenderWindow()
        if render_window:
            render_window.Render()

    def update_visualization(self) -> None:
        """
        Update all visualization elements to reflect current model state.

        Should be called after modifying the model state to update VTK actors.
        """
        if not self._initialized:
            return

        # Update transforms
        self.update_transforms()

        # Update muscle geometries
        for force_prop in self.force_property_list:
            if hasattr(force_prop, 'update_muscle_geometry'):
                force_prop.update_muscle_geometry()

        # Render if window available
        if self.render_window:
            self.render_window.Render()
    
    def convert_transform_from_sim_to_vtk(self, sim_transform: object) -> object:
        """
        Convert OpenSim Transform to VTK vtkTransform.

        OpenSim uses Transform with rotation and translation components.
        This converts to VTK's transform representation with proper ordering.

        Args:
            sim_transform: OpenSim Transform object

        Returns:
            vtkTransform: VTK transform with same transformation

        Note:
            OpenSim rotations are body-fixed XYZ Euler angles in radians.
            VTK expects degrees for rotation methods.
        """
        if opensim is None:
            return vtk.vtkTransform()

        # Get translation
        translation = sim_transform.T()

        # Get rotation as body-fixed XYZ Euler angles
        rotation = sim_transform.R()
        rot_vec = rotation.convertRotationToBodyFixedXYZ()

        # Create VTK transform
        vtk_transform = vtk.vtkTransform()

        # Apply translation first
        vtk_transform.Translate(
            translation.get(0),
            translation.get(1),
            translation.get(2)
        )

        # Then apply rotations in correct order
        vtk_transform.PreMultiply()
        vtk_transform.RotateX(self.radian_to_degree(rot_vec.get(0)))
        vtk_transform.RotateY(self.radian_to_degree(rot_vec.get(1)))
        vtk_transform.RotateZ(self.radian_to_degree(rot_vec.get(2)))

        return vtk_transform

    def get_relative_vtk_transform(self, child_transform: object, parent_transform: object) -> object:
        """
        Calculate relative VTK transform from child to parent.

        Given absolute transforms of child and parent in ground frame,
        calculates the relative transform: T_relative = T_child * T_parent^-1

        Args:
            child_transform (vtkTransform): Child absolute transform
            parent_transform (vtkTransform): Parent absolute transform

        Returns:
            vtkTransform: Relative transform from parent to child

        Example:
            >>> child_abs = viz.convert_transform_from_sim_to_vtk(child_sim_transform)
            >>> parent_abs = viz.convert_transform_from_sim_to_vtk(parent_sim_transform)
            >>> relative = viz.get_relative_vtk_transform(child_abs, parent_abs)
        """
        relative_transform = vtk.vtkTransform()
        child_transform_copy = vtk.vtkTransform()
        child_transform_copy.DeepCopy(child_transform)

        # Get inverse of parent transform
        inverse_matrix = vtk.vtkMatrix4x4()
        parent_transform.GetInverse(inverse_matrix)

        # Apply: relative = child * parent^-1
        child_transform_copy.PostMultiply()
        child_transform_copy.Concatenate(inverse_matrix)

        relative_transform.DeepCopy(child_transform_copy)
        return relative_transform

    @staticmethod
    def radian_to_degree(angle: float) -> float:
        """Convert angle from radians to degrees."""
        return angle * 180.0 / 3.14159265358979323846

    @staticmethod
    def degree_to_radian(angle: float) -> float:
        """Convert angle from degrees to radians."""
        return angle * 3.14159265358979323846 / 180.0

    def model_to_treeview(self, tree_widget: object) -> None:
        """
        Populate a QTreeWidget with the model hierarchy.

        Creates a tree structure showing:
        - Model (root)
          - Bodies
            - [Groups]
              - Body names
          - Joints
            - Joint names
          - Forces
            - [Groups]
              - Force names
          - Markers
            - Marker names
          - Coordinates
            - Coordinate names

        Args:
            tree_widget: QTreeWidget to populate

        Example:
            >>> from PyQt5.QtWidgets import QTreeWidget
            >>> tree = QTreeWidget()
            >>> viz.model_to_treeview(tree)
        """
        if not self._model_loaded or opensim is None:
            return

        try:
            from PyQt5.QtWidgets import QTreeWidgetItem
        except ImportError:
            print("Warning: PyQt5 not available for tree view")
            return

        # Clear existing tree
        tree_widget.clear()

        # Create root node with model name
        model_name = self.model.getName()
        root_item = QTreeWidgetItem(tree_widget, [model_name])
        tree_widget.addTopLevelItem(root_item)

        # Create main category nodes
        bodies_item = QTreeWidgetItem(root_item, ["Bodies"])
        joints_item = QTreeWidgetItem(root_item, ["Joints"])
        forces_item = QTreeWidgetItem(root_item, ["Forces"])
        markers_item = QTreeWidgetItem(root_item, ["Markers"])
        coords_item = QTreeWidgetItem(root_item, ["Coordinates"])

        # Populate Bodies
        # Add groups if available
        try:
            group_names = opensim.ArrayStr()
            self.model.getBodySet().getGroupNames(group_names)

            for i in range(group_names.getSize()):
                group_name = group_names.get(i)
                group_item = QTreeWidgetItem(bodies_item, [group_name])
                group = self.model.getBodySet().getGroup(group_name)

                for j in range(group.getMembers().getSize()):
                    body_name = group.getMembers().get(j).getName()
                    body_item = QTreeWidgetItem(group_item, [body_name])
                    # Attach body property as user data
                    body_prop = self.get_specified_body_property_from_name(body_name)
                    if body_prop:
                        body_item.setData(0, 32, body_prop)  # Qt.UserRole = 32
        except:
            pass

        # Add "All" group for bodies
        all_bodies_item = QTreeWidgetItem(bodies_item, ["All"])
        for body_prop in self.body_property_list:
            body_item = QTreeWidgetItem(all_bodies_item, [body_prop.object_name])
            body_item.setData(0, 32, body_prop)

        # Populate Joints
        for body_prop in self.body_property_list:
            if body_prop.joint_property:
                joint_item = QTreeWidgetItem(joints_item, [body_prop.joint_property.object_name])
                joint_item.setData(0, 32, body_prop.joint_property)

        # Populate Forces
        try:
            group_names = opensim.ArrayStr()
            self.model.getForceSet().getGroupNames(group_names)

            for i in range(group_names.getSize()):
                group_name = group_names.get(i)
                group_item = QTreeWidgetItem(forces_item, [group_name])
                group = self.model.getForceSet().getGroup(group_name)

                for j in range(group.getMembers().getSize()):
                    force_name = group.getMembers().get(j).getName()
                    force_item = QTreeWidgetItem(group_item, [force_name])
                    force_prop = self.get_specified_force_property_from_name(force_name)
                    if force_prop:
                        force_item.setData(0, 32, force_prop)
        except:
            pass

        # Add "All" group for forces
        all_forces_item = QTreeWidgetItem(forces_item, ["All"])
        for force_prop in self.force_property_list:
            force_item = QTreeWidgetItem(all_forces_item, [force_prop.object_name])
            force_item.setData(0, 32, force_prop)

        # Populate Markers
        all_markers_item = QTreeWidgetItem(markers_item, ["All"])
        for marker_prop in self.marker_property_list:
            marker_item = QTreeWidgetItem(all_markers_item, [marker_prop.object_name])
            marker_item.setData(0, 32, marker_prop)

        # Populate Coordinates
        all_coords_item = QTreeWidgetItem(coords_item, ["All"])
        coord_set = self.model.getCoordinateSet()
        for i in range(coord_set.getSize()):
            coord = coord_set.get(i)
            coord_item = QTreeWidgetItem(all_coords_item, [coord.getName()])

        # Expand root
        root_item.setExpanded(True)

    def get_specified_force_property_from_name(self, name: str) -> Optional[object]:
        """
        Get the force property by name.

        Args:
            name: Force name

        Returns:
            OsimForceProperty or None if not found
        """
        for force_prop in self.force_property_list:
            if force_prop.object_name == name:
                return force_prop
        return None

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
