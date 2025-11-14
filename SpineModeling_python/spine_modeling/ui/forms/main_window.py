"""
Main Window (Entry Form) for SpineModeling Application.

This module provides the main entry window with a button to launch
the skeletal image analysis workflow.

Translated from: SpineModeling_CSharp/Form1.cs
Original class: btnmuscular (Form1)
"""

from typing import Optional
from pathlib import Path
from PyQt5.QtWidgets import (
    QMainWindow, QPushButton, QWidget, QMenuBar, QMenu, QAction, QMessageBox
)
from PyQt5.QtCore import QSize, Qt


class MainWindow(QMainWindow):
    """
    Main entry window for the SpineModeling application.

    This window provides the primary interface for launching different
    analysis workflows. Currently implements the Skeletal imaging workflow.

    Attributes:
        btn_skeletal (QPushButton): Button to launch skeletal image analysis.

    Examples:
        >>> from PyQt5.QtWidgets import QApplication
        >>> import sys
        >>> app = QApplication(sys.argv)
        >>> window = MainWindow()
        >>> window.show()
        >>> # app.exec_()
    """

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the main window.

        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)
        self.db_url = self._get_db_url()
        self._setup_ui()

    def _get_db_url(self) -> str:
        """Get the database URL."""
        db_path = Path.home() / ".spinemodeling" / "spinemodeling.db"
        return f"sqlite:///{db_path}"

    def _setup_ui(self) -> None:
        """
        Set up the user interface components.

        Creates and configures all UI elements including the main button
        and window properties.
        """
        # Window properties
        self.setWindowTitle("SpineModeling - Main")
        self.setGeometry(100, 100, 1300, 640)  # Scaled down from 2601x1279

        # Create menu bar
        self._create_menu_bar()

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Skeletal button
        self.btn_skeletal = QPushButton("Skeletal", central_widget)
        self.btn_skeletal.setGeometry(130, 80, 265, 105)  # Scaled from 531x213
        self.btn_skeletal.clicked.connect(self._on_skeletal_clicked)

        # Patient Manager button
        self.btn_patient_manager = QPushButton("Patient Manager", central_widget)
        self.btn_patient_manager.setGeometry(430, 80, 265, 105)
        self.btn_patient_manager.clicked.connect(self._on_patient_manager_clicked)

        # Set button style for visibility
        button_style = """
            QPushButton {
                font-size: 16px;
                font-weight: bold;
            }
        """
        self.btn_skeletal.setStyleSheet(button_style)
        self.btn_patient_manager.setStyleSheet(button_style)

    def _create_menu_bar(self):
        """Create the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        # Patient Manager action
        patient_action = QAction("&Patient Manager", self)
        patient_action.setShortcut("Ctrl+P")
        patient_action.triggered.connect(self._on_patient_manager_clicked)
        file_menu.addAction(patient_action)

        file_menu.addSeparator()

        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self._on_about_clicked)
        help_menu.addAction(about_action)

    def _on_skeletal_clicked(self) -> None:
        """
        Handle Skeletal button click event.

        Launches the image analysis form for skeletal modeling workflow.
        This is the main entry point for the application's primary functionality.
        """
        try:
            # Import here to avoid circular imports
            from spine_modeling.ui.forms.image_analysis import ImageAnalysisForm

            # Create and show the image analysis form as a window
            form = ImageAnalysisForm(self)
            form.show()

        except ImportError as e:
            print(f"Error importing ImageAnalysisForm: {e}")
            # In production, show a proper error dialog
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "Import Error",
                f"Could not load Image Analysis form:\n{e}"
            )
        except Exception as e:
            print(f"Error launching Image Analysis form: {e}")
            from PyQt5.QtWidgets import QMessageBox
            QMessageBox.critical(
                self,
                "Error",
                f"Error launching Image Analysis:\n{e}"
            )

    def _on_image_analysis_clicked(self) -> None:
        """
        Handle Image Analysis button click (placeholder).

        Note: This method is not currently used but matches the C# code structure.
        """
        pass

    def _on_ms_clicked(self) -> None:
        """
        Handle MS button click (placeholder).

        Note: This method is not currently used but matches the C# code structure.
        """
        pass

    def _on_compare_models_clicked(self) -> None:
        """
        Handle Compare Models button click (placeholder).

        Note: This method is not currently used but matches the C# code structure.
        """
        pass

    def _on_perturbator_clicked(self) -> None:
        """
        Handle Perturbator button click (placeholder).

        Note: This method is not currently used but matches the C# code structure.
        """
        pass

    def _on_patient_manager_clicked(self) -> None:
        """
        Handle Patient Manager button/menu click event.

        Launches the patient manager dialog for managing patient data
        and uploading images.
        """
        try:
            from spine_modeling.ui.dialogs.patient_manager_dialog import PatientManagerDialog

            dialog = PatientManagerDialog(self.db_url, self)

            def on_patient_selected(patient_code):
                """Handle patient selection."""
                QMessageBox.information(
                    self,
                    "Patient Selected",
                    f"Selected patient: {patient_code}\n\n"
                    f"You can now use the Skeletal button to analyze this patient's images."
                )

            dialog.patient_selected.connect(on_patient_selected)
            dialog.exec_()

        except Exception as e:
            print(f"Error launching Patient Manager: {e}")
            import traceback
            traceback.print_exc()
            QMessageBox.critical(
                self,
                "Error",
                f"Error launching Patient Manager:\n{e}"
            )

    def _on_about_clicked(self) -> None:
        """
        Handle About menu click event.

        Shows information about the application.
        """
        about_text = """
        <h2>SpineModeling Application</h2>
        <p><b>Version:</b> 1.0.0</p>
        <p>
        A biomechanical spine modeling and analysis system for:
        <ul>
        <li>EOS dual X-ray image analysis</li>
        <li>2D anatomical measurements with ellipse fitting</li>
        <li>3D skeletal reconstruction</li>
        <li>OpenSim biomechanical model visualization</li>
        <li>Patient database management</li>
        </ul>
        </p>
        <p><b>Patient Data Structure:</b><br>
        Supports 75 patients (ASD-001 to ASD-075) with organized folders for:
        <ul>
        <li>EOS X-ray images (Frontal and Lateral)</li>
        <li>CT scans by vertebra level (Sacrum to T1)</li>
        </ul>
        </p>
        """
        QMessageBox.about(self, "About SpineModeling", about_text)


def main():
    """
    Main entry point for the application.

    Creates the QApplication and main window, then starts the event loop.
    """
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    app.setApplicationName("SpineModeling")
    app.setOrganizationName("SpineModeling")

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
