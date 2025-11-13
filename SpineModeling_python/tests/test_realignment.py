"""Test script for spinal realignment functionality."""

import sys
import os

# Add project to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from spine_modeling.analysis.realignment import (
    RealignmentCalculator,
    InteractiveAlignmentTool,
    Landmark3D,
    Landmark2D,
    TransformParameters
)
from spine_modeling.imaging.eos_space import EosSpace
from spine_modeling.imaging.eos_image import EosImage
from spine_modeling.core.position import Position


def create_test_eos_space():
    """Create test EOS space."""
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


def test_transform_parameters():
    """Test TransformParameters dataclass."""
    print("\n" + "="*60)
    print("TEST 1: TransformParameters")
    print("="*60)

    try:
        # Create default parameters
        params = TransformParameters()
        print(f"Default translation: {params.translation}")
        print(f"Default rotation: {params.rotation}")
        print(f"Default scale: {params.scale}")

        # Create custom parameters
        params = TransformParameters(
            translation=(0.1, 0.2, 0.05),
            rotation=(5.0, 10.0, 0.0),
            scale=0.001
        )
        print(f"\nCustom translation: {params.translation}")
        print(f"Custom rotation: {params.rotation}")
        print(f"Custom scale: {params.scale}")

        # Convert to dict
        params_dict = params.to_dict()
        print(f"\nAs dict: {params_dict}")

        print("\n✓ TransformParameters test passed")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_realignment_calculator():
    """Test RealignmentCalculator."""
    print("\n" + "="*60)
    print("TEST 2: RealignmentCalculator")
    print("="*60)

    try:
        eos_space = create_test_eos_space()
        calculator = RealignmentCalculator(eos_space)

        # Test initial position estimation
        for vertebra in ['L1', 'L2', 'L3', 'L4', 'L5']:
            transform = calculator.estimate_initial_position(vertebra)
            print(f"{vertebra} initial position: {transform.translation}")

        # Add 3D landmarks
        calculator.add_3d_landmark(Landmark3D(
            name="L3_superior_anterior",
            position=Position(0.02, 0.03, 0.01),
            vertebra="L3"
        ))

        calculator.add_3d_landmark(Landmark3D(
            name="L3_inferior_posterior",
            position=Position(0.015, 0.015, 0.015),
            vertebra="L3"
        ))

        print(f"\n✓ Added {len(calculator.landmarks_3d)} 3D landmarks")

        # Add 2D landmarks
        calculator.add_2d_landmark(Landmark2D(
            name="L3_superior_anterior",
            position=(0.05, 0.1),
            image_plane="frontal"
        ))

        calculator.add_2d_landmark(Landmark2D(
            name="L3_inferior_posterior",
            position=(0.04, 0.08),
            image_plane="lateral"
        ))

        print(f"✓ Added {len(calculator.landmarks_2d)} 2D landmarks")

        # Test landmark matching
        matched = calculator._match_landmarks()
        print(f"✓ Matched {len(matched)} landmark pairs")

        # Clear landmarks
        calculator.clear_landmarks()
        print(f"✓ Cleared landmarks: {len(calculator.landmarks_3d)} remaining")

        print("\n✓ RealignmentCalculator test passed")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_interactive_alignment_tool():
    """Test InteractiveAlignmentTool."""
    print("\n" + "="*60)
    print("TEST 3: InteractiveAlignmentTool")
    print("="*60)

    try:
        eos_space = create_test_eos_space()
        tool = InteractiveAlignmentTool(eos_space)

        # Set initial transform
        initial = TransformParameters(
            translation=(0.0, 0.1, 0.0),
            rotation=(0.0, 0.0, 0.0),
            scale=0.001
        )
        tool.set_model_transform("L3", initial)
        print(f"Initial L3 transform: {initial.translation}")

        # Translate model
        updated = tool.translate_model("L3", delta_x=0.01, delta_y=0.02, delta_z=0.005)
        print(f"After translation: {updated.translation}")

        # Rotate model
        updated = tool.rotate_model("L3", delta_rx=5.0, delta_ry=10.0)
        print(f"After rotation: {updated.rotation}")

        # Scale model
        updated = tool.scale_model("L3", 0.002)
        print(f"After scaling: scale={updated.scale}")

        # Get current transform
        current = tool.get_model_transform("L3")
        print(f"\nCurrent L3 transform:")
        print(f"  Translation: {current.translation}")
        print(f"  Rotation: {current.rotation}")
        print(f"  Scale: {current.scale}")

        # Test multiple models
        tool.set_model_transform("L4", TransformParameters(
            translation=(0.0, 0.05, 0.0),
            scale=0.001
        ))
        print(f"\nLoaded models: {list(tool.current_transforms.keys())}")

        # Reset a model
        reset = tool.reset_transform("L3")
        print(f"Reset L3 translation: {reset.translation}")

        # Test save/load (to temp file)
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            tool.save_transforms(temp_path)
            print(f"✓ Saved transforms to {temp_path}")

            # Create new tool and load
            tool2 = InteractiveAlignmentTool(eos_space)
            tool2.load_transforms(temp_path)
            print(f"✓ Loaded {len(tool2.current_transforms)} transforms")

            # Verify loaded data
            loaded_l4 = tool2.get_model_transform("L4")
            print(f"Loaded L4 translation: {loaded_l4.translation}")

        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.unlink(temp_path)

        print("\n✓ InteractiveAlignmentTool test passed")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_landmark_classes():
    """Test Landmark3D and Landmark2D dataclasses."""
    print("\n" + "="*60)
    print("TEST 4: Landmark Classes")
    print("="*60)

    try:
        # Create 3D landmark
        lm_3d = Landmark3D(
            name="L3_superior",
            position=Position(0.01, 0.02, 0.03),
            vertebra="L3"
        )
        print(f"3D Landmark: {lm_3d.name}")
        print(f"  Position: ({lm_3d.position.x}, {lm_3d.position.y}, {lm_3d.position.z})")
        print(f"  Vertebra: {lm_3d.vertebra}")

        # Create 2D landmark
        lm_2d = Landmark2D(
            name="L3_superior",
            position=(100.5, 200.3),
            image_plane="frontal"
        )
        print(f"\n2D Landmark: {lm_2d.name}")
        print(f"  Position: {lm_2d.position}")
        print(f"  Image plane: {lm_2d.image_plane}")

        # Create multiple landmarks
        landmarks_3d = [
            Landmark3D(f"L{i}_center", Position(0.0, 0.1*i, 0.0), f"L{i}")
            for i in range(1, 6)
        ]
        print(f"\n✓ Created {len(landmarks_3d)} 3D landmarks")

        landmarks_2d = [
            Landmark2D(f"L{i}_center", (100*i, 200*i), "frontal")
            for i in range(1, 6)
        ]
        print(f"✓ Created {len(landmarks_2d)} 2D landmarks")

        print("\n✓ Landmark classes test passed")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all realignment tests."""
    print("\n" + "#"*60)
    print("# SPINAL REALIGNMENT TESTS")
    print("#"*60)

    results = []

    # Test 1: Transform parameters
    results.append(("TransformParameters", test_transform_parameters()))

    # Test 2: Realignment calculator
    results.append(("RealignmentCalculator", test_realignment_calculator()))

    # Test 3: Interactive alignment tool
    results.append(("InteractiveAlignmentTool", test_interactive_alignment_tool()))

    # Test 4: Landmark classes
    results.append(("Landmark Classes", test_landmark_classes()))

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
        print("\n🎉 All tests passed! Realignment functionality is working.")
        return 0
    else:
        print(f"\n⚠ {total - passed} test(s) failed.")
        return 1


if __name__ == "__main__":
    exit(main())
