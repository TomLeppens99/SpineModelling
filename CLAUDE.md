# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Quick Start for AI Assistants

**Current Focus**: Python application development and enhancement (translation complete)

**Key Commands**:
```bash
# Run the Python application
cd SpineModeling_python && python main.py

# Run tests
cd SpineModeling_python && pytest

# View project status
cat SpineModelling_ProjectMap.md
```

**Most Important Files**:
- `SpineModeling_python/main.py` - Application entry point
- `SpineModeling_python/spine_modeling/` - Main package with all modules
- `SpineModelling_ProjectMap.md` - Complete migration tracking
- `TEST_REPORT.md` - Validation results with sample data

**Active Development Branch**: `claude/claude-md-mhxxcvl1yf5xcmpm-01KVRRMcdNsC3pHryV7zMU8W`

## Project Context

This repository contains **SpineModeling**, a biomechanical spine analysis application. The original **C# .NET Framework** application has been **successfully translated to Python** (completed 2025-11-13). The codebase integrates medical image processing (DICOM/EOS X-rays), 3D skeletal reconstruction, OpenSim biomechanical simulation, and VTK-based 3D visualization for spine modeling.

**Migration Status**: ✅ **ALL 6 PHASES COMPLETED** - Python application is functional and tested with real clinical data.

## Repository Structure

```
SpineModelling/
├── SpineModeling_CSharp/              Original C# application (.NET 4.7.2)
│   ├── Program.cs                     Entry point
│   ├── Form1.cs                       Main window (btnmuscular)
│   ├── DicomDecoder.cs                DICOM parsing
│   ├── EosImage.cs                    EOS X-ray image handling
│   ├── EosSpace.cs                    3D coordinate reconstruction
│   ├── EllipseFit.cs                  Ellipse fitting algorithm
│   ├── SkeletalModeling/              2D/3D analysis panels (16 files)
│   ├── ModelVisualization/            OpenSim rendering engine (21 files)
│   └── CSharpOpenSim/                 SWIG-generated OpenSim wrappers (365 files)
│
├── SpineModeling_python/              ✅ Python translation (COMPLETED)
│   ├── main.py                        Application entry point (204 lines)
│   ├── requirements.txt               Python dependencies
│   ├── pyproject.toml                 Project configuration
│   ├── spine_modeling/                Main package (55 Python files, ~4,400 LOC)
│   │   ├── core/                      Position, EllipsePoint dataclasses
│   │   ├── imaging/                   EosImage, EosSpace, DICOM decoder
│   │   ├── algorithms/                EllipseFit (numpy/scipy)
│   │   ├── visualization/             VTK rendering, OpenSim properties
│   │   ├── ui/                        PyQt5 forms, panels, dialogs
│   │   ├── database/                  SQLAlchemy models
│   │   └── utils/                     Utility functions
│   ├── resources/sample_data/         EOS DICOM + CT STL sample data
│   │   ├── EOS/ASD-043/               Frontal/Lateral X-rays (33MB+31MB)
│   │   └── CT/ASD-043/                L2, L3, L4 vertebrae STL meshes
│   ├── tests/                         Unit, integration, e2e tests
│   └── docs/                          API docs, user guide, migration notes
│
├── SpineModelling_ProjectMap.md       Complete migration project tracker
├── TEST_REPORT.md                     Sample data validation results
├── test_sample_data.py                Integration test script
├── SpineModeling_CSharp_ANALYSIS.md   Comprehensive C# technical analysis
├── QUICK_REFERENCE.md                 Fast lookup reference
└── DOCUMENTATION_INDEX.md             Documentation guide
```

## Architecture Overview

