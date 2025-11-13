#!/usr/bin/env python3
"""
Test script to verify that the sample data works with the translated Python code.
Tests the core modules: Position, EllipsePoint, EosImage, and EosSpace.
"""

import sys
import os

# Add the spine_modeling package to the path
sys.path.insert(0, '/home/user/SpineModelling/SpineModeling_python')

print("=" * 80)
print("SPINE MODELING - SAMPLE DATA TEST")
print("=" * 80)
print()

# Test 1: Import core modules
print("Test 1: Importing core modules...")
try:
    from spine_modeling.core.position import Position
    from spine_modeling.core.ellipse_point import EllipsePoint, PointCollection
    print("✓ Core modules imported successfully")
except Exception as e:
    print(f"✗ Failed to import core modules: {e}")
    sys.exit(1)

# Test 2: Import imaging modules
print("\nTest 2: Importing imaging modules...")
try:
    from spine_modeling.imaging.eos_image import EosImage
    from spine_modeling.imaging.eos_space import EosSpace, Orientation
    print("✓ Imaging modules imported successfully")
except Exception as e:
    print(f"✗ Failed to import imaging modules: {e}")
    sys.exit(1)

# Test 3: Test Position class
print("\nTest 3: Testing Position class...")
try:
    pos1 = Position(1.0, 2.0, 3.0)
    pos2 = Position(4.0, 5.0, 6.0)
    pos3 = pos1 + pos2
    print(f"  Position 1: {pos1}")
    print(f"  Position 2: {pos2}")
    print(f"  Position 1 + 2: {pos3}")
    print(f"  Magnitude of pos3: {pos3.magnitude():.2f}")
    print("✓ Position class working correctly")
except Exception as e:
    print(f"✗ Position class test failed: {e}")

# Test 4: Test EllipsePoint class
print("\nTest 4: Testing EllipsePoint class...")
try:
    point1 = EllipsePoint(10.0, 20.0)
    point2 = EllipsePoint(30.0, 40.0)
    collection = PointCollection()
    collection.append(point1)
    collection.append(point2)
    print(f"  Point 1: {point1}")
    print(f"  Point 2: {point2}")
    print(f"  Collection count: {len(collection)}")
    centroid = collection.centroid()
    print(f"  Centroid: {centroid}")
    print("✓ EllipsePoint class working correctly")
except Exception as e:
    print(f"✗ EllipsePoint class test failed: {e}")

# Test 5: Load sample DICOM files
print("\nTest 5: Loading sample DICOM files...")
sample_data_path = "/home/user/SpineModelling/SpineModeling_python/resources/sample_data/EOS/ASD-043"
frontal_path = os.path.join(sample_data_path, "Patient_F.dcm")
lateral_path = os.path.join(sample_data_path, "Patient_L.dcm")

if not os.path.exists(frontal_path):
    print(f"✗ Frontal DICOM file not found: {frontal_path}")
else:
    print(f"  Frontal DICOM: {frontal_path}")
    print(f"  File size: {os.path.getsize(frontal_path) / 1024 / 1024:.2f} MB")

if not os.path.exists(lateral_path):
    print(f"✗ Lateral DICOM file not found: {lateral_path}")
else:
    print(f"  Lateral DICOM: {lateral_path}")
    print(f"  File size: {os.path.getsize(lateral_path) / 1024 / 1024:.2f} MB")

# Test 6: Load EosImage from DICOM
print("\nTest 6: Loading EOS images from DICOM files...")
try:
    frontal_image = EosImage(directory=frontal_path)
    frontal_image.read_image()
    print(f"  ✓ Frontal image loaded successfully")
    print(f"    Image dimensions: {frontal_image.columns} x {frontal_image.rows} pixels")
    print(f"    Physical size: {frontal_image.width:.3f} x {frontal_image.height:.3f} meters")
    print(f"    Pixel spacing: {frontal_image.pixel_spacing_x*1000:.4f} x {frontal_image.pixel_spacing_y*1000:.4f} mm")
    print(f"    Source to isocenter distance: {frontal_image.distance_source_to_isocenter:.3f} m")
    print(f"    Image plane: {frontal_image.image_plane}")

    lateral_image = EosImage(directory=lateral_path)
    lateral_image.read_image()
    print(f"  ✓ Lateral image loaded successfully")
    print(f"    Image dimensions: {lateral_image.columns} x {lateral_image.rows} pixels")
    print(f"    Physical size: {lateral_image.width:.3f} x {lateral_image.height:.3f} meters")
    print(f"    Pixel spacing: {lateral_image.pixel_spacing_x*1000:.4f} x {lateral_image.pixel_spacing_y*1000:.4f} mm")
    print(f"    Source to isocenter distance: {lateral_image.distance_source_to_isocenter:.3f} m")
    print(f"    Image plane: {lateral_image.image_plane}")

except Exception as e:
    print(f"  ✗ Failed to load EOS images: {e}")
    import traceback
    traceback.print_exc()

# Test 7: Test EosSpace
print("\nTest 7: Testing EosSpace for 3D reconstruction...")
try:
    eos_space = EosSpace(frontal_image, lateral_image)
    print(f"  ✓ EosSpace initialized")
    print(f"    Has frontal image: {eos_space.eos_image_a is not None}")
    print(f"    Has lateral image: {eos_space.eos_image_b is not None}")

    # Calculate the 3D geometry
    eos_space.calculate_eos_space()
    print(f"  ✓ EOS space geometry calculated")
    print(f"    Source 1 position: {eos_space.position_source1}")
    print(f"    Source 2 position: {eos_space.position_source2}")
    print(f"    Patient position: {eos_space.patient_position}")

    # Test orientation
    orientation = Orientation(0, 180, 0)
    print(f"    Orientation test: {orientation}")

except Exception as e:
    print(f"  ✗ EosSpace test failed: {e}")
    import traceback
    traceback.print_exc()

# Test 8: Check for DICOM metadata
print("\nTest 8: Examining DICOM metadata...")
try:
    import pydicom
    ds_frontal = pydicom.dcmread(frontal_path)
    ds_lateral = pydicom.dcmread(lateral_path)

    print(f"  Frontal image metadata:")
    print(f"    Patient ID: {getattr(ds_frontal, 'PatientID', 'N/A')}")
    print(f"    Study Date: {getattr(ds_frontal, 'StudyDate', 'N/A')}")
    print(f"    Modality: {getattr(ds_frontal, 'Modality', 'N/A')}")
    print(f"    Image dimensions: {ds_frontal.Rows} x {ds_frontal.Columns}")
    print(f"    Bits Allocated: {ds_frontal.BitsAllocated}")

    print(f"\n  Lateral image metadata:")
    print(f"    Patient ID: {getattr(ds_lateral, 'PatientID', 'N/A')}")
    print(f"    Study Date: {getattr(ds_lateral, 'StudyDate', 'N/A')}")
    print(f"    Modality: {getattr(ds_lateral, 'Modality', 'N/A')}")
    print(f"    Image dimensions: {ds_lateral.Rows} x {ds_lateral.Columns}")
    print(f"    Bits Allocated: {ds_lateral.BitsAllocated}")

    print("  ✓ DICOM metadata read successfully")

except Exception as e:
    print(f"  ✗ Failed to read DICOM metadata: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)
print("All critical tests completed. Check output above for any failures.")
print()
