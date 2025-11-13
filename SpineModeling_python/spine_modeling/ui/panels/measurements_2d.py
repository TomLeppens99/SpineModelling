"""
2D Measurements Work Panel for SpineModeling Application.

This module provides the panel for 2D image annotation and measurement
on EOS X-ray images (frontal and lateral views).

Translated from: SpineModeling_CSharp/SkeletalModeling/2DMeasurementsWorkpanel.cs
Original class: _2DMeasurementsWorkpanel

Note: This is a streamlined implementation. Complex image manipulation
and annotation features will be refined during integration testing.
"""

from typing import Optional, List, Tuple
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QScrollArea,
    QPushButton, QSplitter, QGroupBox
)
from PyQt5.QtCore import Qt, QPoint, QRect
from PyQt5.QtGui import QPainter, QPen, QPixmap, QImage, QColor, QMouseEvent


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

        # Zoom tracking
        self.upper_left_corner1 = (0, 0, 0)  # (x, y, z)
        self.upper_left_corner2 = (0, 0, 0)

        # Mouse tracking
        self._mouse_down_pos: Optional[QPoint] = None
        self._mouse_move_pos: Optional[QPoint] = None
        self._is_moving: bool = False
        self._draw_circle: bool = False

        # Annotations
        self._circles: List[Tuple[QPoint, QPoint]] = []  # List of (center, radius_point)

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

        self.image1_label = QLabel()
        self.image1_label.setMinimumSize(400, 600)
        self.image1_label.setStyleSheet("border: 1px solid #ccc; background: #000;")
        self.image1_label.setAlignment(Qt.AlignCenter)
        self.image1_label.setScaledContents(False)
        self.image1_label.mousePressEvent = self._on_image1_mouse_press
        self.image1_label.mouseMoveEvent = self._on_image1_mouse_move
        self.image1_label.mouseReleaseEvent = self._on_image1_mouse_release

        scroll1 = QScrollArea()
        scroll1.setWidget(self.image1_label)
        scroll1.setWidgetResizable(True)
        image1_layout.addWidget(scroll1)

        splitter.addWidget(image1_group)

        # Image 2 (Lateral) viewer
        image2_group = QGroupBox("Image 2 (Lateral)")
        image2_layout = QVBoxLayout()
        image2_group.setLayout(image2_layout)

        self.image2_label = QLabel()
        self.image2_label.setMinimumSize(400, 600)
        self.image2_label.setStyleSheet("border: 1px solid #ccc; background: #000;")
        self.image2_label.setAlignment(Qt.AlignCenter)
        self.image2_label.setScaledContents(False)
        self.image2_label.mousePressEvent = self._on_image2_mouse_press
        self.image2_label.mouseMoveEvent = self._on_image2_mouse_move
        self.image2_label.mouseReleaseEvent = self._on_image2_mouse_release

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
        """
        if self.eos_image1 is None or self.eos_image2 is None:
            print("EOS images not set")
            return

        try:
            # Load and display image 1
            if self.eos_image1.pixel_array is not None:
                pixmap1 = self._create_pixmap_from_eos(self.eos_image1)
                self.image1_label.setPixmap(pixmap1)
            else:
                print("Image 1 pixel array not loaded")

            # Load and display image 2
            if self.eos_image2.pixel_array is not None:
                pixmap2 = self._create_pixmap_from_eos(self.eos_image2)
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
            print("Ellipse annotation mode activated")

    def _on_zoom_in(self) -> None:
        """Handle Zoom In button click."""
        print("Zoom in")
        # TODO: Implement zoom functionality

    def _on_zoom_out(self) -> None:
        """Handle Zoom Out button click."""
        print("Zoom out")
        # TODO: Implement zoom functionality

    def _on_zoom_reset(self) -> None:
        """Handle Zoom Reset button click."""
        print("Reset zoom")
        # TODO: Implement zoom reset

    def _on_image1_mouse_press(self, event: QMouseEvent) -> None:
        """
        Handle mouse press on image 1.

        Args:
            event: Mouse event.
        """
        self._mouse_down_pos = event.pos()
        print(f"Image 1 mouse press at {event.pos()}")

        if self.btn_point_mode.isChecked():
            self.single_point_being_drawn_im1 = True
        elif self.btn_ellipse_mode.isChecked():
            self.ellipse_being_drawn_im1 = True

    def _on_image1_mouse_move(self, event: QMouseEvent) -> None:
        """
        Handle mouse move on image 1.

        Args:
            event: Mouse event.
        """
        if self._mouse_down_pos is not None:
            self._mouse_move_pos = event.pos()
            # TODO: Update annotation preview

    def _on_image1_mouse_release(self, event: QMouseEvent) -> None:
        """
        Handle mouse release on image 1.

        Args:
            event: Mouse event.
        """
        print(f"Image 1 mouse release at {event.pos()}")

        if self.single_point_being_drawn_im1:
            # Add point annotation
            # TODO: Implement point annotation
            self.single_point_being_drawn_im1 = False

        elif self.ellipse_being_drawn_im1:
            # Add ellipse annotation
            # TODO: Implement ellipse annotation
            self.ellipse_being_drawn_im1 = False

        self._mouse_down_pos = None
        self._mouse_move_pos = None

    def _on_image2_mouse_press(self, event: QMouseEvent) -> None:
        """
        Handle mouse press on image 2.

        Args:
            event: Mouse event.
        """
        self._mouse_down_pos = event.pos()
        print(f"Image 2 mouse press at {event.pos()}")

        if self.btn_point_mode.isChecked():
            self.single_point_being_drawn_im2 = True
        elif self.btn_ellipse_mode.isChecked():
            self.ellipse_being_drawn_im2 = True

    def _on_image2_mouse_move(self, event: QMouseEvent) -> None:
        """
        Handle mouse move on image 2.

        Args:
            event: Mouse event.
        """
        if self._mouse_down_pos is not None:
            self._mouse_move_pos = event.pos()
            # TODO: Update annotation preview

    def _on_image2_mouse_release(self, event: QMouseEvent) -> None:
        """
        Handle mouse release on image 2.

        Args:
            event: Mouse event.
        """
        print(f"Image 2 mouse release at {event.pos()}")

        if self.single_point_being_drawn_im2:
            # Add point annotation
            # TODO: Implement point annotation
            self.single_point_being_drawn_im2 = False

        elif self.ellipse_being_drawn_im2:
            # Add ellipse annotation
            # TODO: Implement ellipse annotation
            self.ellipse_being_drawn_im2 = False

        self._mouse_down_pos = None
        self._mouse_move_pos = None
