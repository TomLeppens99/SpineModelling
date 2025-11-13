#!/usr/bin/env python3
"""
SpineModeling Integration Test Suite

This script performs comprehensive integration testing of the SpineModeling
application components to ensure all modules work together correctly.

Test Coverage:
1. Database Operations (CRUD for Subject and Measurement)
2. DICOM Image Loading (EOS X-ray files)
3. Ellipse Fitting Algorithm (with sample data)
4. VTK Visualization (initialization and basic rendering)
5. PyQt5 UI Components (forms, panels, dialogs)

Usage:
    python test_integration.py

Results are printed to console and saved to integration_test_report.md
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import traceback

# Add package to path
sys.path.insert(0, str(Path(__file__).parent))

# Test results storage
test_results = []


class TestResult:
    """Store test result information."""

    def __init__(self, name, category, passed, message="", error=None):
        self.name = name
        self.category = category
        self.passed = passed
        self.message = message
        self.error = error
        self.timestamp = datetime.now()

    def __repr__(self):
        status = "PASS" if self.passed else "FAIL"
        return f"[{status}] {self.category}: {self.name}"


def print_header(text):
    """Print formatted section header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def run_test(name, category, test_func):
    """
    Run a single test and record results.

    Args:
        name: Test name
        category: Test category
        test_func: Test function to execute

    Returns:
        TestResult object
    """
    print(f"\n  Testing: {name}...", end=" ")
    try:
        result_message = test_func()
        print("PASS")
        result = TestResult(name, category, True, result_message)
    except Exception as e:
        print("FAIL")
        error_msg = f"{type(e).__name__}: {str(e)}"
        print(f"    Error: {error_msg}")
        result = TestResult(name, category, False, error=error_msg)

    test_results.append(result)
    return result


# ============================================================================
# TEST CATEGORY 1: DATABASE OPERATIONS
# ============================================================================


def test_database_initialization():
    """Test database creation and table initialization."""
    from spine_modeling.database.models import DatabaseManager

    db = DatabaseManager("sqlite:///test_integration_db.db")
    db.initialize_database()
    db.close_session()
    return "Database and tables created successfully"


def test_subject_crud():
    """Test Subject CRUD operations."""
    from spine_modeling.database.models import DatabaseManager

    db = DatabaseManager("sqlite:///test_integration_db.db")

    # Create
    subject = db.create_subject(
        subject_code="TEST-001",
        name="Test Patient",
        gender="F",
        height=165.0,
        weight=58.0
    )
    assert subject.subject_id is not None, "Subject ID not assigned"

    # Read
    retrieved = db.get_subject_by_code("TEST-001")
    assert retrieved is not None, "Failed to retrieve subject"
    assert retrieved.name == "Test Patient", "Subject name mismatch"

    # Update
    updated = db.update_subject(subject.subject_id, height=170.0)
    assert updated.height == 170.0, "Subject update failed"

    # Delete
    deleted = db.delete_subject(subject.subject_id)
    assert deleted, "Subject deletion failed"

    db.close_session()
    return f"Subject CRUD: Create, Read, Update, Delete verified"


def test_measurement_crud():
    """Test Measurement CRUD operations."""
    from spine_modeling.database.models import DatabaseManager

    db = DatabaseManager("sqlite:///test_integration_db.db")

    # Check if subject already exists, delete if so
    existing = db.get_subject_by_code("TEST-002")
    if existing:
        db.delete_subject(existing.subject_id)

    # Create subject first
    subject = db.create_subject(subject_code="TEST-002", name="Test Patient 2")

    # Create measurement
    measurement = db.create_measurement(
        subject_id=subject.subject_id,
        measurement_name="Pedicle Width L2",
        measurement_value=8.5,
        measurement_unit="mm",
        measurement_type="Ellipse",
        image_type="EOS_Frontal"
    )
    assert measurement.measurement_id is not None, "Measurement ID not assigned"

    # Read
    measurements = db.get_measurements_by_subject(subject.subject_id)
    assert len(measurements) == 1, f"Expected 1 measurement, got {len(measurements)}"

    # Update
    updated = db.update_measurement(measurement.measurement_id, measurement_value=9.0)
    assert updated.measurement_value == 9.0, "Measurement update failed"

    # Delete
    deleted = db.delete_measurement(measurement.measurement_id)
    assert deleted, "Measurement deletion failed"

    db.close_session()
    return f"Measurement CRUD: Create, Read, Update, Delete verified"


# ============================================================================
# TEST CATEGORY 2: DICOM IMAGE LOADING
# ============================================================================


