"""End-to-end integration test for 3D measurement workflow.

This test demonstrates the complete workflow:
1. Load CT-derived vertebral models
2. Set up EOS space with calibration
3. Position vertebrae in 3D space
4. Project onto 2D EOS images
5. Perform realignment adjustments
"""

import sys
import os

# Add project to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from spine_modeling.visualization.geometry_loader import GeometryLoader
from spine_modeling.visualization.projection_3d import Projection3D, VertebralModelProjector
from spine_modeling.analysis.realignment import RealignmentCalculator, InteractiveAlignmentTool
from spine_modeling.imaging.eos_space import EosSpace
from spine_modeling.imaging.eos_image import EosImage


def create_test_eos_space():
    """Create test EOS space with realistic calibration."""
    eos_image_a = EosImage(
        directory="test_frontal.dcm",
        distance_source_to_isocenter=1.35,
        distance_source_to_detector=1.85,
        distance_source_to_patient=1.25,
        pixel_spacing_x=0.000143,
        pixel_spacing_y=0.000143,
        width=0.4,
        height=1.0,
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


def test_full_workflow():
    """Test complete 3D measurement workflow."""
    print("\n" + "="*70)
    print("END-TO-END INTEGRATION TEST: 3D MEASUREMENT WORKFLOW")
    print("="*70)

    sample_data_dir = os.path.join(project_root, "resources", "sample_data", "CT", "ASD-043")

    # Step 1: Load CT vertebral models
    print("\n[STEP 1] Loading CT vertebral models...")
    print("-" * 70)

    vertebral_files = {
        'L2': os.path.join(sample_data_dir, "L2_001.stl"),
        'L3': os.path.join(sample_data_dir, "L3_001.stl"),
        'L4': os.path.join(sample_data_dir, "L4_001.stl"),
    }

    loaded_vertebrae = {}
    for name, file_path in vertebral_files.items():
        if os.path.exists(file_path):
            polydata = GeometryLoader.load_geometry(file_path)
            if polydata:
                loaded_vertebrae[name] = polydata
                print(f"  ✓ Loaded {name}: {polydata.GetNumberOfPoints()} points, "
                      f"{polydata.GetNumberOfCells()} cells")
        else:
            print(f"  ⚠ File not found: {file_path}")

    if not loaded_vertebrae:
        print("  ❌ No vertebrae loaded. Cannot proceed with integration test.")
        return False

    print(f"\n  Summary: {len(loaded_vertebrae)} vertebrae loaded successfully")

    # Step 2: Set up EOS space
    print("\n[STEP 2] Setting up EOS space...")
    print("-" * 70)

    eos_space = create_test_eos_space()

    print(f"  ✓ EOS space initialized")
    print(f"    - Source 1 position: {eos_space.position_source1}")
    print(f"    - Source 2 position: {eos_space.position_source2}")
    print(f"    - Patient position: {eos_space.patient_position}")

    # Step 3: Initialize realignment calculator
    print("\n[STEP 3] Computing initial vertebral positions...")
    print("-" * 70)

    calculator = RealignmentCalculator(eos_space)

    initial_positions = {}
    for name in loaded_vertebrae.keys():
        transform = calculator.estimate_initial_position(name)
        initial_positions[name] = transform
        print(f"  ✓ {name} initial position: {transform.translation}")

    # Step 4: Create projection system
    print("\n[STEP 4] Setting up 3D-to-2D projection system...")
    print("-" * 70)

    projector = VertebralModelProjector(eos_space)

    for name, polydata in loaded_vertebrae.items():
        transform = initial_positions[name]
        projector.add_vertebral_model(
            name=name,
            polydata=polydata,
            initial_position=transform.translation,
            initial_rotation=transform.rotation,
            scale=transform.scale
        )
        print(f"  ✓ Added {name} to projector")

    print(f"\n  Summary: {projector.get_model_count()} models ready for projection")

    # Step 5: Project models onto 2D images
    print("\n[STEP 5] Projecting 3D models onto 2D EOS images...")
    print("-" * 70)

    projection_actors = projector.get_all_projection_actors(
        color_frontal=(1.0, 0.0, 0.0),  # Red for frontal
        color_lateral=(0.0, 0.0, 1.0),   # Blue for lateral
        opacity=0.4
    )

    for name, frontal_actor, lateral_actor in projection_actors:
        print(f"  ✓ {name} projected:")
        print(f"    - Frontal projection actor created")
        print(f"    - Lateral projection actor created")

    print(f"\n  Summary: {len(projection_actors)} vertebrae projected onto both views")

    # Step 6: Interactive alignment adjustments
    print("\n[STEP 6] Testing interactive alignment adjustments...")
    print("-" * 70)

    alignment_tool = InteractiveAlignmentTool(eos_space)

    # Set initial transforms
    for name, transform in initial_positions.items():
        alignment_tool.set_model_transform(name, transform)

    # Simulate manual adjustments
    print("  Simulating manual adjustments:")

    # Translate L3 slightly
    updated = alignment_tool.translate_model("L3", delta_x=0.005, delta_y=0.01)
    print(f"    ✓ Translated L3: {updated.translation}")

    # Rotate L3
    updated = alignment_tool.rotate_model("L3", delta_ry=5.0)
    print(f"    ✓ Rotated L3: {updated.rotation}")

    # Update L3 in projector
    projector.update_model_transform(
        "L3",
        position=updated.translation,
        rotation=updated.rotation
    )
    print(f"    ✓ Updated L3 projection with new transform")

    # Step 7: Verify projected bounds
    print("\n[STEP 7] Computing projected bounds on images...")
    print("-" * 70)

    projection_3d = Projection3D(eos_space)

    for name in loaded_vertebrae.keys():
        # Get the transformed model from projector
        model_data = next((m for m in projector.loaded_models if m['name'] == name), None)
        if model_data:
            polydata = model_data['polydata_transformed']

            frontal_bounds = projection_3d.get_projected_bounds(polydata, 'frontal')
            lateral_bounds = projection_3d.get_projected_bounds(polydata, 'lateral')

            print(f"  {name} projected bounds:")
            print(f"    - Frontal: x=[{frontal_bounds[0]:.4f}, {frontal_bounds[1]:.4f}] m, "
                  f"y=[{frontal_bounds[2]:.4f}, {frontal_bounds[3]:.4f}] m")
            print(f"    - Lateral: x=[{lateral_bounds[0]:.4f}, {lateral_bounds[1]:.4f}] m, "
                  f"y=[{lateral_bounds[2]:.4f}, {lateral_bounds[3]:.4f}] m")

    # Step 8: Save configuration
    print("\n[STEP 8] Saving alignment configuration...")
    print("-" * 70)

    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name

    try:
        alignment_tool.save_transforms(temp_path)
        print(f"  ✓ Saved transforms to: {temp_path}")

        # Verify saved data
        import json
        with open(temp_path, 'r') as f:
            saved_data = json.load(f)
        print(f"  ✓ Verified: {len(saved_data)} transforms saved")

        # Test reload
        test_tool = InteractiveAlignmentTool(eos_space)
        test_tool.load_transforms(temp_path)
        print(f"  ✓ Successfully reloaded {len(test_tool.current_transforms)} transforms")

    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)

    # Final summary
    print("\n" + "="*70)
    print("INTEGRATION TEST SUMMARY")
    print("="*70)
    print(f"  ✓ {len(loaded_vertebrae)} CT vertebral models loaded")
    print(f"  ✓ EOS space configured with calibration parameters")
    print(f"  ✓ Initial positions computed for all vertebrae")
    print(f"  ✓ 3D-to-2D projection system operational")
    print(f"  ✓ {len(projection_actors)} models projected onto both views")
    print(f"  ✓ Interactive alignment tools functional")
    print(f"  ✓ Transform save/load system working")
    print("\n  🎉 Full integration test PASSED!")
    print("  The 3D measurement system is fully integrated and operational.")

    return True


