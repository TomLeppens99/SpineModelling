"""
Logs and Messages Dialog for SpineModeling Application.

This module provides a dialog for displaying application logs and messages
in a scrollable text area.

Translated from: SpineModeling_CSharp/SkeletalModeling/frmLogsAndMessages.cs
Original class: frmLogsAndMessages
"""

from typing import Optional
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QWidget


class LogsAndMessagesDialog(QDialog):
    """
    Dialog for displaying logs and messages.

    This dialog shows text content in a read-only text area with
    automatic scrolling to the end of the content.

    Attributes:
        logs_and_messages (str): The text content to display.
        text_edit (QTextEdit): Read-only text widget for displaying content.

    Examples:
        >>> dialog = LogsAndMessagesDialog()
        >>> dialog.logs_and_messages = "Application started\\nLoading model..."
        >>> dialog.exec_()
    """

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the logs and messages dialog.

        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)

        # Public property for log content
        self.logs_and_messages: str = ""

        self._setup_ui()

    def _setup_ui(self) -> None:
        """
        Set up the user interface components.

        Creates a read-only text edit widget for displaying logs.
        """
        # Dialog properties
        self.setWindowTitle("Logs and Messages")
        self.setModal(True)
        self.resize(600, 400)

        # Main layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Text edit widget
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        layout.addWidget(self.text_edit)

    def showEvent(self, event) -> None:
        """
        Handle dialog show event.

        Populates the text area and scrolls to the end when the dialog is shown.

        Args:
            event: Show event.
        """
        super().showEvent(event)

        # Set the text content
        self.text_edit.setText(self.logs_and_messages)

        # Scroll to the end (equivalent to ScrollToCaret in C#)
        scrollbar = self.text_edit.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())


def main():
    """
    Test the logs and messages dialog.

    Creates a standalone application for testing the dialog.
    """
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)

    dialog = LogsAndMessagesDialog()
    dialog.logs_and_messages = """Application started at 2025-11-13 10:00:00
Loading OpenSim model...
Model loaded successfully: spine_model.osim
Initializing visualization engine...
VTK renderer created
Adding bodies to scene...
Adding joints to scene...
Adding muscles to scene...
Visualization complete
Ready for user interaction"""

    dialog.exec_()

    sys.exit(0)


if __name__ == "__main__":
    main()
