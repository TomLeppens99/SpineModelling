# SpineModelling Database Setup Guide

## Overview

The SpineModelling project uses **SQLite** with **SQLAlchemy ORM** to store patient data, measurements from EOS X-ray images, and CT scan information. The database automatically handles:
- Patient/subject demographics
- 2D and 3D measurements
- Ellipse fitting results
- Coordinate data from EOS images

## Database Location

The database is automatically created at:
```
~/.spinemodeling/spinemodeling.db
```
(On Linux/Mac: `/home/username/.spinemodeling/spinemodeling.db`)
(On Windows: `C:\Users\username\.spinemodeling\spinemodeling.db`)

## Quick Start

### 1. Automatic Setup (Recommended)

The database is **automatically initialized** when you run the application:

```bash
cd SpineModeling_python
python main.py
```

The application will:
- Create the `~/.spinemodeling/` directory
- Initialize the SQLite database
- Create all required tables
- Display confirmation: "Database initialized: /path/to/spinemodeling.db"

### 2. Manual Setup (for testing/scripts)

If you want to initialize the database manually or use it in scripts:

```python
from pathlib import Path
from spine_modeling.database.models import DatabaseManager

# Define database path
db_path = Path.home() / ".spinemodeling" / "spinemodeling.db"
db_path.parent.mkdir(parents=True, exist_ok=True)

# Create database manager and initialize
db_url = f"sqlite:///{db_path}"
db_manager = DatabaseManager(db_url)
db_manager.initialize_database()

print(f"Database initialized at: {db_path}")
```

## Database Schema

### Tables Overview

The database has **2 main tables**:

1. **subjects** - Patient information
2. **measurements** - All measurements (2D, 3D, ellipse fits) linked to subjects

### Table: `subjects`

Stores patient/subject information:

| Column | Type | Description |
|--------|------|-------------|
| `subject_id` | INTEGER (PK) | Auto-incrementing primary key |
| `subject_code` | STRING(50) | **Unique** patient code (e.g., "ASD-043") |
| `name` | STRING(200) | Patient full name |
| `date_of_birth` | DATETIME | Date of birth |
| `gender` | STRING(10) | Gender (M/F/Other) |
| `height` | FLOAT | Height in cm |
| `weight` | FLOAT | Weight in kg |
| `created_date` | DATETIME | Record creation timestamp |
| `notes` | TEXT | Additional notes |

**Note**: `subject_code` is indexed and must be unique.

### Table: `measurements`

Stores all measurement data from EOS images and analyses:

| Column | Type | Description |
|--------|------|-------------|
| `measurement_id` | INTEGER (PK) | Auto-incrementing primary key |
| `subject_id` | INTEGER (FK) | Foreign key to subjects table |
| `measurement_name` | STRING(200) | Measurement name (e.g., "Pedicle Width L2") |
| `measurement_value` | FLOAT | Numeric measurement value |
| `measurement_unit` | STRING(50) | Unit (e.g., "mm", "degrees") |
| `measurement_type` | STRING(50) | Type: "2D", "3D", "Ellipse" |
| `image_type` | STRING(50) | Image source: "EOS_Frontal", "EOS_Lateral", "CT" |
| `measurement_date` | DATETIME | When measurement was taken |
| `user` | STRING(100) | User who performed measurement |
| `comment` | TEXT | Additional comments |
| **Coordinate Data** | | |
| `x_coord` | FLOAT | X coordinate (for point measurements) |
| `y_coord` | FLOAT | Y coordinate |
| `z_coord` | FLOAT | Z coordinate (for 3D measurements) |
| **Ellipse Data** | | |
| `ellipse_center_x` | FLOAT | Ellipse center X coordinate |
| `ellipse_center_y` | FLOAT | Ellipse center Y coordinate |
| `ellipse_major_axis` | FLOAT | Major axis length |
| `ellipse_minor_axis` | FLOAT | Minor axis length |
| `ellipse_angle` | FLOAT | Rotation angle in degrees |
| `created_date` | DATETIME | Record creation timestamp |

**Note**: `subject_id` is indexed for fast lookups. Measurements are cascade-deleted when a subject is deleted.

## Current Limitations: File Path Storage

### What's Missing

The current database schema **does NOT store file paths** for:
- EOS DICOM images (.dcm files)
- CT STL meshes (.stl files)
- OpenSim models (.osim files)

### Why This Matters

Currently, the workflow is:
1. User manually loads EOS images via File → Import EOS Images
2. Application processes images and stores measurements
3. **Image file paths are not saved**
4. Next session: User must reload images manually

