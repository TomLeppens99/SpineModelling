"""
Patient Data Manager - Utilities for managing patient folder structure.

This module provides utilities for creating and managing the organized
folder structure for patient imaging data (EOS X-rays and CT scans).

The folder structure is:
    patient_data/
    ├── ASD-001/
    │   ├── EOS/
    │   │   ├── frontal/
    │   │   └── lateral/
    │   └── CT/
    │       ├── Sacrum/
    │       ├── L5/
    │       ├── L4/
    │       ├── L3/
    │       ├── L2/
    │       ├── L1/
    │       ├── T12/
    │       ├── T11/
    │       ├── T10/
    │       ├── T9/
    │       ├── T8/
    │       ├── T7/
    │       ├── T6/
    │       ├── T5/
    │       ├── T4/
    │       ├── T3/
    │       ├── T2/
    │       └── T1/
    ├── ASD-002/
    ...
    └── ASD-075/
"""

from pathlib import Path
from typing import List, Optional
import shutil
import os


# Define vertebra levels from Sacrum to T1
VERTEBRA_LEVELS = [
    "Sacrum",
    "L5", "L4", "L3", "L2", "L1",
    "T12", "T11", "T10", "T9", "T8", "T7",
    "T6", "T5", "T4", "T3", "T2", "T1"
]


