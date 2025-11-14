# Patient Data Management System

## Overview

This system provides comprehensive patient data management for the SpineModeling application, supporting 75 patients (ASD-001 to ASD-075) with organized folder structures for EOS X-ray images and CT scans by vertebra level.

## Features

- **Patient Database**: SQLite database with patient records, demographics, and image tracking
- **Organized Folder Structure**: Automatic folder creation for each patient
  - EOS folders (frontal and lateral views)
  - CT folders by vertebra (Sacrum to T1)
- **Patient Manager UI**: Easy-to-use dialog for:
  - Patient selection and search
  - Image upload (EOS and CT)
  - Patient information management
- **Image Tracking**: Database records for all uploaded images with metadata

## Quick Start

### 1. Initialize All Patients

Run the initialization script to create folder structures and database entries for all 75 patients:

```bash
cd SpineModeling_python
python initialize_all_patients.py
```

This will create:
- Folder structure for ASD-001 to ASD-075
- Database entries for all patients
- Organized EOS and CT subfolders

### 2. Launch the Application

```bash
python main.py
```

### 3. Use the Patient Manager

1. Click the **"Patient Manager"** button on the main window (or press Ctrl+P)
2. Search for a patient using the search box (e.g., "ASD-043")
3. Select a patient from the list
4. Upload images:
   - **EOS Frontal**: Click "Upload Frontal Image"
   - **EOS Lateral**: Click "Upload Lateral Image"
   - **CT Scans**: Select vertebra level, then click "Upload CT Image/Mesh"
5. Edit patient information in the "Patient Information" tab
6. Click "Select Patient" to close and work with that patient

## Folder Structure

Each patient has the following folder structure:

```
resources/patient_data/
└── ASD-XXX/
    ├── EOS/
    │   ├── frontal/          # Frontal X-ray images (.dcm, .png, .jpg)
    │   └── lateral/          # Lateral X-ray images (.dcm, .png, .jpg)
    └── CT/
        ├── Sacrum/           # Sacrum CT scans/meshes
        ├── L5/               # Lumbar vertebrae
        ├── L4/
        ├── L3/
        ├── L2/
        ├── L1/
        ├── T12/              # Thoracic vertebrae
        ├── T11/
        ├── T10/
        ├── T9/
        ├── T8/
        ├── T7/
        ├── T6/
        ├── T5/
        ├── T4/
        ├── T3/
        ├── T2/
        └── T1/
```

## Database Schema

### Subject Table

Stores patient information:
- `subject_id`: Primary key
- `subject_code`: Patient code (e.g., "ASD-043")
- `name`: Patient name
- `date_of_birth`: Date of birth
- `gender`: Gender (M/F/Other)
- `height`: Height in cm
- `weight`: Weight in kg
- `data_folder`: Path to patient's data folder
- `notes`: Additional notes
- `created_date`: Record creation date

### PatientImage Table

Tracks uploaded images:
- `image_id`: Primary key
- `subject_id`: Foreign key to Subject
- `image_type`: "EOS_Frontal", "EOS_Lateral", or "CT"
- `vertebra_level`: Vertebra level (for CT images)
- `file_path`: Relative path to image file
- `file_name`: Original filename
- `upload_date`: When image was uploaded
- `file_size`: File size in bytes
- `notes`: Additional notes

## Usage Examples

### Programmatic Access

```python
from pathlib import Path
from spine_modeling.database.models import DatabaseManager
from spine_modeling.utils.patient_data_manager import PatientDataManager

# Initialize managers
db_path = Path.home() / ".spinemodeling" / "spinemodeling.db"
db_url = f"sqlite:///{db_path}"
db_manager = DatabaseManager(db_url)
data_manager = PatientDataManager()

# Get a patient
subject = db_manager.get_subject_by_code("ASD-043")
print(f"Patient: {subject.subject_code}, Folder: {subject.data_folder}")

# Get patient's images
images = db_manager.get_images_by_subject(subject.subject_id)
for img in images:
    print(f"  {img.image_type}: {img.file_name}")

# Get specific image type
eos_frontal = db_manager.get_images_by_type(subject.subject_id, "EOS_Frontal")
ct_l2 = db_manager.get_images_by_vertebra(subject.subject_id, "L2")

# Upload an image
dest_path = data_manager.copy_file_to_patient_folder(
    Path("/path/to/image.dcm"),
    "ASD-043",
    "EOS_Frontal"
)

# Record in database
db_manager.create_patient_image(
    subject_id=subject.subject_id,
    image_type="EOS_Frontal",
    file_path=str(dest_path),
    file_name="image.dcm",
    file_size=32870000
)
```

