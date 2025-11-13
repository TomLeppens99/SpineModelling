"""
Skeletal Modeling Preferences Dialog for SpineModeling Application.

This module provides a dialog for configuring geometry directory preferences
for OpenSim model visualization.

Translated from: SpineModeling_CSharp/SkeletalModeling/frmSkeletalModelingPreferences.cs
Original class: frmSkeletalModelingPreferences
"""

import os
from typing import Optional, List
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTextEdit, QWidget, QMessageBox, QPushButton
)
from PyQt5.QtCore import Qt


class SkeletalModelingPreferencesDialog(QDialog):
    """
    Dialog for managing skeletal modeling preferences.

    This dialog allows users to configure geometry directory paths for
    OpenSim model visualization. The preferences are saved per user.

    Attributes:
        geometry_dirs (List[str]): List of geometry directory paths.
        app_data: Application data instance containing global settings.
        text_geometry_dirs (QTextEdit): Text area for editing directory paths.

    Examples:
        >>> from spine_modeling.database.app_data import AppData
        >>> dialog = SkeletalModelingPreferencesDialog()
        >>> dialog.app_data = AppData()
        >>> if dialog.exec_() == QDialog.Accepted:
        ...     print(f"Geometry directories: {dialog.geometry_dirs}")
    """

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the preferences dialog.

        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)

        # Public properties
        self.geometry_dirs: List[str] = []
        self.app_data = None

        self._setup_ui()

    def _setup_ui(self) -> None:
        """
        Set up the user interface components.

        Creates a text area for entering/editing geometry directory paths.
        """
        # Dialog properties
        self.setWindowTitle("Skeletal Modeling Preferences")
        self.setModal(True)
        self.resize(600, 400)

        # Main layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Title label
        title = QLabel("Geometry Directory Preferences")
        title.setStyleSheet("font-size: 14pt; font-weight: bold; color: #4682B4;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Explanation label
        explanation = QLabel(
            "Enter geometry directory paths (one per line).\n"
            'Use "SWS" for default Stanford Whole Skeleton paths.\n'
            "Invalid directories will be ignored on save."
        )
        explanation.setStyleSheet("font-size: 10pt; color: #666;")
        explanation.setWordWrap(True)
        layout.addWidget(explanation)

        # Text area for geometry directories
        self.text_geometry_dirs = QTextEdit()
        self.text_geometry_dirs.setPlaceholderText("Enter directory paths here...")
        layout.addWidget(self.text_geometry_dirs)

        # Close button
        btn_close = QPushButton("Close")
        btn_close.clicked.connect(self._on_close)
        layout.addWidget(btn_close)

    def showEvent(self, event) -> None:
        """
        Handle dialog show event.

        Loads preferences when the dialog is shown.

        Args:
            event: Show event.
        """
        super().showEvent(event)
        self._load_preferences()

    def _load_preferences(self) -> None:
        """
        Load geometry directory preferences from file.

        Reads the preferences file for the current user, or uses
        default value "SWS" if file doesn't exist.
        """
        self.geometry_dirs.clear()

        if self.app_data is None:
            self.geometry_dirs.append("SWS")
        else:
            # Get preferences file path
            user_id = getattr(
                getattr(self.app_data, "global_user", None), "_UserID", "default"
            )
            prefs_file = os.path.join(
                os.getcwd(), f"GeometryPreferences_{user_id}.txt"
            )

            if os.path.exists(prefs_file):
                self._read_lines_from_file(prefs_file)
            else:
                self.geometry_dirs.append("SWS")

        # Display in text area
        self.text_geometry_dirs.clear()
        for directory in self.geometry_dirs:
            self.text_geometry_dirs.append(directory)

    def _read_lines_from_file(self, file_path: str) -> None:
        """
        Read directory paths from preferences file.

        Args:
            file_path: Path to the preferences file.
        """
        try:
            with open(file_path, "r") as file:
                for line in file:
                    stripped_line = line.strip()
                    if stripped_line:
                        self.geometry_dirs.append(stripped_line)
        except Exception as e:
            print(f"Error reading preferences file: {e}")

    def _on_close(self) -> None:
        """
        Handle close button click.

        Validates and saves directory paths, then closes the dialog.
        """
        self._save_preferences()
        self.accept()

    def closeEvent(self, event) -> None:
        """
        Handle dialog close event.

        Saves preferences when the dialog is closed.

        Args:
            event: Close event.
        """
        self._save_preferences()
        super().closeEvent(event)

    def _save_preferences(self) -> None:
        """
        Save geometry directory preferences to file.

        Validates each directory path and saves only valid paths.
        Shows a warning if any directories were invalid.
        """
        self.geometry_dirs.clear()

        # Parse text area content
        lines = self.text_geometry_dirs.toPlainText().split("\n")

        lines_checked = []
        has_invalid = False

        for line in lines:
            directory = line.strip()

            if not directory:
                continue

            # "SWS" is a special keyword for default paths
            if directory.upper() == "SWS":
                lines_checked.append(directory)
            elif os.path.isdir(directory):
                lines_checked.append(directory)
            else:
                has_invalid = True

        # Save valid directories
        if self.app_data is not None:
            user_id = getattr(
                getattr(self.app_data, "global_user", None), "_UserID", "default"
            )
            prefs_file = os.path.join(
                os.getcwd(), f"GeometryPreferences_{user_id}.txt"
            )
            self._save_lines_to_file(prefs_file, lines_checked)

        # Update geometry_dirs with validated paths
        self.geometry_dirs = lines_checked

        # Show warning if any directories were invalid
        if has_invalid:
            QMessageBox.warning(
                self,
                "Directory not found",
                "One or more of the directories you entered could not be found. "
                "Correct directories were saved.",
                QMessageBox.Ok,
            )

    def _save_lines_to_file(self, file_path: str, lines: List[str]) -> None:
        """
        Save directory paths to preferences file.

        Args:
            file_path: Path to the preferences file.
            lines: List of directory paths to save.
        """
        try:
            with open(file_path, "w") as file:
                for line in lines:
                    file.write(f"{line}\n")
        except Exception as e:
            print(f"Error saving preferences file: {e}")

    def just_read(self) -> None:
        """
        Read preferences without displaying the dialog.

        This method loads the preferences into geometry_dirs without
        showing the UI.
        """
        self._load_preferences()


def main():
    """
    Test the preferences dialog.

    Creates a standalone application for testing the dialog.
    """
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)

    dialog = SkeletalModelingPreferencesDialog()
    # dialog.app_data = AppData()  # Would normally set app_data here

    if dialog.exec_() == QDialog.Accepted:
        print(f"Geometry directories: {dialog.geometry_dirs}")
    else:
        print("Dialog cancelled")

    sys.exit(0)


if __name__ == "__main__":
    main()
