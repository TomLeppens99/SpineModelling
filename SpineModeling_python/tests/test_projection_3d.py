"""Test script for 3D-to-2D projection functionality."""

import sys
import os

# Add project to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from spine_modeling.visualization.projection_3d import Projection3D, VertebralModelProjector
from spine_modeling.visualization.geometry_loader import GeometryLoader
from spine_modeling.imaging.eos_space import EosSpace
from spine_modeling.imaging.eos_image import EosImage
from spine_modeling.core.position import Position


def create_test_eos_space():
    """Create a test EOS space with sample calibration parameters."""
    # Create mock EOS images with typical EOS calibration parameters
    eos_image_a = EosImage(
        directory="test_frontal.dcm",
        distance_source_to_isocenter=1.35,  # meters
        distance_source_to_detector=1.85,  # meters
        distance_source_to_patient=1.25,  # meters
        pixel_spacing_x=0.000143,  # meters (143 microns)
        pixel_spacing_y=0.000143,
        width=0.4,  # meters
        height=1.0,  # meters
        image_plane="frontal"
    )

    eos_image_b = EosImage(
        directory="test_lateral.dcm",
        distance_source_to_isocenter=1.35,
        distance_source_to_detector=1.85,
        distance_source_to_patient=1.25,
        pixel_spacing_x=0.000143,
        pixel_spacing_y=0.000143,
        width=0.4,
        height=1.0,
        image_plane="lateral"
    )

    eos_space = EosSpace(eos_image_a, eos_image_b)
    eos_space.calculate_eos_space()

    return eos_space


