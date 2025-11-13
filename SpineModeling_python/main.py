#!/usr/bin/env python3
"""
SpineModeling Application - Main Entry Point

This is the main entry point for the SpineModeling application, a biomechanical
spine modeling and analysis system ported from C# to Python.

The application provides:
- EOS dual X-ray image analysis
- 2D anatomical measurements with ellipse fitting
- 3D skeletal reconstruction
- OpenSim biomechanical model visualization
- Patient database management

Usage:
    python main.py

Requirements:
    - Python 3.8+
    - PyQt5 (GUI framework)
    - vtk (3D visualization)
    - pydicom (DICOM image reading)
    - numpy, scipy (numerical computing)
    - sqlalchemy (database ORM)
    - opencv-python (image processing)
    - opensim (optional, for biomechanical modeling)
"""

import sys
import os
from pathlib import Path

# Add the package directory to the Python path
package_dir = Path(__file__).parent
sys.path.insert(0, str(package_dir))


def check_dependencies():
    """
    Check if all required dependencies are available.

    Returns:
        tuple: (success: bool, missing_packages: list, warnings: list)
    """
    required_packages = {
        "PyQt5": "PyQt5",
        "numpy": "numpy",
        "scipy": "scipy",
        "pydicom": "pydicom",
        "cv2": "opencv-python",
        "sqlalchemy": "sqlalchemy",
        "vtk": "vtk",
    }

    optional_packages = {
        "opensim": "opensim (required for biomechanical modeling)",
    }

    missing = []
    warnings = []

    # Check required packages
    for module_name, package_name in required_packages.items():
        try:
            __import__(module_name)
        except ImportError:
            missing.append(package_name)

    # Check optional packages
    for module_name, description in optional_packages.items():
        try:
            __import__(module_name)
        except ImportError:
            warnings.append(f"Optional: {description}")

    success = len(missing) == 0
    return success, missing, warnings


def print_system_info():
    """Print system and environment information."""
    import platform
    print("=" * 60)
    print("SpineModeling Application - System Information")
    print("=" * 60)
    print(f"Python Version: {sys.version}")
    print(f"Platform: {platform.platform()}")
    print(f"Architecture: {platform.machine()}")
    print(f"Working Directory: {os.getcwd()}")
    print("=" * 60)


def print_dependency_status(missing, warnings):
    """
    Print dependency check results.

    Args:
        missing: List of missing required packages
        warnings: List of warning messages for optional packages
    """
    if missing:
        print("\nERROR: Missing required dependencies:")
        for pkg in missing:
            print(f"  - {pkg}")
        print("\nPlease install missing dependencies:")
        print(f"  pip install {' '.join(missing)}")
        print("\nOr install all requirements:")
        print("  pip install -r requirements.txt")

    if warnings:
        print("\nWARNING: Optional dependencies not available:")
        for warning in warnings:
            print(f"  - {warning}")
        print("\nSome features may be limited without optional packages.")


def initialize_database():
    """
    Initialize the application database.

    Creates the database file and tables if they don't exist.
    """
    from spine_modeling.database.models import DatabaseManager

    db_path = Path.home() / ".spinemodeling" / "spinemodeling.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)

    db_url = f"sqlite:///{db_path}"
    db_manager = DatabaseManager(db_url)
    db_manager.initialize_database()
    db_manager.close_session()

    print(f"\nDatabase initialized: {db_path}")
    return db_url


def main():
    """
    Main application entry point.

    Initializes the PyQt5 application and launches the main window.
    """
    # Print system information
    print_system_info()

    # Check dependencies
    print("\nChecking dependencies...")
    success, missing, warnings = check_dependencies()
    print_dependency_status(missing, warnings)

    if not success:
        print("\nApplication cannot start due to missing dependencies.")
        return 1

    print("\nAll required dependencies found!")

    # Initialize database
    try:
        db_url = initialize_database()
    except Exception as e:
        print(f"\nERROR: Failed to initialize database: {e}")
        return 1

    # Import PyQt5 (after dependency check)
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import Qt

    # Import main window
    try:
        from spine_modeling.ui.forms.main_window import MainWindow
    except ImportError as e:
        print(f"\nERROR: Failed to import main window: {e}")
        return 1

    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("SpineModeling")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("SpineModeling")

    # Enable high DPI scaling
    if hasattr(Qt, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    # Create and show main window
    print("\nLaunching SpineModeling application...")
    try:
        main_window = MainWindow()
        main_window.show()
    except Exception as e:
        print(f"\nERROR: Failed to create main window: {e}")
        import traceback
        traceback.print_exc()
        return 1

    # Run application event loop
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