def test_dicom_decoder_import():
    """Test DICOM decoder module import."""
    from spine_modeling.imaging.dicom_decoder import DicomDecoder
    from spine_modeling.imaging.dicom_dictionary import DicomDictionary

    return "DicomDecoder and DicomDictionary imported successfully"


def test_dicom_dictionary():
    """Test DICOM dictionary functionality."""
    from spine_modeling.imaging.dicom_dictionary import DicomDictionary

    dd = DicomDictionary()
    assert dd.get_tag_tuple("PatientName") == (0x0010, 0x0010), "PatientName tag incorrect"
    assert dd.get_vr("00100010") == "PN", "PatientName VR incorrect"
    assert "Patient" in dd.get_description("00100010"), "Description not found"

    return f"DICOM dictionary: {len(dd.dict)} tags verified"


def test_eos_image_loading():
    """Test loading EOS DICOM images."""
    from spine_modeling.imaging.eos_image import EosImage

    sample_data_dir = Path(__file__).parent / "SpineModeling_python" / "resources" / "sample_data" / "EOS" / "ASD-043"
    frontal_path = sample_data_dir / "Patient_F.dcm"
    lateral_path = sample_data_dir / "Patient_L.dcm"

    if not frontal_path.exists():
        return f"SKIPPED: Sample data not found at {frontal_path}"

    # Load frontal image
    eos_front = EosImage(str(frontal_path))
    assert eos_front.file_path == str(frontal_path), "File path not set"
    assert eos_front.rows > 0, "Image rows not loaded"
    assert eos_front.columns > 0, "Image columns not loaded"

    # Load lateral image
    eos_lat = EosImage(str(lateral_path))
    assert eos_lat.rows > 0, "Lateral image rows not loaded"

    return f"EOS images loaded: F={eos_front.rows}x{eos_front.columns}, L={eos_lat.rows}x{eos_lat.columns}"


# ============================================================================
# TEST CATEGORY 3: ALGORITHMS
# ============================================================================


def test_ellipse_fit_import():
    """Test ellipse fitting module import."""
    from spine_modeling.algorithms.ellipse_fit import EllipseFit

    return "EllipseFit imported successfully"


def test_ellipse_fit_perfect_circle():
    """Test ellipse fitting on perfect circle data."""
    import numpy as np
    from spine_modeling.algorithms.ellipse_fit import EllipseFit

    # Generate perfect circle
    theta = np.linspace(0, 2 * np.pi, 50)
    radius = 10.0
    center_x, center_y = 15.0, 20.0
    x = center_x + radius * np.cos(theta)
    y = center_y + radius * np.sin(theta)
    points = np.column_stack([x, y])

    # Fit ellipse
    fitter = EllipseFit()
    coeffs = fitter.fit(points)
    center, axes, angle = fitter.get_ellipse_parameters(coeffs)

    # Verify (should be a circle)
    center_error = np.sqrt((center[0] - center_x)**2 + (center[1] - center_y)**2)
    assert center_error < 0.01, f"Center error too large: {center_error}"

    axes_mean = (axes[0] + axes[1]) / 2
    radius_error = abs(axes_mean - radius)
    assert radius_error < 0.01, f"Radius error too large: {radius_error}"

    return f"Perfect circle fit: center error={center_error:.6f}, radius error={radius_error:.6f}"


def test_ellipse_fit_noisy_ellipse():
    """Test ellipse fitting on noisy ellipse data."""
    import numpy as np
    from spine_modeling.algorithms.ellipse_fit import EllipseFit

    # Generate ellipse with noise
    theta = np.linspace(0, 2 * np.pi, 100)
    a, b = 15.0, 8.0  # major, minor axes
    center_x, center_y = 10.0, 15.0
    angle_deg = 30.0
    angle_rad = np.deg2rad(angle_deg)

    x = center_x + a * np.cos(theta) * np.cos(angle_rad) - b * np.sin(theta) * np.sin(angle_rad)
    y = center_y + a * np.cos(theta) * np.sin(angle_rad) + b * np.sin(theta) * np.cos(angle_rad)

    # Add noise
    noise = np.random.normal(0, 0.5, (len(x), 2))
    points = np.column_stack([x + noise[:, 0], y + noise[:, 1]])

    # Fit ellipse
    fitter = EllipseFit()
    coeffs = fitter.fit(points)
    center, axes, fitted_angle = fitter.get_ellipse_parameters(coeffs)

    # Compute fit error
    mean_error, max_error = fitter.compute_fit_error(coeffs, points)

    center_x = float(center[0])
    center_y = float(center[1])

    return f"Noisy ellipse fit: mean error={mean_error:.6f}, center=({center_x:.2f}, {center_y:.2f})"


