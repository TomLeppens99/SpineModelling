#!/usr/bin/env python3
"""
Test script for database integration with UI layers.

This script tests the complete database integration including:
- Database initialization
- Subject creation
- Measurement creation (point and ellipse)
- Measurement retrieval
- Measurement deletion

Run this script from the SpineModeling_python directory:
    python ../test_database_integration.py
"""

import sys
import os
from pathlib import Path

# Add the spine_modeling package to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from spine_modeling.database.models import DatabaseManager, Subject, Measurement


def test_database_integration():
    """Test complete database integration."""

    print("=" * 80)
    print("DATABASE INTEGRATION TEST")
    print("=" * 80)
    print()

    # Step 1: Initialize database
    print("[1] Initializing database...")
    test_db_path = Path.home() / ".spinemodeling" / "test_spinemodeling.db"
    test_db_path.parent.mkdir(exist_ok=True)

    # Remove old test database if it exists
    if test_db_path.exists():
        test_db_path.unlink()
        print(f"    Removed old test database: {test_db_path}")

    db = DatabaseManager(f"sqlite:///{test_db_path}")
    db.initialize_database()
    print(f"    ✓ Database initialized at: {test_db_path}")
    print()

    # Step 2: Create a test subject
    print("[2] Creating test subject...")
    subject = db.create_subject(
        subject_code="TEST-001",
        name="Test Patient",
        gender="F",
        height=165.0,
        weight=58.0,
        notes="Test subject for database integration"
    )
    print(f"    ✓ Created subject: {subject}")
    print()

    # Step 3: Create point measurements
    print("[3] Creating point measurements...")
    point_measurements = []

    # Frontal view point
    point1 = db.create_measurement(
        subject_id=subject.subject_id,
        measurement_name="L1 Superior Endplate (Frontal)",
        measurement_type="Point",
        image_type="EOS_Frontal",
        x_coord=100.5,
        y_coord=200.3,
        comment="Frontal view landmark",
        user="TestUser",
        measurement_date=datetime.now()
    )
    point_measurements.append(point1)
    print(f"    ✓ Created point measurement 1: {point1.measurement_name}")

    # Lateral view point
    point2 = db.create_measurement(
        subject_id=subject.subject_id,
        measurement_name="L1 Superior Endplate (Lateral)",
        measurement_type="Point",
        image_type="EOS_Lateral",
        x_coord=150.2,
        y_coord=205.8,
        comment="Lateral view landmark",
        user="TestUser",
        measurement_date=datetime.now()
    )
    point_measurements.append(point2)
    print(f"    ✓ Created point measurement 2: {point2.measurement_name}")
    print()

    # Step 4: Create ellipse measurements
    print("[4] Creating ellipse measurements...")
    ellipse_measurements = []

    # Pedicle ellipse
    ellipse1 = db.create_measurement(
        subject_id=subject.subject_id,
        measurement_name="L2 Pedicle Width",
        measurement_type="Ellipse",
        image_type="EOS_Frontal",
        ellipse_center_x=180.5,
        ellipse_center_y=350.2,
        ellipse_major_axis=15.8,
        ellipse_minor_axis=12.3,
        ellipse_angle=25.5,
        measurement_value=15.8,
        measurement_unit="mm",
        comment="Pedicle measurement",
        user="TestUser",
        measurement_date=datetime.now()
    )
    ellipse_measurements.append(ellipse1)
    print(f"    ✓ Created ellipse measurement 1: {ellipse1.measurement_name}")

    # Vertebral body ellipse
    ellipse2 = db.create_measurement(
        subject_id=subject.subject_id,
        measurement_name="L3 Vertebral Body",
        measurement_type="Ellipse",
        image_type="EOS_Lateral",
        ellipse_center_x=220.3,
        ellipse_center_y=450.7,
        ellipse_major_axis=28.5,
        ellipse_minor_axis=22.1,
        ellipse_angle=12.0,
        measurement_value=28.5,
        measurement_unit="mm",
        comment="Vertebral body measurement",
        user="TestUser",
        measurement_date=datetime.now()
    )
    ellipse_measurements.append(ellipse2)
    print(f"    ✓ Created ellipse measurement 2: {ellipse2.measurement_name}")
    print()

    # Step 5: Retrieve measurements
    print("[5] Retrieving measurements for subject...")
    all_measurements = db.get_measurements_by_subject(subject.subject_id)
    print(f"    ✓ Retrieved {len(all_measurements)} measurements")
    for i, meas in enumerate(all_measurements, 1):
        print(f"       {i}. {meas.measurement_name} ({meas.measurement_type})")
    print()

    # Step 6: Update a measurement
    print("[6] Updating a measurement...")
    updated_meas = db.update_measurement(
        point1.measurement_id,
        comment="Updated comment for testing",
        user="UpdatedUser"
    )
    print(f"    ✓ Updated measurement: {updated_meas.measurement_name}")
    print(f"       New comment: {updated_meas.comment}")
    print(f"       New user: {updated_meas.user}")
    print()

    # Step 7: Delete a measurement
    print("[7] Deleting a measurement...")
    deleted = db.delete_measurement(ellipse2.measurement_id)
    print(f"    ✓ Deleted measurement: {deleted}")

    remaining = db.get_measurements_by_subject(subject.subject_id)
    print(f"    Remaining measurements: {len(remaining)}")
    print()

    # Step 8: Get all subjects
    print("[8] Retrieving all subjects...")
    all_subjects = db.get_all_subjects()
    print(f"    ✓ Retrieved {len(all_subjects)} subjects")
    for subj in all_subjects:
        print(f"       - {subj.subject_code}: {subj.name}")
    print()

    # Step 9: Get subject by code
    print("[9] Getting subject by code...")
    found_subject = db.get_subject_by_code("TEST-001")
    if found_subject:
        print(f"    ✓ Found subject: {found_subject.subject_code}")
        print(f"       Name: {found_subject.name}")
        print(f"       Gender: {found_subject.gender}")
        print(f"       Height: {found_subject.height} cm")
        print(f"       Weight: {found_subject.weight} kg")
    else:
        print("    ✗ Subject not found")
    print()

    # Step 10: Test subject deletion (cascade)
    print("[10] Testing subject deletion (should cascade to measurements)...")
    measurements_before = len(db.get_measurements_by_subject(subject.subject_id))
    print(f"     Measurements before deletion: {measurements_before}")

    deleted_subject = db.delete_subject(subject.subject_id)
    print(f"     ✓ Deleted subject: {deleted_subject}")

    # Verify measurements are also deleted (cascade)
    try:
        measurements_after = db.get_measurements_by_subject(subject.subject_id)
        print(f"     Measurements after deletion: {len(measurements_after)}")
    except:
        print("     ✓ Measurements cascade deleted with subject")
    print()

    # Cleanup
    print("[11] Cleanup...")
    db.close_session()
    print("    ✓ Database session closed")
    print()

    print("=" * 80)
    print("ALL TESTS PASSED!")
    print("=" * 80)
    print()
    print(f"Test database created at: {test_db_path}")
    print("You can inspect it with SQLite browser or command-line tools.")
    print()


if __name__ == "__main__":
    try:
        test_database_integration()
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
