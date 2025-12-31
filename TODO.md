# SpineModeling - Feature Improvement Roadmap

This document outlines 10 high-impact features to improve workflow efficiency and automation in the SpineModeling application. These features are prioritized based on their potential to save time for clinical users and improve the overall user experience.

---

## Completed Features

### Template-Based Ellipse Placement (Implemented 2025-12-31)

**Status:** COMPLETED

Based on clinical insight from Saïd: marker ellipses have standardized sizes, eliminating the need for eigenvalue-based fitting.

**Implementation:** `spine_modeling/algorithms/ellipse_template.py`

**Features:**
- **Fixed-size templates:**
  - Cluster markers (M, R, L): 3mm diameter
  - Single markers: 5mm diameter
  - Custom sizes supported

- **Click-to-place workflow:**
  - User clicks center point → ellipse appears instantly
  - No fitting computation required
  - Can manually adjust if needed

- **Automatic circular marker detection:**
  - Uses OpenCV Hough Circle Transform
  - Blob detection as complementary method
  - Configurable sensitivity and size range

**Usage:**
```python
from spine_modeling.algorithms import EllipseTemplate, EllipsePlacementManager

# Quick placement
template = EllipseTemplate.for_cluster_marker()  # 3mm
ellipse = template.place_at(x=100, y=200, pixel_spacing=0.000179)

# Or use the manager for full workflow
manager = EllipsePlacementManager(eos_image)
ellipse = manager.place_cluster_marker(x=100, y=200)

# Auto-detect all markers
detected = manager.auto_detect_markers()
```

**Impact:** Reduces ellipse placement from ~30 manual points to 1 click per marker.

---

## Planned Features

## 1. Automatic Vertebra Detection and Segmentation

**Priority:** HIGH
**Estimated Impact:** Save 80% of manual annotation time

### Description
Implement computer vision-based automatic detection and segmentation of vertebrae in EOS X-ray images using machine learning.

### Implementation Approach
- Use a pre-trained U-Net or Mask R-CNN model for vertebra segmentation
- Integrate with OpenCV for image preprocessing (contrast enhancement, edge detection)
- Provide confidence scores for each detected vertebra
- Allow user confirmation/correction of automated detections

### Technical Requirements
```python
# New module: spine_modeling/algorithms/vertebra_detector.py
class VertebraDetector:
    def detect(self, eos_image: EosImage) -> List[VertebraRegion]
    def segment(self, eos_image: EosImage) -> np.ndarray  # Segmentation mask
    def get_landmarks(self, region: VertebraRegion) -> List[EllipsePoint]
```

### User Workflow Impact
- **Before:** User manually annotates 30+ points per vertebra
- **After:** User clicks to confirm/adjust 3-5 key points per vertebra

---

## 2. Batch Processing Pipeline

**Priority:** HIGH
**Estimated Impact:** Process 10+ patients per session

### Description
Enable processing of multiple patients in a single session with queued operations and background processing.

### Implementation Approach
- Create a processing queue with priority levels
- Implement threaded/async processing for I/O-bound operations
- Add progress tracking with estimated time remaining
- Support pause/resume functionality

### Technical Requirements
```python
# New module: spine_modeling/utils/batch_processor.py
class BatchProcessor:
    def add_to_queue(self, subject_code: str, operations: List[Operation])
    def process_all(self, progress_callback: Callable)
    def get_status(self) -> BatchStatus
    def export_results(self, format: str) -> Path
```

### Features
- [ ] Queue management UI panel
- [ ] Background DICOM loading
- [ ] Parallel ellipse fitting
- [ ] Batch export to Excel/CSV

---

## 3. Template-Based Measurement Presets

**Priority:** MEDIUM
**Estimated Impact:** Reduce setup time by 60%

### Description
Create and save measurement templates for common clinical protocols (scoliosis assessment, lordosis measurement, etc.).

### Implementation Approach
- Define JSON schema for measurement templates
- Include standard measurement definitions per vertebral level
- Support template sharing between users
- Auto-populate measurement names and expected ranges

