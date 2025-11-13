"""
Model Templates Dialog for SpineModeling Application.

This module provides a dialog for managing and selecting OpenSim model
templates for skeletal modeling analysis.

Translated from: SpineModeling_CSharp/SkeletalModeling/frmModelTemplates.cs
Original class: frmModelTemplates
"""

from typing import Optional
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QWidget, QListWidget, QPushButton, QHBoxLayout
)
from PyQt5.QtCore import Qt


class ModelTemplatesDialog(QDialog):
    """
    Dialog for selecting and managing model templates.

    This dialog allows users to browse and select from available
    OpenSim model templates stored in the application data.

    Attributes:
        app_data: Application data instance containing global settings.
        template_list (QListWidget): List widget for displaying templates.

    Examples:
        >>> from spine_modeling.database.app_data import AppData
        >>> dialog = ModelTemplatesDialog()
        >>> dialog.app_data = AppData()
        >>> dialog.exec_()
    """

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the model templates dialog.

        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)

        # Public property for application data
        self.app_data = None

        self._setup_ui()

    def _setup_ui(self) -> None:
        """
        Set up the user interface components.

        Creates a list widget for displaying available model templates.
        """
        # Dialog properties
        self.setWindowTitle("Model Templates")
        self.setModal(True)
        self.resize(500, 400)

        # Main layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Title label
        title = QLabel("Select a Model Template")
        title.setStyleSheet("font-size: 14pt; font-weight: bold; color: #4682B4;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Template list
        self.template_list = QListWidget()
        layout.addWidget(self.template_list)

        # Button layout
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)

        # Select button
        btn_select = QPushButton("Select")
        btn_select.clicked.connect(self.accept)
        button_layout.addWidget(btn_select)

        # Cancel button
        btn_cancel = QPushButton("Cancel")
        btn_cancel.clicked.connect(self.reject)
        button_layout.addWidget(btn_cancel)

    def showEvent(self, event) -> None:
        """
        Handle dialog show event.

        Loads available templates when the dialog is shown.

        Args:
            event: Show event.
        """
        super().showEvent(event)
        self._load_templates()

    def _load_templates(self) -> None:
        """
        Load available model templates from application data.

        Populates the template list with available .osim model files.
        """
        self.template_list.clear()

        # TODO: Implement template loading from app_data
        # For now, add placeholder templates
        placeholder_templates = [
            "Default Spine Model",
            "Thoracic Spine Model",
            "Lumbar Spine Model",
            "Full Body Model",
        ]

        for template in placeholder_templates:
            self.template_list.addItem(template)

    def get_selected_template(self) -> Optional[str]:
        """
        Get the currently selected template.

        Returns:
            Name of the selected template, or None if no selection.
        """
        current_item = self.template_list.currentItem()
        if current_item:
            return current_item.text()
        return None


def main():
    """
    Test the model templates dialog.

    Creates a standalone application for testing the dialog.
    """
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)

    dialog = ModelTemplatesDialog()
    result = dialog.exec_()

    if result == QDialog.Accepted:
        print(f"Selected template: {dialog.get_selected_template()}")
    else:
        print("Dialog cancelled")

    sys.exit(0)


if __name__ == "__main__":
    main()
