#!/usr/bin/env python3
"""
Test script for 3D visualization functionality.

This script tests:
1. Loading STL vertebrae meshes
2. Loading EOS DICOM images
3. Displaying both in 3D space
"""

import sys
import os

# Add the SpineModeling_python directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'SpineModeling_python'))

def test_3d_visualization():
    """Test the 3D visualization functionality."""
    print("=" * 60)
    print("Testing 3D Visualization Functionality")
    print("=" * 60)
    print()

    # Import required modules
    print("1. Importing modules...")
    try:
        from PyQt5.QtWidgets import QApplication
        from spine_modeling.ui.forms.image_analysis import ImageAnalysisForm
        from spine_modeling.imaging.eos_image import EosImage
        from spine_modeling.imaging.eos_space import EosSpace
        print("   ✓ Modules imported successfully")
    except ImportError as e:
        print(f"   ✗ Failed to import modules: {e}")
        return False

    # Create Qt application
    print("\n2. Creating Qt application...")
    app = QApplication(sys.argv)
    print("   ✓ Qt application created")

    # Create main form
    print("\n3. Creating image analysis form...")
    form = ImageAnalysisForm()
    print("   ✓ Form created successfully")

    # Check that 3D modeling panel exists
    print("\n4. Checking 3D modeling panel...")
    if form.modeling_3d_panel is None:
        print("   ✗ 3D modeling panel not initialized")
        return False
    print("   ✓ 3D modeling panel exists")

    # Check for sample data
    print("\n5. Checking for sample data...")
    sample_data_dir = os.path.join(
        os.path.dirname(__file__),
        'SpineModeling_python',
        'resources',
        'sample_data'
    )

    # Check for EOS images
    eos_frontal = os.path.join(sample_data_dir, 'EOS', 'ASD-043', 'Patient_F.dcm')
    eos_lateral = os.path.join(sample_data_dir, 'EOS', 'ASD-043', 'Patient_L.dcm')

    if os.path.exists(eos_frontal) and os.path.exists(eos_lateral):
        print(f"   ✓ Found EOS images:")
        print(f"     - Frontal: {eos_frontal}")
        print(f"     - Lateral: {eos_lateral}")
    else:
        print("   ✗ EOS images not found")
        return False

    # Check for STL meshes
    stl_dir = os.path.join(sample_data_dir, 'CT', 'ASD-043')
    stl_files = []
    if os.path.exists(stl_dir):
        stl_files = [f for f in os.listdir(stl_dir) if f.endswith('.stl')]
        if stl_files:
            print(f"   ✓ Found {len(stl_files)} STL mesh files:")
            for stl_file in stl_files:
                print(f"     - {stl_file}")
        else:
            print("   ⚠ No STL mesh files found")
    else:
        print("   ⚠ STL directory not found")

    # Test loading EOS images
    print("\n6. Testing EOS image loading...")
    try:
        form.load_eos_images(eos_frontal, eos_lateral)
        print("   ✓ EOS images loaded successfully")

        # Check if images are displayed in 3D
        if form.modeling_3d_panel.eos_image_actor1 is not None:
            print("   ✓ EOS Image 1 (frontal) displayed in 3D")
        else:
            print("   ⚠ EOS Image 1 not displayed in 3D")

        if form.modeling_3d_panel.eos_image_actor2 is not None:
            print("   ✓ EOS Image 2 (lateral) displayed in 3D")
        else:
            print("   ⚠ EOS Image 2 not displayed in 3D")

    except Exception as e:
        print(f"   ✗ Failed to load EOS images: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test loading STL meshes
    if stl_files:
        print("\n7. Testing STL mesh loading...")
        try:
            import vtk

            stl_path = os.path.join(stl_dir, stl_files[0])
            print(f"   Loading: {stl_files[0]}")

            # Create STL reader
            stl_reader = vtk.vtkSTLReader()
            stl_reader.SetFileName(stl_path)
            stl_reader.Update()

            # Create mapper and actor
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(stl_reader.GetOutputPort())

            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(0.9, 0.9, 0.8)
            actor.GetProperty().SetOpacity(0.8)

            # Add to 3D panel
            form.modeling_3d_panel.add_stl_actor(actor, name=stl_files[0])

            print(f"   ✓ STL mesh loaded and displayed in 3D")

        except Exception as e:
            print(f"   ✗ Failed to load STL mesh: {e}")
            import traceback
            traceback.print_exc()

    # Show the form
    print("\n8. Displaying the application window...")
    print("   (Close the window to complete the test)")
    form.show()

    # Run the application
    print("\n" + "=" * 60)
    print("Application is running. You should see:")
    print("  - The main application window")
    print("  - EOS X-ray images in the 3D viewport (if loaded successfully)")
    print("  - Vertebra mesh in the 3D viewport (if loaded successfully)")
    print("\nClose the window to exit the test.")
    print("=" * 60)

    sys.exit(app.exec_())


if __name__ == '__main__':
    test_3d_visualization()
