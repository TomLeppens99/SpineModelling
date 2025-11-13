# SpineModeling_CSharp - Quick Reference Guide

## Key Statistics

| Metric | Value |
|--------|-------|
| Total Lines of Code (Root) | 2,904 |
| Total Files | 402 |
| - Main Application Files | 12 |
| - SkeletalModeling Components | 16 |
| - ModelVisualization Components | 21 |
| - CSharpOpenSim Wrappers | 365 |
| Framework | .NET 4.7.2 |
| GUI Framework | Windows Forms |
| Application Type | WinExe (Desktop) |

## Module Breakdown

### 1. Root Level (2,904 lines)
```
Program.cs                    - Main entry point
Form1.cs                      - Main window (btnmuscular)
DicomDecoder.cs      (29KB)  - DICOM file parsing
DicomDictionary.cs   (42KB)  - DICOM tag definitions
EosImage.cs          (11KB)  - EOS image handling
EosSpace.cs          (14KB)  - 3D coordinate reconstruction
EllipseFit.cs                - Ellipse fitting algorithm
Position.cs                  - 3D vector data structure
Ellipse_Point.cs             - 2D point structure
frmManualImportEOSimages.cs  - Import dialog
```

### 2. SkeletalModeling (16 files)
**Main Files:**
- `frmImageAnalysis_new.cs` (55KB) - Main analysis form
- `2DMeasurementsWorkpanel.cs` (45KB) - 2D image panel
- `UC_3DModelingWorkpanel.cs` (97KB) - 3D visualization panel
- `UC_measurementsMain.cs` (42KB) - Measurement management
- `frmCalculateDynamicLandmarks.cs` (185KB) - Advanced landmark tool
- `frmFundamentalModelComponentProp.cs` (184KB) - Property editor

### 3. ModelVisualization (21 files)
**Core Classes:**
- `SimModelVisualization.cs` (104KB) - Main visualization engine
- `OsimBodyProperty.cs` (25KB) - Body representation
- `OsimForceProperty.cs` (28KB) - Muscle/force visualization
- `OsimJointProperty.cs` (20KB) - Joint representation
- `OsimGeometryProperty.cs` (14KB) - Geometry shapes
- `OsimMarkerProperty.cs` - Marker visualization
- `OsimGroupElement.cs` - Hierarchical grouping

**Related Forms:**
- `frmAttachMarkerToModel.cs` (19KB)
- `frmUpdateMuscleAndCP.cs` (11KB)

### 4. CSharpOpenSim (365 auto-generated files)
SWIG wrappers for OpenSim C++ library providing:
- Core classes: Model, Body, Joint, Muscle, State
- Muscle models: Millard2012, Thelen2003, etc.
- Analysis tools: IK, ID, CMC, Forward Dynamics
- Data structures: Arrays, Storage, Probes
- Geometry: Markers, Contact, Decorative shapes

## Core Dependencies

| Library | Version | Purpose |
|---------|---------|---------|
| EvilDICOM | 1.0.6 | DICOM parsing |
| VTK (Activiz) | 5.8.0 | 3D visualization |
| OpenCV (Emgu) | 3.1.0.1 | Image processing |
| OpenSim | (Wrapped) | Biomechanics |
| Meta.Numerics | N/A | Matrix operations |
| ClosedXML | N/A | Excel I/O |
| ITK | N/A | Advanced imaging |

## Application Flow

```
Program.Main()
  └─ Application.Run(new btnmuscular())
       └─ btnmuscular.btnSkeletal_Click()
            └─ frmImageAnalysis_new()
                 ├─ _2DMeasurementsWorkpanel (2D image analysis)
                 ├─ UC_3DModelingWorkpanel (3D visualization)
                 │  └─ SimModelVisualization (OpenSim rendering)
                 └─ Measurement DB interactions
```

## Key Data Flows

