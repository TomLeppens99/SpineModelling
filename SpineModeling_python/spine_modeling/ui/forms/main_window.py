"""
Main Window (Entry Form) for SpineModeling Application.

This module provides the main entry window with a button to launch
the skeletal image analysis workflow.

Translated from: SpineModeling_CSharp/Form1.cs
Original class: btnmuscular (Form1)
"""

from typing import Optional
from PyQt5.QtWidgets import QMainWindow, QPushButton, QWidget


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
        self._setup_ui()

    def _setup_ui(self) -> None:
        """
        Set up the user interface components.

        Creates and configures all UI elements including the main button
        and window properties.
        """
        # Window properties
        self.setWindowTitle("SpineModeling - Main")
        self.setGeometry(100, 100, 1300, 640)  # Scaled down from 2601x1279

        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Skeletal button
        self.btn_skeletal = QPushButton("Skeletal", central_widget)
        self.btn_skeletal.setGeometry(130, 80, 265, 105)  # Scaled from 531x213
        self.btn_skeletal.clicked.connect(self._on_skeletal_clicked)

        # Set button style for visibility
        self.btn_skeletal.setStyleSheet("""
            QPushButton {
                font-size: 16px;
                font-weight: bold;
            }
        """)

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

    def _on_ms_clicked(self) -> None:
        """
        Handle MS button click (placeholder).

        Note: This method is not currently used but matches the C# code structure.
        """

    def _on_compare_models_clicked(self) -> None:
        """
        Handle Compare Models button click (placeholder).

        Note: This method is not currently used but matches the C# code structure.
        """

    def _on_perturbator_clicked(self) -> None:
        """
        Handle Perturbator button click (placeholder).

        Note: This method is not currently used but matches the C# code structure.
        """


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
