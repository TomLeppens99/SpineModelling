"""
EOS Images Import Dialog for SpineModeling Application.

This module provides a dialog for manually importing EOS X-ray images
(frontal and lateral views) for skeletal modeling analysis.

Translated from: SpineModeling_CSharp/frmManualImportEOSimages.cs
Original class: frmManualImportEOSimages
"""

from typing import Optional, Tuple
from PyQt5.QtWidgets import (
    QDialog, QLabel, QLineEdit, QPushButton, QGridLayout,
    QFileDialog, QWidget, QApplication
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QCursor


class ImportEosImagesDialog(QDialog):
    """
    Dialog for importing two EOS X-ray images (frontal and lateral).

    This dialog allows users to select two DICOM image files representing
    the frontal and lateral views of EOS X-ray imaging. The dialog validates
    that both files are selected before allowing confirmation.

    Attributes:
        file1 (str): Path to the first image file (frontal view).
        file2 (str): Path to the second image file (lateral view).
        txt_filename1 (QLineEdit): Text box displaying path to file 1.
        txt_filename2 (QLineEdit): Text box displaying path to file 2.
        btn_file1 (QPushButton): Button to browse for file 1.
        btn_file2 (QPushButton): Button to browse for file 2.
        btn_confirm (QPushButton): Confirm button (initially hidden).
        btn_return (QPushButton): Return/cancel button.

    Examples:
        >>> dialog = ImportEosImagesDialog()
        >>> if dialog.exec_() == QDialog.Accepted:
        ...     frontal_path, lateral_path = dialog.get_files()
        ...     print(f"Frontal: {frontal_path}")
        ...     print(f"Lateral: {lateral_path}")
    """

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the import dialog.

        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)

        # Public properties for selected files
        self.file1: str = ""
        self.file2: str = ""

        self._setup_ui()

    def _setup_ui(self) -> None:
        """
        Set up the user interface components.

        Creates a grid layout with:
        - Title label at top
        - Two rows for image selection (label, text box, browse button)
        - Bottom row with return and confirm buttons
        """
        # Dialog properties
        self.setWindowTitle("Select EOS images")
        self.setModal(True)
        self.setFixedSize(1029, 291)
        self.setStyleSheet("background-color: white;")

        # Main grid layout (4 columns, 5 rows)
        layout = QGridLayout()
        self.setLayout(layout)

        # Row 0: Title label
        lbl_title = QLabel("Please select your EOS images")
        lbl_title.setStyleSheet("""
            font-family: 'Tw Cen MT', Arial;
            font-size: 24pt;
            font-weight: bold;
            color: #4682B4;
        """)
        lbl_title.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_title, 0, 1, 1, 2)  # Row 0, col 1-2

        # Row 1: Image 1 (Frontal)
        lbl_frontal = QLabel("Image 1\n(Frontal)")
        lbl_frontal.setStyleSheet("""
            font-family: 'Tw Cen MT', Arial;
            font-size: 12pt;
            color: #4682B4;
        """)
        lbl_frontal.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_frontal, 1, 0)

        self.txt_filename1 = QLineEdit()
        self.txt_filename1.setReadOnly(True)
        layout.addWidget(self.txt_filename1, 1, 1)

        self.btn_file1 = QPushButton()
        self.btn_file1.setFixedSize(74, 54)
        self.btn_file1.setText("📁")  # Folder icon
        self.btn_file1.setStyleSheet("""
            QPushButton {
                background-color: #87CEEB;
                border: 1px solid white;
                font-size: 24pt;
            }
            QPushButton:hover {
                background-color: #ADD8E6;
            }
        """)
        self.btn_file1.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_file1.clicked.connect(self._on_file1_clicked)
        layout.addWidget(self.btn_file1, 1, 2)

        # Row 2: Image 2 (Lateral)
        lbl_lateral = QLabel("Image 2\n(Lateral)")
        lbl_lateral.setStyleSheet("""
            font-family: 'Tw Cen MT', Arial;
            font-size: 12pt;
            color: #4682B4;
        """)
        lbl_lateral.setAlignment(Qt.AlignCenter)
        layout.addWidget(lbl_lateral, 2, 0)

        self.txt_filename2 = QLineEdit()
        self.txt_filename2.setReadOnly(True)
        layout.addWidget(self.txt_filename2, 2, 1)

        self.btn_file2 = QPushButton()
        self.btn_file2.setFixedSize(74, 54)
        self.btn_file2.setText("📁")  # Folder icon
        self.btn_file2.setStyleSheet("""
            QPushButton {
                background-color: #87CEEB;
                border: 1px solid white;
                font-size: 24pt;
            }
            QPushButton:hover {
                background-color: #ADD8E6;
            }
        """)
        self.btn_file2.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_file2.clicked.connect(self._on_file2_clicked)
        layout.addWidget(self.btn_file2, 2, 2)

        # Row 3: Spacer
        layout.setRowMinimumHeight(3, 20)

        # Row 4: Return and Confirm buttons
        self.btn_return = QPushButton("Return")
        self.btn_return.setFixedSize(94, 70)
        self.btn_return.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 10pt;
                color: #4682B4;
            }
            QPushButton:hover {
                color: #1E90FF;
            }
        """)
        self.btn_return.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_return.clicked.connect(self.reject)
        layout.addWidget(self.btn_return, 4, 0)

        self.btn_confirm = QPushButton("✓")  # Check mark
        self.btn_confirm.setFixedSize(53, 70)
        self.btn_confirm.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                font-size: 32pt;
                color: #32CD32;
            }
            QPushButton:hover {
                color: #00FF00;
            }
        """)
        self.btn_confirm.setCursor(QCursor(Qt.PointingHandCursor))
        self.btn_confirm.setVisible(False)  # Initially hidden
        self.btn_confirm.clicked.connect(self._on_confirm_clicked)
        layout.addWidget(self.btn_confirm, 4, 3)

        # Column stretching
        layout.setColumnStretch(0, 0)  # Fixed width
        layout.setColumnStretch(1, 1)  # Stretch text boxes
        layout.setColumnStretch(2, 0)  # Fixed width
        layout.setColumnStretch(3, 0)  # Fixed width

    def _run_file_dialog(self) -> str:
        """
        Open a file dialog to select a DICOM image file.

        Returns:
            Selected file path, or empty string if cancelled.
        """
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select EOS Image",
            "",
            "DICOM Files (*.dcm *.DCM *.dicom *.DICOM);;All Files (*.*)"
        )
        return file_path if file_path else ""

    def _on_file1_clicked(self) -> None:
        """
        Handle File 1 button click event.

        Opens a file dialog to select the frontal EOS image.
        Disables the button after selection and checks for completion.
        """
        file_path = self._run_file_dialog()
        if file_path:
            self.txt_filename1.setText(file_path)
            self.btn_file1.setEnabled(False)
            self._check_completion()

    def _on_file2_clicked(self) -> None:
        """
        Handle File 2 button click event.

        Opens a file dialog to select the lateral EOS image.
        Disables the button after selection and checks for completion.
        """
        file_path = self._run_file_dialog()
        if file_path:
            self.txt_filename2.setText(file_path)
            self.btn_file2.setEnabled(False)
            self._check_completion()

    def _check_completion(self) -> None:
        """
        Check if both files have been selected.

        Shows the confirm button when both file selections are complete.
        """
        if not self.btn_file1.isEnabled() and not self.btn_file2.isEnabled():
            self.btn_confirm.setVisible(True)

    def _on_confirm_clicked(self) -> None:
        """
        Handle Confirm button click event.

        Saves the selected file paths and closes the dialog with acceptance.
        """
        self.file1 = self.txt_filename1.text()
        self.file2 = self.txt_filename2.text()
        self.accept()

    def get_files(self) -> Tuple[str, str]:
        """
        Get the selected file paths.

        Returns:
            Tuple of (file1_path, file2_path).

        Examples:
            >>> dialog = ImportEosImagesDialog()
            >>> if dialog.exec_() == QDialog.Accepted:
            ...     frontal, lateral = dialog.get_files()
        """
        return (self.file1, self.file2)

    def showEvent(self, event) -> None:
        """
        Handle dialog show event.

        Resets the cursor to normal (not wait cursor).

        Args:
            event: Show event.
        """
        super().showEvent(event)
        QApplication.restoreOverrideCursor()


def main():
    """
    Test the import dialog.

    Creates a standalone application for testing the dialog.
    """
    import sys

    app = QApplication(sys.argv)

    dialog = ImportEosImagesDialog()
    result = dialog.exec_()

    if result == QDialog.Accepted:
        file1, file2 = dialog.get_files()
        print(f"File 1 (Frontal): {file1}")
        print(f"File 2 (Lateral): {file2}")
    else:
        print("Dialog cancelled")

    sys.exit(0)


if __name__ == "__main__":
    main()