def test_basic_projection():
    """Test basic 3D point projection."""
    print("\n" + "="*60)
    print("TEST 1: Basic 3D Point Projection")
    print("="*60)

    try:
        eos_space = create_test_eos_space()
        projection = Projection3D(eos_space)

        # Test projecting a point at the isocenter
        point_3d = (0.0, 0.0, 0.0)
        frontal_coords, lateral_coords = projection.project_point_to_images(point_3d)

        print(f"3D point: {point_3d}")
        print(f"Frontal projection: {frontal_coords}")
        print(f"Lateral projection: {lateral_coords}")

        # Test projecting a point offset from isocenter
        point_3d = (0.1, 0.2, 0.05)
        frontal_coords, lateral_coords = projection.project_point_to_images(point_3d)

        print(f"\n3D point: {point_3d}")
        print(f"Frontal projection: {frontal_coords}")
        print(f"Lateral projection: {lateral_coords}")

        print("\n✓ Basic projection test passed")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_polydata_projection():
    """Test projecting a vertebral model polydata."""
    print("\n" + "="*60)
    print("TEST 2: Vertebral Model Projection")
    print("="*60)

    sample_data_dir = os.path.join(project_root, "resources", "sample_data", "CT", "ASD-043")
    l3_file = os.path.join(sample_data_dir, "L3_001.stl")

    if not os.path.exists(l3_file):
        print(f"❌ Sample file not found: {l3_file}")
        return False

    try:
        # Load the vertebral model
        polydata = GeometryLoader.load_geometry(l3_file)
        if polydata is None:
            print("❌ Failed to load vertebral model")
            return False

        num_points = polydata.GetNumberOfPoints()
        print(f"Loaded L3 vertebra: {num_points} points")

        # Create EOS space and projection
        eos_space = create_test_eos_space()
        projection = Projection3D(eos_space)

        # Project the entire polydata
        frontal_poly, lateral_poly = projection.project_polydata(polydata)

        if frontal_poly is None or lateral_poly is None:
            print("❌ Projection failed")
            return False

        frontal_points = frontal_poly.GetNumberOfPoints()
        lateral_points = lateral_poly.GetNumberOfPoints()

        print(f"✓ Projected to frontal: {frontal_points} points")
        print(f"✓ Projected to lateral: {lateral_points} points")

        # Check that point counts match
        if frontal_points != num_points or lateral_points != num_points:
            print("⚠ Warning: Point count mismatch")
            return False

        # Get projected bounds
        frontal_bounds = projection.get_projected_bounds(polydata, 'frontal')
        lateral_bounds = projection.get_projected_bounds(polydata, 'lateral')

        print(f"\nFrontal bounds: x=[{frontal_bounds[0]:.4f}, {frontal_bounds[1]:.4f}], "
              f"y=[{frontal_bounds[2]:.4f}, {frontal_bounds[3]:.4f}]")
        print(f"Lateral bounds: x=[{lateral_bounds[0]:.4f}, {lateral_bounds[1]:.4f}], "
              f"y=[{lateral_bounds[2]:.4f}, {lateral_bounds[3]:.4f}]")

        print("\n✓ Polydata projection test passed")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_projection_actors():
    """Test creating VTK actors for projections."""
    print("\n" + "="*60)
    print("TEST 3: Projection Actor Creation")
    print("="*60)

    sample_data_dir = os.path.join(project_root, "resources", "sample_data", "CT", "ASD-043")
    l2_file = os.path.join(sample_data_dir, "L2_001.stl")

    if not os.path.exists(l2_file):
        print(f"❌ Sample file not found: {l2_file}")
        return False

    try:
        # Load vertebral model
        polydata = GeometryLoader.load_geometry(l2_file)
        if polydata is None:
            print("❌ Failed to load model")
            return False

        print(f"Loaded L2 vertebra: {polydata.GetNumberOfPoints()} points")

        # Create projection
        eos_space = create_test_eos_space()
        projection = Projection3D(eos_space)

        # Transform to EOS space (scale from mm to m)
        transformed = projection.transform_model_to_eos_space(
            polydata,
            translation=(0, 0, 0),
            rotation=(0, 0, 0),
            scale=0.001  # mm to meters
        )

        print(f"Transformed model: {transformed.GetNumberOfPoints()} points")

        # Create projection actors
        frontal_actor, lateral_actor = projection.create_projection_actors(
            transformed,
            color_frontal=(1.0, 0.0, 0.0),
            color_lateral=(0.0, 0.0, 1.0),
            opacity=0.5
        )

        if frontal_actor is None or lateral_actor is None:
            print("❌ Failed to create actors")
            return False

        print("✓ Created frontal projection actor")
        print("✓ Created lateral projection actor")

        # Check actor properties
        frontal_color = frontal_actor.GetProperty().GetColor()
        lateral_color = lateral_actor.GetProperty().GetColor()

        print(f"  Frontal color: RGB({frontal_color[0]:.1f}, {frontal_color[1]:.1f}, {frontal_color[2]:.1f})")
        print(f"  Lateral color: RGB({lateral_color[0]:.1f}, {lateral_color[1]:.1f}, {lateral_color[2]:.1f})")

        print("\n✓ Projection actor creation test passed")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_vertebral_model_projector():
    """Test high-level VertebralModelProjector class."""
    print("\n" + "="*60)
    print("TEST 4: VertebralModelProjector")
    print("="*60)

    sample_data_dir = os.path.join(project_root, "resources", "sample_data", "CT", "ASD-043")

    vertebral_files = {
        'L2': os.path.join(sample_data_dir, "L2_001.stl"),
        'L3': os.path.join(sample_data_dir, "L3_001.stl"),
        'L4': os.path.join(sample_data_dir, "L4_001.stl"),
    }

    try:
        # Create projector
        eos_space = create_test_eos_space()
        projector = VertebralModelProjector(eos_space)

        # Load multiple vertebrae
        loaded_count = 0
        for name, file_path in vertebral_files.items():
            if os.path.exists(file_path):
                polydata = GeometryLoader.load_geometry(file_path)
                if polydata:
                    projector.add_vertebral_model(
                        name=name,
                        polydata=polydata,
                        initial_position=(0, 0, 0),
                        scale=0.001  # mm to meters
                    )
                    loaded_count += 1
                    print(f"✓ Loaded {name}: {polydata.GetNumberOfPoints()} points")

        if loaded_count == 0:
            print("❌ No models loaded")
            return False

        print(f"\nTotal models loaded: {projector.get_model_count()}")
        print(f"Model names: {projector.get_model_names()}")

        # Get projection actors for all models
        actors = projector.get_all_projection_actors(
            color_frontal=(1.0, 0.0, 0.0),
            color_lateral=(0.0, 0.0, 1.0),
            opacity=0.4
        )

        print(f"\nCreated projection actors for {len(actors)} models")

        for name, frontal_actor, lateral_actor in actors:
            print(f"  ✓ {name}: frontal and lateral actors created")

        # Test updating transform
        projector.update_model_transform(
            'L3',
            position=(0.02, 0.1, 0.01),
            rotation=(0, 0, 10)
        )
        print("\n✓ Updated L3 transform")

        print("\n✓ VertebralModelProjector test passed")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all projection tests."""
    print("\n" + "#"*60)
    print("# 3D-TO-2D PROJECTION TESTS")
    print("#"*60)

    results = []

    # Test 1: Basic projection
    results.append(("Basic Projection", test_basic_projection()))

    # Test 2: Polydata projection
    results.append(("Polydata Projection", test_polydata_projection()))

    # Test 3: Projection actors
    results.append(("Projection Actors", test_projection_actors()))

    # Test 4: High-level projector
    results.append(("VertebralModelProjector", test_vertebral_model_projector()))

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
        print("\n🎉 All tests passed! 3D-to-2D projection is working.")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    exit(main())