# ============================================================================
# TEST CATEGORY 4: CORE DATA MODELS
# ============================================================================


def test_position_class():
    """Test Position class functionality."""
    from spine_modeling.core.position import Position

    p1 = Position(1.0, 2.0, 3.0)
    p2 = Position(4.0, 5.0, 6.0)

    # Test arithmetic
    p3 = p1 + p2
    assert p3.x == 5.0 and p3.y == 7.0 and p3.z == 9.0, "Addition failed"

    # Test magnitude
    p4 = Position(3.0, 4.0, 0.0)
    assert abs(p4.magnitude() - 5.0) < 0.01, "Magnitude calculation failed"

    return "Position class: arithmetic and magnitude verified"


def test_ellipse_point_class():
    """Test EllipsePoint and PointCollection classes."""
    from spine_modeling.core.ellipse_point import EllipsePoint, PointCollection

    # Create points
    p1 = EllipsePoint(10.0, 20.0)
    p2 = EllipsePoint(15.0, 25.0)

    # Test collection
    collection = PointCollection()
    collection.append(p1)
    collection.append(p2)

    assert len(collection) == 2, "Collection length incorrect"

    # Test centroid
    centroid = collection.centroid()
    assert centroid.x == 12.5 and centroid.y == 22.5, "Centroid calculation failed"

    return f"EllipsePoint and PointCollection: {len(collection)} points, centroid verified"


# ============================================================================
# TEST CATEGORY 5: VTK VISUALIZATION
# ============================================================================


def test_vtk_import():
    """Test VTK module import."""
    import vtk

    version = vtk.vtkVersion.GetVTKVersion()
    return f"VTK imported successfully (version {version})"


def test_vtk_basic_rendering():
    """Test basic VTK rendering setup."""
    import vtk

    # Create renderer
    renderer = vtk.vtkRenderer()
    renderer.SetBackground(0.1, 0.2, 0.3)

    # Create render window
    render_window = vtk.vtkRenderWindow()
    render_window.AddRenderer(renderer)
    render_window.SetSize(800, 600)

    # Create simple sphere
    sphere = vtk.vtkSphereSource()
    sphere.SetRadius(10.0)

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(sphere.GetOutputPort())

    actor = vtk.vtkActor()
    actor.SetMapper(mapper)

    renderer.AddActor(actor)

    return "VTK rendering pipeline: renderer, window, sphere actor created"


def test_sim_model_visualization_import():
    """Test SimModelVisualization import."""
    from spine_modeling.visualization.sim_model_visualization import SimModelVisualization

    return "SimModelVisualization imported successfully"


# ============================================================================
# TEST CATEGORY 6: PYQT5 UI COMPONENTS
# ============================================================================


def test_pyqt5_import():
    """Test PyQt5 module import."""
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import QT_VERSION_STR

    return f"PyQt5 imported successfully (Qt version {QT_VERSION_STR})"


def test_main_window_import():
    """Test MainWindow import."""
    from spine_modeling.ui.forms.main_window import MainWindow

    return "MainWindow imported successfully"


def test_image_analysis_form_import():
    """Test ImageAnalysisForm import."""
    from spine_modeling.ui.forms.image_analysis import ImageAnalysisForm

    return "ImageAnalysisForm imported successfully"


def test_panels_import():
    """Test UI panels import."""
    from spine_modeling.ui.panels.measurements_2d import Measurements2DPanel
    from spine_modeling.ui.panels.modeling_3d import Modeling3DPanel
    from spine_modeling.ui.panels.measurements_main import MeasurementsMainPanel

    return "All UI panels imported successfully"


def test_dialogs_import():
    """Test UI dialogs import."""
    from spine_modeling.ui.dialogs.component_property import ComponentPropertyDialog
    from spine_modeling.ui.dialogs.logs_and_messages import LogsAndMessagesDialog
    from spine_modeling.ui.dialogs.model_templates import ModelTemplatesDialog
    from spine_modeling.ui.dialogs.preferences import SkeletalModelingPreferencesDialog

    return "All UI dialogs imported successfully"


# ============================================================================
# MAIN TEST RUNNER
# ============================================================================


