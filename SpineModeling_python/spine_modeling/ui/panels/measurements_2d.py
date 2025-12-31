"""
2D Measurements Work Panel for SpineModeling Application.

This module provides the panel for 2D image annotation and measurement
on EOS X-ray images (frontal and lateral views).

Translated from: SpineModeling_CSharp/SkeletalModeling/2DMeasurementsWorkpanel.cs
Original class: _2DMeasurementsWorkpanel

Features:
- Point annotation on images with visual feedback
- Ellipse fitting from multiple points
- Zoom/pan functionality with coordinate tracking
- Database integration for measurements
- Real-time preview and suggestion lines
"""

import logging
from datetime import datetime
from typing import Optional, List, Tuple
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QPushButton, QSplitter, QGroupBox, QMessageBox, QInputDialog
)
from PyQt5.QtCore import Qt, QPoint, QRect, QPointF, QRectF
from PyQt5.QtGui import QPainter, QPen, QPixmap, QImage, QColor, QMouseEvent, QBrush, QPainterPath
import numpy as np

# Set up logging
logger = logging.getLogger(__name__)


class Measurements2DPanel(QWidget):
    """
    Panel for 2D image measurements and annotations.

    This panel displays dual EOS X-ray images (frontal and lateral) and
    provides tools for annotating anatomical landmarks with points and
    ellipses.

    Attributes:
        app_data: Application-wide data and settings.
        sql_db: Database connection for measurements.
        subject: Current subject/patient.
        eos_image1: First EOS X-ray image (frontal).
        eos_image2: Second EOS X-ray image (lateral).
        eos_space: 3D space reconstruction from dual X-rays.
        measurements_main_panel: Reference to measurements data grid panel.
        loaded_2d (bool): Flag indicating if 2D panel is loaded.

    Examples:
        >>> panel = Measurements2DPanel()
        >>> panel.load_images()
    """

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize the 2D measurements panel.

        Args:
            parent: Optional parent widget.
        """
        super().__init__(parent)

        # Data objects
        self.app_data = None
        self.sql_db = None
        self.subject = None
        self.eos_image1 = None
        self.eos_image2 = None
        self.eos_space = None
        self.measurements_main_panel = None

        # Panel state
        self.loaded_2d: bool = False
        self.single_point_being_drawn_im1: bool = False
        self.ellipse_being_drawn_im1: bool = False
        self.single_point_being_drawn_im2: bool = False
        self.ellipse_being_drawn_im2: bool = False

        # Template mode state (Saïd's suggestion: fixed-size ellipses)
        self._template_mode: Optional[str] = None  # 'cluster' (3mm) or 'single' (5mm)
        self._template_manager1 = None  # EllipsePlacementManager for image 1
        self._template_manager2 = None  # EllipsePlacementManager for image 2

        # Zoom tracking (offset from original image coordinates)
        self.upper_left_corner1 = QPoint(0, 0)
        self.upper_left_corner2 = QPoint(0, 0)

        # Original images (for reset functionality)
        self._original_pixmap1: Optional[QPixmap] = None
        self._original_pixmap2: Optional[QPixmap] = None

        # Mouse tracking for zoom/pan
        self._selecting: bool = False
        self._selection: QRect = QRect()  # In image coordinates
        self._selection_local: QRect = QRect()  # In widget coordinates
        self._mouse_down_pos: Optional[QPoint] = None
        self._mouse_move_pos: Optional[QPoint] = None

        # Circle/ellipse preview
        self._draw_circle: bool = False
        self._is_moving: bool = False
        self.mouse_down_position: QPoint = QPoint()
        self.mouse_move_position: QPoint = QPoint()

        # Annotations storage
        self._image1_points: List[QPoint] = []  # Points in image coordinates
        self._image2_points: List[QPoint] = []
        self._ellipse1_points: List[QPoint] = []  # Ellipse points for image 1
        self._ellipse2_points: List[QPoint] = []  # Ellipse points for image 2

        # Zoom/scale factors
        self._zoom_scale1: float = 1.0
        self._zoom_scale2: float = 1.0

        self._setup_ui()

    def _setup_ui(self) -> None:
        """
        Set up the user interface components.

        Creates dual image viewers in a split view with toolbars for
        annotation and measurement controls.
        """
        # Main layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Toolbar for controls
        toolbar_layout = QHBoxLayout()
        layout.addLayout(toolbar_layout)

        # Annotation mode buttons
        self.btn_point_mode = QPushButton("Point Mode")
        self.btn_point_mode.setCheckable(True)
        self.btn_point_mode.clicked.connect(self._on_point_mode_clicked)
        toolbar_layout.addWidget(self.btn_point_mode)

        self.btn_ellipse_mode = QPushButton("Ellipse Mode")
        self.btn_ellipse_mode.setCheckable(True)
        self.btn_ellipse_mode.clicked.connect(self._on_ellipse_mode_clicked)
        toolbar_layout.addWidget(self.btn_ellipse_mode)

        # Template mode buttons (Saïd's suggestion: fixed-size ellipses)
        self.btn_template_cluster = QPushButton("Cluster (3mm)")
        self.btn_template_cluster.setCheckable(True)
        self.btn_template_cluster.setToolTip("Click to place 3mm marker (M, R, L clusters)")
        self.btn_template_cluster.clicked.connect(self._on_template_cluster_clicked)
        toolbar_layout.addWidget(self.btn_template_cluster)

        self.btn_template_single = QPushButton("Single (5mm)")
        self.btn_template_single.setCheckable(True)
        self.btn_template_single.setToolTip("Click to place 5mm single marker")
        self.btn_template_single.clicked.connect(self._on_template_single_clicked)
        toolbar_layout.addWidget(self.btn_template_single)

        # Auto-detect button
        self.btn_auto_detect = QPushButton("Auto Detect")
        self.btn_auto_detect.setToolTip("Automatically detect circular markers")
        self.btn_auto_detect.clicked.connect(self._on_auto_detect_clicked)
        toolbar_layout.addWidget(self.btn_auto_detect)

        toolbar_layout.addStretch()

        # Zoom controls
        btn_zoom_in = QPushButton("Zoom In")
        btn_zoom_in.clicked.connect(self._on_zoom_in)
        toolbar_layout.addWidget(btn_zoom_in)

        btn_zoom_out = QPushButton("Zoom Out")
        btn_zoom_out.clicked.connect(self._on_zoom_out)
        toolbar_layout.addWidget(btn_zoom_out)

        btn_zoom_reset = QPushButton("Reset")
        btn_zoom_reset.clicked.connect(self._on_zoom_reset)
        toolbar_layout.addWidget(btn_zoom_reset)

        # Splitter for dual image view
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)

        # Image 1 (Frontal) viewer
        image1_group = QGroupBox("Image 1 (Frontal)")
        image1_layout = QVBoxLayout()
        image1_group.setLayout(image1_layout)

        # Create custom image widget for image 1
        self.image1_label = ImageLabel(self, image_num=1)
        self.image1_label.setMinimumSize(400, 600)
        self.image1_label.setStyleSheet("border: 1px solid #ccc; background: #000;")
        self.image1_label.setAlignment(Qt.AlignCenter)
        self.image1_label.setScaledContents(False)
        self.image1_label.setMouseTracking(True)

        scroll1 = QScrollArea()
        scroll1.setWidget(self.image1_label)
        scroll1.setWidgetResizable(True)
        image1_layout.addWidget(scroll1)

        splitter.addWidget(image1_group)

        # Image 2 (Lateral) viewer
        image2_group = QGroupBox("Image 2 (Lateral)")
        image2_layout = QVBoxLayout()
        image2_group.setLayout(image2_layout)

        # Create custom image widget for image 2
        self.image2_label = ImageLabel(self, image_num=2)
        self.image2_label.setMinimumSize(400, 600)
        self.image2_label.setStyleSheet("border: 1px solid #ccc; background: #000;")
        self.image2_label.setAlignment(Qt.AlignCenter)
        self.image2_label.setScaledContents(False)
        self.image2_label.setMouseTracking(True)

        scroll2 = QScrollArea()
        scroll2.setWidget(self.image2_label)
        scroll2.setWidgetResizable(True)
        image2_layout.addWidget(scroll2)

        splitter.addWidget(image2_group)

        # Set equal splitter sizes
        splitter.setSizes([700, 700])

        # Bottom section for measurements main panel (embedded)
        # Note: In the C# version, UC_measurementsMain is a separate control
        # We'll create a reference to it when both panels are initialized
        self.measurements_grid_container = QWidget()
        measurements_grid_layout = QVBoxLayout()
        self.measurements_grid_container.setLayout(measurements_grid_layout)
        layout.addWidget(self.measurements_grid_container)

    def load_images(self) -> None:
        """
        Load and display EOS images in the viewers.

        Reads the EOS image data and displays it in the dual image viewers.
        Stores original pixmaps for reset functionality.
        """
        if self.eos_image1 is None or self.eos_image2 is None:
            print("EOS images not set")
            return

        try:
            # Load and display image 1
            if self.eos_image1.pixel_array is not None:
                pixmap1 = self._create_pixmap_from_eos(self.eos_image1)
                self._original_pixmap1 = pixmap1.copy()  # Store original
                self.image1_label.setPixmap(pixmap1)
            else:
                print("Image 1 pixel array not loaded")

            # Load and display image 2
            if self.eos_image2.pixel_array is not None:
                pixmap2 = self._create_pixmap_from_eos(self.eos_image2)
                self._original_pixmap2 = pixmap2.copy()  # Store original
                self.image2_label.setPixmap(pixmap2)
            else:
                print("Image 2 pixel array not loaded")

            self.loaded_2d = True
            print("2D images loaded successfully")

        except Exception as e:
            print(f"Error loading images: {e}")
            import traceback
            traceback.print_exc()
            self.loaded_2d = False

    def _create_pixmap_from_eos(self, eos_image) -> QPixmap:
        """
        Create a QPixmap from EOS image data.

        Args:
            eos_image: EosImage object with pixel data.

        Returns:
            QPixmap containing the image data.
        """
        try:
            import numpy as np

            pixel_array = eos_image.pixel_array

            # Normalize pixel values to 8-bit range (0-255)
            # DICOM images often have 12-bit or 16-bit data
            pixel_min = np.min(pixel_array)
            pixel_max = np.max(pixel_array)

            if pixel_max > pixel_min:
                # Normalize to 0-255 range
                normalized = ((pixel_array - pixel_min) / (pixel_max - pixel_min) * 255).astype(np.uint8)
            else:
                normalized = np.zeros_like(pixel_array, dtype=np.uint8)

            # Get image dimensions
            height, width = normalized.shape

            # Create QImage from numpy array (grayscale format)
            bytes_per_line = width
            qimage = QImage(normalized.data, width, height, bytes_per_line, QImage.Format_Grayscale8)

            # Convert to QPixmap
            pixmap = QPixmap.fromImage(qimage)

            # Scale to fit display (max 800 pixels in either dimension)
            max_display_size = 800
            if width > max_display_size or height > max_display_size:
                pixmap = pixmap.scaled(
                    max_display_size, max_display_size,
                    Qt.KeepAspectRatio, Qt.SmoothTransformation
                )

            return pixmap

        except Exception as e:
            print(f"Error creating pixmap: {e}")
            import traceback
            traceback.print_exc()
            # Return placeholder on error
            placeholder = QPixmap(512, 512)
            placeholder.fill(QColor(50, 50, 50))
            return placeholder

    def _on_point_mode_clicked(self) -> None:
        """Handle Point Mode button click."""
        if self.btn_point_mode.isChecked():
            self.btn_ellipse_mode.setChecked(False)
            print("Point annotation mode activated")

    def _on_ellipse_mode_clicked(self) -> None:
        """Handle Ellipse Mode button click."""
        if self.btn_ellipse_mode.isChecked():
            self.btn_point_mode.setChecked(False)
            self.btn_template_cluster.setChecked(False)
            self.btn_template_single.setChecked(False)
            self._template_mode = None
            print("Ellipse annotation mode activated (multi-point fitting)")

    def _on_template_cluster_clicked(self) -> None:
        """Handle Cluster Template (3mm) button click."""
        if self.btn_template_cluster.isChecked():
            self.btn_point_mode.setChecked(False)
            self.btn_ellipse_mode.setChecked(False)
            self.btn_template_single.setChecked(False)
            self._template_mode = 'cluster'
            print("Template mode: Cluster markers (3mm) - click to place")
        else:
            self._template_mode = None

    def _on_template_single_clicked(self) -> None:
        """Handle Single Template (5mm) button click."""
        if self.btn_template_single.isChecked():
            self.btn_point_mode.setChecked(False)
            self.btn_ellipse_mode.setChecked(False)
            self.btn_template_cluster.setChecked(False)
            self._template_mode = 'single'
            print("Template mode: Single markers (5mm) - click to place")
        else:
            self._template_mode = None

    def _on_auto_detect_clicked(self) -> None:
        """Handle Auto Detect button click - detect circular markers automatically."""
        # Show configuration dialog first
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSlider, QSpinBox, QDialogButtonBox, QProgressDialog, QComboBox, QCheckBox
        from PyQt5.QtCore import Qt

        # Check if images are loaded
        if self.eos_image1 is None and self.eos_image2 is None:
            QMessageBox.warning(
                self, "Auto Detection",
                "No images loaded. Please load EOS images first."
            )
            return

        # Create configuration dialog
        dialog = QDialog(self)
        dialog.setWindowTitle("Auto Detect Markers")
        dialog.setMinimumWidth(350)
        layout = QVBoxLayout(dialog)

        # Marker type selection
        type_layout = QHBoxLayout()
        type_layout.addWidget(QLabel("Marker type to detect:"))
        marker_type_combo = QComboBox()
        marker_type_combo.addItems(["All markers", "Cluster only (3mm)", "Single only (5mm)"])
        type_layout.addWidget(marker_type_combo)
        layout.addLayout(type_layout)

        # Sensitivity slider
        sens_layout = QHBoxLayout()
        sens_layout.addWidget(QLabel("Detection sensitivity:"))
        sensitivity_slider = QSlider(Qt.Horizontal)
        sensitivity_slider.setRange(1, 10)
        sensitivity_slider.setValue(5)
        sensitivity_slider.setTickPosition(QSlider.TicksBelow)
        sens_label = QLabel("5")
        sensitivity_slider.valueChanged.connect(lambda v: sens_label.setText(str(v)))
        sens_layout.addWidget(sensitivity_slider)
        sens_layout.addWidget(sens_label)
        layout.addLayout(sens_layout)

        # Min/max radius
        radius_layout = QHBoxLayout()
        radius_layout.addWidget(QLabel("Min radius (mm):"))
        min_radius_spin = QSpinBox()
        min_radius_spin.setRange(1, 10)
        min_radius_spin.setValue(1)
        radius_layout.addWidget(min_radius_spin)
        radius_layout.addWidget(QLabel("Max radius (mm):"))
        max_radius_spin = QSpinBox()
        max_radius_spin.setRange(2, 15)
        max_radius_spin.setValue(4)
        radius_layout.addWidget(max_radius_spin)
        layout.addLayout(radius_layout)

        # Image selection
        img_layout = QHBoxLayout()
        detect_img1 = QCheckBox("Detect on Image 1 (Frontal)")
        detect_img1.setChecked(self.eos_image1 is not None)
        detect_img1.setEnabled(self.eos_image1 is not None)
        detect_img2 = QCheckBox("Detect on Image 2 (Lateral)")
        detect_img2.setChecked(self.eos_image2 is not None)
        detect_img2.setEnabled(self.eos_image2 is not None)
        img_layout.addWidget(detect_img1)
        img_layout.addWidget(detect_img2)
        layout.addLayout(img_layout)

        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec_() != QDialog.Accepted:
            return

        # Get configuration values
        sensitivity = sensitivity_slider.value() / 10.0  # 0.1 to 1.0
        min_radius_mm = min_radius_spin.value()
        max_radius_mm = max_radius_spin.value()
        detect_on_img1 = detect_img1.isChecked()
        detect_on_img2 = detect_img2.isChecked()
        marker_type_filter = marker_type_combo.currentIndex()  # 0=All, 1=Cluster, 2=Single

        # Run detection with progress dialog
        self._run_auto_detection(
            sensitivity=sensitivity,
            min_radius_mm=min_radius_mm,
            max_radius_mm=max_radius_mm,
            detect_on_img1=detect_on_img1,
            detect_on_img2=detect_on_img2,
            marker_type_filter=marker_type_filter
        )

    def _run_auto_detection(
        self,
        sensitivity: float,
        min_radius_mm: float,
        max_radius_mm: float,
        detect_on_img1: bool,
        detect_on_img2: bool,
        marker_type_filter: int
    ) -> None:
        """
        Run automatic marker detection with the given parameters.

        Args:
            sensitivity: Detection sensitivity (0.1 to 1.0)
            min_radius_mm: Minimum marker radius in mm
            max_radius_mm: Maximum marker radius in mm
            detect_on_img1: Whether to detect on image 1
            detect_on_img2: Whether to detect on image 2
            marker_type_filter: 0=All, 1=Cluster only, 2=Single only
        """
        from PyQt5.QtWidgets import QProgressDialog
        from PyQt5.QtCore import Qt

        try:
            from ...algorithms.ellipse_template import CircularMarkerDetector, EllipsePlacementManager, MarkerType

            # Show progress dialog
            progress = QProgressDialog("Detecting markers...", "Cancel", 0, 100, self)
            progress.setWindowModality(Qt.WindowModal)
            progress.setMinimumDuration(0)
            progress.setValue(0)

            detected_count = 0
            all_detected = []

            # Create detector with specified parameters
            detector = CircularMarkerDetector(
                min_radius_mm=min_radius_mm,
                max_radius_mm=max_radius_mm,
                sensitivity=sensitivity
            )

            # Detect on image 1
            if detect_on_img1 and self.eos_image1 is not None:
                progress.setLabelText("Loading image 1...")
                progress.setValue(10)

                if progress.wasCanceled():
                    return

                # Ensure pixel array is loaded
                pixel_array1 = self.eos_image1.load_pixel_array()
                if pixel_array1 is not None:
                    progress.setLabelText("Detecting markers on image 1...")
                    progress.setValue(20)

                    detected1 = detector.detect(
                        pixel_array1,
                        pixel_spacing=self.eos_image1.pixel_spacing_x
                    )

                    progress.setValue(40)

                    # Filter by marker type if specified
                    for marker in detected1:
                        # Calculate diameter in mm
                        diameter_mm = (marker.radius * 2 * self.eos_image1.pixel_spacing_x) * 1000

                        # Filter based on marker type
                        if marker_type_filter == 1 and diameter_mm > 4.0:  # Cluster only
                            continue
                        if marker_type_filter == 2 and diameter_mm <= 4.0:  # Single only
                            continue

                        # Create EllipseParameters
                        from ...algorithms.ellipse_template import EllipseParameters
                        ellipse = EllipseParameters(
                            center_x=marker.x,
                            center_y=marker.y,
                            semi_major=marker.radius,
                            semi_minor=marker.radius,
                            angle=0.0,
                            diameter_mm=diameter_mm,
                            marker_type=MarkerType.CLUSTER if diameter_mm < 4.0 else MarkerType.SINGLE
                        )

                        # Draw and save
                        self._draw_template_ellipse(1, ellipse)
                        self._save_template_ellipse(1, ellipse)
                        detected_count += 1
                        all_detected.append(('Image 1', ellipse))

            if progress.wasCanceled():
                return

            # Detect on image 2
            if detect_on_img2 and self.eos_image2 is not None:
                progress.setLabelText("Loading image 2...")
                progress.setValue(50)

                if progress.wasCanceled():
                    return

                # Ensure pixel array is loaded
                pixel_array2 = self.eos_image2.load_pixel_array()
                if pixel_array2 is not None:
                    progress.setLabelText("Detecting markers on image 2...")
                    progress.setValue(60)

                    detected2 = detector.detect(
                        pixel_array2,
                        pixel_spacing=self.eos_image2.pixel_spacing_x
                    )

                    progress.setValue(80)

                    # Filter by marker type if specified
                    for marker in detected2:
                        # Calculate diameter in mm
                        diameter_mm = (marker.radius * 2 * self.eos_image2.pixel_spacing_x) * 1000

                        # Filter based on marker type
                        if marker_type_filter == 1 and diameter_mm > 4.0:  # Cluster only
                            continue
                        if marker_type_filter == 2 and diameter_mm <= 4.0:  # Single only
                            continue

                        # Create EllipseParameters
                        from ...algorithms.ellipse_template import EllipseParameters
                        ellipse = EllipseParameters(
                            center_x=marker.x,
                            center_y=marker.y,
                            semi_major=marker.radius,
                            semi_minor=marker.radius,
                            angle=0.0,
                            diameter_mm=diameter_mm,
                            marker_type=MarkerType.CLUSTER if diameter_mm < 4.0 else MarkerType.SINGLE
                        )

                        # Draw and save
                        self._draw_template_ellipse(2, ellipse)
                        self._save_template_ellipse(2, ellipse)
                        detected_count += 1
                        all_detected.append(('Image 2', ellipse))

            progress.setValue(100)
            progress.close()

            # Show results
            if detected_count > 0:
                # Build details message
                details = f"Detected {detected_count} circular markers:\n\n"
                for img_name, ellipse in all_detected[:10]:  # Show first 10
                    details += f"  • {img_name}: ({ellipse.center_x:.0f}, {ellipse.center_y:.0f}) - {ellipse.diameter_mm:.1f}mm\n"
                if len(all_detected) > 10:
                    details += f"  ... and {len(all_detected) - 10} more\n"
                details += "\nReview and adjust positions if needed."

                QMessageBox.information(self, "Auto Detection Complete", details)
            else:
                QMessageBox.information(
                    self, "Auto Detection",
                    "No circular markers detected.\n\n"
                    "Tips:\n"
                    "• Try increasing sensitivity\n"
                    "• Adjust the radius range\n"
                    "• Ensure markers are visible in the image\n"
                    "• Use manual placement for difficult cases"
                )

        except ImportError as e:
            QMessageBox.warning(
                self, "Auto Detection",
                f"OpenCV is required for auto-detection.\n\n"
                f"Install with: pip install opencv-python\n\n"
                f"Error: {e}"
            )
        except Exception as e:
            logger.error(f"Auto detection error: {e}", exc_info=True)
            QMessageBox.warning(
                self, "Auto Detection Error",
                f"Error during detection:\n{e}"
            )

    def _place_template_ellipse(self, image_panel: int, abs_x: int, abs_y: int) -> None:
        """
        Place a template ellipse at the clicked position.

        Args:
            image_panel: 1 for frontal, 2 for lateral
            abs_x: Absolute X coordinate in image pixels
            abs_y: Absolute Y coordinate in image pixels
        """
        try:
            from ...algorithms.ellipse_template import EllipseTemplate, EllipsePlacementManager

            # Get the appropriate EOS image
            eos_image = self.eos_image1 if image_panel == 1 else self.eos_image2
            if eos_image is None:
                logger.warning("No EOS image loaded for template placement")
                return

            # Initialize manager if needed
            if image_panel == 1:
                if self._template_manager1 is None:
                    self._template_manager1 = EllipsePlacementManager(eos_image)
                manager = self._template_manager1
            else:
                if self._template_manager2 is None:
                    self._template_manager2 = EllipsePlacementManager(eos_image)
                manager = self._template_manager2

            # Place ellipse based on template mode
            if self._template_mode == 'cluster':
                ellipse = manager.place_cluster_marker(abs_x, abs_y)
            else:  # 'single'
                ellipse = manager.place_single_marker(abs_x, abs_y)

            logger.info(f"Placed {self._template_mode} marker at ({abs_x}, {abs_y})")

            # Draw the ellipse on the image
            self._draw_template_ellipse(image_panel, ellipse)

            # Save to database
            self._save_template_ellipse(image_panel, ellipse)

        except Exception as e:
            logger.error(f"Error placing template ellipse: {e}", exc_info=True)

    def _draw_template_ellipse(self, image_panel: int, ellipse) -> None:
        """
        Draw a template ellipse on the image.

        Args:
            image_panel: 1 for frontal, 2 for lateral
            ellipse: EllipseParameters object
        """
        # Get the image label and current pixmap
        image_label = self.image1_label if image_panel == 1 else self.image2_label
        pixmap = image_label.pixmap()
        if pixmap is None:
            return

        # Create a painter to draw on the pixmap
        from PyQt5.QtGui import QPainter, QPen, QColor

        painter = QPainter(pixmap)
        pen = QPen(QColor(0, 255, 0), 2)  # Green, 2px width
        painter.setPen(pen)

        # Calculate ellipse rectangle
        cx = int(ellipse.center_x)
        cy = int(ellipse.center_y)
        rx = int(ellipse.semi_major)
        ry = int(ellipse.semi_minor)

        # Draw ellipse
        painter.drawEllipse(QPoint(cx, cy), rx, ry)

        # Draw center crosshair
        cross_size = 5
        painter.drawLine(cx - cross_size, cy, cx + cross_size, cy)
        painter.drawLine(cx, cy - cross_size, cx, cy + cross_size)

        painter.end()

        # Update the label
        image_label.setPixmap(pixmap)
        image_label.update()

    def _save_template_ellipse(self, image_panel: int, ellipse) -> None:
        """
        Save a template ellipse to the database.

        Args:
            image_panel: 1 for frontal, 2 for lateral
            ellipse: EllipseParameters object
        """
        if self.sql_db is None or self.subject is None:
            return

        try:
            image_type = "EOS_Frontal" if image_panel == 1 else "EOS_Lateral"
            marker_type = ellipse.marker_type.name if hasattr(ellipse, 'marker_type') else "TEMPLATE"

            subject_code = getattr(self.subject, 'subject_code', 'DEFAULT')
            subject_obj = self.sql_db.get_subject_by_code(subject_code)

            if subject_obj:
                measurement_name = f"Template {marker_type} {image_type}"
                self.sql_db.create_measurement(
                    subject_id=subject_obj.subject_id,
                    measurement_name=measurement_name,
                    measurement_type="Template",
                    image_type=image_type,
                    ellipse_center_x=float(ellipse.center_x),
                    ellipse_center_y=float(ellipse.center_y),
                    ellipse_major_axis=float(ellipse.semi_major),
                    ellipse_minor_axis=float(ellipse.semi_minor),
                    ellipse_angle=float(ellipse.angle),
                    measurement_value=float(ellipse.diameter_mm),
                    measurement_unit="mm",
                    user="User",
                    comment=f"{ellipse.diameter_mm}mm template marker",
                    measurement_date=datetime.now()
                )

                logger.info(f"Saved template ellipse to database: {measurement_name}")

                # Refresh measurements grid
                if self.measurements_main_panel and hasattr(self.measurements_main_panel, 'refresh_measurements'):
                    self.measurements_main_panel.refresh_measurements()

        except Exception as e:
            logger.error(f"Error saving template ellipse to database: {e}", exc_info=True)

    def _on_zoom_in(self) -> None:
        """Handle Zoom In button click - scale up current images."""
        # Scale both images by 1.25x
        if self.image1_label.pixmap():
            current = self.image1_label.pixmap()
            scaled = current.scaled(
                int(current.width() * 1.25),
                int(current.height() * 1.25),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image1_label.setPixmap(scaled)
            self._zoom_scale1 *= 1.25

        if self.image2_label.pixmap():
            current = self.image2_label.pixmap()
            scaled = current.scaled(
                int(current.width() * 1.25),
                int(current.height() * 1.25),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image2_label.setPixmap(scaled)
            self._zoom_scale2 *= 1.25

        print(f"Zoom in: scale={self._zoom_scale1:.2f}")

    def _on_zoom_out(self) -> None:
        """Handle Zoom Out button click - scale down current images."""
        # Scale both images by 0.8x
        if self.image1_label.pixmap():
            current = self.image1_label.pixmap()
            scaled = current.scaled(
                int(current.width() * 0.8),
                int(current.height() * 0.8),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image1_label.setPixmap(scaled)
            self._zoom_scale1 *= 0.8

        if self.image2_label.pixmap():
            current = self.image2_label.pixmap()
            scaled = current.scaled(
                int(current.width() * 0.8),
                int(current.height() * 0.8),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image2_label.setPixmap(scaled)
            self._zoom_scale2 *= 0.8

        print(f"Zoom out: scale={self._zoom_scale1:.2f}")

    def _on_zoom_reset(self) -> None:
        """Handle Zoom Reset button click - restore original images."""
        if self._original_pixmap1:
            self.image1_label.setPixmap(self._original_pixmap1.copy())
            self.upper_left_corner1 = QPoint(0, 0)
            self._zoom_scale1 = 1.0
            self._image1_points.clear()
            self._ellipse1_points.clear()

        if self._original_pixmap2:
            self.image2_label.setPixmap(self._original_pixmap2.copy())
            self.upper_left_corner2 = QPoint(0, 0)
            self._zoom_scale2 = 1.0
            self._image2_points.clear()
            self._ellipse2_points.clear()

        print("Zoom reset to original")

    def _on_image1_mouse_press(self, event: QMouseEvent) -> None:
        """
        Handle mouse press on image 1 (frontal view).

        Implements:
        - Left click: Add point/ellipse annotation
        - Right click: Start zoom selection

        Based on C# pictureBox1_MouseDown (lines 888-944).

        Args:
            event: Mouse event.
        """
        if event.button() == Qt.LeftButton:
            # Single point mode
            if self.btn_point_mode.isChecked():
                img_x, img_y = self._convert_coordinates(self.image1_label, event.x(), event.y())
                abs_x = img_x + self.upper_left_corner1.x()
                abs_y = img_y + self.upper_left_corner1.y()

                # Draw point on image
                self._draw_point_on_label(self.image1_label, event.x(), event.y())

                # Save to database
                self._save_point_annotation(1, abs_x, abs_y, is_single_point=True)

                # Draw suggestion line on opposite image
                self._draw_suggestion_line_at_height(self.image2_label, abs_y, self.upper_left_corner2)

            # Ellipse mode
            elif self.btn_ellipse_mode.isChecked():
                img_x, img_y = self._convert_coordinates(self.image1_label, event.x(), event.y())
                abs_x = img_x + self.upper_left_corner1.x()
                abs_y = img_y + self.upper_left_corner1.y()

                # Draw point on image
                self._draw_point_on_label(self.image1_label, event.x(), event.y())

                # Add to ellipse points collection
                self._ellipse1_points.append(QPoint(abs_x, abs_y))

                # Save to database
                self._save_point_annotation(1, abs_x, abs_y, is_single_point=False)

                # Try to fit ellipse and draw suggestion line
                center_y = self._calculate_and_fit_ellipse(1)
                if center_y != -1:
                    self._draw_suggestion_line_at_height(self.image2_label, center_y, self.upper_left_corner2)

            # Template mode (Saïd's suggestion: 1-click placement)
            elif self._template_mode is not None:
                img_x, img_y = self._convert_coordinates(self.image1_label, event.x(), event.y())
                abs_x = img_x + self.upper_left_corner1.x()
                abs_y = img_y + self.upper_left_corner1.y()

                # Place template ellipse with 1 click
                self._place_template_ellipse(1, abs_x, abs_y)

                # Draw suggestion line on opposite image
                self._draw_suggestion_line_at_height(self.image2_label, abs_y, self.upper_left_corner2)

            # Circle preview mode
            elif self._draw_circle:
                self._is_moving = True
                self.mouse_down_position = event.pos()

        elif event.button() == Qt.RightButton:
            # Start zoom selection
            img_x, img_y = self._convert_coordinates(self.image1_label, event.x(), event.y())

            if not self.image1_label.pixmap():
                return

            # Check bounds
            if img_x < 0 or img_x > self.image1_label.pixmap().width():
                self._selecting = False
                return
            if img_y < 0 or img_y > self.image1_label.pixmap().height():
                self._selecting = False
                return

            self._selecting = True
            self._selection = QRect(QPoint(img_x, img_y), QRect().size())
            self._selection_local = QRect(event.pos(), QRect().size())

    def _on_image1_mouse_move(self, event: QMouseEvent) -> None:
        """
        Handle mouse move on image 1 (frontal view).

        Updates coordinate display and handles selection box preview.
        Based on C# pictureBox1_MouseMove (lines 847-886).

        Args:
            event: Mouse event.
        """
        if not self.image1_label.pixmap():
            return

        # Convert coordinates for display
        img_x, img_y = self._convert_coordinates(self.image1_label, event.x(), event.y())
        abs_x = img_x + self.upper_left_corner1.x()
        abs_y = img_y + self.upper_left_corner1.y()

        # Update coordinate display (would show in status bar)
        # print(f"Image 1: X={abs_x}, Y={abs_y}")

        # Update selection box if selecting
        if self._selecting:
            img_width = self.image1_label.pixmap().width()
            img_height = self.image1_label.pixmap().height()

            # Update selection rectangle
            if img_x > img_width:
                self._selection.setWidth(img_width - self._selection.x())
            else:
                self._selection.setWidth(img_x - self._selection.x())

            if img_y > img_height:
                self._selection.setHeight(img_height - self._selection.y())
            else:
                self._selection.setHeight(img_y - self._selection.y())

            self._selection_local.setWidth(event.x() - self._selection_local.x())
            self._selection_local.setHeight(event.y() - self._selection_local.y())

            self.image1_label.update()  # Trigger repaint

        # Update circle preview if drawing
        if self._draw_circle and self._is_moving:
            self.mouse_move_position = event.pos()
            self.image1_label.update()  # Trigger repaint

    def _on_image1_mouse_release(self, event: QMouseEvent) -> None:
        """
        Handle mouse release on image 1 (frontal view).

        Finalizes zoom selection or circle preview.
        Based on C# pictureBox1_MouseUp (lines 751-785).

        Args:
            event: Mouse event.
        """
        if event.button() == Qt.RightButton and self._selecting:
            # Finalize zoom selection
            if self._selection.height() < 0 or self._selection.width() < 0:
                self._selecting = False
                return

            if not self.image1_label.pixmap():
                self._selecting = False
                return

            # Crop the image to selection
            pixmap = self.image1_label.pixmap()
            cropped = pixmap.copy(self._selection)
            self.image1_label.setPixmap(cropped)

            # Update offset
            self.upper_left_corner1 += QPoint(self._selection.x(), self._selection.y())
            self._selecting = False

        # Circle preview mode
        if self._draw_circle and self._is_moving:
            self._is_moving = False
            self._draw_circle = False
            self.image1_label.update()

    def _on_image2_mouse_press(self, event: QMouseEvent) -> None:
        """
        Handle mouse press on image 2 (lateral view).

        Implements:
        - Left click: Add point/ellipse annotation
        - Right click: Start zoom selection

        Based on C# pictureBox2_MouseDown (lines 262-317).

        Args:
            event: Mouse event.
        """
        if event.button() == Qt.LeftButton:
            # Single point mode
            if self.btn_point_mode.isChecked():
                img_x, img_y = self._convert_coordinates(self.image2_label, event.x(), event.y())
                abs_x = img_x + self.upper_left_corner2.x()
                abs_y = img_y + self.upper_left_corner2.y()

                # Draw point on image
                self._draw_point_on_label(self.image2_label, event.x(), event.y())

                # Save to database
                self._save_point_annotation(2, abs_x, abs_y, is_single_point=True)

                # Draw suggestion line on opposite image
                self._draw_suggestion_line_at_height(self.image1_label, abs_y, self.upper_left_corner1)

            # Ellipse mode
            elif self.btn_ellipse_mode.isChecked():
                img_x, img_y = self._convert_coordinates(self.image2_label, event.x(), event.y())
                abs_x = img_x + self.upper_left_corner2.x()
                abs_y = img_y + self.upper_left_corner2.y()

                # Draw point on image
                self._draw_point_on_label(self.image2_label, event.x(), event.y())

                # Add to ellipse points collection
                self._ellipse2_points.append(QPoint(abs_x, abs_y))

                # Save to database
                self._save_point_annotation(2, abs_x, abs_y, is_single_point=False)

                # Try to fit ellipse and draw suggestion line
                center_y = self._calculate_and_fit_ellipse(2)
                if center_y != -1:
                    self._draw_suggestion_line_at_height(self.image1_label, center_y, self.upper_left_corner1)

            # Template mode (Saïd's suggestion: 1-click placement)
            elif self._template_mode is not None:
                img_x, img_y = self._convert_coordinates(self.image2_label, event.x(), event.y())
                abs_x = img_x + self.upper_left_corner2.x()
                abs_y = img_y + self.upper_left_corner2.y()

                # Place template ellipse with 1 click
                self._place_template_ellipse(2, abs_x, abs_y)

                # Draw suggestion line on opposite image
                self._draw_suggestion_line_at_height(self.image1_label, abs_y, self.upper_left_corner1)

            # Circle preview mode
            elif self._draw_circle:
                self._is_moving = True
                self.mouse_down_position = event.pos()

        elif event.button() == Qt.RightButton:
            # Start zoom selection
            img_x, img_y = self._convert_coordinates(self.image2_label, event.x(), event.y())

            if not self.image2_label.pixmap():
                return

            # Check bounds
            if img_x < 0 or img_x > self.image2_label.pixmap().width():
                self._selecting = False
                return
            if img_y < 0 or img_y > self.image2_label.pixmap().height():
                self._selecting = False
                return

            self._selecting = True
            self._selection = QRect(QPoint(img_x, img_y), QRect().size())
            self._selection_local = QRect(event.pos(), QRect().size())

    def _on_image2_mouse_move(self, event: QMouseEvent) -> None:
        """
        Handle mouse move on image 2 (lateral view).

        Updates coordinate display and handles selection box preview.
        Based on C# pictureBox2_MouseMove (lines 461-495).

        Args:
            event: Mouse event.
        """
        if not self.image2_label.pixmap():
            return

        # Convert coordinates for display
        img_x, img_y = self._convert_coordinates(self.image2_label, event.x(), event.y())
        abs_x = img_x + self.upper_left_corner2.x()
        abs_y = img_y + self.upper_left_corner2.y()

        # Update selection box if selecting
        if self._selecting:
            img_width = self.image2_label.pixmap().width()
            img_height = self.image2_label.pixmap().height()

            # Update selection rectangle
            if img_x > img_width:
                self._selection.setWidth(img_width - self._selection.x())
            else:
                self._selection.setWidth(img_x - self._selection.x())

            if img_y > img_height:
                self._selection.setHeight(img_height - self._selection.y())
            else:
                self._selection.setHeight(img_y - self._selection.y())

            self._selection_local.setWidth(event.x() - self._selection_local.x())
            self._selection_local.setHeight(event.y() - self._selection_local.y())

            self.image2_label.update()  # Trigger repaint

        # Update circle preview if drawing
        if self._draw_circle and self._is_moving:
            self.mouse_move_position = event.pos()
            self.image2_label.update()  # Trigger repaint

    def _on_image2_mouse_release(self, event: QMouseEvent) -> None:
        """
        Handle mouse release on image 2 (lateral view).

        Finalizes zoom selection or circle preview.
        Based on C# pictureBox2_MouseUp (lines 497-532).

        Args:
            event: Mouse event.
        """
        if event.button() == Qt.RightButton and self._selecting:
            # Finalize zoom selection
            if self._selection.height() < 0 or self._selection.width() < 0:
                self._selecting = False
                return

            if not self.image2_label.pixmap():
                self._selecting = False
                return

            # Crop the image to selection
            pixmap = self.image2_label.pixmap()
            cropped = pixmap.copy(self._selection)
            self.image2_label.setPixmap(cropped)

            # Update offset
            self.upper_left_corner2 += QPoint(self._selection.x(), self._selection.y())
            self._selecting = False

        # Circle preview mode
        if self._draw_circle and self._is_moving:
            self._is_moving = False
            self._draw_circle = False
            self.image2_label.update()

    # ========================================================================
    # Helper Methods for Annotation
    # ========================================================================

    def _convert_coordinates(self, label: QLabel, widget_x: int, widget_y: int) -> Tuple[int, int]:
        """
        Convert widget coordinates to image coordinates.

        Handles Qt.KeepAspectRatio scaling mode (Zoom mode).
        Based on C# ConvertCoordinates method (lines 1062-1114).

        Args:
            label: The QLabel containing the image
            widget_x: X coordinate in widget space
            widget_y: Y coordinate in widget space

        Returns:
            Tuple of (image_x, image_y) in image coordinate space
        """
        if not label.pixmap():
            return (widget_x, widget_y)

        pic_height = label.height()
        pic_width = label.width()
        img_height = label.pixmap().height()
        img_width = label.pixmap().width()

        if pic_height == 0 or img_height == 0:
            return (widget_x, widget_y)

        # Calculate aspect ratios
        pic_aspect = pic_width / pic_height
        img_aspect = img_width / img_height

        # For Zoom mode (Qt.KeepAspectRatio)
        if pic_aspect > img_aspect:
            # PictureBox is wider/shorter than the image
            # Image fills the height
            img_y = int(img_height * widget_y / pic_height)

            # Get scaled width
            scaled_width = img_width * pic_height / img_height
            dx = (pic_width - scaled_width) / 2
            img_x = int((widget_x - dx) * img_height / pic_height)
        else:
            # PictureBox is taller/thinner than the image
            # Image fills the width
            img_x = int(img_width * widget_x / pic_width)

            # Get scaled height
            scaled_height = img_height * pic_width / img_width
            dy = (pic_height - scaled_height) / 2
            img_y = int((widget_y - dy) * img_width / pic_width)

        return (img_x, img_y)

    def _draw_point_on_label(self, label: QLabel, widget_x: int, widget_y: int) -> None:
        """
        Draw a point marker on the image label.

        Based on C# DrawPointOnImage (lines 398-408).

        Args:
            label: The image label to draw on
            widget_x: X coordinate in widget space
            widget_y: Y coordinate in widget space
        """
        if not label.pixmap():
            return

        # Get the pixmap and draw on it
        pixmap = label.pixmap().copy()  # Make a copy to avoid modifying original
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # Use green-yellow brush like C# (line 400)
        brush = QBrush(QColor(173, 255, 47))  # GreenYellow
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)

        # Convert to image coordinates for drawing
        img_x, img_y = self._convert_coordinates(label, widget_x, widget_y)

        # Draw circle at the point (7x7 pixels like C#, line 402)
        painter.drawEllipse(QPointF(img_x, img_y), 3.5, 3.5)

        painter.end()
        label.setPixmap(pixmap)
        label.update()

    def _draw_suggestion_line_at_height(self, label: QLabel, image_y: int,
                                        upper_left_corner: QPoint) -> None:
        """
        Draw a horizontal suggestion line on the opposite image.

        Based on C# DrawSuggestionLine (lines 411-431).

        Args:
            label: The image label to draw on
            image_y: Y coordinate in image space (absolute)
            upper_left_corner: Upper left corner offset for this image
        """
        if not label.pixmap():
            return

        # Get the pixmap and draw on it
        pixmap = label.pixmap().copy()
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)

        # SlateBlue pen like C# (lines 428-429)
        pen = QPen(QColor(106, 90, 205), 5)  # SlateBlue, width 5
        painter.setPen(pen)

        # Adjust Y coordinate for current zoom
        local_y = image_y - upper_left_corner.y()

        # Draw horizontal line across the image
        painter.drawLine(0, local_y, pixmap.width(), local_y)

        painter.end()
        label.setPixmap(pixmap)
        label.update()

    def _save_point_annotation(self, image_panel: int, image_x: int, image_y: int,
                                is_single_point: bool) -> None:
        """
        Save a point annotation to the database.

        Based on C# SavePointOnImage (lines 318-366).

        Args:
            image_panel: 1 for frontal, 2 for lateral
            image_x: X coordinate in image space
            image_y: Y coordinate in image space
            is_single_point: True for single point, False for ellipse point
        """
        # Determine image type
        image_type = "EOS_Frontal" if image_panel == 1 else "EOS_Lateral"

        # Log the annotation
        logger.info(f"Point annotation: panel={image_panel}, x={image_x}, y={image_y}, "
                   f"single={is_single_point}")

        # If single point and database available, save it
        if is_single_point and self.sql_db and self.subject:
            try:
                # Get or create subject
                subject_code = getattr(self.subject, 'subject_code', 'DEFAULT')
                subject_obj = self.sql_db.get_subject_by_code(subject_code)

                if subject_obj is None:
                    subject_name = getattr(self.subject, 'name', 'Unknown')
                    subject_obj = self.sql_db.create_subject(
                        subject_code=subject_code,
                        name=subject_name
                    )

                # Create measurement
                measurement_name = f"Point {image_type}"
                self.sql_db.create_measurement(
                    subject_id=subject_obj.subject_id,
                    measurement_name=measurement_name,
                    measurement_type="Point",
                    image_type=image_type,
                    x_coord=float(image_x),
                    y_coord=float(image_y),
                    user="User",
                    measurement_date=datetime.now()
                )

                logger.info(f"Saved point to database: {measurement_name}")

                # Refresh measurements grid if available
                if self.measurements_main_panel and hasattr(self.measurements_main_panel, 'refresh_measurements'):
                    self.measurements_main_panel.refresh_measurements()

            except Exception as e:
                logger.error(f"Error saving point to database: {e}", exc_info=True)

    def _calculate_and_fit_ellipse(self, image_panel: int) -> int:
        """
        Calculate ellipse center from collected points using EllipseFit algorithm.

        Based on C# CalculateEllipseCenter (lines 1117-1224).

        Args:
            image_panel: 1 for frontal, 2 for lateral

        Returns:
            Y-coordinate of ellipse center, or -1 if insufficient points
        """
        # Get points for the selected panel
        points = self._ellipse1_points if image_panel == 1 else self._ellipse2_points

        if len(points) < 5:
            logger.debug(f"Not enough points for ellipse fitting: {len(points)}/5")
            return -1

        try:
            # Import EllipseFit
            from ...algorithms.ellipse_fit import EllipseFit
            from ...core.ellipse_point import EllipsePoint

            # Filter duplicate or near-duplicate points (like C#, lines 1191-1200)
            unique_points = []
            x_values = []
            y_values = []

            for p in points:
                x, y = p.x(), p.y()

                # Check if this point is too close to an existing point
                is_duplicate = False
                for existing_x, existing_y in zip(x_values, y_values):
                    if (abs(x - existing_x) <= 1 and abs(y - existing_y) <= 1):
                        is_duplicate = True
                        break

                if not is_duplicate:
                    unique_points.append(EllipsePoint(x, y))
                    x_values.append(x)
                    y_values.append(y)

            if len(unique_points) < 5:
                logger.debug(f"Not enough unique points for ellipse fitting: {len(unique_points)}/5")
                return -1

            # Fit ellipse
            fitter = EllipseFit()
            coefficients = fitter.fit(unique_points)

            # Get ellipse parameters (lines 1215-1216 in C#)
            (cx, cy), (a, b), angle = fitter.get_ellipse_parameters(coefficients)

            logger.info(f"Ellipse fitted: center=({cx:.1f}, {cy:.1f}), "
                       f"axes=({a:.1f}, {b:.1f}), angle={angle:.1f}°")

            # Save center point to database (line 1220 in C#)
            self._save_point_annotation(image_panel, int(cx), int(cy), is_single_point=True)

            # Save full ellipse measurement if database available
            if self.sql_db and self.subject:
                image_type = "EOS_Frontal" if image_panel == 1 else "EOS_Lateral"

                try:
                    subject_code = getattr(self.subject, 'subject_code', 'DEFAULT')
                    subject_obj = self.sql_db.get_subject_by_code(subject_code)

                    if subject_obj:
                        measurement_name = f"Ellipse {image_type}"
                        self.sql_db.create_measurement(
                            subject_id=subject_obj.subject_id,
                            measurement_name=measurement_name,
                            measurement_type="Ellipse",
                            image_type=image_type,
                            ellipse_center_x=float(cx),
                            ellipse_center_y=float(cy),
                            ellipse_major_axis=float(a),
                            ellipse_minor_axis=float(b),
                            ellipse_angle=float(angle),
                            measurement_value=float(a),
                            measurement_unit="pixels",
                            user="User",
                            measurement_date=datetime.now()
                        )

                        logger.info(f"Saved ellipse to database: {measurement_name}")

                        # Refresh measurements grid
                        if self.measurements_main_panel and hasattr(self.measurements_main_panel, 'refresh_measurements'):
                            self.measurements_main_panel.refresh_measurements()

                except Exception as e:
                    logger.error(f"Error saving ellipse to database: {e}", exc_info=True)

            return int(cy)

        except Exception as e:
            logger.error(f"Error fitting ellipse: {e}", exc_info=True)
            return -1

    def save_point_measurement(
        self,
        x: float,
        y: float,
        image_type: str,
        measurement_name: str = None,
        comment: str = None,
        user: str = None
    ) -> bool:
        """
        Save a point measurement to the database.

        Args:
            x: X coordinate of the point.
            y: Y coordinate of the point.
            image_type: Type of image (e.g., "EOS_Frontal", "EOS_Lateral").
            measurement_name: Name of the measurement (optional, will prompt if None).
            comment: Comment about the measurement.
            user: User who performed the measurement.

        Returns:
            True if saved successfully, False otherwise.
        """
        if self.sql_db is None:
            QMessageBox.warning(
                self,
                "Database Error",
                "Database not connected. Cannot save measurement."
            )
            return False

        if self.subject is None:
            QMessageBox.warning(
                self,
                "Subject Error",
                "No subject selected. Please select a subject first."
            )
            return False

        try:
            # Prompt for measurement name if not provided
            if measurement_name is None:
                measurement_name, ok = QInputDialog.getText(
                    self,
                    "Measurement Name",
                    "Enter measurement name:",
                    text="Point Measurement"
                )
                if not ok or not measurement_name:
                    return False

            # Prompt for comment if not provided
            if comment is None:
                comment, ok = QInputDialog.getText(
                    self,
                    "Measurement Comment",
                    "Enter comment (optional):"
                )
                if not ok:
                    comment = ""

            # Get or create subject
            subject_obj = self.sql_db.get_subject_by_code(self.subject.subject_code if hasattr(self.subject, 'subject_code') else "DEFAULT")
            if subject_obj is None:
                # Create new subject if it doesn't exist
                subject_code = self.subject.subject_code if hasattr(self.subject, 'subject_code') else "DEFAULT"
                subject_name = self.subject.name if hasattr(self.subject, 'name') else "Unknown"
                subject_obj = self.sql_db.create_subject(
                    subject_code=subject_code,
                    name=subject_name
                )

            # Create measurement
            measurement = self.sql_db.create_measurement(
                subject_id=subject_obj.subject_id,
                measurement_name=measurement_name,
                measurement_type="Point",
                image_type=image_type,
                x_coord=x,
                y_coord=y,
                comment=comment,
                user=user or "Unknown",
                measurement_date=datetime.now()
            )

            logger.info(f"Saved point measurement: {measurement_name} at ({x}, {y})")
            QMessageBox.information(
                self,
                "Success",
                f"Measurement '{measurement_name}' saved successfully."
            )

            # Refresh measurements grid if available
            if self.measurements_main_panel is not None:
                self.measurements_main_panel.refresh_measurements()

            return True

        except Exception as e:
            logger.error(f"Error saving point measurement: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Database Error",
                f"Failed to save measurement:\n{e}"
            )
            return False

    def save_ellipse_measurement(
        self,
        center_x: float,
        center_y: float,
        major_axis: float,
        minor_axis: float,
        angle: float,
        image_type: str,
        measurement_name: str = None,
        comment: str = None,
        user: str = None
    ) -> bool:
        """
        Save an ellipse measurement to the database.

        Args:
            center_x: X coordinate of ellipse center.
            center_y: Y coordinate of ellipse center.
            major_axis: Length of major axis.
            minor_axis: Length of minor axis.
            angle: Rotation angle in degrees.
            image_type: Type of image (e.g., "EOS_Frontal", "EOS_Lateral").
            measurement_name: Name of the measurement (optional, will prompt if None).
            comment: Comment about the measurement.
            user: User who performed the measurement.

        Returns:
            True if saved successfully, False otherwise.
        """
        if self.sql_db is None:
            QMessageBox.warning(
                self,
                "Database Error",
                "Database not connected. Cannot save measurement."
            )
            return False

        if self.subject is None:
            QMessageBox.warning(
                self,
                "Subject Error",
                "No subject selected. Please select a subject first."
            )
            return False

        try:
            # Prompt for measurement name if not provided
            if measurement_name is None:
                measurement_name, ok = QInputDialog.getText(
                    self,
                    "Measurement Name",
                    "Enter measurement name:",
                    text="Ellipse Measurement"
                )
                if not ok or not measurement_name:
                    return False

            # Prompt for comment if not provided
            if comment is None:
                comment, ok = QInputDialog.getText(
                    self,
                    "Measurement Comment",
                    "Enter comment (optional):"
                )
                if not ok:
                    comment = ""

            # Get or create subject
            subject_obj = self.sql_db.get_subject_by_code(self.subject.subject_code if hasattr(self.subject, 'subject_code') else "DEFAULT")
            if subject_obj is None:
                # Create new subject if it doesn't exist
                subject_code = self.subject.subject_code if hasattr(self.subject, 'subject_code') else "DEFAULT"
                subject_name = self.subject.name if hasattr(self.subject, 'name') else "Unknown"
                subject_obj = self.sql_db.create_subject(
                    subject_code=subject_code,
                    name=subject_name
                )

            # Create measurement
            measurement = self.sql_db.create_measurement(
                subject_id=subject_obj.subject_id,
                measurement_name=measurement_name,
                measurement_type="Ellipse",
                image_type=image_type,
                ellipse_center_x=center_x,
                ellipse_center_y=center_y,
                ellipse_major_axis=major_axis,
                ellipse_minor_axis=minor_axis,
                ellipse_angle=angle,
                measurement_value=major_axis,  # Store major axis as the primary value
                measurement_unit="pixels",
                comment=comment,
                user=user or "Unknown",
                measurement_date=datetime.now()
            )

            logger.info(f"Saved ellipse measurement: {measurement_name} at ({center_x}, {center_y})")
            QMessageBox.information(
                self,
                "Success",
                f"Ellipse measurement '{measurement_name}' saved successfully."
            )

            # Refresh measurements grid if available
            if self.measurements_main_panel is not None:
                self.measurements_main_panel.refresh_measurements()

            return True

        except Exception as e:
            logger.error(f"Error saving ellipse measurement: {e}", exc_info=True)
            QMessageBox.critical(
                self,
                "Database Error",
                f"Failed to save measurement:\n{e}"
            )
            return False


# ImageLabel class for custom mouse event handling
class ImageLabel(QLabel):
    """
    Custom QLabel for image display with annotation capabilities.

    This class extends QLabel to handle mouse events for drawing
    points and ellipses on medical images.
    """

    def __init__(self, parent, image_num: int = 1):
        """
        Initialize the ImageLabel.

        Args:
            parent: Parent Measurements2DPanel instance.
            image_num: Image number (1 or 2).
        """
        super().__init__()
        self.parent_panel = parent
        self.image_num = image_num

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press events."""
        if self.image_num == 1:
            self.parent_panel._on_image1_mouse_press(event)
        else:
            self.parent_panel._on_image2_mouse_press(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle mouse move events."""
        if self.image_num == 1:
            self.parent_panel._on_image1_mouse_move(event)
        else:
            self.parent_panel._on_image2_mouse_move(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Handle mouse release events."""
        if self.image_num == 1:
            self.parent_panel._on_image1_mouse_release(event)
        else:
            self.parent_panel._on_image2_mouse_release(event)

    def paintEvent(self, event) -> None:
        """
        Custom paint event to draw overlays.

        Draws selection rectangle and circle preview.
        Based on C# pictureBox1_Paint and pictureBox2_Paint (lines 787-845).

        Args:
            event: Paint event
        """
        # First call parent to draw the pixmap
        super().paintEvent(event)

        # Then draw overlays
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw selection rectangle if selecting
        if self.parent_panel._selecting:
            pen = QPen(QColor(173, 255, 47), 2)  # GreenYellow
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(self.parent_panel._selection_local)

        # Draw circle preview if in circle mode
        if self.parent_panel._draw_circle and self.parent_panel._is_moving:
            pen = QPen(QColor(255, 0, 0), 2)  # Red
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)

            # Calculate radius
            dx = self.parent_panel.mouse_down_position.x() - self.parent_panel.mouse_move_position.x()
            dy = self.parent_panel.mouse_down_position.y() - self.parent_panel.mouse_move_position.y()
            radius = np.sqrt(dx*dx + dy*dy)

            # Draw circle
            painter.drawEllipse(
                QPointF(self.parent_panel.mouse_down_position),
                radius,
                radius
            )

        painter.end()