### Image Analysis Path
```
DICOM File → DicomDecoder → EosImage (metadata) → 
_2DMeasurementsWorkpanel (display) → 
EllipseFit (measurement) → Measurement DB
```

### Model Visualization Path
```
.osim File → OpenSim Model → SimModelVisualization →
OsimBodyProperty/Joint/Force objects →
VTK Renderer → 3D Display
```

### 3D Coordinate System
```
EOS Images (left/right) → EosSpace.CalculateEosSpace() →
Position objects → VTK coordinate visualization
```

## Important Classes & Methods

### DicomDecoder
- `ReadImage()` - Parse DICOM headers
- Properties: width, height, bitsAllocated, pixelSpacing, etc.

### EosImage
- `ReadImageTagsToProperties()` - Extract calibration data
- Properties: DistanceSourceToIsocenter, ImagerPixelSpacing, etc.

### EosSpace
- `CalculateEosSpace()` - Compute 3D geometry
- Properties: PositionSource1/2, PatientPosition, etc.

### EllipseFit
- `Fit(List<Ellipse_Point> points)` - Eigenvalue ellipse fitting
- Returns: 6x1 ellipse coefficient matrix

### SimModelVisualization
- `InitializeModelInRen(vtkRenderer)` - Setup model in renderer
- `InitializedBodiesInRendererNEW(renderer)` - Render bodies
- `InitializeMarkersinRenderer(renderer)` - Add markers
- `InitializeMusclesInRenderer(renderer)` - Render muscles

### OsimBodyProperty
- Encapsulates: Body object + VTK visualization
- Manages: geometry, color, visibility, transforms

### frmImageAnalysis_new
- Main form coordinating 2D/3D analysis
- Manages: image display, measurement, model visualization

## Configuration

**Framework:** .NET 4.7.2  
**Platform:** AnyCPU (Windows-only)  
**Entry Point:** SpineModeling.Program.Main()  
**Main Window:** SpineModeling.Form1.btnmuscular

## Data Storage

- **DICOM Images:** EOS/, binary files
- **OpenSim Models:** osim/, XML .osim files
- **Geometry Assets:** Geometry files/, geometry definitions
- **Measurements:** Database (SQL Server - external)
- **App State:** AppData singleton (in-memory)

## UI Structure

**Main Window (btnmuscular):**
- Workflow buttons (Image Analysis, Skeletal, etc.)

**frmImageAnalysis_new (Tab Control):**
- Tab 1: 2D Measurements (_2DMeasurementsWorkpanel)
- Tab 2: 3D Modeling (UC_3DModelingWorkpanel)
- Tab 3: Measurements (UC_measurementsMain)

**3D View (UC_3DModelingWorkpanel):**
- Main render window (model)
- Image 1 projection window
- Image 2 projection window
- TreeView for component hierarchy

## Python Migration Equivalents

| C# Class | Python Module |
|----------|---------------|
| Windows Forms | PyQt5 |
| VTK | vtk (same underlying library) |
| OpenSim | opensim Python package |
| EvilDICOM | pydicom |
| Emgu.CV | opencv-python |
| DataGridView | pandas DataFrame + PyQt |
| LINQ | list comprehensions, pandas |

## Key Algorithms

**Ellipse Fitting:**
- Fitzgibbon et al. eigenvalue-based method
- Used for vertebra and anatomical boundary detection

**3D Reconstruction:**
- Dual X-ray triangulation from EOS images
- Coordinate transformation calculations

**OpenSim Visualization:**
- VTK assembly hierarchy for model components
- Transform stack for body kinematics

## Known TODOs in Code

1. EosImage.cs - Non-uniform pixel spacing support
2. EosSpace.cs - Automate image orientation detection
3. General - Extensive error handling improvements
4. UI - Some large form files could be refactored

## Entry Points for Translation

**For Python Migration, start with:**
1. Position, EosImage, EosSpace classes
2. EllipseFit algorithm
3. SimModelVisualization architecture
4. Then port forms to PyQt5