### Recommended Enhancement

Add file path tracking to better manage patient imaging data. See below for implementation.

## Working with the Database

### Example 1: Create a New Patient

```python
from spine_modeling.database.models import DatabaseManager

# Connect to database
db = DatabaseManager("sqlite:///~/.spinemodeling/spinemodeling.db")

# Create a new subject
subject = db.create_subject(
    subject_code="ASD-043",
    name="John Doe",
    date_of_birth="1985-03-15",
    gender="M",
    height=175.0,  # cm
    weight=70.0,   # kg
    notes="Scoliosis patient, EOS imaging on 2025-11-13"
)

print(f"Created subject: {subject.subject_code} (ID: {subject.subject_id})")
```

### Example 2: Store Measurement from EOS Image

```python
# Create measurement from EOS frontal view
measurement = db.create_measurement(
    subject_id=subject.subject_id,
    measurement_name="Pedicle Width L2",
    measurement_value=8.5,
    measurement_unit="mm",
    measurement_type="Ellipse",
    image_type="EOS_Frontal",
    ellipse_center_x=512.3,
    ellipse_center_y=1024.7,
    ellipse_major_axis=10.2,
    ellipse_minor_axis=8.5,
    ellipse_angle=15.3,
    user="Dr. Smith",
    comment="Measured using Fitzgibbon ellipse fit"
)

print(f"Stored measurement: {measurement.measurement_name}")
```

### Example 3: Store 3D Coordinate from EOS Reconstruction

```python
# Store 3D point from dual X-ray reconstruction
measurement_3d = db.create_measurement(
    subject_id=subject.subject_id,
    measurement_name="L2 Superior Endplate Center",
    measurement_type="3D",
    image_type="EOS_Dual",
    x_coord=0.015,  # meters
    y_coord=0.123,
    z_coord=0.456,
    measurement_unit="m",
    user="Dr. Smith",
    comment="Reconstructed from frontal + lateral EOS views"
)
```

### Example 4: Retrieve All Measurements for a Patient

```python
# Get subject by code
subject = db.get_subject_by_code("ASD-043")

# Get all measurements for this subject
measurements = db.get_measurements_by_subject(subject.subject_id)

print(f"Patient {subject.subject_code} has {len(measurements)} measurements:")
for m in measurements:
    print(f"  - {m.measurement_name}: {m.measurement_value} {m.measurement_unit}")
```

### Example 5: Query Specific Measurement Types

```python
from spine_modeling.database.models import Measurement

# Get database session
session = db.get_session()

# Query all ellipse measurements for frontal EOS images
ellipse_measurements = session.query(Measurement).filter(
    Measurement.measurement_type == "Ellipse",
    Measurement.image_type == "EOS_Frontal"
).all()

print(f"Found {len(ellipse_measurements)} ellipse measurements from frontal EOS")
```

### Example 6: Update Patient Information

```python
# Update subject information
db.update_subject(
    subject_id=subject.subject_id,
    weight=72.0,  # Updated weight
    notes="Weight updated after follow-up visit"
)
```

### Example 7: Delete Patient and All Measurements

```python
# Delete subject (cascade deletes all associated measurements)
success = db.delete_subject(subject_id=subject.subject_id)
if success:
    print("Subject and all measurements deleted")
```

## Enhanced Schema for File Path Storage

### Recommended Addition: `imaging_sessions` Table

To properly track EOS images and STL files, consider adding this table:

```python
class ImagingSession(Base):
    """
    Stores imaging session data including file paths.
    """
    __tablename__ = "imaging_sessions"

    session_id = Column(Integer, primary_key=True, autoincrement=True)
    subject_id = Column(Integer, ForeignKey("subjects.subject_id"), nullable=False)
    session_date = Column(DateTime, default=datetime.now, nullable=False)
    session_type = Column(String(50), nullable=False)  # "EOS", "CT", "MRI"

    # EOS image paths
    eos_frontal_path = Column(String(500), nullable=True)
    eos_lateral_path = Column(String(500), nullable=True)

    # CT/MRI paths (can store multiple as JSON)
    ct_paths = Column(Text, nullable=True)  # JSON array of STL file paths

    # Metadata
    notes = Column(Text, nullable=True)
    created_date = Column(DateTime, default=datetime.now, nullable=False)

    # Relationship
    subject = relationship("Subject", back_populates="imaging_sessions")
```

### Implementation Steps

If you want to add file path tracking:

1. **Add the new table definition** to `SpineModeling_python/spine_modeling/database/models.py`
2. **Add relationship** to Subject model:
   ```python
   imaging_sessions = relationship("ImagingSession", back_populates="subject")
   ```
3. **Add methods** to DatabaseManager:
   ```python
   def create_imaging_session(self, subject_id, session_type, **kwargs):
       # Implementation

   def get_sessions_by_subject(self, subject_id):
       # Implementation
   ```
4. **Re-initialize database** to create new table

## Database Maintenance

### Backup Database

```bash
# Simple file copy (database is a single file)
cp ~/.spinemodeling/spinemodeling.db ~/.spinemodeling/spinemodeling_backup_$(date +%Y%m%d).db
```

### View Database Contents (SQLite Browser)

```bash
# Install SQLite browser
sudo apt install sqlitebrowser  # Linux
brew install --cask db-browser-for-sqlite  # Mac

# Open database
sqlitebrowser ~/.spinemodeling/spinemodeling.db
```

### Reset Database

```bash
# Delete database file to start fresh
rm ~/.spinemodeling/spinemodeling.db

# Re-run application to recreate
python main.py
```

### Export Data to CSV

```python
import pandas as pd
from spine_modeling.database.models import DatabaseManager, Subject, Measurement

db = DatabaseManager("sqlite:///~/.spinemodeling/spinemodeling.db")
session = db.get_session()

# Export subjects to CSV
subjects = pd.read_sql_table("subjects", con=db.engine)
subjects.to_csv("subjects_export.csv", index=False)

# Export measurements to CSV
measurements = pd.read_sql_table("measurements", con=db.engine)
measurements.to_csv("measurements_export.csv", index=False)
```

## Sample Data Example

The project includes sample data for testing:

**Location**: `SpineModeling_python/resources/sample_data/`
- `EOS/ASD-043/Patient_F.dcm` - Frontal EOS X-ray (32.87 MB)
- `EOS/ASD-043/Patient_L.dcm` - Lateral EOS X-ray (30.58 MB)
- `CT/ASD-043/*.stl` - L2, L3, L4 vertebrae meshes (7.8-18.9 MB each)

### Creating Sample Database Entry

```python
from pathlib import Path
from spine_modeling.database.models import DatabaseManager

db = DatabaseManager("sqlite:///~/.spinemodeling/spinemodeling.db")
db.initialize_database()

# Create subject for sample data
subject = db.create_subject(
    subject_code="ASD-043",
    name="Sample Patient",
    gender="Unknown",
    notes="Sample data from resources/sample_data/"
)

# Create measurement entry (after loading EOS images in app)
measurement = db.create_measurement(
    subject_id=subject.subject_id,
    measurement_name="Test Measurement",
    measurement_type="2D",
    image_type="EOS_Frontal",
    user="System",
    comment="Sample data validation"
)

print(f"Sample database entry created for {subject.subject_code}")
```

## Troubleshooting

### Issue: "No such table: subjects"
**Solution**: Database not initialized. Run `python main.py` or call `db.initialize_database()`

### Issue: "UNIQUE constraint failed: subjects.subject_code"
**Solution**: Subject code already exists. Either:
- Use a different subject_code
- Retrieve existing subject: `db.get_subject_by_code("ASD-043")`
- Delete existing subject: `db.delete_subject(subject_id)`

### Issue: Database file permission denied
**Solution**: Check file permissions:
```bash
chmod 644 ~/.spinemodeling/spinemodeling.db
```

### Issue: Can't find database file
**Solution**: Check the path printed during app startup or use:
```python
from pathlib import Path
print(Path.home() / ".spinemodeling" / "spinemodeling.db")
```

## Next Steps

1. **Run the application** to auto-create database: `python main.py`
2. **Load sample EOS images** via File → Import EOS Images
3. **Create measurements** using the 2D analysis panel
4. **View stored data** using database queries or SQLite browser
5. **(Optional) Enhance schema** to store file paths for better data management

## Summary

- **Database Type**: SQLite (single file, no server required)
- **Location**: `~/.spinemodeling/spinemodeling.db`
- **Setup**: Automatic when running `python main.py`
- **Tables**: `subjects` (patients), `measurements` (all measurement data)
- **Current Gap**: File paths for EOS/STL files not stored (manual loading required)
- **Recommended**: Add `imaging_sessions` table for file path tracking

For questions or to enhance the database schema, refer to:
- Implementation: `SpineModeling_python/spine_modeling/database/models.py`
- Main entry: `SpineModeling_python/main.py` (lines 117-134)