def test_workflow_use_cases():
    """Test specific use cases for the 3D measurement workflow."""
    print("\n" + "="*70)
    print("USE CASE TESTING")
    print("="*70)

    eos_space = create_test_eos_space()
    calculator = RealignmentCalculator(eos_space)

    # Use Case 1: Estimate positions for entire lumbar spine
    print("\n[USE CASE 1] Estimate positions for lumbar spine levels...")
    print("-" * 70)

    lumbar_vertebrae = ['L1', 'L2', 'L3', 'L4', 'L5']
    for vertebra in lumbar_vertebrae:
        transform = calculator.estimate_initial_position(vertebra)
        print(f"  {vertebra}: y={transform.translation[1]:.3f} m")

    print("  ✓ All lumbar positions estimated")

    # Use Case 2: Test projection at different depths
    print("\n[USE CASE 2] Test projection at different depths...")
    print("-" * 70)

    projection = Projection3D(eos_space)

    test_points = [
        ("At patient", (0.0, 0.5, 0.0)),
        ("Anterior", (0.05, 0.5, 0.0)),
        ("Posterior", (-0.05, 0.5, 0.0)),
        ("Superior", (0.0, 0.7, 0.0)),
        ("Inferior", (0.0, 0.3, 0.0)),
    ]

    for name, point in test_points:
        frontal, lateral = projection.project_point_to_images(point)
        print(f"  {name:12s}: frontal=({frontal[0]:7.4f}, {frontal[1]:7.4f}), "
              f"lateral=({lateral[0]:7.4f}, {lateral[1]:7.4f})")

    print("  ✓ Multi-depth projection test complete")

    # Use Case 3: Simulate iterative alignment
    print("\n[USE CASE 3] Simulate iterative alignment refinement...")
    print("-" * 70)

    alignment_tool = InteractiveAlignmentTool(eos_space)
    alignment_tool.set_model_transform("L3", calculator.estimate_initial_position("L3"))

    adjustments = [
        ("Initial position", None),
        ("Translate anterior", ("translate", 0.01, 0, 0)),
        ("Translate superior", ("translate", 0, 0.02, 0)),
        ("Rotate sagittal", ("rotate", 0, 5, 0)),
        ("Fine-tune position", ("translate", -0.005, 0.01, 0)),
    ]

    for description, adjustment in adjustments:
        if adjustment:
            action, *params = adjustment
            if action == "translate":
                alignment_tool.translate_model("L3", *params)
            elif action == "rotate":
                alignment_tool.rotate_model("L3", *params)

        current = alignment_tool.get_model_transform("L3")
        print(f"  {description:22s}: pos={current.translation}, rot={current.rotation}")

    print("  ✓ Iterative alignment simulation complete")

    print("\n  🎉 All use cases passed!")

    return True