### Template Structure
```json
{
  "name": "Scoliosis Protocol - AIS",
  "version": "1.0",
  "measurements": [
    {
      "name": "Cobb Angle T5-T12",
      "type": "angle",
      "vertebrae": ["T5", "T12"],
      "normal_range": [0, 10],
      "units": "degrees"
    },
    {
      "name": "Pedicle Width L3",
      "type": "ellipse",
      "vertebra": "L3",
      "normal_range": [7.5, 12.0],
      "units": "mm"
    }
  ]
}
```

### Features
- [ ] Template editor UI
- [ ] Import/export templates
- [ ] Clinical protocol library
- [ ] Automatic range validation with warnings

---

## 4. Real-Time 3D Reconstruction Preview

**Priority:** MEDIUM
**Estimated Impact:** Improve accuracy, reduce iterations

### Description
Show live 3D reconstruction as the user annotates points on 2D images, providing immediate feedback on annotation quality.

### Implementation Approach
- Stream annotation updates to EosSpace for 3D calculation
- Use lightweight VTK rendering for preview
- Highlight discrepancies between frontal/lateral views
- Show confidence indicators for reconstruction quality

### Technical Requirements
```python
# Enhancement to existing EosSpace class
class EosSpace:
    def compute_3d_position_live(self, frontal_point, lateral_point) -> Position3D
    def get_reconstruction_quality(self) -> float  # 0-1 confidence score
    def suggest_corrections(self) -> List[CorrectionSuggestion]
```

### Features
- [ ] Split-screen preview (2D + 3D)
- [ ] Real-time quality metrics
- [ ] Suggested point adjustments
- [ ] Export 3D model preview

---

## 5. Automated Report Generation

**Priority:** HIGH
**Estimated Impact:** Save 30 min per patient

### Description
Generate comprehensive PDF reports with measurements, visualizations, and clinical interpretations.

### Implementation Approach
- Use ReportLab or WeasyPrint for PDF generation
- Include measurement tables, annotated images, and 3D screenshots
- Support customizable report templates
- Add DICOM-compliant headers and footers

### Report Sections
1. Patient Information
2. Study Details (Date, Protocol, Operator)
3. Measurement Summary Table
4. Annotated 2D Images (Frontal + Lateral)
5. 3D Reconstruction Views
6. Clinical Interpretation (optional)
7. Comparison with Previous Studies

### Features
- [ ] PDF report generator
- [ ] Custom logo/header support
- [ ] Multi-language support
- [ ] Trend analysis across visits

---

## 6. Measurement History and Trend Analysis

**Priority:** MEDIUM
**Estimated Impact:** Enable longitudinal tracking

### Description
Track measurements over time and visualize trends for monitoring patient progression.

### Implementation Approach
- Extend database schema for temporal queries
- Implement statistical analysis for trend detection
- Generate time-series visualizations
- Alert on significant changes

### Technical Requirements
```python
# New module: spine_modeling/analysis/trend_analyzer.py
class TrendAnalyzer:
    def get_measurement_history(self, subject_id: int, measurement_name: str) -> TimeSeries
    def calculate_trend(self, history: TimeSeries) -> TrendResult
    def detect_significant_change(self, history: TimeSeries) -> bool
    def generate_chart(self, history: TimeSeries) -> matplotlib.Figure
```

### Features
- [ ] Timeline visualization UI
- [ ] Comparison between visits
- [ ] Statistical significance testing
- [ ] Export trend charts

---

## 7. Multi-User Collaboration and Review Workflow

**Priority:** LOW
**Estimated Impact:** Improve quality assurance

### Description
Enable multiple users to collaborate on measurements with review and approval workflows.

### Implementation Approach
- Add user authentication and roles
- Implement measurement status (draft, review, approved)
- Track revision history with user attribution
- Support annotations and comments

### User Roles
- **Technician:** Create measurements
- **Reviewer:** Approve/reject measurements
- **Administrator:** Manage users and templates

### Features
- [ ] User management panel
- [ ] Review queue
- [ ] Audit trail
- [ ] Comment system on measurements

---

## 8. DICOM Integration and PACS Connectivity

**Priority:** HIGH
**Estimated Impact:** Eliminate manual file transfers

