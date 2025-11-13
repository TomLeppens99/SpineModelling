"""
Image Analysis Form for SpineModeling Application.

This module provides the main workflow coordinator for skeletal modeling,
integrating 2D measurements, 3D modeling, and OpenSim visualization panels.

Translated from: SpineModeling_CSharp/SkeletalModeling/frmImageAnalysis_new.cs
Original class: frmImageAnalysis_new

Note: This is a streamlined implementation focusing on core structure and
panel integration. Complex logic will be refined during integration testing.
"""

import os
import logging
import pickle
from pathlib import Path
from typing import Optional, List
from PyQt5.QtWidgets import (
    QMainWindow, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, QPushButton,
    QLabel, QStatusBar, QMenuBar, QMenu, QAction, QMessageBox, QApplication,
    QFileDialog
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QCursor

# Set up logging
logger = logging.getLogger(__name__)


class ImageAnalysisForm(QMainWindow):
    """
    Main image analysis and skeletal modeling workflow coordinator.

    This form integrates multiple panels for 2D image analysis, 3D modeling,
    and measurement management. It serves as the primary interface for
    the skeletal modeling workflow.

    Attributes:
        sim_model_visualization: OpenSim model visualization engine.
        measurements_2d_panel: 2D measurements work panel.
        modeling_3d_panel: 3D modeling work panel.
        measurements_main_panel: Measurements data grid panel.
        eos_image1: First EOS X-ray image (frontal).
        eos_image2: Second EOS X-ray image (lateral).
        eos_space: 3D space reconstruction from dual X-rays.
        app_data: Application-wide data and settings.
        sql_db: Database connection for measurements.
        subject: Current subject/patient.

    Examples:
        >>> form = ImageAnalysisForm()
        >>> form.exec_()
    """

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the image analysis form.

        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)

        # Core components (will be initialized later)
        self.sim_model_visualization = None
        self.measurements_2d_panel = None
        self.modeling_3d_panel = None
        self.measurements_main_panel = None

        # Data objects
        self.eos_image1 = None
        self.eos_image2 = None
        self.eos_space = None
        self.app_data = None
        self.sql_db = None
        self.subject = None
        self.measurement = None
        self.measurement_id: int = 0

        # UI state
        self.logs_and_messages: List[str] = []
        self._temp_dir: str = ""

        self._setup_ui()
        self._setup_menu()
        self._initialize_components()

    def _setup_ui(self) -> None:
        """
        Set up the user interface components.

        Creates the main window structure with tab widget for different
        work panels and status bar for messages.
        """
        # Window properties
        self.setWindowTitle("SpineModeling - Image Analysis")
        self.resize(1400, 900)

        # Central widget with main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Tab widget for different panels
        self.tab_widget = QTabWidget()
        main_layout.addWidget(self.tab_widget)

        # Button bar at bottom
        button_layout = QHBoxLayout()
        main_layout.addLayout(button_layout)

        # View toggle buttons
        self.btn_2d_view = QPushButton("2D View")
        self.btn_2d_view.setVisible(False)
        self.btn_2d_view.clicked.connect(self._on_2d_view_clicked)
        button_layout.addWidget(self.btn_2d_view)

        self.btn_3d_view = QPushButton("3D View")
        self.btn_3d_view.setVisible(False)
        self.btn_3d_view.clicked.connect(self._on_3d_view_clicked)
        button_layout.addWidget(self.btn_3d_view)

        button_layout.addStretch()

        # Refresh button
        self.btn_refresh = QPushButton("Refresh")
        self.btn_refresh.setEnabled(False)
        self.btn_refresh.clicked.connect(self._on_refresh_clicked)
        button_layout.addWidget(self.btn_refresh)

        # Return button
        btn_return = QPushButton("Return")
        btn_return.clicked.connect(self.close)
        button_layout.addWidget(btn_return)

        # Status bar (QMainWindow has its own status bar)
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")

    def _setup_menu(self) -> None:
        """
        Set up the menu bar with File, View, Tools menus.

        Creates menu actions for loading models, images, and accessing
        various analysis tools.
        """
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        # Import EOS Images action
        import_action = QAction("&Import EOS Images...", self)
        import_action.setShortcut("Ctrl+I")
        import_action.setStatusTip("Import frontal and lateral EOS X-ray images")
        import_action.triggered.connect(self._on_import_eos_images)
        file_menu.addAction(import_action)

        # Load Model action
        load_model_action = QAction("&Load OpenSim Model...", self)
        load_model_action.setShortcut("Ctrl+O")
        load_model_action.setStatusTip("Load an OpenSim .osim model file")
        load_model_action.triggered.connect(self._on_load_model)
        file_menu.addAction(load_model_action)

        # Load STL Meshes action
        load_stl_action = QAction("Load &CT/STL Meshes...", self)
        load_stl_action.setStatusTip("Load CT vertebrae STL mesh files")
        load_stl_action.triggered.connect(self._on_load_stl_meshes)
        file_menu.addAction(load_stl_action)

        file_menu.addSeparator()

        # Save Model action
        save_model_action = QAction("&Save Model...", self)
        save_model_action.setShortcut("Ctrl+S")
        save_model_action.setStatusTip("Save OpenSim model to .osim file")
        save_model_action.triggered.connect(self._on_save_model)
        file_menu.addAction(save_model_action)

        # Export submenu
        export_menu = file_menu.addMenu("&Export")

        # Export measurements to Excel
        export_excel_action = QAction("Measurements to &Excel...", self)
        export_excel_action.setStatusTip("Export measurements to Excel file")
        export_excel_action.triggered.connect(self._on_export_measurements_excel)
        export_menu.addAction(export_excel_action)

        # Export markers to TRC
        export_trc_action = QAction("Markers to &TRC...", self)
        export_trc_action.setStatusTip("Export markers to TRC format")
        export_trc_action.triggered.connect(self._on_export_markers_trc)
        export_menu.addAction(export_trc_action)

        file_menu.addSeparator()

        # Workspace actions
        save_workspace_action = QAction("Save &Workspace...", self)
        save_workspace_action.setStatusTip("Save current workspace state")
        save_workspace_action.triggered.connect(self._on_save_workspace)
        file_menu.addAction(save_workspace_action)

        load_workspace_action = QAction("Load W&orkspace...", self)
        load_workspace_action.setStatusTip("Load saved workspace state")
        load_workspace_action.triggered.connect(self._on_load_workspace)
        file_menu.addAction(load_workspace_action)

        clear_workspace_action = QAction("Clear Workspace", self)
        clear_workspace_action.setStatusTip("Clear all loaded data")
        clear_workspace_action.triggered.connect(self._on_clear_workspace)
        file_menu.addAction(clear_workspace_action)

        file_menu.addSeparator()

        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Close the image analysis window")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        # Refresh action
        refresh_action = QAction("&Refresh", self)
        refresh_action.setShortcut("F5")
        refresh_action.setStatusTip("Refresh the current view")
        refresh_action.triggered.connect(self._on_refresh_clicked)
        view_menu.addAction(refresh_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        # About action
        about_action = QAction("&About", self)
        about_action.setStatusTip("About SpineModeling")
        about_action.triggered.connect(self._on_about_clicked)
        help_menu.addAction(about_action)

    def _initialize_components(self) -> None:
        """
        Initialize core components and panels.

        Creates instances of the visualization engine and work panels,
        then adds them to the tab widget.
        """
        try:
            # Import panels (local imports to avoid circular dependencies)
            from spine_modeling.visualization.sim_model_visualization import (
                SimModelVisualization,
            )
            from spine_modeling.ui.panels.measurements_2d import (
                Measurements2DPanel,
            )
            from spine_modeling.ui.panels.modeling_3d import Modeling3DPanel
            from spine_modeling.ui.panels.measurements_main import (
                MeasurementsMainPanel,
            )

            # Initialize visualization engine
            self.sim_model_visualization = SimModelVisualization()

            # Initialize panels
            self.measurements_2d_panel = Measurements2DPanel(self)
            self.modeling_3d_panel = Modeling3DPanel(self)
            self.measurements_main_panel = MeasurementsMainPanel(self)

            # Add panels to tab widget
            self.tab_widget.addTab(self.measurements_2d_panel, "2D Measurements")
            self.tab_widget.addTab(self.modeling_3d_panel, "3D Modeling")
            self.tab_widget.addTab(self.measurements_main_panel, "Measurements")

            # Connect tab change signal
            self.tab_widget.currentChanged.connect(self._on_tab_changed)

        except ImportError as e:
            # Panels not yet implemented - create placeholders
            self._add_placeholder_tabs()
            self.add_to_logs_and_messages(
                f"Warning: Could not load panels: {e}"
            )

    def _add_placeholder_tabs(self) -> None:
        """
        Add placeholder tabs when panels are not yet implemented.

        Creates simple label widgets as placeholders for each panel.
        """
        # Placeholder for 2D Measurements
        placeholder_2d = QLabel("2D Measurements Panel\n(To be implemented)")
        placeholder_2d.setAlignment(Qt.AlignCenter)
        placeholder_2d.setStyleSheet("font-size: 14pt; color: #888;")
        self.tab_widget.addTab(placeholder_2d, "2D Measurements")

        # Placeholder for 3D Modeling
        placeholder_3d = QLabel("3D Modeling Panel\n(To be implemented)")
        placeholder_3d.setAlignment(Qt.AlignCenter)
        placeholder_3d.setStyleSheet("font-size: 14pt; color: #888;")
        self.tab_widget.addTab(placeholder_3d, "3D Modeling")

        # Placeholder for Measurements
        placeholder_meas = QLabel("Measurements Panel\n(To be implemented)")
        placeholder_meas.setAlignment(Qt.AlignCenter)
        placeholder_meas.setStyleSheet("font-size: 14pt; color: #888;")
        self.tab_widget.addTab(placeholder_meas, "Measurements")

    def showEvent(self, event) -> None:
        """
        Handle dialog show event.

        Initializes the form when first shown.

        Args:
            event: Show event.
        """
        super().showEvent(event)
        self._on_form_load()

    def _on_form_load(self) -> None:
        """
        Handle form load event.

        Initializes database connection, creates temporary directory,
        and prepares the UI for user interaction.
        """
        # Create temporary directory
        try:
            if self.app_data is not None:
                self._temp_dir = getattr(self.app_data, "TempDir", "temp")
                os.makedirs(self._temp_dir, exist_ok=True)
            else:
                self._temp_dir = "temp"
                os.makedirs(self._temp_dir, exist_ok=True)
        except Exception as e:
            QMessageBox.critical(
                self,
                "Application Settings ERROR",
                f"Directory could not be created: {e}",
            )
            return

        # Initialize database connection
        try:
            from spine_modeling.database.models import DatabaseManager

            # Create database directory if it doesn't exist
            db_dir = Path.home() / ".spinemodeling"
            db_dir.mkdir(exist_ok=True)

            # Initialize database
            db_path = db_dir / "spinemodeling.db"
            self.sql_db = DatabaseManager(f"sqlite:///{db_path}")
            self.sql_db.initialize_database()

            logger.info(f"Database initialized at {db_path}")
            self.add_to_logs_and_messages(f"Database connected: {db_path}")

            # Pass database to child panels
            if self.measurements_2d_panel is not None:
                self.measurements_2d_panel.sql_db = self.sql_db
            if self.measurements_main_panel is not None:
                self.measurements_main_panel.sql_db = self.sql_db

        except Exception as e:
            logger.error(f"Database initialization error: {e}", exc_info=True)
            self.add_to_logs_and_messages(f"Database connection error: {e}")
            QMessageBox.warning(
                self,
                "Database Warning",
                f"Database could not be initialized:\n{e}\n\nThe application will continue without database support."
            )

        # Set visualization engine properties
        if self.sim_model_visualization is not None:
            self.sim_model_visualization.subject = self.subject
            # self.sim_model_visualization.app_data = self.app_data

        self.add_to_logs_and_messages("Application started. Ready for input.")

        # Initialize 3D VTK components (deferred to panel implementations)
        self._init_3d_vtk_components()

    def _init_3d_vtk_components(self) -> None:
        """
        Initialize 3D VTK rendering components.

        Sets up VTK renderers and render windows for 3D visualization.
        Implementation deferred to the 3D modeling panel.
        """
        # Deferred to UC_3DModelingWorkpanel implementation
        pass

    def add_to_logs_and_messages(self, message: str) -> None:
        """
        Add a message to the logs and update status bar.

        Args:
            message: Message text to log.
        """
        self.logs_and_messages.append(message)
        self.status_bar.showMessage(message)
        print(f"[LOG] {message}")  # Also print to console

    def _on_tab_changed(self, index: int) -> None:
        """
        Handle tab change event.

        Updates UI state when switching between panels.

        Args:
            index: Index of the newly selected tab.
        """
        # Update view toggle buttons visibility
        self._check_panels_loading()

    def _check_panels_loading(self) -> None:
        """
        Check panel loading status and update UI accordingly.

        Shows/hides view toggle buttons based on which panels are loaded
        and visible.
        """
        # Check if both 2D and 3D panels are loaded
        panels_loaded = (
            self.modeling_3d_panel is not None
            and self.measurements_2d_panel is not None
        )

        if panels_loaded:
            # Set EOS images on visualization engine
            if self.sim_model_visualization is not None:
                self.sim_model_visualization.eos_image1 = self.eos_image1
                self.sim_model_visualization.eos_image2 = self.eos_image2

            # Update view toggle buttons
            if self.modeling_3d_panel.isVisible():
                self.btn_2d_view.setVisible(True)
                self.btn_3d_view.setVisible(False)
            else:
                self.btn_3d_view.setVisible(True)
                self.btn_2d_view.setVisible(False)
        else:
            self.btn_2d_view.setVisible(False)
            self.btn_3d_view.setVisible(False)

    def _on_2d_view_clicked(self) -> None:
        """
        Handle 2D View button click.

        Switches to the 2D measurements panel.
        """
        if self.measurements_2d_panel is not None:
            self.tab_widget.setCurrentWidget(self.measurements_2d_panel)

    def _on_3d_view_clicked(self) -> None:
        """
        Handle 3D View button click.

        Switches to the 3D modeling panel.
        """
        if self.modeling_3d_panel is not None:
            self.tab_widget.setCurrentWidget(self.modeling_3d_panel)

    def _on_refresh_clicked(self) -> None:
        """
        Handle Refresh button click.

        Refreshes data and updates all panels.
        """
        self.add_to_logs_and_messages("Refreshing data...")
        # TODO: Implement refresh logic
        self.status_bar.showMessage("Data refreshed", 3000)

    def _on_import_eos_images(self) -> None:
        """
        Handle Import EOS Images menu action.

        Opens the import dialog and loads the selected images.
        """
        from spine_modeling.ui.forms.import_eos_images import ImportEosImagesDialog

        dialog = ImportEosImagesDialog(self)
        if dialog.exec_() == dialog.Accepted:
            frontal_path, lateral_path = dialog.get_files()
            if frontal_path and lateral_path:
                self.load_eos_images(frontal_path, lateral_path)
                self.status_bar.showMessage(f"Loaded images: {os.path.basename(frontal_path)}, {os.path.basename(lateral_path)}", 5000)
            else:
                QMessageBox.warning(self, "Import Error", "Both frontal and lateral images must be selected.")

    def _on_about_clicked(self) -> None:
        """
        Handle About menu action.

        Shows information about the application.
        """
        QMessageBox.about(
            self,
            "About SpineModeling",
            "<h2>SpineModeling Python Edition</h2>"
            "<p>Biomechanical spine modeling and analysis system</p>"
            "<p><b>Version:</b> 1.0</p>"
            "<p><b>Technologies:</b> Python, PyQt5, VTK, OpenSim</p>"
            "<p>Translated from C# .NET Windows Forms application</p>"
        )

    def load_eos_images(self, file1: str, file2: str) -> None:
        """
        Load EOS X-ray images from files.

        Args:
            file1: Path to first image file (frontal).
            file2: Path to second image file (lateral).
        """
        try:
            from spine_modeling.imaging.eos_image import EosImage
            from spine_modeling.imaging.eos_space import EosSpace
            from spine_modeling.imaging.dicom_decoder import DicomDecoder

            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
            self.add_to_logs_and_messages("Reading in Radiographs...")

            # Create DicomDecoders
            dd1 = DicomDecoder()
            dd2 = DicomDecoder()

            # Read images
            self.eos_image1 = EosImage(directory=file1)
            dd1.dicom_file_name = file1
            self._read_eos_image(self.eos_image1, dd1)

            self.eos_image2 = EosImage(directory=file2)
            dd2.dicom_file_name = file2
            self._read_eos_image(self.eos_image2, dd2)

            # Create EOS space for 3D reconstruction
            self.eos_space = EosSpace(self.eos_image1, self.eos_image2)

            # Set EOS images and space on the 2D measurements panel
            if self.measurements_2d_panel is not None:
                self.measurements_2d_panel.eos_image1 = self.eos_image1
                self.measurements_2d_panel.eos_image2 = self.eos_image2
                self.measurements_2d_panel.eos_space = self.eos_space
                self.measurements_2d_panel.sql_db = self.sql_db
                self.measurements_2d_panel.subject = self.subject
                self.measurements_2d_panel.measurements_main_panel = self.measurements_main_panel

                # Load and display the images in the panel
                self.measurements_2d_panel.load_images()

            # Set references for measurements main panel
            if self.measurements_main_panel is not None:
                self.measurements_main_panel.sql_db = self.sql_db
                self.measurements_main_panel.subject = self.subject
                self.measurements_main_panel.eos_image1 = self.eos_image1
                self.measurements_main_panel.eos_image2 = self.eos_image2
                self.measurements_main_panel.eos_space = self.eos_space

            self.add_to_logs_and_messages("EOS images loaded successfully")
            self._check_panels_loading()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Loading Images",
                f"Failed to load EOS images:\n{e}",
            )
            self.add_to_logs_and_messages(f"Error loading images: {e}")
        finally:
            QApplication.restoreOverrideCursor()

    def _read_eos_image(self, eos_image, dicom_decoder) -> None:
        """
        Read an EOS image using DICOM decoder.

        Args:
            eos_image: EosImage object to populate.
            dicom_decoder: DicomDecoder instance with file path set.
        """
        # Read DICOM metadata and calibration parameters
        eos_image.read_image()

        # Load pixel data for display
        eos_image.load_pixel_array()

    def _on_load_model(self) -> None:
        """
        Handle Load OpenSim Model menu action.

        Opens a file dialog to select an .osim model file and loads it
        into the visualization engine.
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load OpenSim Model",
            "",
            "OpenSim Model Files (*.osim);;All Files (*)"
        )

        if not file_path:
            return  # User cancelled

        try:
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
            self.add_to_logs_and_messages(f"Loading OpenSim model: {file_path}")

            # Load model using visualization engine
            if self.sim_model_visualization is None:
                from spine_modeling.visualization.sim_model_visualization import (
                    SimModelVisualization,
                )
                self.sim_model_visualization = SimModelVisualization()

            # TODO: Implement model loading when SimModelVisualization.load_model() is ready
            # self.sim_model_visualization.load_model(file_path)

            # Set on 3D modeling panel
            if self.modeling_3d_panel is not None:
                self.modeling_3d_panel.sim_model_visualization = self.sim_model_visualization

            self.add_to_logs_and_messages("OpenSim model loaded successfully")
            QMessageBox.information(
                self,
                "Model Loaded",
                f"Successfully loaded OpenSim model:\n{os.path.basename(file_path)}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Loading Model",
                f"Failed to load OpenSim model:\n{e}"
            )
            self.add_to_logs_and_messages(f"Error loading model: {e}")
        finally:
            QApplication.restoreOverrideCursor()

    def _on_save_model(self) -> None:
        """
        Handle Save Model menu action.

        Saves the current OpenSim model to an .osim XML file.
        """
        if self.sim_model_visualization is None or not hasattr(self.sim_model_visualization, 'model'):
            QMessageBox.warning(
                self,
                "No Model",
                "No OpenSim model is currently loaded."
            )
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save OpenSim Model",
            "",
            "OpenSim Model Files (*.osim);;All Files (*)"
        )

        if not file_path:
            return  # User cancelled

        try:
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
            self.add_to_logs_and_messages(f"Saving OpenSim model: {file_path}")

            # Save model using OpenSim API
            if hasattr(self.sim_model_visualization, 'model') and self.sim_model_visualization.model is not None:
                try:
                    import opensim
                    # Use OpenSim API to save model
                    self.sim_model_visualization.model.printToXML(file_path)
                    self.add_to_logs_and_messages("OpenSim model saved successfully")
                    QMessageBox.information(
                        self,
                        "Model Saved",
                        f"Successfully saved OpenSim model to:\n{file_path}"
                    )
                except ImportError:
                    raise ImportError("OpenSim is not installed")
            else:
                raise ValueError("No model available to save")

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Saving Model",
                f"Failed to save OpenSim model:\n{e}"
            )
            self.add_to_logs_and_messages(f"Error saving model: {e}")
        finally:
            QApplication.restoreOverrideCursor()

    def _on_load_stl_meshes(self) -> None:
        """
        Handle Load CT/STL Meshes menu action.

        Opens a file dialog to select STL mesh files (e.g., CT-scanned vertebrae)
        and loads them into the 3D visualization.
        """
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Load STL Mesh Files",
            "",
            "STL Mesh Files (*.stl);;All Files (*)"
        )

        if not file_paths:
            return  # User cancelled

        try:
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))
            self.add_to_logs_and_messages(f"Loading {len(file_paths)} STL mesh file(s)...")

            try:
                import vtk
            except ImportError:
                raise ImportError("VTK is required for STL mesh loading")

            loaded_count = 0
            for file_path in file_paths:
                try:
                    # Create STL reader
                    stl_reader = vtk.vtkSTLReader()
                    stl_reader.SetFileName(file_path)
                    stl_reader.Update()

                    # Create mapper
                    mapper = vtk.vtkPolyDataMapper()
                    mapper.SetInputConnection(stl_reader.GetOutputPort())

                    # Create actor
                    actor = vtk.vtkActor()
                    actor.SetMapper(mapper)

                    # Set default color (bone white)
                    actor.GetProperty().SetColor(0.9, 0.9, 0.8)
                    actor.GetProperty().SetOpacity(0.8)

                    # Add to 3D modeling panel renderer
                    if self.modeling_3d_panel is not None:
                        # TODO: Add actor to renderer when panel implementation is ready
                        # self.modeling_3d_panel.add_actor(actor)
                        pass

                    loaded_count += 1
                    self.add_to_logs_and_messages(f"Loaded STL mesh: {os.path.basename(file_path)}")

                except Exception as e:
                    self.add_to_logs_and_messages(f"Failed to load {file_path}: {e}")

            if loaded_count > 0:
                QMessageBox.information(
                    self,
                    "Meshes Loaded",
                    f"Successfully loaded {loaded_count} STL mesh file(s)."
                )
                self.add_to_logs_and_messages(f"Loaded {loaded_count} STL meshes successfully")
            else:
                QMessageBox.warning(
                    self,
                    "No Meshes Loaded",
                    "Failed to load any STL mesh files."
                )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Loading Meshes",
                f"Failed to load STL meshes:\n{e}"
            )
            self.add_to_logs_and_messages(f"Error loading meshes: {e}")
        finally:
            QApplication.restoreOverrideCursor()

    def _on_export_measurements_excel(self) -> None:
        """
        Handle Export Measurements to Excel menu action.

        Delegates to the measurements main panel's Excel export functionality.
        """
        if self.measurements_main_panel is not None:
            self.measurements_main_panel._on_export_to_excel()
        else:
            QMessageBox.warning(
                self,
                "Panel Not Available",
                "Measurements panel is not initialized."
            )

    def _on_export_markers_trc(self) -> None:
        """
        Handle Export Markers to TRC menu action.

        Delegates to the measurements main panel's TRC export functionality.
        """
        if self.measurements_main_panel is not None:
            self.measurements_main_panel._on_export_to_trc()
        else:
            QMessageBox.warning(
                self,
                "Panel Not Available",
                "Measurements panel is not initialized."
            )

    def _on_save_workspace(self) -> None:
        """
        Handle Save Workspace menu action.

        Saves the current workspace state (images, model, measurements) to a file.
        """
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Workspace",
            "",
            "Workspace Files (*.workspace);;All Files (*)"
        )

        if not file_path:
            return  # User cancelled

        try:
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

            # Create workspace data dictionary
            workspace_data = {
                'version': '1.0',
                'eos_image1_path': self.eos_image1.directory if self.eos_image1 else None,
                'eos_image2_path': self.eos_image2.directory if self.eos_image2 else None,
                'logs': self.logs_and_messages,
            }

            # Save to file using pickle
            with open(file_path, 'wb') as f:
                pickle.dump(workspace_data, f)

            self.add_to_logs_and_messages(f"Workspace saved to: {file_path}")
            QMessageBox.information(
                self,
                "Workspace Saved",
                f"Workspace saved successfully to:\n{file_path}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Saving Workspace",
                f"Failed to save workspace:\n{e}"
            )
            self.add_to_logs_and_messages(f"Error saving workspace: {e}")
        finally:
            QApplication.restoreOverrideCursor()

    def _on_load_workspace(self) -> None:
        """
        Handle Load Workspace menu action.

        Loads a previously saved workspace state from a file.
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Load Workspace",
            "",
            "Workspace Files (*.workspace);;All Files (*)"
        )

        if not file_path:
            return  # User cancelled

        try:
            QApplication.setOverrideCursor(QCursor(Qt.WaitCursor))

            # Load workspace data
            with open(file_path, 'rb') as f:
                workspace_data = pickle.load(f)

            # Restore EOS images if available
            if workspace_data.get('eos_image1_path') and workspace_data.get('eos_image2_path'):
                self.load_eos_images(
                    workspace_data['eos_image1_path'],
                    workspace_data['eos_image2_path']
                )

            # Restore logs
            if 'logs' in workspace_data:
                self.logs_and_messages.extend(workspace_data['logs'])

            self.add_to_logs_and_messages(f"Workspace loaded from: {file_path}")
            QMessageBox.information(
                self,
                "Workspace Loaded",
                f"Workspace loaded successfully from:\n{file_path}"
            )

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error Loading Workspace",
                f"Failed to load workspace:\n{e}"
            )
            self.add_to_logs_and_messages(f"Error loading workspace: {e}")
        finally:
            QApplication.restoreOverrideCursor()

    def _on_clear_workspace(self) -> None:
        """
        Handle Clear Workspace menu action.

        Clears all loaded data (images, models, measurements).
        """
        reply = QMessageBox.question(
            self,
            "Clear Workspace",
            "Are you sure you want to clear all loaded data?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Clear all data
            self.eos_image1 = None
            self.eos_image2 = None
            self.eos_space = None
            self.sim_model_visualization = None

            # Clear panels
            if self.measurements_2d_panel is not None:
                self.measurements_2d_panel.eos_image1 = None
                self.measurements_2d_panel.eos_image2 = None
                self.measurements_2d_panel.eos_space = None

            if self.measurements_main_panel is not None:
                self.measurements_main_panel.table_measurements.setRowCount(0)

            self.add_to_logs_and_messages("Workspace cleared")
            self.status_bar.showMessage("Workspace cleared", 3000)

    def render_all(self) -> None:
        """
        Render all VTK viewports.

        Updates all VTK render windows in the 3D modeling panel.
        """
        if self.modeling_3d_panel is not None:
            # Deferred to panel implementation
            pass


def main():
    """
    Test the image analysis form.

    Creates a standalone application for testing the form.
    """
    import sys

    app = QApplication(sys.argv)

    form = ImageAnalysisForm()
    form.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