**Layered Architecture:**
- **UI Layer**: Windows Forms (C#) → target: PyQt5 (Python)
- **Business Logic**: Image processing, measurements, OpenSim model management
- **Visualization**: VTK-based 3D rendering
- **Data Layer**: DICOM images, OpenSim models (.osim XML), measurement database

**Key Data Flows:**
1. **Image Analysis**: DICOM → DicomDecoder → EosImage → Display → Annotation → EllipseFit → Database
2. **Model Visualization**: .osim file → OpenSim Model → SimModelVisualization → VTK Actors → Render
3. **3D Reconstruction**: EOS Images (dual X-ray) → EosSpace → 3D coordinates → VTK visualization

## Critical Components

### Core Files (C#)
- `SimModelVisualization.cs` (104KB): Main rendering engine for OpenSim models
- `frmImageAnalysis_new.cs` (55KB): Central workflow coordinator
- `UC_3DModelingWorkpanel.cs` (97KB): 3D visualization panel with VTK integration
- `_2DMeasurementsWorkpanel.cs` (45KB): 2D image annotation and measurement

### Key Algorithms
1. **Ellipse Fitting** (`EllipseFit.cs`): Fitzgibbon eigenvalue-based method for anatomical feature detection
2. **3D Reconstruction** (`EosSpace.cs`): Dual X-ray triangulation from calibration parameters
3. **OpenSim Visualization**: VTK assembly hierarchy for biomechanical model rendering

## Technology Stack

### Current (C#)
| Component | Library | Version |
|-----------|---------|---------|
| Framework | .NET Framework | 4.7.2 |
| GUI | Windows Forms | Built-in |
| 3D Graphics | VTK (Activiz.NET) | 5.8.0 |
| Biomechanics | OpenSim (SWIG) | Wrapped |
| DICOM | EvilDICOM | 1.0.6 |
| Image Processing | Emgu.CV (OpenCV) | 3.1.0.1 |
| Matrix Operations | Meta.Numerics | N/A |

### Target (Python)
| Component | Python Package |
|-----------|---------------|
| GUI | PyQt5 |
| 3D Graphics | vtk (same underlying library) |
| Biomechanics | opensim |
| DICOM | pydicom |
| Image Processing | opencv-python |
| Matrix Operations | numpy, scipy |

## Python Implementation Status (2025-11-13)

### ✅ Phase 1: Core Data Models (COMPLETED)
**Files**: 4 Python modules, 1,485 lines
- `Position` → dataclass with 3D vector operations
- `EllipsePoint` + `PointCollection` → 2D point handling
- `EosImage` → EOS X-ray with full pydicom integration
- `EosSpace` → 3D reconstruction with dual-view geometry

### ✅ Phase 2: Image Processing & Algorithms (COMPLETED)
**Files**: 3 Python modules, 2,180 lines
- `DicomDecoder` → Binary DICOM parser (8/16/24-bit support)
- `DicomDictionary` → 777 DICOM tags with utilities
- `EllipseFit` → Fitzgibbon eigenvalue method (numpy/scipy)

### ✅ Phase 3: Visualization Engine (COMPLETED)
**Files**: 17 Python modules covering all property classes
- `SimModelVisualization` → VTK-based OpenSim rendering
- Property classes: Body, Force, Muscle, Joint, Marker, etc.
- VTK assembly hierarchy for model components
- Interactive selection with vtkPropPicker

### ✅ Phase 4: UI Layer (COMPLETED)
**Files**: PyQt5 forms, panels, dialogs
- `MainWindow` → Application shell with menu bar
- `ImageAnalysisForm` → Image loading and display
- `Measurements2DPanel` → 2D measurement tools
- `Modeling3DPanel` → 3D visualization workspace
- Dialog classes for preferences, templates, properties

### ✅ Phase 5: Database Layer (COMPLETED)
**Files**: SQLAlchemy ORM models
- `DatabaseManager` → SQLite database operations
- `Subject`, `Measurement`, `Session` models
- Migration from SQL Server (C#) to SQLite (Python)

### ✅ Phase 6: Integration & Testing (COMPLETED)
**Results**: All tests passed with real clinical data
- Validated with 33MB EOS DICOM files (Patient ASD-043)
- Full image loading and calibration parameter extraction
- 3D reconstruction geometry verified
- Application launches successfully

## Working with This Codebase

### For Python Development (Current Focus)
- **Entry point**: `SpineModeling_python/main.py` → Launches PyQt5 MainWindow
- **Package structure**: `spine_modeling/` contains all modules organized by function
- **Running application**: `cd SpineModeling_python && python main.py`
- **Testing**: `pytest` from SpineModeling_python directory
- **Sample data**: Real EOS DICOM files in `resources/sample_data/` for testing
- **Dependencies**: Install with `pip install -r requirements.txt` (OpenSim via conda)

### For C# Code Analysis (Reference)
- **Entry point**: `Program.cs` → `Form1.cs` (btnmuscular) → `frmImageAnalysis_new.cs`
- **Main workflow**: Click "Skeletal" button → launches image analysis form
- **CSharpOpenSim folder**: Auto-generated SWIG wrappers (365 files) - rarely need modification
- **Large forms**: Some forms are 100-200KB due to extensive UI and VTK interaction code

### Key Python Modules
- **core/**: `position.py`, `ellipse_point.py` - Core dataclasses
- **imaging/**: `eos_image.py`, `eos_space.py`, `dicom_decoder.py` - Medical imaging
- **algorithms/**: `ellipse_fit.py` - Fitzgibbon ellipse fitting
- **visualization/**: OpenSim model rendering with VTK
- **ui/**: PyQt5 forms, panels, and dialogs
- **database/**: SQLAlchemy models for patient data

### Key Design Patterns
- **Property Object Pattern**: OsimBodyProperty, OsimForceProperty encapsulate OpenSim objects with VTK visualization
- **Panel Composition**: Complex UI built from reusable UserControl components
- **State Management**: OpenSim State object tracks model configuration (positions, velocities)

## Important Workflows

### Image Analysis Workflow
1. Load DICOM images (dual EOS X-rays)
2. Extract calibration parameters (source distance, pixel spacing)
3. Display images in dual viewers
4. User annotates anatomy (points, ellipses)
5. Fit ellipses using eigenvalue method
6. Store measurements in database

### 3D Model Visualization Workflow
1. Load .osim model file via OpenSim API
2. Initialize model state: `model.initSystem()`
3. For each body: extract geometry → create VTK actors → apply transforms
4. Render joints (lines), muscles (polylines), markers (spheres)
5. Enable interactive selection with vtkPropPicker
6. Update visualization when model state changes

## Known Issues & TODOs

### From Python Implementation:
- **OpenSim installation**: Not available via pip, requires conda: `conda install -c opensim-org opensim`
- **Non-uniform pixel spacing**: TODO in `eos_image.py` (lines 148, 153) - needs implementation
- **Image orientation**: Currently hardcoded in `eos_space.py` - should be automated
- **STL mesh loading**: CT data files present but loading not yet tested
- **Full UI workflow testing**: Individual components validated, end-to-end testing in progress
- **API documentation**: Need to generate Sphinx/mkdocs from Python docstrings
- **User guide**: Documentation in development

### From C# Codebase (Reference):
- Some forms are very large (185-200KB) - Python version is more modular
- Database layer migrated from SQL Server to SQLite successfully

## Database Layer

### Python Implementation (Current)
**Location**: `SpineModeling_python/spine_modeling/database/`
- **DatabaseManager**: SQLite operations with SQLAlchemy ORM
- **Models**: `Subject`, `Measurement`, `Session` classes
- **Database file**: `~/.spinemodeling/spinemodeling.db` (created on first run)
- **Migration**: Successfully migrated from SQL Server (C#) to SQLite (Python)

### C# Reference (Original)
The C# application used external database components:
- `AppData` singleton for application-wide state
- `DataBase` class for SQL Server operations
- `Measurement`, `Subject` classes for data models

## File Formats

- **.osim**: OpenSim XML model files (biomechanical models)
- **.dcm/.DCM**: DICOM medical images (EOS X-rays)
- **.png**: Standard image format (VTK-supported)

## VTK Integration Notes

The VTK rendering pipeline is consistent between C# and Python:
```
vtkRenderer → vtkRenderWindow → vtkRenderWindowInteractor
vtkActor ← vtkMapper ← vtkPolyData (geometry)
vtkAssembly (for hierarchical transforms)
```

Key VTK classes used:
- `vtkRenderer`: Scene container
- `vtkActor`, `vtkAssembly`: Renderable objects
- `vtkPolyData`, `vtkPolyLine`: Geometry
- `vtkTransform`: Transformations
- `vtkPropPicker`: Interactive selection
- `vtkAxesActor`: Coordinate frames

## OpenSim Integration Notes

Core OpenSim workflow:
```python
# Load model
model = opensim.Model("path/to/model.osim")
state = model.initSystem()

# Access components
bodies = model.getBodySet()
joints = model.getJointSet()
muscles = model.getForceSet()

# Update visualization
model.realizeVelocity(state)
```

The OpenSim Python API closely mirrors the C++ (and C# wrapper) API structure.

## Ellipse Fitting Algorithm

Uses Fitzgibbon et al. eigenvalue-based method:
1. Build design matrices from point cloud
2. Compute scatter matrices
3. Solve generalized eigenvalue problem
4. Extract ellipse coefficients

Python implementation should use numpy/scipy for matrix operations:
- `numpy.linalg.eig` for eigenvalue computation
- Matrix operations for design/scatter matrices
- Return 6-parameter ellipse representation

## Documentation

### Project Documentation
- **CLAUDE.md** (this file): AI assistant guidance and project overview
- **SpineModelling_ProjectMap.md**: Complete migration tracker with phase-by-phase details
- **TEST_REPORT.md**: Sample data validation results and test outcomes
- **QUICK_REFERENCE.md**: Fast lookup for classes, methods, dependencies
- **SpineModeling_CSharp_ANALYSIS.md**: Comprehensive 26KB C# technical specification
- **DOCUMENTATION_INDEX.md**: Guide to documentation structure
- **README_ANALYSIS.txt**: Original analysis notes

### Python-Specific Documentation
- **SpineModeling_python/README.md**: Python project overview and setup
- **SpineModeling_python/docs/migration_notes/**: Phase-by-phase migration reports
- **SpineModeling_python/docs/api/**: API documentation (to be generated)
- **SpineModeling_python/docs/user_guide/**: User guide (in development)

## Development Approach

### For New Features or Bug Fixes (Python)
1. **Understand the context**: Check SpineModelling_ProjectMap.md for current state
2. **Review existing code**: Python implementation in `SpineModeling_python/spine_modeling/`
3. **Check C# reference**: If behavior unclear, consult corresponding C# file
4. **Follow Python idioms**: Use dataclasses, type hints, context managers
5. **Preserve algorithm accuracy**: Especially for medical/biomechanical calculations
6. **Test with sample data**: Use resources/sample_data/ for validation
7. **Update documentation**: Keep ProjectMap and relevant docs current

### Translation Reference (Completed, for Reference Only)
The following approach was used during the C# to Python migration:
1. Read the corresponding C# file to understand functionality
2. Identify external dependencies (VTK, OpenSim, DICOM)
3. Map C# types to Python equivalents (class → class, struct → dataclass)
4. Preserve algorithm logic exactly (especially EllipseFit, coordinate calculations)
5. Use Python idioms (list comprehensions, context managers, properties)
6. Keep VTK API calls nearly identical to C# version
7. Test with sample data (EOS images, .osim models)

## Codebase Statistics

### C# (Original Implementation)
- **Total C# files**: 402
- **Lines of code**: ~130,000 (including SWIG wrappers)
- **Root level files**: 12 main files, 2,904 lines
- **SkeletalModeling**: 16 files
- **ModelVisualization**: 21 files
- **CSharpOpenSim**: 365 auto-generated wrapper files

### Python (Translated Implementation)
- **Total Python files**: 55 modules
- **Lines of code**: ~4,400 (excluding tests)
- **Main entry point**: main.py (204 lines)
- **Core modules**: 4 files (Position, EllipsePoint, EosImage, EosSpace)
- **Imaging/algorithms**: 5 files (DicomDecoder, DicomDictionary, EllipseFit)
- **Visualization**: 17 files (property classes, rendering engine)
- **UI**: 12 files (forms, panels, dialogs)
- **Database**: 3 files (SQLAlchemy models)
- **Tests**: Comprehensive unit and integration tests

## Recent Development Activity

### Latest Commits (as of 2025-11-13)
- **Image loading functionality**: Fixed radiograph loading with proper EosSpace initialization
- **EOS image import**: Implemented menu bar and DICOM import functionality
- **Phase 6 completion**: All migration phases completed and tested
- **Sample data integration**: 33MB+ EOS DICOM files validated with real clinical data

### Active Branches
- `claude/claude-md-mhxxcvl1yf5xcmpm-01KVRRMcdNsC3pHryV7zMU8W`: Current working branch
- `claude/read-project-docs-019sVrrZbrWhXVgG2H8yoyy9`: Previous development branch

### Known Working Features (Validated)
✅ **Core Data Structures**
- Position 3D vector operations
- EllipsePoint 2D point handling with collections
- Centroid and geometric calculations

✅ **Medical Imaging**
- DICOM file loading (8/16/24-bit support)
- EOS X-ray calibration parameter extraction
- Pixel spacing conversions (mm → meters)
- Image metadata parsing (Patient ID, Study Date, Modality)

✅ **3D Reconstruction**
- Dual-view geometry calculations
- X-ray source positioning (frontal/lateral)
- Patient position calculation at isocenter
- Orientation detection (Left-Front, Posterior-Front)

✅ **Application Infrastructure**
- PyQt5 GUI framework initialization
- SQLite database creation and management
- Dependency checking and validation
- High DPI display support

### TODO / Known Limitations
- **OpenSim**: Not installed via pip (requires conda installation)
- **Non-uniform pixel spacing**: Mentioned in EosImage TODOs
- **Image orientation**: Currently hardcoded, needs automation
- **STL loading**: CT data loading not yet tested
- **Full UI workflow**: Individual components work, full integration in progress

## Testing and Validation

### Sample Data Available
**Location**: `SpineModeling_python/resources/sample_data/`

**EOS X-ray Images** (Patient ASD-043):
- Frontal view: `Patient_F.dcm` (32.87 MB, 1896×9087 pixels)
- Lateral view: `Patient_L.dcm` (30.58 MB, 1764×9087 pixels)
- Format: 16-bit DICOM with full calibration metadata
- Status: ✅ Successfully validated with Python implementation

**CT Vertebrae Meshes** (Patient ASD-043):
- L2, L3, L4 vertebrae in STL format (7.8-18.9 MB each)
- Status: ⏳ Loading functionality not yet tested

### Test Script
**File**: `test_sample_data.py` (root directory)
- Tests all Phase 2 core modules with real clinical data
- Validates DICOM loading, calibration extraction, 3D geometry
- Run with: `python test_sample_data.py`

### Automated Tests
**Location**: `SpineModeling_python/tests/`
- Unit tests: `tests/unit/` (core, imaging, visualization)
- Integration tests: `tests/integration/`
- End-to-end tests: `tests/e2e/`
- Run with: `pytest` from SpineModeling_python directory

### Validation Results
See **TEST_REPORT.md** for comprehensive validation results including:
- ✅ All core data structures working correctly
- ✅ DICOM file loading with 8/16/24-bit support
- ✅ Calibration parameter extraction verified
- ✅ 3D reconstruction geometry calculated accurately
- ✅ Application launches without errors
