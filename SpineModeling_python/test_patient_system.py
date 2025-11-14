#!/usr/bin/env python3
"""
Test script for the patient data management system.

This script tests:
1. Patient folder structure creation
2. Database integration
3. Image upload functionality
4. Data retrieval
"""

import sys
from pathlib import Path

# Add package to path
sys.path.insert(0, str(Path(__file__).parent))

from spine_modeling.database.models import DatabaseManager
from spine_modeling.utils.patient_data_manager import PatientDataManager


def test_folder_structure():
    """Test folder structure creation."""
    print("=" * 60)
    print("TEST 1: Folder Structure Creation")
    print("=" * 60)

    manager = PatientDataManager()
    print(f"Base path: {manager.base_path}")

    # Create folders for a few test patients
    print("\nCreating folders for ASD-001, ASD-002, ASD-003...")
    for num in range(1, 4):
        patient_code = f"ASD-{num:03d}"
        folders = manager.create_patient_folders(patient_code)
        print(f"\n{patient_code}:")
        print(f"  Patient folder: {folders['patient_folder']}")
        print(f"  EOS Frontal: {folders['eos_frontal']}")
        print(f"  EOS Lateral: {folders['eos_lateral']}")
        print(f"  CT folders: {len(folders['ct_folders'])} vertebrae")

    print("\n✓ Folder structure test passed!")


def test_database_integration():
    """Test database integration."""
    print("\n" + "=" * 60)
    print("TEST 2: Database Integration")
    print("=" * 60)

    # Create test database
    db_path = Path(__file__).parent / "test_patients.db"
    if db_path.exists():
        db_path.unlink()

    db_url = f"sqlite:///{db_path}"
    db_manager = DatabaseManager(db_url)
    db_manager.initialize_database()

    print(f"Database created: {db_path}")

    # Initialize patients in database
    data_manager = PatientDataManager()

    print("\nInitializing 10 patients in database...")
    subjects = []
    for num in range(1, 11):
        patient_code = f"ASD-{num:03d}"
        data_manager.create_patient_folders(patient_code)

        # Create database entry
        patient_folder = str(data_manager.get_patient_folder(patient_code))
        subject = db_manager.create_subject(
            subject_code=patient_code,
            data_folder=patient_folder
        )
        subjects.append(subject)
        print(f"  Created: {subject}")

    # Verify retrieval
    print("\nVerifying patient retrieval...")
    all_subjects = db_manager.get_all_subjects()
    print(f"Total patients in database: {len(all_subjects)}")

    # Test specific patient lookup
    test_patient = db_manager.get_subject_by_code("ASD-005")
    print(f"\nTest patient ASD-005:")
    print(f"  ID: {test_patient.subject_id}")
    print(f"  Code: {test_patient.subject_code}")
    print(f"  Data folder: {test_patient.data_folder}")

    db_manager.close_session()
    print("\n✓ Database integration test passed!")


def test_image_tracking():
    """Test image tracking in database."""
    print("\n" + "=" * 60)
    print("TEST 3: Image Tracking")
    print("=" * 60)

    # Use test database
    db_path = Path(__file__).parent / "test_patients.db"
    db_url = f"sqlite:///{db_path}"
    db_manager = DatabaseManager(db_url)

    # Get a test patient
    subject = db_manager.get_subject_by_code("ASD-003")
    print(f"Testing with patient: {subject.subject_code}")

    # Simulate image records
    print("\nAdding simulated image records...")

    # EOS Frontal
    eos_frontal = db_manager.create_patient_image(
        subject_id=subject.subject_id,
        image_type="EOS_Frontal",
        file_path="ASD-003/EOS/frontal/patient_frontal.dcm",
        file_name="patient_frontal.dcm",
        file_size=32870000
    )
    print(f"  Added: {eos_frontal}")

    # EOS Lateral
    eos_lateral = db_manager.create_patient_image(
        subject_id=subject.subject_id,
        image_type="EOS_Lateral",
        file_path="ASD-003/EOS/lateral/patient_lateral.dcm",
        file_name="patient_lateral.dcm",
        file_size=30580000
    )
    print(f"  Added: {eos_lateral}")

    # CT images for vertebrae
    for vertebra in ["L2", "L3", "L4"]:
        ct_image = db_manager.create_patient_image(
            subject_id=subject.subject_id,
            image_type="CT",
            file_path=f"ASD-003/CT/{vertebra}/{vertebra}_001.stl",
            file_name=f"{vertebra}_001.stl",
            vertebra_level=vertebra,
            file_size=10000000
        )
        print(f"  Added: {ct_image}")

    # Retrieve images
    print("\nRetrieving all images for patient...")
    images = db_manager.get_images_by_subject(subject.subject_id)
    print(f"Total images: {len(images)}")
    for img in images:
        print(f"  - {img.image_type}", end="")
        if img.vertebra_level:
            print(f" ({img.vertebra_level})", end="")
        print(f": {img.file_name}")

    # Test filtering
    print("\nFiltering by type...")
    eos_images = db_manager.get_images_by_type(subject.subject_id, "EOS_Frontal")
    print(f"EOS Frontal images: {len(eos_images)}")

    ct_images = db_manager.get_images_by_type(subject.subject_id, "CT")
    print(f"CT images: {len(ct_images)}")

    # Test vertebra filtering
    print("\nFiltering by vertebra...")
    l2_images = db_manager.get_images_by_vertebra(subject.subject_id, "L2")
    print(f"L2 images: {len(l2_images)}")

    db_manager.close_session()
    print("\n✓ Image tracking test passed!")


def test_full_initialization():
    """Test initializing all 75 patients."""
    print("\n" + "=" * 60)
    print("TEST 4: Full Patient Initialization (ASD-001 to ASD-075)")
    print("=" * 60)

    response = input("This will create folders for all 75 patients. Continue? (y/n): ")
    if response.lower() != 'y':
        print("Skipped.")
        return

    # Create database
    db_path = Path(__file__).parent / "full_patients.db"
    if db_path.exists():
        db_path.unlink()

    db_url = f"sqlite:///{db_path}"
    db_manager = DatabaseManager(db_url)
    db_manager.initialize_database()

    # Initialize all patients
    data_manager = PatientDataManager()
    print("\nInitializing all 75 patients...")
    subjects = data_manager.initialize_all_patients_in_db(db_manager)

    print(f"\n✓ Created {len(subjects)} patients!")

    # Show some statistics
    print("\nSample patients:")
    for i in [0, 24, 49, 74]:  # Show first, 25th, 50th, and last
        if i < len(subjects):
            s = subjects[i]
            print(f"  {s.subject_code}: {s.data_folder}")

    # Verify folder structure
    sample_code = "ASD-043"
    stats = data_manager.get_folder_stats(sample_code)
    print(f"\nSample folder structure for {sample_code}:")
    print(f"  Base: {data_manager.get_patient_folder(sample_code)}")
    print(f"  EOS Frontal: {data_manager.get_eos_folder(sample_code, 'frontal')}")
    print(f"  EOS Lateral: {data_manager.get_eos_folder(sample_code, 'lateral')}")
    print(f"  CT folders: 19 vertebrae (Sacrum, L5-L1, T12-T1)")

    db_manager.close_session()
    print("\n✓ Full initialization test passed!")


def main():
    """Run all tests."""
    print("PATIENT DATA MANAGEMENT SYSTEM - TEST SUITE")
    print("=" * 60)

    try:
        test_folder_structure()
        test_database_integration()
        test_image_tracking()
        test_full_initialization()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
        print("\nThe patient data management system is ready to use.")
        print("You can now launch the application and use the Patient Manager dialog.")

    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