### Using the Patient Manager Dialog

```python
from PyQt5.QtWidgets import QApplication
from spine_modeling.ui.dialogs import PatientManagerDialog

app = QApplication(sys.argv)
dialog = PatientManagerDialog(db_url)

def on_patient_selected(patient_code):
    print(f"Selected: {patient_code}")

dialog.patient_selected.connect(on_patient_selected)
dialog.exec_()
```

## File Types Supported

### EOS Images
- `.dcm` - DICOM format (primary)
- `.dicom` - DICOM format
- `.png` - PNG image format
- `.jpg`, `.jpeg` - JPEG image format

### CT Scans
- `.stl` - STL mesh format (primary for 3D models)
- `.obj` - OBJ mesh format
- `.dcm` - DICOM format

## Database Location

The SQLite database is stored at:
```
~/.spinemodeling/spinemodeling.db
```

On Linux/Mac: `/home/username/.spinemodeling/spinemodeling.db`
On Windows: `C:\Users\username\.spinemodeling\spinemodeling.db`

## Patient Data Location

Patient data folders are stored at:
```
<project_root>/SpineModeling_python/resources/patient_data/
```

## API Reference

### PatientDataManager

Main class for managing patient folders:

- `get_patient_folder(patient_code)`: Get patient's root folder
- `get_eos_folder(patient_code, view=None)`: Get EOS folder or specific view
- `get_ct_folder(patient_code, vertebra=None)`: Get CT folder or specific vertebra
- `create_patient_folders(patient_code)`: Create folder structure for one patient
- `create_all_patient_folders()`: Create folders for all 75 patients
- `copy_file_to_patient_folder(source, patient_code, image_type, vertebra=None)`: Copy and organize an image file
- `list_patient_images(patient_code)`: List all images for a patient
- `get_folder_stats(patient_code)`: Get statistics about patient's data

### DatabaseManager

Database operations:

**Subject Operations:**
- `create_subject(subject_code, name=None, **kwargs)`: Create new patient
- `get_subject_by_code(subject_code)`: Get patient by code
- `get_all_subjects()`: Get all patients
- `update_subject(subject_id, **kwargs)`: Update patient info
- `delete_subject(subject_id)`: Delete patient and all data

**Image Operations:**
- `create_patient_image(subject_id, image_type, file_path, file_name, **kwargs)`: Record new image
- `get_images_by_subject(subject_id)`: Get all images for patient
- `get_images_by_type(subject_id, image_type)`: Filter by image type
- `get_images_by_vertebra(subject_id, vertebra_level)`: Get CT images for specific vertebra
- `delete_patient_image(image_id)`: Delete image record

## Testing

Run the test suite:

```bash
cd SpineModeling_python
python test_patient_system.py
```

This tests:
1. Folder structure creation
2. Database integration
3. Image tracking
4. Full initialization (optional)

## Troubleshooting

### Database is locked
If you get a "database is locked" error, close all applications using the database and try again.

### Folder permissions
Ensure the application has write permissions to:
- `~/.spinemodeling/` (for database)
- `<project>/SpineModeling_python/resources/patient_data/` (for patient data)

### Missing dependencies
Install required packages:
```bash
pip install sqlalchemy pyqt5 numpy scipy pydicom opencv-python
```

## Migration Notes

If you have existing patient data:

1. **Backup your database**: Copy `~/.spinemodeling/spinemodeling.db` to a safe location
2. **Run initialization**: This will create missing patients and folders
3. **Migrate existing images**: Use the Patient Manager to re-upload or move files to correct folders

## Future Enhancements

Potential future features:
- Batch image upload
- DICOM metadata extraction and display
- Image preview in Patient Manager
- Export patient data
- Import from external systems
- Advanced search and filtering
- Patient data archiving

## Support

For issues or questions:
1. Check the main project documentation: `CLAUDE.md`
2. Review test scripts for usage examples
3. Check database schema in `spine_modeling/database/models.py`

## Version History

- **v1.0.0** (2025-11-14): Initial release
  - 75 patient support (ASD-001 to ASD-075)
  - EOS and CT folder organization
  - Patient Manager UI
  - Database integration
  - Image tracking system
