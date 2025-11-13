# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Context

This repository contains **SpineModeling_CSharp**, a C# biomechanical analysis application that is being **translated to Python**. The codebase integrates medical image processing (DICOM/EOS X-rays), 3D skeletal reconstruction, OpenSim biomechanical simulation, and VTK-based 3D visualization for spine modeling.

## Repository Structure

```
SpineModelling/
├── SpineModeling_CSharp/           Original C# application (.NET 4.7.2)
│   ├── Program.cs                  Entry point
│   ├── Form1.cs                    Main window (btnmuscular)
│   ├── DicomDecoder.cs             DICOM parsing
│   ├── EosImage.cs                 EOS X-ray image handling
│   ├── EosSpace.cs                 3D coordinate reconstruction
│   ├── EllipseFit.cs               Ellipse fitting algorithm
│   ├── SkeletalModeling/           2D/3D analysis panels (16 files)
│   ├── ModelVisualization/         OpenSim rendering engine (21 files)
│   └── CSharpOpenSim/              SWIG-generated OpenSim wrappers (365 files)
│
├── SpineModeling_CSharp_ANALYSIS.md   Comprehensive technical analysis
├── QUICK_REFERENCE.md                 Fast lookup reference
├── DOCUMENTATION_INDEX.md             Documentation guide
└── (Python translation files - to be added)
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

## Translation Strategy

### Phase 1: Core Data Models
Translate foundational data structures:
- `Position.cs` → Python dataclass/NamedTuple
- `EosImage.cs` → Python class with pydicom integration
- `EosSpace.cs` → 3D coordinate calculations
- `Measurement` classes → Python data models

### Phase 2: Image Processing
- `DicomDecoder.cs` → pydicom-based parser
- `EllipseFit.cs` → numpy/scipy implementation
- Image handling → opencv-python + vtk

### Phase 3: Visualization Engine
- `SimModelVisualization.cs` → Python class with vtk
- Property classes (`OsimBodyProperty`, `OsimForceProperty`, etc.) → Python dataclasses
- VTK rendering pipeline → direct vtk Python API

### Phase 4: UI Layer
- Windows Forms → PyQt5 widgets
- `frmImageAnalysis_new` → QMainWindow with tab controls
- UserControl panels → QWidget subclasses

### Phase 5: Integration
- OpenSim model loading and state management
- Database layer implementation
- Testing and optimization

## Working with This Codebase

### For C# Code Analysis
- **Entry point**: `Program.cs` → `Form1.cs` (btnmuscular) → `frmImageAnalysis_new.cs`
- **Main workflow**: Click "Skeletal" button → launches image analysis form
- **CSharpOpenSim folder**: Auto-generated SWIG wrappers (365 files) - rarely need modification
- **Large forms**: Some forms are 100-200KB due to extensive UI and VTK interaction code

### For Python Translation
1. Start with QUICK_REFERENCE.md for technology mapping
2. Use SpineModeling_CSharp_ANALYSIS.md for detailed component specifications
3. Focus on core algorithms first (EllipseFit, EosSpace calculations)
4. VTK API is nearly identical between C# and Python
5. OpenSim Python package has equivalent functionality to C# wrappers

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

From C# codebase:
- `EosImage.cs`: Non-uniform pixel spacing support needed
- `EosSpace.cs`: Image orientation detection should be automated
- Some forms are very large (185-200KB) and could benefit from refactoring
- Database layer classes (AppData, DataBase, Subject) are referenced but not included in source

## Database Layer

The C# application references external database components:
- `AppData` singleton for application-wide state
- `DataBase` class for SQL Server operations
- `Measurement`, `Subject` classes for data models

When translating to Python, consider SQLAlchemy for ORM and database abstraction.

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

Before working on specific components, consult:
- **QUICK_REFERENCE.md**: Fast lookup for classes, methods, dependencies
- **SpineModeling_CSharp_ANALYSIS.md**: Comprehensive 26KB technical specification
- **DOCUMENTATION_INDEX.md**: Guide to documentation structure

## Development Approach

When translating components:
1. Read the corresponding C# file to understand functionality
2. Identify external dependencies (VTK, OpenSim, DICOM)
3. Map C# types to Python equivalents (class → class, struct → dataclass)
4. Preserve algorithm logic exactly (especially EllipseFit, coordinate calculations)
5. Use Python idioms (list comprehensions, context managers, properties)
6. Keep VTK API calls nearly identical to C# version
7. Test with sample data (EOS images, .osim models)

## Codebase Statistics

- **Total C# files**: 402
- **Lines of code**: ~130,000 (including SWIG wrappers)
- **Root level files**: 12 main files, 2,904 lines
- **SkeletalModeling**: 16 files
- **ModelVisualization**: 21 files
- **CSharpOpenSim**: 365 auto-generated wrapper files
