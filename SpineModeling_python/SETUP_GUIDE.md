# Patient Data System - Setup Guide

## Quick Setup (3 Steps)

### Step 1: Migrate Existing Database (If Needed)

If you have an existing database, run the migration script first:

```bash
cd SpineModeling_python
python migrate_database.py
```

**What it does:**
- Backs up your existing database automatically
- Adds new columns: `subjects.data_folder`
- Creates new table: `patient_images`
- Preserves all existing patient and measurement data

**When to run this:**
- If you get "no such column: subjects.data_folder" error
- If you get "no such table: patient_images" error
- After pulling new code with database schema changes

**Safe to run:**
- ✓ Creates automatic backup before migration
- ✓ Preserves all existing data
- ✓ Can be run multiple times (checks if migration is needed)

---

### Step 2: Initialize All Patients

Create folder structures and database entries for all 75 patients:

```bash
python initialize_all_patients.py
```

**What it does:**
- Creates folder structure for ASD-001 to ASD-075
- Each patient gets:
  - `EOS/frontal/` folder
  - `EOS/lateral/` folder
  - `CT/` folder with 19 vertebra subfolders (Sacrum, L5-L1, T12-T1)
- Creates/updates database entries for all patients

**Folder structure created:**
```
resources/patient_data/
├── ASD-001/
│   ├── EOS/
│   │   ├── frontal/
│   │   └── lateral/
│   └── CT/
│       ├── Sacrum/
│       ├── L5/, L4/, L3/, L2/, L1/
│       └── T12/, T11/, ..., T2/, T1/
├── ASD-002/
...
└── ASD-075/
```

---

### Step 3: Launch the Application

```bash
python main.py
```

Then click **"Patient Manager"** button (or press **Ctrl+P**)

---

## Using the Patient Manager

### Search and Select a Patient

1. **Search**: Type patient code in search box (e.g., "ASD-043")
2. **Select**: Click on patient in the list
3. **Upload Images**: Use the upload buttons for EOS or CT images
4. **Edit Info**: Switch to "Patient Information" tab to add demographics

### Upload EOS Images

1. Select a patient
2. Click **"Upload Frontal Image"** or **"Upload Lateral Image"**
3. Browse to your DICOM or image file (.dcm, .png, .jpg)
4. File is automatically copied to the correct folder
5. Database record is created

### Upload CT Scans

1. Select a patient
2. Choose vertebra level from dropdown (e.g., "L2", "T12", "Sacrum")
3. Click **"Upload CT Image/Mesh"**
4. Browse to your mesh or DICOM file (.stl, .obj, .dcm)
5. File is automatically organized by vertebra level

### Edit Patient Information

1. Select a patient
2. Go to "Patient Information" tab
3. Enter:
   - Name
   - Date of Birth
   - Gender
   - Height (cm)
   - Weight (kg)
   - Notes
4. Click **"Save Patient Information"**

---

## Troubleshooting

### "no such column: subjects.data_folder"

**Solution:** Run the migration script:
```bash
python migrate_database.py
```

### "Database is locked"

**Solution:** Close the application and any other programs accessing the database, then try again.

### "Permission denied" when creating folders

**Solution:** Check that you have write permissions to:
- `~/.spinemodeling/` (for database)
- `SpineModeling_python/resources/patient_data/` (for patient folders)

### Can't find uploaded images

**Solution:** Click "Refresh Image List" button in the Patient Manager

### Migration failed

**Solution:** Your database was automatically backed up. Check:
- `~/.spinemodeling/spinemodeling_backup_YYYYMMDD_HHMMSS.db`

To restore manually:
```bash
# On Linux/Mac
cp ~/.spinemodeling/spinemodeling_backup_*.db ~/.spinemodeling/spinemodeling.db

# On Windows
copy %USERPROFILE%\.spinemodeling\spinemodeling_backup_*.db %USERPROFILE%\.spinemodeling\spinemodeling.db
```

---

## Database Location

Your database is stored at:

**Linux/Mac:**
```
~/.spinemodeling/spinemodeling.db
```

**Windows:**
```
C:\Users\YourUsername\.spinemodeling\spinemodeling.db
```

---

## Patient Data Location

Patient folders are stored at:
```
<project>/SpineModeling_python/resources/patient_data/
```

---

## File Types Supported

### EOS Images
- `.dcm`, `.dicom` - DICOM format (recommended)
- `.png` - PNG images
- `.jpg`, `.jpeg` - JPEG images

### CT Scans
- `.stl` - STL mesh format (recommended for 3D models)
- `.obj` - OBJ mesh format
- `.dcm`, `.dicom` - DICOM format

---

## Complete Workflow Example

```bash
# 1. Migrate database (if you have existing data)
cd SpineModeling_python
python migrate_database.py
# Answer 'yes' to continue

# 2. Initialize all patients
python initialize_all_patients.py
# Answer 'yes' to continue

# 3. Launch application
python main.py

# 4. In the application:
#    - Click "Patient Manager" button
#    - Search for "ASD-043"
#    - Upload EOS frontal image
#    - Upload EOS lateral image
#    - Select "L2" from dropdown
#    - Upload L2 CT scan
#    - Fill in patient information
#    - Click "Save Patient Information"
```

---

## What Gets Created

After running the setup scripts, you will have:

✓ **Database** at `~/.spinemodeling/spinemodeling.db` with:
  - 75 patient records (ASD-001 to ASD-075)
  - Patient demographics table
  - Image tracking table

✓ **75 Patient Folders** at `resources/patient_data/` with:
  - EOS folders (frontal/lateral) for each patient
  - CT folders (19 vertebrae) for each patient
  - ~1600 empty folders ready to receive images

✓ **UI Integration**:
  - "Patient Manager" button on main window
  - Menu item: File → Patient Manager (Ctrl+P)
  - About dialog with patient system info

---

## Next Steps

After setup, you can:

1. **Upload Images**: Use Patient Manager to organize your imaging data
2. **Analyze Images**: Use "Skeletal" button to perform image analysis
3. **Track Data**: All uploaded images are tracked in the database
4. **Manage Patients**: Edit patient information as needed

For more details, see: `PATIENT_DATA_SYSTEM_README.md`
