# SpineModeling Python

Biomechanical spine modeling and analysis application - Python implementation.

## Overview

SpineModeling is a sophisticated application for analyzing medical images (DICOM/EOS X-rays), performing 3D skeletal reconstruction, and biomechanical simulation using OpenSim. This is the Python implementation translated from the original C# application.

## Features

- Medical image processing (DICOM/EOS X-rays)
- 3D skeletal reconstruction from dual X-ray images
- OpenSim biomechanical simulation integration
- VTK-based 3D visualization
- Ellipse fitting algorithms for anatomical feature detection
- Comprehensive measurement and analysis tools

## Requirements

- Python 3.8+
- See `requirements.txt` for Python package dependencies

## Installation

```bash
# Clone the repository
cd SpineModeling_python

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install -r requirements-dev.txt
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run unit tests only
pytest tests/unit/

# Run with coverage report
pytest --cov=spine_modeling --cov-report=html
```

### Code Quality

```bash
# Format code with Black
black spine_modeling/

# Check code style
flake8 spine_modeling/

# Type checking
mypy spine_modeling/
```

## Project Structure

```
spine_modeling/          # Main package
├── core/               # Core data models
├── imaging/            # Image processing
├── visualization/      # 3D rendering
├── algorithms/         # Core algorithms
├── ui/                 # PyQt5 interface
├── database/           # Database layer
└── utils/              # Utilities
```

## Technology Stack

- **GUI**: PyQt5
- **3D Graphics**: VTK
- **Biomechanics**: OpenSim
- **Medical Imaging**: pydicom
- **Image Processing**: OpenCV
- **Numerical Computing**: NumPy, SciPy
- **Database**: SQLite (via SQLAlchemy)

## Documentation

See the `docs/` directory for detailed documentation.

## License

[Specify license]

## Migration Notes

This is a Python translation of the original C# SpineModeling application. See `docs/migration_notes/` for details on the translation process and API differences.