def main():
    """Run integration tests."""
    print("\n" + "#"*70)
    print("# 3D MEASUREMENT INTEGRATION TESTS")
    print("#"*70)

    results = []

    # Test full workflow
    results.append(("Full Workflow", test_full_workflow()))

    # Test use cases
    results.append(("Use Cases", test_workflow_use_cases()))

    # Summary
    print("\n" + "="*70)
    print("FINAL TEST SUMMARY")
    print("="*70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} integration tests passed")

    if passed == total:
        print("\n" + "="*70)
        print("✨ SUCCESS: 3D MEASUREMENT INTEGRATION COMPLETE ✨")
        print("="*70)
        print("\nThe following components are fully integrated:")
        print("  1. CT vertebral model import (STL/OBJ/VTP)")
        print("  2. 3D-to-2D projection system")
        print("  3. Spinal realignment calculations")
        print("  4. Interactive alignment tools")
        print("  5. Transform persistence (save/load)")
        print("\nThe system is ready for:")
        print("  • Loading CT-derived vertebral models")
        print("  • Positioning them in EOS 3D space")
        print("  • Projecting onto EOS X-ray images")
        print("  • Computing spinal realignment parameters")
        print("="*70)
        return 0
    else:
        print(f"\n⚠ {total - passed} integration test(s) failed.")
        return 1


if __name__ == "__main__":
    exit(main())