def run_all_tests():
    """Run all integration tests."""
    print_header("SPINEMODELING INTEGRATION TEST SUITE")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Category 1: Database Operations
    print_header("CATEGORY 1: DATABASE OPERATIONS")
    run_test("Database Initialization", "Database", test_database_initialization)
    run_test("Subject CRUD Operations", "Database", test_subject_crud)
    run_test("Measurement CRUD Operations", "Database", test_measurement_crud)

    # Category 2: DICOM Image Loading
    print_header("CATEGORY 2: DICOM IMAGE LOADING")
    run_test("DICOM Decoder Import", "DICOM", test_dicom_decoder_import)
    run_test("DICOM Dictionary", "DICOM", test_dicom_dictionary)
    run_test("EOS Image Loading", "DICOM", test_eos_image_loading)

    # Category 3: Algorithms
    print_header("CATEGORY 3: ALGORITHMS")
    run_test("Ellipse Fit Import", "Algorithms", test_ellipse_fit_import)
    run_test("Ellipse Fit - Perfect Circle", "Algorithms", test_ellipse_fit_perfect_circle)
    run_test("Ellipse Fit - Noisy Ellipse", "Algorithms", test_ellipse_fit_noisy_ellipse)

    # Category 4: Core Data Models
    print_header("CATEGORY 4: CORE DATA MODELS")
    run_test("Position Class", "Core", test_position_class)
    run_test("EllipsePoint and PointCollection", "Core", test_ellipse_point_class)

    # Category 5: VTK Visualization
    print_header("CATEGORY 5: VTK VISUALIZATION")
    run_test("VTK Import", "VTK", test_vtk_import)
    run_test("VTK Basic Rendering", "VTK", test_vtk_basic_rendering)
    run_test("SimModelVisualization Import", "VTK", test_sim_model_visualization_import)

    # Category 6: PyQt5 UI Components
    print_header("CATEGORY 6: PYQT5 UI COMPONENTS")
    run_test("PyQt5 Import", "UI", test_pyqt5_import)
    run_test("MainWindow Import", "UI", test_main_window_import)
    run_test("ImageAnalysisForm Import", "UI", test_image_analysis_form_import)
    run_test("Panels Import", "UI", test_panels_import)
    run_test("Dialogs Import", "UI", test_dialogs_import)


def print_summary():
    """Print test summary."""
    print_header("TEST SUMMARY")

    total = len(test_results)
    passed = sum(1 for r in test_results if r.passed)
    failed = total - passed

    print(f"\n  Total Tests: {total}")
    print(f"  Passed: {passed} ({100*passed//total if total > 0 else 0}%)")
    print(f"  Failed: {failed}")

    if failed > 0:
        print("\n  Failed Tests:")
        for result in test_results:
            if not result.passed:
                print(f"    - {result.category}: {result.name}")
                print(f"      Error: {result.error}")

    # Group by category
    categories = {}
    for result in test_results:
        if result.category not in categories:
            categories[result.category] = {"passed": 0, "failed": 0}
        if result.passed:
            categories[result.category]["passed"] += 1
        else:
            categories[result.category]["failed"] += 1

    print("\n  Results by Category:")
    for category, counts in sorted(categories.items()):
        total_cat = counts["passed"] + counts["failed"]
        print(f"    {category}: {counts['passed']}/{total_cat} passed")


def generate_report():
    """Generate markdown test report."""
    report_path = Path(__file__).parent / "integration_test_report.md"

    with open(report_path, "w") as f:
        f.write("# SpineModeling Integration Test Report\n\n")
        f.write(f"**Date**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

        total = len(test_results)
        passed = sum(1 for r in test_results if r.passed)
        failed = total - passed

        f.write("## Summary\n\n")
        f.write(f"- **Total Tests**: {total}\n")
        f.write(f"- **Passed**: {passed} ({100*passed//total if total > 0 else 0}%)\n")
        f.write(f"- **Failed**: {failed}\n\n")

        # Group by category
        categories = {}
        for result in test_results:
            if result.category not in categories:
                categories[result.category] = []
            categories[result.category].append(result)

        f.write("## Detailed Results\n\n")
        for category, results in sorted(categories.items()):
            f.write(f"### {category}\n\n")
            for result in results:
                status = "✓ PASS" if result.passed else "✗ FAIL"
                f.write(f"- {status}: **{result.name}**\n")
                if result.message:
                    f.write(f"  - {result.message}\n")
                if result.error:
                    f.write(f"  - Error: `{result.error}`\n")
            f.write("\n")

    print(f"\n  Report saved to: {report_path}")


def main():
    """Main test execution."""
    try:
        run_all_tests()
        print_summary()
        generate_report()

        # Return exit code based on results
        failed = sum(1 for r in test_results if not r.passed)
        return 0 if failed == 0 else 1

    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        traceback.print_exc()
        return 2


if __name__ == "__main__":
    sys.exit(main())
