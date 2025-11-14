#!/usr/bin/env python3
"""
Initialize all patients (ASD-001 to ASD-075) in the system.

This script creates:
1. Folder structure for all 75 patients
2. Database entries for all patients
3. Organized folders for EOS and CT images by vertebra

Run this script once during initial setup.
"""

import sys
from pathlib import Path

# Add package to path
sys.path.insert(0, str(Path(__file__).parent))

from spine_modeling.database.models import DatabaseManager
from spine_modeling.utils.patient_data_manager import PatientDataManager


def main():
    """Initialize all patients."""
    print("=" * 70)
    print("SPINE MODELING - PATIENT DATA INITIALIZATION")
    print("=" * 70)
    print()
    print("This script will initialize all 75 patients (ASD-001 to ASD-075).")
    print()
    print("What will be created:")
    print("  • Folder structure for each patient")
    print("  • EOS folders (frontal and lateral)")
    print("  • CT folders for each vertebra (Sacrum, L5-L1, T12-T1)")
    print("  • Database entries for all patients")
    print()

    response = input("Do you want to continue? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("\nOperation cancelled.")
        return 0

    print("\nInitializing...")

    try:
        # Get database URL
        db_path = Path.home() / ".spinemodeling" / "spinemodeling.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        db_url = f"sqlite:///{db_path}"

        # Initialize database
        db_manager = DatabaseManager(db_url)

        try:
            db_manager.initialize_database()
            print(f"✓ Database initialized: {db_path}")
        except Exception as db_error:
            if "no such column" in str(db_error):
                print(f"\n❌ Database schema is outdated!")
                print(f"\nYour existing database at:")
                print(f"  {db_path}")
                print(f"\nneeds to be migrated to the new schema.")
                print(f"\nPlease run the migration script first:")
                print(f"  python migrate_database.py")
                print(f"\nThen run this script again.")
                return 1
            else:
                raise

        # Initialize patients
        data_manager = PatientDataManager()
        print(f"✓ Base directory: {data_manager.base_path}")
        print()
        print("Creating patient folders and database entries...")

        subjects = data_manager.initialize_all_patients_in_db(db_manager)

        print(f"\n✓ Successfully initialized {len(subjects)} patients!")
        print()
        print("Sample patient folders created:")
        for i in [0, 24, 49, 74]:  # Show first, 25th, 50th, and last
            if i < len(subjects):
                s = subjects[i]
                print(f"  • {s.subject_code}")

        print()
        print("Folder structure for each patient:")
        print("  patient_data/")
        print("  └── ASD-XXX/")
        print("      ├── EOS/")
        print("      │   ├── frontal/")
        print("      │   └── lateral/")
        print("      └── CT/")
        print("          ├── Sacrum/")
        print("          ├── L5/, L4/, L3/, L2/, L1/")
        print("          └── T12/, T11/, ..., T2/, T1/")
        print()
        print("=" * 70)
        print("INITIALIZATION COMPLETE!")
        print("=" * 70)
        print()
        print("You can now:")
        print("  1. Run the application: python main.py")
        print("  2. Click 'Patient Manager' button")
        print("  3. Select a patient and upload images")
        print()

        db_manager.close_session()

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
