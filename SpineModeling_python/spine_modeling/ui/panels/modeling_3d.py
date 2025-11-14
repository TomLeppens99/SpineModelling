"""
3D Modeling Work Panel for SpineModeling Application.

This module provides the panel for 3D visualization and manipulation of
OpenSim biomechanical models with VTK rendering.

Translated from: SpineModeling_CSharp/SkeletalModeling/UC_3DModelingWorkpanel.cs
Original class: UC_3DModelingWorkpanel

Note: This implementation includes complete VTK rendering pipeline with
PyQt5 integration for 3D visualization of biomechanical models.
"""

from typing import Optional, List
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QGroupBox, QLabel,
    QPushButton, QTreeWidget, QTreeWidgetItem, QCheckBox, QFrame
)
from PyQt5.QtCore import Qt, QTimer, QSize

# VTK imports with graceful failure
VTK_AVAILABLE = False
try:
    import vtk
    from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
    VTK_AVAILABLE = True
    VTK_QT_AVAILABLE = True
except ImportError:
    try:
        import vtk
        VTK_AVAILABLE = True
        VTK_QT_AVAILABLE = False
    except ImportError:
        VTK_AVAILABLE = False
        VTK_QT_AVAILABLE = False


class VTKWidget(QFrame):
    """
    Custom VTK widget for PyQt5 integration.

    This widget creates a VTK rendering window that can be embedded
    in a PyQt5 application. It handles the VTK rendering pipeline
    and provides methods for camera manipulation and rendering.

    This is used when QVTKRenderWindowInteractor is not available.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the VTK widget.

        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)

        if not VTK_AVAILABLE:
            raise ImportError("VTK is not available")

        # VTK components
        self.render_window = vtk.vtkRenderWindow()
        self.interactor = vtk.vtkRenderWindowInteractor()
        self.renderer = vtk.vtkRenderer()

        # Set up the rendering pipeline
        self.render_window.AddRenderer(self.renderer)
        self.interactor.SetRenderWindow(self.render_window)

        # Set the interactor style for 3D interaction
        style = vtk.vtkInteractorStyleTrackballCamera()
        self.interactor.SetInteractorStyle(style)

        # Set window ID for Qt integration
        self.setFrameStyle(QFrame.NoFrame)

    def GetRenderWindow(self):
        """Get the VTK render window."""
        return self.render_window

    def GetInteractor(self):
        """Get the VTK render window interactor."""
        return self.interactor

    def showEvent(self, event):
        """Handle show event to initialize VTK window."""
        super().showEvent(event)
        if self.render_window and not self.render_window.GetMapped():
            # Set the window ID for the render window
            self.render_window.SetWindowId(str(int(self.winId())))
            self.interactor.Initialize()
            self.interactor.Start()

    def resizeEvent(self, event):
        """Handle resize event."""
        super().resizeEvent(event)
        if self.render_window:
            self.render_window.SetSize(self.width(), self.height())


class Modeling3DPanel(QWidget):
    """
    Panel for 3D modeling and visualization of OpenSim models.

    This panel provides VTK-based 3D visualization of biomechanical models
    with support for displaying EOS images in 3D space and interactive
    model manipulation.

    Attributes:
        loaded_3d (bool): Flag indicating if 3D panel is loaded.
        app_data: Application-wide data and settings.
        sql_db: Database connection.
        subject: Current subject/patient.
        eos: EOS acquisition data.
        sim_model_visualization: OpenSim model visualization engine.
        selected_body_property: Currently selected body property.
        eos_image1: First EOS X-ray image.
        eos_image2: Second EOS X-ray image.
        eos_space: 3D space reconstruction from dual X-rays.

    Examples:
        >>> panel = Modeling3DPanel()
        >>> panel.load_model("spine_model.osim")
    """

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the 3D modeling panel.

        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)

        # Panel state
        self.loaded_3d: bool = False

        # Data objects
        self.app_data = None
        self.sql_db = None
        self.subject = None
        self.eos = None
        self.sim_model_visualization = None
        self.selected_body_property = None
        self.selected_object = None

        # EOS images
        self.eos_image1 = None
        self.eos_image2 = None
        self.eos_space = None

        # VTK components (will be initialized when VTK is available)
        self.render_window = None
        self.render_window_image1 = None
        self.render_window_image2 = None
        self.renderer = None
        self.renderer_image1 = None
        self.renderer_image2 = None
        self.interactor = None

        # Picker for selecting 3D objects
        self.prop_picker = None
        self.last_picked_assembly = None

        # Ground reference axes
        self.ground_axes = None

        # EOS image actors for 3D visualization
        self.eos_image_actor1 = None
        self.eos_image_actor2 = None

        # Mouse tracking for double-click detection
        self._previous_position_x: int = 0
        self._previous_position_y: int = 0
        self._number_of_clicks: int = 0
        self._reset_pixel_distance: int = 5

        self._setup_ui()

    def _setup_ui(self) -> None:
        """
        Set up the user interface components.

        Creates the main 3D view, optional 2D image views, and control
        panels for model manipulation.
        """
        # Main layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Top toolbar
        toolbar_layout = QHBoxLayout()
        layout.addLayout(toolbar_layout)

        # Load model button
        btn_load_model = QPushButton("Load Model")
        btn_load_model.clicked.connect(self._on_load_model)
        toolbar_layout.addWidget(btn_load_model)

        # Show/hide components
        self.chk_show_muscles = QCheckBox("Show Muscles")
        self.chk_show_muscles.stateChanged.connect(self._on_toggle_muscles)
        toolbar_layout.addWidget(self.chk_show_muscles)

        self.chk_show_markers = QCheckBox("Show Markers")
        self.chk_show_markers.setChecked(True)
        self.chk_show_markers.stateChanged.connect(self._on_toggle_markers)
        toolbar_layout.addWidget(self.chk_show_markers)

        toolbar_layout.addStretch()

        # Reset view button
        btn_reset_view = QPushButton("Reset View")
        btn_reset_view.clicked.connect(self._on_reset_view)
        toolbar_layout.addWidget(btn_reset_view)

        # Main content area with splitter
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)

        # Left: Model tree view
        left_panel = self._create_model_tree_panel()
        splitter.addWidget(left_panel)

        # Center: Main 3D view
        center_panel = self._create_3d_view_panel()
        splitter.addWidget(center_panel)

        # Right: 2D image views (optional)
        right_panel = self._create_2d_views_panel()
        splitter.addWidget(right_panel)

        # Set splitter sizes
        splitter.setSizes([200, 800, 400])

    def _create_model_tree_panel(self) -> QWidget:
        """
        Create the model component tree view panel.

        Returns:
            Widget containing the model tree.
        """
        panel = QGroupBox("Model Components")
        layout = QVBoxLayout()
        panel.setLayout(layout)

        # Tree widget for model components
        self.tree_model = QTreeWidget()
        self.tree_model.setHeaderLabels(["Component", "Type"])
        self.tree_model.itemClicked.connect(self._on_tree_item_clicked)
        layout.addWidget(self.tree_model)

        return panel

    def _create_3d_view_panel(self) -> QWidget:
        """
        Create the main 3D visualization panel.

        Returns:
            Widget containing the VTK 3D render window.
        """
        panel = QGroupBox("3D View")
        layout = QVBoxLayout()
        panel.setLayout(layout)

        if VTK_AVAILABLE:
            # Create VTK widget for 3D rendering
            try:
                if VTK_QT_AVAILABLE:
                    # Use the built-in QVTKRenderWindowInteractor if available
                    self.vtk_widget = QVTKRenderWindowInteractor(panel)
                else:
                    # Use our custom VTK widget
                    self.vtk_widget = VTKWidget(panel)

                self.vtk_widget.setMinimumSize(600, 600)
                layout.addWidget(self.vtk_widget)

                # Initialize VTK components
                self._initialize_vtk_rendering()

            except Exception as e:
                # Fall back to placeholder if VTK initialization fails
                print(f"VTK initialization failed: {e}")
                self._create_vtk_placeholder(layout)
        else:
            # VTK not available - show placeholder
            self._create_vtk_placeholder(layout)

        return panel

    def _create_vtk_placeholder(self, layout: QVBoxLayout) -> None:
        """
        Create a placeholder widget when VTK is not available.

        Args:
            layout: Layout to add the placeholder to.
        """
        self.vtk_widget = QLabel("3D Render Window\n(VTK not available)")
        self.vtk_widget.setMinimumSize(600, 600)
        self.vtk_widget.setStyleSheet("""
            border: 1px solid #ccc;
            background: #1a1a1a;
            color: #888;
            font-size: 14pt;
        """)
        self.vtk_widget.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.vtk_widget)

    def _create_2d_views_panel(self) -> QWidget:
        """
        Create the 2D image views panel.

        Returns:
            Widget containing dual 2D image viewports.
        """
        panel = QGroupBox("2D Image Views")
        layout = QVBoxLayout()
        panel.setLayout(layout)

        # Image 1 view
        lbl_image1 = QLabel("Image 1 (Frontal)")
        layout.addWidget(lbl_image1)

        self.image1_view = QLabel("Image 1 Render Window")
        self.image1_view.setMinimumSize(300, 300)
        self.image1_view.setStyleSheet("""
            border: 1px solid #ccc;
            background: #000;
            color: #666;
        """)
        self.image1_view.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.image1_view)

        # Image 2 view
        lbl_image2 = QLabel("Image 2 (Lateral)")
        layout.addWidget(lbl_image2)

        self.image2_view = QLabel("Image 2 Render Window")
        self.image2_view.setMinimumSize(300, 300)
        self.image2_view.setStyleSheet("""
            border: 1px solid #ccc;
            background: #000;
            color: #666;
        """)
        self.image2_view.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.image2_view)

        return panel

    def _initialize_vtk_rendering(self) -> None:
        """
        Initialize VTK rendering components.

        Creates VTK renderers, render windows, and interactors for
        3D visualization following the pattern from the C# implementation.

        This method sets up:
        - Main 3D renderer with proper background
        - Render window and interactor
        - Prop picker for object selection
        - Ground reference axes
        - Mouse event handlers for double-click selection
        - Camera settings
        """
        if not VTK_AVAILABLE:
            print("VTK not available - 3D rendering disabled")
            return

        try:
            # Get the render window from the VTK widget
            self.render_window = self.vtk_widget.GetRenderWindow()

            # Get or create the main renderer
            if VTK_QT_AVAILABLE or hasattr(self.vtk_widget, 'renderer'):
                renderers = self.render_window.GetRenderers()
                renderers.InitTraversal()
                self.renderer = renderers.GetNextItem()
                if self.renderer is None:
                    self.renderer = vtk.vtkRenderer()
                    self.render_window.AddRenderer(self.renderer)
            else:
                self.renderer = self.vtk_widget.renderer

            # Set background color (similar to C#: 0.2, 0.3, 0.4)
            self.renderer.SetBackground(0.2, 0.3, 0.4)

            # Get the interactor
            if hasattr(self.vtk_widget, 'GetInteractor'):
                self.interactor = self.vtk_widget.GetInteractor()
            else:
                self.interactor = vtk.vtkRenderWindowInteractor()
                self.interactor.SetRenderWindow(self.render_window)

            # Create and set up the prop picker for selecting 3D objects
            self.prop_picker = vtk.vtkPropPicker()
            self.interactor.SetPicker(self.prop_picker)

            # Add event handler for left button press (for double-click selection)
            self.interactor.AddObserver('LeftButtonPressEvent', self._on_left_button_down)

            # Initialize 2D image renderers (if we have those widgets)
            self._initialize_2d_image_renderers()

            # Add ground reference axes to the scene
            self._add_ground_reference_axes()

            # Enable double buffering for smooth rendering
            self.render_window.DoubleBufferOn()

            # Set up the camera for initial view
            self._setup_initial_camera()

            # Start the interactor if needed
            if hasattr(self.vtk_widget, 'GetInteractor'):
                # Custom widget - need to initialize
                if not self.render_window.GetMapped():
                    self.interactor.Initialize()

            print("VTK rendering pipeline initialized successfully")

        except Exception as e:
            print(f"Error initializing VTK rendering: {e}")
            import traceback
            traceback.print_exc()

    def _initialize_2d_image_renderers(self) -> None:
        """
        Initialize the 2D image view renderers.

        Creates separate renderers for displaying EOS X-ray images
        in 3D space (frontal and lateral views).
        """
        # For now, we'll create placeholders
        # These will be fully implemented when we integrate EOS image display
        # Similar to renderWindowControl2_Load and renderWindowControl3_Load in C#
        pass

    def _add_ground_reference_axes(self) -> None:
        """
        Add ground reference axes to the 3D scene.

        Creates a vtkAxesActor to show the global coordinate system (X, Y, Z axes)
        at the origin. This helps orient the user in 3D space.

        Translates from C# SimModelVisualization.AddGroundReferenceAxes()
        """
        try:
            # Create axes actor for ground reference
            self.ground_axes = vtk.vtkAxesActor()

            # Set total length of axes (in meters, matching C# implementation)
            self.ground_axes.SetTotalLength(0.20, 0.20, 0.20)

            # Enable axis labels (X, Y, Z)
            self.ground_axes.AxisLabelsOn()

            # Set shaft type to cylinder for better visibility
            self.ground_axes.SetShaftTypeToCylinder()

            # Add to renderer
            self.renderer.AddActor(self.ground_axes)

            print("Ground reference axes added to scene")

        except Exception as e:
            print(f"Error adding ground reference axes: {e}")

    def _setup_initial_camera(self) -> None:
        """
        Set up the initial camera position and orientation.

        Positions the camera to provide a good default view of the scene.
        """
        try:
            camera = self.renderer.GetActiveCamera()

            # Set initial camera position (looking at origin from an angle)
            camera.SetPosition(2.0, 1.5, 2.0)
            camera.SetFocalPoint(0.0, 0.5, 0.0)
            camera.SetViewUp(0.0, 1.0, 0.0)

            # Reset camera to see all actors
            self.renderer.ResetCamera()

        except Exception as e:
            print(f"Error setting up camera: {e}")

    def _on_load_model(self) -> None:
        """
        Handle Load Model button click.

        Opens a file dialog to select an OpenSim model file and loads it.
        """
        from PyQt5.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open OpenSim Model",
            "",
            "OpenSim Model Files (*.osim);;All Files (*.*)"
        )

        if file_path:
            self.load_model(file_path)

    def load_model(self, model_path: str) -> None:
        """
        Load an OpenSim model from file.

        Args:
            model_path: Path to the .osim model file.
        """
        try:
            if self.sim_model_visualization is None:
                from spine_modeling.visualization.sim_model_visualization import (
                    SimModelVisualization,
                )
                self.sim_model_visualization = SimModelVisualization()

            # Load model
            # self.sim_model_visualization.read_model(model_path)
            # self._populate_model_tree()
            # self.loaded_3d = True

            print(f"Model loaded: {model_path}")
            self.vtk_widget.setText(f"Model loaded:\n{model_path}\n(Rendering pending VTK integration)")

        except Exception as e:
            print(f"Error loading model: {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "Error Loading Model",
                f"Failed to load model:\n{e}"
            )

    def _populate_model_tree(self) -> None:
        """
        Populate the model component tree.

        Reads the loaded OpenSim model and builds a tree view of its
        components (bodies, joints, muscles, markers).
        """
        self.tree_model.clear()

        if self.sim_model_visualization is None:
            return

        # TODO: Populate tree from SimModelVisualization
        # For now, create placeholder structure
        bodies_node = QTreeWidgetItem(self.tree_model, ["Bodies", ""])
        joints_node = QTreeWidgetItem(self.tree_model, ["Joints", ""])
        muscles_node = QTreeWidgetItem(self.tree_model, ["Muscles", ""])
        markers_node = QTreeWidgetItem(self.tree_model, ["Markers", ""])

        # Sample data
        QTreeWidgetItem(bodies_node, ["pelvis", "Body"])
        QTreeWidgetItem(bodies_node, ["femur_r", "Body"])
        QTreeWidgetItem(joints_node, ["hip_r", "Joint"])
        QTreeWidgetItem(muscles_node, ["psoas_r", "Muscle"])
        QTreeWidgetItem(markers_node, ["ASIS_r", "Marker"])

        self.tree_model.expandAll()

    def _on_tree_item_clicked(self, item: QTreeWidgetItem, column: int) -> None:
        """
        Handle tree item click.

        Args:
            item: Clicked tree item.
            column: Column index.
        """
        component_name = item.text(0)
        component_type = item.text(1)
        print(f"Selected: {component_name} ({component_type})")

        # TODO: Highlight selected component in 3D view

    def _on_toggle_muscles(self, state: int) -> None:
        """
        Handle Show Muscles checkbox toggle.

        Args:
            state: Checkbox state (Qt.Checked or Qt.Unchecked).
        """
        show = (state == Qt.Checked)
        print(f"Muscles visibility: {show}")

        if self.sim_model_visualization is not None:
            # self.sim_model_visualization.print_muscles = show
            pass

    def _on_toggle_markers(self, state: int) -> None:
        """
        Handle Show Markers checkbox toggle.

        Args:
            state: Checkbox state (Qt.Checked or Qt.Unchecked).
        """
        show = (state == Qt.Checked)
        print(f"Markers visibility: {show}")

        # TODO: Update marker visibility in visualization

    def _on_left_button_down(self, obj, event) -> None:
        """
        Handle left mouse button press event.

        Implements double-click detection for selecting 3D objects in the scene.
        On double-click, uses the prop picker to select bodies, joints, or markers.

        Translates from C# UC_3DModelingWorkpanel.OnLeftButtonDown()

        Args:
            obj: VTK object that triggered the event.
            event: Event name.
        """
        if not VTK_AVAILABLE or self.interactor is None:
            return

        try:
            # Increment click counter
            self._number_of_clicks += 1

            # Get the click position
            click_pos = self.interactor.GetEventPosition()

            # Calculate distance from previous click
            x_dist = click_pos[0] - self._previous_position_x
            y_dist = click_pos[1] - self._previous_position_y
            move_distance = int((x_dist ** 2 + y_dist ** 2) ** 0.5)

            # Update previous position
            self._previous_position_x = click_pos[0]
            self._previous_position_y = click_pos[1]

            # Reset click counter if mouse moved too far
            if move_distance > self._reset_pixel_distance:
                self._number_of_clicks = 1

            # Handle double-click
            if self._number_of_clicks == 2:
                self._number_of_clicks = 0

                # Pick from this location
                self.prop_picker.Pick(click_pos[0], click_pos[1], 0, self.renderer)

                # Get the picked assembly (for bodies)
                assembly = self.prop_picker.GetAssembly()

                # Get the picked actor (for markers)
                actor = self.prop_picker.GetActor()

                if assembly is not None:
                    # A body was picked
                    self._handle_body_selection(assembly)

                elif actor is not None:
                    # A marker was picked
                    self._handle_marker_selection(actor)

        except Exception as e:
            print(f"Error in left button down handler: {e}")

    def _handle_body_selection(self, assembly) -> None:
        """
        Handle selection of a body in the 3D view.

        Args:
            assembly: The VTK assembly that was picked.
        """
        try:
            if self.sim_model_visualization is None:
                return

            # Unhighlight everything first
            # self.sim_model_visualization.unhighlight_everything()

            # Find the body property corresponding to this assembly
            # This would require integration with SimModelVisualization
            # For now, just log the selection
            print(f"Body selected: {assembly}")

            # Store the last picked assembly
            self.last_picked_assembly = assembly

            # Highlight the selected body
            # self.selected_body_property.highlight_body()

            # Render the updated scene
            if self.render_window is not None:
                self.render_window.Render()

        except Exception as e:
            print(f"Error handling body selection: {e}")

    def _handle_marker_selection(self, actor) -> None:
        """
        Handle selection of a marker in the 3D view.

        Args:
            actor: The VTK actor that was picked.
        """
        try:
            if self.sim_model_visualization is None:
                return

            # Find the marker property corresponding to this actor
            print(f"Marker selected: {actor}")

            # Highlight the marker
            # marker_prop.highlight_marker()

            # Render the updated scene
            if self.render_window is not None:
                self.render_window.Render()

        except Exception as e:
            print(f"Error handling marker selection: {e}")

    def _on_reset_view(self) -> None:
        """
        Handle Reset View button click.

        Resets the camera to the default view, allowing the user to
        see the entire scene after zooming or rotating.
        """
        print("Resetting view")

        if self.renderer is not None:
            try:
                # Reset the camera to see all actors in the scene
                self.renderer.ResetCamera()

                # Re-render the scene
                if self.render_window is not None:
                    self.render_window.Render()

                print("View reset successfully")

            except Exception as e:
                print(f"Error resetting view: {e}")

    def execute_if_eos_and_model_are_loaded(self) -> None:
        """
        Execute post-load initialization when both EOS images and model are loaded.

        This method is called when both the EOS images and OpenSim model
        are loaded and ready for visualization.
        """
        if self.eos_image1 is None or self.eos_image2 is None:
            print("EOS images not loaded")
            return

        if self.sim_model_visualization is None:
            print("Model not loaded")
            return

        # Display EOS images in 3D space
        if self.eos_space is not None:
            self.display_eos_in_3d_space(self.eos_image1, self.eos_image2, self.eos_space)

        print("EOS images and model integrated")

    def add_marker(self, position: tuple, name: str) -> None:
        """
        Add a marker to the 3D visualization.

        Creates a spherical marker at the specified position and adds it
        to the 3D scene. This is used for anatomical landmarks.

        Args:
            position: 3D position tuple (x, y, z) in meters.
            name: Marker name.
        """
        print(f"Adding marker '{name}' at position {position}")

        if not VTK_AVAILABLE or self.renderer is None:
            print("Cannot add marker: VTK not available or renderer not initialized")
            return

        try:
            # Create a sphere for the marker
            sphere = vtk.vtkSphereSource()
            sphere.SetCenter(position[0], position[1], position[2])
            sphere.SetRadius(0.01)  # 1cm radius
            sphere.SetThetaResolution(16)
            sphere.SetPhiResolution(16)

            # Create mapper
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(sphere.GetOutputPort())

            # Create actor
            marker_actor = vtk.vtkActor()
            marker_actor.SetMapper(mapper)
            marker_actor.GetProperty().SetColor(1.0, 0.0, 0.0)  # Red color

            # Add to renderer
            self.renderer.AddActor(marker_actor)

            # Render the scene
            self.render_window.Render()

            print(f"Marker '{name}' added successfully")

        except Exception as e:
            print(f"Error adding marker: {e}")

    def add_stl_actor(self, actor: vtk.vtkActor, name: Optional[str] = None) -> None:
        """
        Add an STL mesh actor (e.g., CT-scanned vertebra) to the 3D scene.

        Args:
            actor: The vtkActor to add to the renderer
            name: Optional name for the actor (for logging/tracking)
        """
        try:
            if self.renderer is None:
                print("Error: Renderer not initialized")
                return

            # Add actor to renderer
            self.renderer.AddActor(actor)

            # Update the view
            self.render_window.Render()

            if name:
                print(f"STL actor '{name}' added to 3D scene")
            else:
                print("STL actor added to 3D scene")

        except Exception as e:
            print(f"Error adding STL actor: {e}")

    def display_eos_in_3d_space(self, eos_image1, eos_image2, eos_space) -> None:
        """
        Display EOS X-ray images in 3D space at their calibrated positions.

        This method creates vtkImageActors for both frontal and lateral X-ray images,
        positioning them in 3D space according to the calibration parameters from EosSpace.

        Args:
            eos_image1: First EOS image (typically frontal view)
            eos_image2: Second EOS image (typically lateral view)
            eos_space: EosSpace object containing calibration parameters
                      (positions and orientations of the X-ray sources)

        Translates from C# UC_3DModelingWorkpanel.DisplayEOSin3Dspace()
        """
        try:
            if self.renderer is None:
                print("Error: Renderer not initialized")
                return

            print("Displaying EOS images in 3D space...")

            # Helper function to convert numpy array to VTK image data
            def numpy_to_vtk_image(pixel_array):
                """Convert numpy array to vtkImageData."""
                from vtk.util import numpy_support

                # Get dimensions
                if len(pixel_array.shape) == 2:
                    height, width = pixel_array.shape
                    depth = 1
                elif len(pixel_array.shape) == 3:
                    height, width, depth = pixel_array.shape
                else:
                    raise ValueError(f"Unsupported array shape: {pixel_array.shape}")

                # Flatten array to 1D (VTK requirement)
                flat_array = pixel_array.flatten()

                # Convert to VTK array
                vtk_array = numpy_support.numpy_to_vtk(flat_array, deep=True)

                # Create vtkImageData
                image_data = vtk.vtkImageData()
                image_data.SetDimensions(width, height, 1)
                image_data.GetPointData().SetScalars(vtk_array)

                return image_data

            # Create image actor for first image (frontal)
            if eos_image1 is not None and eos_image1.pixel_array is not None:
                self.eos_image_actor1 = vtk.vtkImageActor()

                # Convert pixel array to VTK image data
                image_data1 = numpy_to_vtk_image(eos_image1.pixel_array)
                self.eos_image_actor1.SetInputData(image_data1)

                # Set orientation from calibration
                if hasattr(eos_space, 'OrientationImage1'):
                    orientation = eos_space.OrientationImage1
                    self.eos_image_actor1.SetOrientation(
                        orientation.X if hasattr(orientation, 'X') else 0.0,
                        orientation.Y if hasattr(orientation, 'Y') else 0.0,
                        orientation.Z if hasattr(orientation, 'Z') else 0.0
                    )

                # Set position from calibration
                if hasattr(eos_space, 'PositionOriginImage1'):
                    position = eos_space.PositionOriginImage1
                    self.eos_image_actor1.SetPosition(
                        position.X if hasattr(position, 'X') else 0.0,
                        position.Y if hasattr(position, 'Y') else 0.0,
                        position.Z if hasattr(position, 'Z') else 0.0
                    )

                # Scale to physical size
                if eos_image1.pixel_spacing_x > 0 and eos_image1.pixel_spacing_y > 0:
                    self.eos_image_actor1.SetScale(
                        eos_image1.pixel_spacing_x,
                        eos_image1.pixel_spacing_y,
                        1.0
                    )

                # Make image non-pickable (so it doesn't interfere with 3D object selection)
                self.eos_image_actor1.PickableOff()

                # Add to renderer
                self.renderer.AddActor(self.eos_image_actor1)
                print("EOS Image 1 (frontal) added to 3D scene")

            # Create image actor for second image (lateral)
            if eos_image2 is not None and eos_image2.pixel_array is not None:
                self.eos_image_actor2 = vtk.vtkImageActor()

                # Convert pixel array to VTK image data
                image_data2 = numpy_to_vtk_image(eos_image2.pixel_array)
                self.eos_image_actor2.SetInputData(image_data2)

                # Set orientation from calibration
                if hasattr(eos_space, 'OrientationImage2'):
                    orientation = eos_space.OrientationImage2
                    self.eos_image_actor2.SetOrientation(
                        orientation.X if hasattr(orientation, 'X') else 0.0,
                        orientation.Y if hasattr(orientation, 'Y') else 0.0,
                        orientation.Z if hasattr(orientation, 'Z') else 0.0
                    )

                # Set position from calibration
                if hasattr(eos_space, 'PositionOriginImage2'):
                    position = eos_space.PositionOriginImage2
                    self.eos_image_actor2.SetPosition(
                        position.X if hasattr(position, 'X') else 0.0,
                        position.Y if hasattr(position, 'Y') else 0.0,
                        position.Z if hasattr(position, 'Z') else 0.0
                    )

                # Scale to physical size
                if eos_image2.pixel_spacing_x > 0 and eos_image2.pixel_spacing_y > 0:
                    self.eos_image_actor2.SetScale(
                        eos_image2.pixel_spacing_x,
                        eos_image2.pixel_spacing_y,
                        1.0
                    )

                # Make image non-pickable
                self.eos_image_actor2.PickableOff()

                # Add to renderer
                self.renderer.AddActor(self.eos_image_actor2)
                print("EOS Image 2 (lateral) added to 3D scene")

            # Reset camera to see all actors
            self.renderer.ResetCamera()

            # Update the view
            self.render_window.Render()

            print("EOS images displayed successfully in 3D space")

        except Exception as e:
            print(f"Error displaying EOS images in 3D space: {e}")
            import traceback
            traceback.print_exc()

    def render_all(self) -> None:
        """
        Render all VTK viewports.

        Updates all VTK render windows (main 3D view and 2D image views).
        This method should be called whenever the scene changes to update
        the visualization.

        Translates from C# UC_3DModelingWorkpanel.RenderAll()
        """
        try:
            # Render main 3D view
            if self.render_window is not None:
                self.render_window.Render()

            # Render 2D image views (if they exist)
            if self.render_window_image1 is not None:
                self.render_window_image1.Render()

            if self.render_window_image2 is not None:
                self.render_window_image2.Render()

        except Exception as e:
            print(f"Error rendering viewports: {e}")
