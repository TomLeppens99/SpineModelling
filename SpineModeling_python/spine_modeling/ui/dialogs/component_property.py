"""
Component Property Dialog for SpineModeling Application.

This module provides a dialog for displaying and editing properties
of OpenSim model components using a property grid/tree view.

Translated from: SpineModeling_CSharp/SkeletalModeling/frmComponentProperty.cs
Original class: frmComponentProperty
"""

from typing import Optional, Any
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QWidget
from PyQt5.QtCore import Qt


class ComponentPropertyDialog(QDialog):
    """
    Dialog for displaying and editing component properties.

    This dialog uses a tree widget to display object properties in a
    hierarchical format, similar to Windows Forms PropertyGrid.

    Attributes:
        selected_object: The object whose properties to display.
        property_tree (QTreeWidget): Tree widget for displaying properties.

    Examples:
        >>> dialog = ComponentPropertyDialog()
        >>> dialog.selected_object = some_opensim_component
        >>> dialog.exec_()
    """

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the component property dialog.

        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)

        # Public property for the selected object
        self.selected_object: Optional[Any] = None

        self._setup_ui()

    def _setup_ui(self) -> None:
        """
        Set up the user interface components.

        Creates a tree widget to display properties in a hierarchical format.
        """
        # Dialog properties
        self.setWindowTitle("Component Properties")
        self.setModal(True)
        self.resize(400, 500)

        # Main layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Property tree widget
        self.property_tree = QTreeWidget()
        self.property_tree.setHeaderLabels(["Property", "Value"])
        self.property_tree.setColumnWidth(0, 200)
        layout.addWidget(self.property_tree)

    def showEvent(self, event) -> None:
        """
        Handle dialog show event.

        Populates the property tree when the dialog is shown.

        Args:
            event: Show event.
        """
        super().showEvent(event)

        if self.selected_object is not None:
            self._populate_properties()

    def _populate_properties(self) -> None:
        """
        Populate the property tree with object properties.

        Uses introspection to discover and display object attributes
        and their values.
        """
        self.property_tree.clear()

        if self.selected_object is None:
            return

        # Get object attributes
        try:
            # For dataclasses and simple objects
            if hasattr(self.selected_object, "__dict__"):
                for name, value in self.selected_object.__dict__.items():
                    if not name.startswith("_"):  # Skip private attributes
                        item = QTreeWidgetItem([name, str(value)])
                        self.property_tree.addTopLevelItem(item)

            # For objects with properties
            for attr_name in dir(self.selected_object):
                if not attr_name.startswith("_") and not callable(
                    getattr(self.selected_object, attr_name, None)
                ):
                    try:
                        value = getattr(self.selected_object, attr_name)
                        item = QTreeWidgetItem([attr_name, str(value)])
                        self.property_tree.addTopLevelItem(item)
                    except Exception:
                        pass  # Skip properties that can't be accessed

        except Exception as e:
            error_item = QTreeWidgetItem(["Error", str(e)])
            self.property_tree.addTopLevelItem(error_item)


def main():
    """
    Test the component property dialog.

    Creates a standalone application for testing the dialog.
    """
    import sys
    from PyQt5.QtWidgets import QApplication

    # Sample test object
    class TestComponent:
        def __init__(self):
            self.name = "Test Component"
            self.mass = 5.0
            self.center_of_mass = [0.0, 0.0, 0.0]
            self.visible = True

    app = QApplication(sys.argv)

    dialog = ComponentPropertyDialog()
    dialog.selected_object = TestComponent()
    dialog.exec_()

    sys.exit(0)


if __name__ == "__main__":
    main()
