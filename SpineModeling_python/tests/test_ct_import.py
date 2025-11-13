"""Test script for CT vertebral model import functionality."""

import sys
import os

# Add project to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from spine_modeling.visualization.geometry_loader import GeometryLoader, CT3DModelLoader
from spine_modeling.visualization.properties.osim_geometry_property import OsimGeometryProperty


def test_geometry_loader():
    """Test basic geometry loading functionality."""
    print("\n" + "="*60)
    print("TEST 1: GeometryLoader Basic Functionality")
    print("="*60)

    # Find sample STL files
    sample_data_dir = os.path.join(project_root, "resources", "sample_data", "CT", "ASD-043")

    if not os.path.exists(sample_data_dir):
        print(f"❌ Sample data directory not found: {sample_data_dir}")
        return False

    # Test loading L2 vertebra
    l2_file = os.path.join(sample_data_dir, "L2_001.stl")

    if not os.path.exists(l2_file):
        print(f"❌ L2 file not found: {l2_file}")
        return False

    print(f"Loading: {l2_file}")

    try:
        polydata = GeometryLoader.load_geometry(l2_file)

        if polydata is None:
            print("❌ Failed to load polydata")
            return False

        num_points = polydata.GetNumberOfPoints()
        num_cells = polydata.GetNumberOfCells()

        print(f"✓ Successfully loaded L2 vertebra")
        print(f"  - Points: {num_points}")
        print(f"  - Cells: {num_cells}")

        # Test actor creation
        actor, _ = GeometryLoader.load_and_create_actor(
            l2_file,
            color=(0.9, 0.9, 0.7),
            opacity=0.8,
            add_axes=True
        )

        if actor is None:
            print("❌ Failed to create actor")
            return False

        print(f"✓ Successfully created VTK actor")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ct_model_loader():
    """Test CT3DModelLoader for loading vertebral models."""
    print("\n" + "="*60)
    print("TEST 2: CT3DModelLoader")
    print("="*60)

    sample_data_dir = os.path.join(project_root, "resources", "sample_data", "CT", "ASD-043")

    # Find all vertebral files
    vertebral_files = []
    for filename in ["L2_001.stl", "L3_001.stl", "L4_001.stl"]:
        file_path = os.path.join(sample_data_dir, filename)
        if os.path.exists(file_path):
            vertebral_files.append(file_path)

    if not vertebral_files:
        print("❌ No vertebral files found")
        return False

    print(f"Found {len(vertebral_files)} vertebral models")

    try:
        loader = CT3DModelLoader()
        loaded_models = loader.load_multiple_vertebrae(vertebral_files)

        if len(loaded_models) != len(vertebral_files):
            print(f"⚠ Warning: Only {len(loaded_models)}/{len(vertebral_files)} models loaded")

        for actor, polydata, file_path in loaded_models:
            filename = os.path.basename(file_path)
            num_points = polydata.GetNumberOfPoints()
            print(f"✓ {filename}: {num_points} points")

        print(f"\n✓ Successfully loaded {len(loaded_models)} vertebral models")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_osim_geometry_property():
    """Test OsimGeometryProperty integration."""
    print("\n" + "="*60)
    print("TEST 3: OsimGeometryProperty Integration")
    print("="*60)

    sample_data_dir = os.path.join(project_root, "resources", "sample_data", "CT", "ASD-043")
    l3_file = os.path.join(sample_data_dir, "L3_001.stl")

    if not os.path.exists(l3_file):
        print(f"❌ L3 file not found: {l3_file}")
        return False

    try:
        # Create property object
        geom_prop = OsimGeometryProperty()

        # Set geometry file
        if not geom_prop.set_geometry_file(l3_file):
            print("❌ Failed to set geometry file")
            return False

        print(f"✓ Set geometry file: {geom_prop.geometry_file}")
        print(f"  - Extension: {geom_prop.extension}")

        # Create VTK actor
        if not geom_prop.make_vtk_actor(add_axes=True, axes_scale=10.0):
            print("❌ Failed to create VTK actor")
            return False

        print(f"✓ Created VTK actor")

        # Check actor properties
        actor = geom_prop.vtk_actor
        if actor is None:
            print("❌ Actor is None")
            return False

        # Check polydata
        polydata = geom_prop.vtk_polydata
        num_points = polydata.GetNumberOfPoints()
        print(f"  - Points in polydata: {num_points}")

        # Test 2D actors creation
        if not geom_prop.make_2d_actors():
            print("❌ Failed to create 2D actors")
            return False

        print(f"✓ Created 2D projection actors")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all CT import tests."""
    print("\n" + "#"*60)
    print("# CT VERTEBRAL MODEL IMPORT TESTS")
    print("#"*60)

    results = []

    # Test 1: Basic geometry loader
    results.append(("GeometryLoader", test_geometry_loader()))

    # Test 2: CT model loader
    results.append(("CT3DModelLoader", test_ct_model_loader()))

    # Test 3: OsimGeometryProperty integration
    results.append(("OsimGeometryProperty", test_osim_geometry_property()))

    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! CT import functionality is working.")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    exit(main())
