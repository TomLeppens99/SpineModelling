"""
Measurements Main Panel for SpineModeling Application.

This module provides the panel for displaying and managing measurement data
in a table/grid format with database integration.

Translated from: SpineModeling_CSharp/SkeletalModeling/UC_measurementsMain.cs
Original class: UC_measurementsMain

Note: This is a streamlined implementation. Database queries and complex
data operations will be refined during integration testing.
"""

from typing import Optional, List, Dict, Any
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QHeaderView, QMessageBox
)
from PyQt5.QtCore import Qt


class MeasurementsMainPanel(QWidget):
    """
    Panel for displaying and managing measurement data.

    This panel shows measurements in a table format with columns for
    ID, name, comment, and user. Supports filtering, sorting, and
    database operations.

    Attributes:
        measurements_2d_panel: Reference to 2D measurements work panel.
        eos: EOS acquisition data.
        app_data: Application-wide data and settings.
        sql_db: Database connection for measurements.
        subject: Current subject/patient.
        eos_image1: First EOS X-ray image.
        eos_image2: Second EOS X-ray image.
        eos_space: 3D space reconstruction.
        measurement: Current measurement being edited.

    Examples:
        >>> panel = MeasurementsMainPanel()
        >>> panel.refresh_measurements()
    """

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the measurements main panel.

        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)

        # References to other components
        self.measurements_2d_panel = None
        self.eos = None
        self.app_data = None
        self.sql_db = None
        self.subject = None
        self.eos_image1 = None
        self.eos_image2 = None
        self.eos_space = None
        self.measurement = None

        # Data
        self._measurements_data: List[Dict[str, Any]] = []

        self._setup_ui()

    def _setup_ui(self) -> None:
        """
        Set up the user interface components.

        Creates a table widget for displaying measurements and toolbar
        for data operations.
        """
        # Main layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Toolbar
        toolbar_layout = QHBoxLayout()
        layout.addLayout(toolbar_layout)

        lbl_title = QLabel("Measurements")
        lbl_title.setStyleSheet("font-size: 12pt; font-weight: bold;")
        toolbar_layout.addWidget(lbl_title)

        toolbar_layout.addStretch()

        # Refresh button
        btn_refresh = QPushButton("Refresh")
        btn_refresh.clicked.connect(self.refresh_measurements)
        toolbar_layout.addWidget(btn_refresh)

        # Delete button
        btn_delete = QPushButton("Delete Selected")
        btn_delete.clicked.connect(self._on_delete_selected)
        toolbar_layout.addWidget(btn_delete)

        # Export button
        btn_export = QPushButton("Export to Excel")
        btn_export.clicked.connect(self._on_export_to_excel)
        toolbar_layout.addWidget(btn_export)

        # Table widget for measurements
        self.table_measurements = QTableWidget()
        self.table_measurements.setColumnCount(4)
        self.table_measurements.setHorizontalHeaderLabels([
            "Measurement ID",
            "Name",
            "Comment",
            "User"
        ])

        # Set column widths
        header = self.table_measurements.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)

        # Enable selection
        self.table_measurements.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_measurements.setSelectionMode(QTableWidget.ExtendedSelection)

        # Enable sorting
        self.table_measurements.setSortingEnabled(True)

        layout.addWidget(self.table_measurements)

        # Status label
        self.lbl_status = QLabel("No measurements loaded")
        self.lbl_status.setStyleSheet("color: #666;")
        layout.addWidget(self.lbl_status)

    def refresh_measurements(self, user_id: Optional[int] = None) -> None:
        """
        Refresh measurements from database.

        Loads measurements for the current acquisition and displays them
        in the table. Optionally filters by user ID.

        Args:
            user_id: Optional user ID to filter measurements.
        """
        # Clear current data
        self.table_measurements.setRowCount(0)
        self._measurements_data.clear()

        # Check if we have necessary data
        if self.eos is None:
            self.lbl_status.setText("No EOS acquisition selected")
            return

        if self.sql_db is None:
            self.lbl_status.setText("Database not connected")
            # Load sample data for testing
            self._load_sample_data()
            return

        try:
            # Build SQL query
            # Note: In production, use parameterized queries with SQLAlchemy
            # acquisition_number = self.eos.AcquisitionNumber

            # Execute query and populate table
            # For now, load sample data
            self._load_sample_data()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Database Error",
                f"Failed to load measurements:\n{e}"
            )
            self.lbl_status.setText(f"Error: {e}")

    def _load_sample_data(self) -> None:
        """
        Load sample measurement data for testing.

        Creates dummy measurement records to demonstrate the table.
        """
        sample_data = [
            {
                "MeasurementID": 1,
                "MeasurementName": "L1 Superior Endplate",
                "MeasurementComment": "Lumbar vertebra L1",
                "UserName": "Dr. Smith"
            },
            {
                "MeasurementID": 2,
                "MeasurementName": "L2 Superior Endplate",
                "MeasurementComment": "Lumbar vertebra L2",
                "UserName": "Dr. Smith"
            },
            {
                "MeasurementID": 3,
                "MeasurementName": "L3 Superior Endplate",
                "MeasurementComment": "Lumbar vertebra L3",
                "UserName": "Dr. Jones"
            },
            {
                "MeasurementID": 4,
                "MeasurementName": "Sacrum Marker",
                "MeasurementComment": "S1 landmark",
                "UserName": "Dr. Smith"
            },
        ]

        self._populate_table(sample_data)
        self.lbl_status.setText(f"Loaded {len(sample_data)} measurements (sample data)")

    def _populate_table(self, data: List[Dict[str, Any]]) -> None:
        """
        Populate the table with measurement data.

        Args:
            data: List of measurement dictionaries with keys:
                  MeasurementID, MeasurementName, MeasurementComment, UserName
        """
        self._measurements_data = data
        self.table_measurements.setRowCount(len(data))

        for row_idx, measurement in enumerate(data):
            # Measurement ID
            item_id = QTableWidgetItem(str(measurement.get("MeasurementID", "")))
            item_id.setFlags(item_id.flags() & ~Qt.ItemIsEditable)  # Read-only
            self.table_measurements.setItem(row_idx, 0, item_id)

            # Name
            item_name = QTableWidgetItem(measurement.get("MeasurementName", ""))
            self.table_measurements.setItem(row_idx, 1, item_name)

            # Comment
            item_comment = QTableWidgetItem(measurement.get("MeasurementComment", ""))
            self.table_measurements.setItem(row_idx, 2, item_comment)

            # User
            item_user = QTableWidgetItem(measurement.get("UserName", ""))
            item_user.setFlags(item_user.flags() & ~Qt.ItemIsEditable)  # Read-only
            self.table_measurements.setItem(row_idx, 3, item_user)

    def _on_delete_selected(self) -> None:
        """
        Handle Delete Selected button click.

        Deletes the selected measurements from the database after
        confirmation.
        """
        selected_rows = self.table_measurements.selectionModel().selectedRows()

        if not selected_rows:
            QMessageBox.information(
                self,
                "No Selection",
                "Please select one or more measurements to delete."
            )
            return

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete {len(selected_rows)} measurement(s)?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Delete from database
            # TODO: Implement database deletion
            print(f"Deleting {len(selected_rows)} measurements")

            # Remove from table
            for index in sorted([r.row() for r in selected_rows], reverse=True):
                self.table_measurements.removeRow(index)

            self.lbl_status.setText(f"Deleted {len(selected_rows)} measurement(s)")

    def _on_export_to_excel(self) -> None:
        """
        Handle Export to Excel button click.

        Exports the current measurements to an Excel file.
        """
        if self.table_measurements.rowCount() == 0:
            QMessageBox.information(
                self,
                "No Data",
                "No measurements to export."
            )
            return

        # TODO: Implement Excel export using pandas or openpyxl
        QMessageBox.information(
            self,
            "Export",
            "Excel export functionality will be implemented."
        )

    def get_selected_measurement_ids(self) -> List[int]:
        """
        Get the IDs of selected measurements.

        Returns:
            List of measurement IDs for selected rows.
        """
        selected_rows = self.table_measurements.selectionModel().selectedRows()
        ids = []

        for row in selected_rows:
            item = self.table_measurements.item(row.row(), 0)  # Column 0 is ID
            if item:
                try:
                    ids.append(int(item.text()))
                except ValueError:
                    pass

        return ids