class PatientDataManager:
    """
    Manages patient data folder structure.

    This class handles creation and management of organized folder structures
    for patient imaging data.

    Attributes:
        base_path: Base directory for all patient data
    """

    def __init__(self, base_path: Optional[Path] = None):
        """
        Initialize the patient data manager.

        Args:
            base_path: Base directory for patient data. If None, uses
                      resources/patient_data in the project root.
        """
        if base_path is None:
            # Default to resources/patient_data
            project_root = Path(__file__).parent.parent.parent
            base_path = project_root / "resources" / "patient_data"

        self.base_path = Path(base_path)

    def get_patient_folder(self, patient_code: str) -> Path:
        """
        Get the folder path for a specific patient.

        Args:
            patient_code: Patient code (e.g., "ASD-043")

        Returns:
            Path to patient's data folder
        """
        return self.base_path / patient_code

    def get_eos_folder(self, patient_code: str, view: Optional[str] = None) -> Path:
        """
        Get the EOS folder path for a patient.

        Args:
            patient_code: Patient code (e.g., "ASD-043")
            view: Optional view type ("frontal" or "lateral")

        Returns:
            Path to EOS folder or specific view subfolder
        """
        eos_folder = self.get_patient_folder(patient_code) / "EOS"
        if view:
            return eos_folder / view
        return eos_folder

    def get_ct_folder(self, patient_code: str, vertebra: Optional[str] = None) -> Path:
        """
        Get the CT folder path for a patient.

        Args:
            patient_code: Patient code (e.g., "ASD-043")
            vertebra: Optional vertebra level (e.g., "L2", "T12")

        Returns:
            Path to CT folder or specific vertebra subfolder
        """
        ct_folder = self.get_patient_folder(patient_code) / "CT"
        if vertebra:
            return ct_folder / vertebra
        return ct_folder

    def create_patient_folders(self, patient_code: str) -> dict:
        """
        Create the complete folder structure for a single patient.

        Args:
            patient_code: Patient code (e.g., "ASD-043")

        Returns:
            Dictionary with paths to created folders
        """
        patient_folder = self.get_patient_folder(patient_code)

        # Create main patient folder
        patient_folder.mkdir(parents=True, exist_ok=True)

        # Create EOS subfolders
        eos_frontal = self.get_eos_folder(patient_code, "frontal")
        eos_lateral = self.get_eos_folder(patient_code, "lateral")
        eos_frontal.mkdir(parents=True, exist_ok=True)
        eos_lateral.mkdir(parents=True, exist_ok=True)

        # Create CT vertebra subfolders
        ct_folders = {}
        for vertebra in VERTEBRA_LEVELS:
            vertebra_folder = self.get_ct_folder(patient_code, vertebra)
            vertebra_folder.mkdir(parents=True, exist_ok=True)
            ct_folders[vertebra] = vertebra_folder

        return {
            "patient_folder": patient_folder,
            "eos_frontal": eos_frontal,
            "eos_lateral": eos_lateral,
            "ct_folders": ct_folders
        }

    def create_all_patient_folders(
        self,
        start_num: int = 1,
        end_num: int = 75,
        prefix: str = "ASD"
    ) -> List[str]:
        """
        Create folder structures for all patients.

        Args:
            start_num: Starting patient number (default: 1)
            end_num: Ending patient number (default: 75)
            prefix: Patient code prefix (default: "ASD")

        Returns:
            List of created patient codes
        """
        created_patients = []

        for num in range(start_num, end_num + 1):
            patient_code = f"{prefix}-{num:03d}"
            self.create_patient_folders(patient_code)
            created_patients.append(patient_code)

        return created_patients

    def initialize_all_patients_in_db(self, db_manager):
        """
        Initialize all patients (ASD-001 to ASD-075) in the database.

        Creates folder structures and database entries for all patients.

        Args:
            db_manager: DatabaseManager instance

        Returns:
            List of created Subject objects
        """
        from spine_modeling.database.models import Subject

        created_subjects = []

        # Create folder structures
        patient_codes = self.create_all_patient_folders()

        # Create database entries
        for patient_code in patient_codes:
            # Check if patient already exists
            existing = db_manager.get_subject_by_code(patient_code)
            if existing:
                # Update the data folder path
                patient_folder = str(self.get_patient_folder(patient_code))
                db_manager.update_subject(existing.subject_id, data_folder=patient_folder)
                created_subjects.append(existing)
            else:
                # Create new patient record
                patient_folder = str(self.get_patient_folder(patient_code))
                subject = db_manager.create_subject(
                    subject_code=patient_code,
                    data_folder=patient_folder
                )
                created_subjects.append(subject)

        return created_subjects

    def copy_file_to_patient_folder(
        self,
        source_file: Path,
        patient_code: str,
        image_type: str,
        vertebra: Optional[str] = None
    ) -> Path:
        """
        Copy a file to the appropriate patient folder.

        Args:
            source_file: Source file path
            patient_code: Patient code (e.g., "ASD-043")
            image_type: "EOS_Frontal", "EOS_Lateral", or "CT"
            vertebra: Vertebra level (required for CT images)

        Returns:
            Destination file path

        Raises:
            ValueError: If image_type is invalid or vertebra is missing for CT
        """
        source_file = Path(source_file)

        # Determine destination folder
        if image_type == "EOS_Frontal":
            dest_folder = self.get_eos_folder(patient_code, "frontal")
        elif image_type == "EOS_Lateral":
            dest_folder = self.get_eos_folder(patient_code, "lateral")
        elif image_type == "CT":
            if not vertebra:
                raise ValueError("Vertebra level is required for CT images")
            dest_folder = self.get_ct_folder(patient_code, vertebra)
        else:
            raise ValueError(f"Invalid image_type: {image_type}")

        # Ensure destination folder exists
        dest_folder.mkdir(parents=True, exist_ok=True)

        # Copy file
        dest_file = dest_folder / source_file.name
        shutil.copy2(source_file, dest_file)

        return dest_file

    def get_relative_path(self, absolute_path: Path) -> str:
        """
        Get relative path from base_path.

        Args:
            absolute_path: Absolute file path

        Returns:
            Relative path as string
        """
        absolute_path = Path(absolute_path)
        try:
            return str(absolute_path.relative_to(self.base_path))
        except ValueError:
            # If path is not relative to base_path, return as-is
            return str(absolute_path)

    def list_patient_images(self, patient_code: str) -> dict:
        """
        List all images for a patient.

        Args:
            patient_code: Patient code

        Returns:
            Dictionary with lists of image files organized by type
        """
        result = {
            "eos_frontal": [],
            "eos_lateral": [],
            "ct": {}
        }

        # List EOS frontal images
        frontal_folder = self.get_eos_folder(patient_code, "frontal")
        if frontal_folder.exists():
            result["eos_frontal"] = [
                f for f in frontal_folder.iterdir()
                if f.is_file() and f.suffix.lower() in ['.dcm', '.dicom', '.png', '.jpg']
            ]

        # List EOS lateral images
        lateral_folder = self.get_eos_folder(patient_code, "lateral")
        if lateral_folder.exists():
            result["eos_lateral"] = [
                f for f in lateral_folder.iterdir()
                if f.is_file() and f.suffix.lower() in ['.dcm', '.dicom', '.png', '.jpg']
            ]

        # List CT images by vertebra
        for vertebra in VERTEBRA_LEVELS:
            vertebra_folder = self.get_ct_folder(patient_code, vertebra)
            if vertebra_folder.exists():
                result["ct"][vertebra] = [
                    f for f in vertebra_folder.iterdir()
                    if f.is_file() and f.suffix.lower() in ['.stl', '.obj', '.dcm', '.dicom']
                ]

        return result

    def get_folder_stats(self, patient_code: str) -> dict:
        """
        Get statistics about a patient's data folders.

        Args:
            patient_code: Patient code

        Returns:
            Dictionary with folder statistics
        """
        images = self.list_patient_images(patient_code)

        stats = {
            "patient_code": patient_code,
            "eos_frontal_count": len(images["eos_frontal"]),
            "eos_lateral_count": len(images["eos_lateral"]),
            "ct_vertebra_counts": {v: len(files) for v, files in images["ct"].items() if files},
            "total_ct_count": sum(len(files) for files in images["ct"].values())
        }

        return stats


# Convenience functions
def get_default_manager() -> PatientDataManager:
    """Get a PatientDataManager with default settings."""
    return PatientDataManager()


def initialize_patient_data_structure():
    """
    Initialize the complete patient data structure (ASD-001 to ASD-075).

    This is a convenience function for initial setup.
    """
    manager = get_default_manager()
    created = manager.create_all_patient_folders()
    print(f"Created folder structures for {len(created)} patients")
    print(f"Base directory: {manager.base_path}")
    return manager


if __name__ == "__main__":
    # Example usage: Initialize all patient folders
    print("Initializing patient data folder structure...")
    manager = initialize_patient_data_structure()

    # Show some statistics
    print("\nSample folder structure:")
    sample_patient = "ASD-001"
    stats = manager.get_folder_stats(sample_patient)
    print(f"Patient: {stats['patient_code']}")
    print(f"Folder: {manager.get_patient_folder(sample_patient)}")