### Description
Connect directly to hospital PACS systems to retrieve and store DICOM images automatically.

### Implementation Approach
- Implement DICOM C-FIND, C-GET, C-STORE operations
- Use pynetdicom for PACS communication
- Support worklist integration
- Automatic study matching

### Technical Requirements
```python
# New module: spine_modeling/imaging/pacs_client.py
class PACSClient:
    def connect(self, ae_title: str, host: str, port: int)
    def search_studies(self, patient_id: str) -> List[StudyInfo]
    def retrieve_study(self, study_uid: str) -> List[EosImage]
    def store_results(self, study_uid: str, measurements: List[Measurement])
```

### Features
- [ ] PACS configuration panel
- [ ] Study browser
- [ ] Automatic image download
- [ ] Structured report (SR) export

---

## 9. AI-Assisted Measurement Validation

**Priority:** MEDIUM
**Estimated Impact:** Reduce errors by 50%

### Description
Use machine learning to validate measurements and flag potential errors or outliers.

### Implementation Approach
- Train model on historical measurement data
- Learn normal ranges per vertebral level
- Detect anatomically implausible values
- Suggest corrections based on patterns

### Validation Checks
1. **Range Validation:** Measurement within normal bounds
2. **Symmetry Check:** Left/right measurements balanced
3. **Consistency Check:** Measurements follow expected patterns
4. **Anatomical Plausibility:** Values make anatomical sense

### Features
- [ ] Real-time validation indicators
- [ ] Warning system for outliers
- [ ] Suggested corrections
- [ ] Learning from user corrections

---

## 10. OpenSim Model Parameter Fitting

**Priority:** LOW
**Estimated Impact:** Enable biomechanical simulations

### Description
Automatically fit OpenSim model parameters to patient-specific measurements for personalized biomechanical analysis.

### Implementation Approach
- Scale generic models based on measured dimensions
- Adjust joint parameters from range of motion data
- Optimize muscle attachment points
- Validate model against patient data

### Technical Requirements
```python
# New module: spine_modeling/modeling/model_fitter.py
class OpenSimModelFitter:
    def load_generic_model(self, model_path: str) -> opensim.Model
    def scale_to_patient(self, measurements: Dict[str, float]) -> opensim.Model
    def optimize_parameters(self, target_values: Dict) -> opensim.Model
    def validate_model(self) -> ValidationResult
```

### Features
- [ ] Model scaling wizard
- [ ] Parameter optimization panel
- [ ] Validation report
- [ ] Export patient-specific model

---

## Implementation Priority Matrix

| Feature | Priority | Complexity | Dependencies |
|---------|----------|------------|--------------|
| 1. Auto Vertebra Detection | HIGH | HIGH | ML models, training data |
| 2. Batch Processing | HIGH | MEDIUM | Async/threading |
| 3. Measurement Templates | MEDIUM | LOW | JSON schema |
| 4. Real-Time 3D Preview | MEDIUM | MEDIUM | VTK optimization |
| 5. Report Generation | HIGH | MEDIUM | PDF library |
| 6. Trend Analysis | MEDIUM | MEDIUM | Database queries |
| 7. Multi-User Workflow | LOW | HIGH | Authentication |
| 8. PACS Integration | HIGH | HIGH | pynetdicom, DICOM |
| 9. AI Validation | MEDIUM | HIGH | ML models |
| 10. OpenSim Fitting | LOW | HIGH | OpenSim API |

## Quick Wins (Can be implemented in 1-2 days)

1. **Keyboard Shortcuts:** Add keyboard shortcuts for common operations
2. **Recent Files:** Remember and quick-access recently opened files
3. **Auto-Save:** Automatically save work every 5 minutes
4. **Dark Mode:** Add dark theme for reduced eye strain
5. **Measurement Presets:** Quick buttons for common measurement types

---

## Contributing

To contribute to any of these features:

1. Create a feature branch: `git checkout -b feature/feature-name`
2. Implement with tests
3. Update documentation
4. Submit pull request

## Changelog

- **2025-12-31:** Initial TODO.md created with 10 feature proposals
