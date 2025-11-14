"""
Patient Manager Dialog - UI for selecting patients and uploading images.

This module provides a comprehensive patient management interface with:
- Patient selection/search
- Image upload for EOS (frontal/lateral) and CT (by vertebra)
- Patient creation and initialization
"""

from pathlib import Path
from typing import Optional
from datetime import datetime

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QComboBox, QLineEdit, QGroupBox, QFileDialog, QMessageBox,
    QListWidget, QListWidgetItem, QTabWidget, QWidget, QFormLayout,
    QTextEdit, QDateEdit, QDoubleSpinBox, QRadioButton, QButtonGroup
)
from PyQt5.QtCore import Qt, QDate, pyqtSignal

from spine_modeling.database.models import DatabaseManager
from spine_modeling.utils.patient_data_manager import PatientDataManager, VERTEBRA_LEVELS


class PatientManagerDialog(QDialog):
    """
    Dialog for managing patients and uploading images.

    Provides interface for:
    - Searching/selecting patients
    - Creating new patients
    - Uploading EOS and CT images
    - Viewing patient information

    Signals:
        patient_selected: Emitted when a patient is selected (patient_code: str)
    """

    patient_selected = pyqtSignal(str)

    def __init__(self, db_url: str, parent: Optional[QWidget] = None):
        """
        Initialize the patient manager dialog.

        Args:
            db_url: Database URL for SQLAlchemy
            parent: Optional parent widget
        """
        super().__init__(parent)
        self.db_manager = DatabaseManager(db_url)
        self.data_manager = PatientDataManager()
        self.current_patient_code = None

        self._setup_ui()
        self._load_patients()

    def _setup_ui(self):
        """Set up the user interface."""
        self.setWindowTitle("Patient Data Manager")
        self.setGeometry(100, 100, 900, 700)

        layout = QVBoxLayout()

        # Patient selection section
        selection_group = self._create_selection_group()
        layout.addWidget(selection_group)

        # Tabs for image upload and patient info
        tabs = QTabWidget()
        tabs.addTab(self._create_upload_tab(), "Upload Images")
        tabs.addTab(self._create_patient_info_tab(), "Patient Information")
        layout.addWidget(tabs)

        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        self.btn_select = QPushButton("Select Patient")
        self.btn_select.clicked.connect(self._on_select_patient)
        self.btn_select.setEnabled(False)
        button_layout.addWidget(self.btn_select)

        self.btn_close = QPushButton("Close")
        self.btn_close.clicked.connect(self.reject)
        button_layout.addWidget(self.btn_close)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _create_selection_group(self) -> QGroupBox:
        """Create patient selection group."""
        group = QGroupBox("Patient Selection")
        layout = QVBoxLayout()

        # Search/filter
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter patient code (e.g., ASD-043)")
        self.search_input.textChanged.connect(self._filter_patients)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Patient list
        self.patient_list = QListWidget()
        self.patient_list.itemClicked.connect(self._on_patient_clicked)
        self.patient_list.itemDoubleClicked.connect(self._on_patient_double_clicked)
        layout.addWidget(self.patient_list)

        # Initialize all patients button
        init_layout = QHBoxLayout()
        self.btn_init_all = QPushButton("Initialize All Patients (ASD-001 to ASD-075)")
        self.btn_init_all.clicked.connect(self._initialize_all_patients)
        init_layout.addWidget(self.btn_init_all)
        layout.addLayout(init_layout)

        group.setLayout(layout)
        return group

    def _create_upload_tab(self) -> QWidget:
        """Create image upload tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        # Current patient label
        self.current_patient_label = QLabel("No patient selected")
        self.current_patient_label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        layout.addWidget(self.current_patient_label)

        # EOS Upload Section
        eos_group = QGroupBox("EOS X-ray Images")
        eos_layout = QVBoxLayout()

        # Frontal
        frontal_layout = QHBoxLayout()
        frontal_layout.addWidget(QLabel("Frontal:"))
        self.btn_upload_frontal = QPushButton("Upload Frontal Image")
        self.btn_upload_frontal.clicked.connect(lambda: self._upload_eos_image("frontal"))
        self.btn_upload_frontal.setEnabled(False)
        frontal_layout.addWidget(self.btn_upload_frontal)
        frontal_layout.addStretch()
        eos_layout.addLayout(frontal_layout)

        # Lateral
        lateral_layout = QHBoxLayout()
        lateral_layout.addWidget(QLabel("Lateral:"))
        self.btn_upload_lateral = QPushButton("Upload Lateral Image")
        self.btn_upload_lateral.clicked.connect(lambda: self._upload_eos_image("lateral"))
        self.btn_upload_lateral.setEnabled(False)
        lateral_layout.addWidget(self.btn_upload_lateral)
        lateral_layout.addStretch()
        eos_layout.addLayout(lateral_layout)

        eos_group.setLayout(eos_layout)
        layout.addWidget(eos_group)

        # CT Upload Section
        ct_group = QGroupBox("CT Scans (by Vertebra)")
        ct_layout = QVBoxLayout()

        # Vertebra selection
        vertebra_select_layout = QHBoxLayout()
        vertebra_select_layout.addWidget(QLabel("Select Vertebra:"))
        self.vertebra_combo = QComboBox()
        self.vertebra_combo.addItems(VERTEBRA_LEVELS)
        self.vertebra_combo.setEnabled(False)
        vertebra_select_layout.addWidget(self.vertebra_combo)

        self.btn_upload_ct = QPushButton("Upload CT Image/Mesh")
        self.btn_upload_ct.clicked.connect(self._upload_ct_image)
        self.btn_upload_ct.setEnabled(False)
        vertebra_select_layout.addWidget(self.btn_upload_ct)
        vertebra_select_layout.addStretch()

        ct_layout.addLayout(vertebra_select_layout)
        ct_group.setLayout(ct_layout)
        layout.addWidget(ct_group)

        # Image list for current patient
        images_group = QGroupBox("Uploaded Images")
        images_layout = QVBoxLayout()
        self.images_list = QListWidget()
        images_layout.addWidget(self.images_list)

        refresh_btn = QPushButton("Refresh Image List")
        refresh_btn.clicked.connect(self._refresh_image_list)
        images_layout.addWidget(refresh_btn)

        images_group.setLayout(images_layout)
        layout.addWidget(images_group)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _create_patient_info_tab(self) -> QWidget:
        """Create patient information tab."""
        widget = QWidget()
        layout = QVBoxLayout()

        form = QFormLayout()

        self.patient_code_display = QLineEdit()
        self.patient_code_display.setReadOnly(True)
        form.addRow("Patient Code:", self.patient_code_display)

        self.patient_name = QLineEdit()
        form.addRow("Name:", self.patient_name)

        self.patient_dob = QDateEdit()
        self.patient_dob.setCalendarPopup(True)
        self.patient_dob.setDate(QDate.currentDate())
        form.addRow("Date of Birth:", self.patient_dob)

        # Gender
        gender_layout = QHBoxLayout()
        self.gender_group = QButtonGroup()
        self.gender_male = QRadioButton("Male")
        self.gender_female = QRadioButton("Female")
        self.gender_other = QRadioButton("Other")
        self.gender_group.addButton(self.gender_male)
        self.gender_group.addButton(self.gender_female)
        self.gender_group.addButton(self.gender_other)
        gender_layout.addWidget(self.gender_male)
        gender_layout.addWidget(self.gender_female)
        gender_layout.addWidget(self.gender_other)
        gender_layout.addStretch()
        form.addRow("Gender:", gender_layout)

        self.patient_height = QDoubleSpinBox()
        self.patient_height.setRange(0, 300)
        self.patient_height.setSuffix(" cm")
        form.addRow("Height:", self.patient_height)

        self.patient_weight = QDoubleSpinBox()
        self.patient_weight.setRange(0, 500)
        self.patient_weight.setSuffix(" kg")
        form.addRow("Weight:", self.patient_weight)

        self.patient_notes = QTextEdit()
        self.patient_notes.setMaximumHeight(100)
        form.addRow("Notes:", self.patient_notes)

        layout.addLayout(form)

        # Save button
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        self.btn_save_info = QPushButton("Save Patient Information")
        self.btn_save_info.clicked.connect(self._save_patient_info)
        self.btn_save_info.setEnabled(False)
        save_layout.addWidget(self.btn_save_info)
        layout.addLayout(save_layout)

        layout.addStretch()
        widget.setLayout(layout)
        return widget

    def _load_patients(self):
        """Load all patients from database."""
        self.patient_list.clear()
        subjects = self.db_manager.get_all_subjects()

        for subject in subjects:
            item = QListWidgetItem(f"{subject.subject_code} - {subject.name or 'No name'}")
            item.setData(Qt.UserRole, subject.subject_code)
            self.patient_list.addItem(item)

    def _filter_patients(self):
        """Filter patient list based on search text."""
        search_text = self.search_input.text().upper()

        for i in range(self.patient_list.count()):
            item = self.patient_list.item(i)
            item.setHidden(search_text not in item.text().upper())

    def _on_patient_clicked(self, item: QListWidgetItem):
        """Handle patient list item clicked."""
        patient_code = item.data(Qt.UserRole)
        self._select_patient(patient_code)

    def _on_patient_double_clicked(self, item: QListWidgetItem):
        """Handle patient list item double-clicked."""
        patient_code = item.data(Qt.UserRole)
        self._select_patient(patient_code)
        self._on_select_patient()

    def _select_patient(self, patient_code: str):
        """
        Select a patient and update UI.

        Args:
            patient_code: Patient code to select
        """
        self.current_patient_code = patient_code
        self.current_patient_label.setText(f"Current Patient: {patient_code}")

        # Enable upload buttons
        self.btn_upload_frontal.setEnabled(True)
        self.btn_upload_lateral.setEnabled(True)
        self.vertebra_combo.setEnabled(True)
        self.btn_upload_ct.setEnabled(True)
        self.btn_select.setEnabled(True)
        self.btn_save_info.setEnabled(True)

        # Load patient info
        self._load_patient_info(patient_code)

        # Load images
        self._refresh_image_list()

    def _load_patient_info(self, patient_code: str):
        """Load patient information from database."""
        subject = self.db_manager.get_subject_by_code(patient_code)

        if subject:
            self.patient_code_display.setText(subject.subject_code)
            self.patient_name.setText(subject.name or "")

            if subject.date_of_birth:
                qdate = QDate(
                    subject.date_of_birth.year,
                    subject.date_of_birth.month,
                    subject.date_of_birth.day
                )
                self.patient_dob.setDate(qdate)

            if subject.gender:
                if subject.gender.upper() == "M":
                    self.gender_male.setChecked(True)
                elif subject.gender.upper() == "F":
                    self.gender_female.setChecked(True)
                else:
                    self.gender_other.setChecked(True)

            if subject.height:
                self.patient_height.setValue(subject.height)

            if subject.weight:
                self.patient_weight.setValue(subject.weight)

            if subject.notes:
                self.patient_notes.setText(subject.notes)

    def _save_patient_info(self):
        """Save patient information to database."""
        if not self.current_patient_code:
            return

        subject = self.db_manager.get_subject_by_code(self.current_patient_code)
        if not subject:
            return

        # Get gender
        gender = None
        if self.gender_male.isChecked():
            gender = "M"
        elif self.gender_female.isChecked():
            gender = "F"
        elif self.gender_other.isChecked():
            gender = "Other"

        # Get date of birth
        qdate = self.patient_dob.date()
        dob = datetime(qdate.year(), qdate.month(), qdate.day())

        # Update subject
        self.db_manager.update_subject(
            subject.subject_id,
            name=self.patient_name.text() or None,
            date_of_birth=dob,
            gender=gender,
            height=self.patient_height.value() if self.patient_height.value() > 0 else None,
            weight=self.patient_weight.value() if self.patient_weight.value() > 0 else None,
            notes=self.patient_notes.toPlainText() or None
        )

        QMessageBox.information(self, "Success", "Patient information saved successfully!")
        self._load_patients()

    def _upload_eos_image(self, view: str):
        """
        Upload an EOS image (frontal or lateral).

        Args:
            view: "frontal" or "lateral"
        """
        if not self.current_patient_code:
            return

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Select EOS {view.capitalize()} Image",
            "",
            "DICOM Files (*.dcm *.dicom);;Image Files (*.png *.jpg *.jpeg);;All Files (*.*)"
        )

        if file_path:
            try:
                # Copy file to patient folder
                image_type = f"EOS_{view.capitalize()}"
                dest_path = self.data_manager.copy_file_to_patient_folder(
                    Path(file_path),
                    self.current_patient_code,
                    image_type
                )

                # Get subject
                subject = self.db_manager.get_subject_by_code(self.current_patient_code)

                # Record in database
                relative_path = self.data_manager.get_relative_path(dest_path)
                self.db_manager.create_patient_image(
                    subject_id=subject.subject_id,
                    image_type=image_type,
                    file_path=relative_path,
                    file_name=Path(file_path).name,
                    file_size=Path(file_path).stat().st_size
                )

                QMessageBox.information(
                    self,
                    "Success",
                    f"EOS {view} image uploaded successfully!"
                )
                self._refresh_image_list()

            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to upload image: {str(e)}"
                )

    def _upload_ct_image(self):
        """Upload a CT image for selected vertebra."""
        if not self.current_patient_code:
            return

        vertebra = self.vertebra_combo.currentText()

        file_path, _ = QFileDialog.getOpenFileName(
            self,
            f"Select CT Image for {vertebra}",
            "",
            "Mesh Files (*.stl *.obj);;DICOM Files (*.dcm *.dicom);;All Files (*.*)"
        )

        if file_path:
            try:
                # Copy file to patient folder
                dest_path = self.data_manager.copy_file_to_patient_folder(
                    Path(file_path),
                    self.current_patient_code,
                    "CT",
                    vertebra=vertebra
                )

                # Get subject
                subject = self.db_manager.get_subject_by_code(self.current_patient_code)

                # Record in database
                relative_path = self.data_manager.get_relative_path(dest_path)
                self.db_manager.create_patient_image(
                    subject_id=subject.subject_id,
                    image_type="CT",
                    file_path=relative_path,
                    file_name=Path(file_path).name,
                    vertebra_level=vertebra,
                    file_size=Path(file_path).stat().st_size
                )

                QMessageBox.information(
                    self,
                    "Success",
                    f"CT image for {vertebra} uploaded successfully!"
                )
                self._refresh_image_list()

            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to upload image: {str(e)}"
                )

    def _refresh_image_list(self):
        """Refresh the list of uploaded images for current patient."""
        self.images_list.clear()

        if not self.current_patient_code:
            return

        subject = self.db_manager.get_subject_by_code(self.current_patient_code)
        if not subject:
            return

        images = self.db_manager.get_images_by_subject(subject.subject_id)

        for image in images:
            display_text = f"{image.image_type}"
            if image.vertebra_level:
                display_text += f" - {image.vertebra_level}"
            display_text += f" - {image.file_name}"

            self.images_list.addItem(display_text)

    def _initialize_all_patients(self):
        """Initialize all patients (ASD-001 to ASD-075) in database and folders."""
        reply = QMessageBox.question(
            self,
            "Initialize All Patients",
            "This will create folder structures and database entries for "
            "all patients (ASD-001 to ASD-075).\n\n"
            "Do you want to continue?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                subjects = self.data_manager.initialize_all_patients_in_db(self.db_manager)
                QMessageBox.information(
                    self,
                    "Success",
                    f"Successfully initialized {len(subjects)} patients!"
                )
                self._load_patients()

            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error",
                    f"Failed to initialize patients: {str(e)}"
                )

    def _on_select_patient(self):
        """Handle select patient button click."""
        if self.current_patient_code:
            self.patient_selected.emit(self.current_patient_code)
            self.accept()

    def get_selected_patient_code(self) -> Optional[str]:
        """
        Get the currently selected patient code.

        Returns:
            Selected patient code or None
        """
        return self.current_patient_code

    def closeEvent(self, event):
        """Handle dialog close event."""
        self.db_manager.close_session()
        super().closeEvent(event)


if __name__ == "__main__":
    """Test the patient manager dialog."""
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)

    # Create test database
    db_url = "sqlite:///test_patient_manager.db"
    db_manager = DatabaseManager(db_url)
    db_manager.initialize_database()

    # Show dialog
    dialog = PatientManagerDialog(db_url)

    def on_patient_selected(patient_code):
        print(f"Selected patient: {patient_code}")

    dialog.patient_selected.connect(on_patient_selected)
    dialog.exec_()

    sys.exit()
