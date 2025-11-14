"""
Database models for SpineModeling application.

This module defines the SQLAlchemy ORM models for storing patient measurements
and subject information in the SpineModeling database.
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    DateTime,
    ForeignKey,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, Session

Base = declarative_base()


class Subject(Base):
    """
    Represents a patient/subject in the database.

    Attributes:
        subject_id: Primary key, auto-incrementing subject identifier
        subject_code: Unique subject code (e.g., "ASD-043")
        name: Subject's full name
        date_of_birth: Subject's date of birth
        gender: Subject's gender (M/F/Other)
        height: Subject's height in cm
        weight: Subject's weight in kg
        created_date: Timestamp when record was created
        notes: Additional notes about the subject
        data_folder: Path to the patient's data folder
    """
    __tablename__ = "subjects"

    subject_id = Column(Integer, primary_key=True, autoincrement=True)
    subject_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=True)
    date_of_birth = Column(DateTime, nullable=True)
    gender = Column(String(10), nullable=True)
    height = Column(Float, nullable=True)  # cm
    weight = Column(Float, nullable=True)  # kg
    created_date = Column(DateTime, default=datetime.now, nullable=False)
    notes = Column(Text, nullable=True)
    data_folder = Column(String(500), nullable=True)  # Path to patient data folder

    # Relationship to measurements and images
    measurements = relationship("Measurement", back_populates="subject", cascade="all, delete-orphan")
    images = relationship("PatientImage", back_populates="subject", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Subject(id={self.subject_id}, code='{self.subject_code}', name='{self.name}')>"


class PatientImage(Base):
    """
    Represents an image file (EOS or CT) associated with a patient.

    Attributes:
        image_id: Primary key, auto-incrementing image identifier
        subject_id: Foreign key to subject
        image_type: Type of image (EOS_Frontal, EOS_Lateral, CT)
        vertebra_level: Vertebra level for CT images (e.g., "L2", "T12", "Sacrum")
        file_path: Relative path to the image file
        file_name: Original filename
        upload_date: When the image was uploaded
        file_size: File size in bytes
        notes: Additional notes about the image
    """
    __tablename__ = "patient_images"

    image_id = Column(Integer, primary_key=True, autoincrement=True)
    subject_id = Column(Integer, ForeignKey("subjects.subject_id"), nullable=False, index=True)
    image_type = Column(String(50), nullable=False)  # EOS_Frontal, EOS_Lateral, CT
    vertebra_level = Column(String(20), nullable=True)  # L2, T12, Sacrum, etc. (for CT images)
    file_path = Column(String(500), nullable=False)  # Relative path to image file
    file_name = Column(String(255), nullable=False)  # Original filename
    upload_date = Column(DateTime, default=datetime.now, nullable=False)
    file_size = Column(Integer, nullable=True)  # bytes
    notes = Column(Text, nullable=True)

    # Relationship to subject
    subject = relationship("Subject", back_populates="images")

    def __repr__(self):
        return (
            f"<PatientImage(id={self.image_id}, "
            f"subject_id={self.subject_id}, "
            f"type='{self.image_type}', "
            f"vertebra='{self.vertebra_level}')>"
        )


class Measurement(Base):
    """
    Represents a measurement record in the database.

    Attributes:
        measurement_id: Primary key, auto-incrementing measurement identifier
        subject_id: Foreign key to subject
        measurement_name: Name/type of measurement (e.g., "Pedicle Width L2")
        measurement_value: Numeric measurement value
        measurement_unit: Unit of measurement (e.g., "mm", "degrees")
        measurement_type: Type/category (e.g., "2D", "3D", "Ellipse")
        image_type: Image modality (e.g., "EOS_Frontal", "EOS_Lateral", "CT")
        measurement_date: When measurement was taken
        user: User who performed the measurement
        comment: Additional comments about the measurement
        x_coord: X coordinate (for point-based measurements)
        y_coord: Y coordinate (for point-based measurements)
        z_coord: Z coordinate (for 3D measurements)
        ellipse_center_x: Ellipse center X coordinate
        ellipse_center_y: Ellipse center Y coordinate
        ellipse_major_axis: Ellipse major axis length
        ellipse_minor_axis: Ellipse minor axis length
        ellipse_angle: Ellipse rotation angle (degrees)
        created_date: Timestamp when record was created
    """
    __tablename__ = "measurements"

    measurement_id = Column(Integer, primary_key=True, autoincrement=True)
    subject_id = Column(Integer, ForeignKey("subjects.subject_id"), nullable=False, index=True)
    measurement_name = Column(String(200), nullable=False)
    measurement_value = Column(Float, nullable=True)
    measurement_unit = Column(String(50), nullable=True)
    measurement_type = Column(String(50), nullable=True)  # 2D, 3D, Ellipse, etc.
    image_type = Column(String(50), nullable=True)  # EOS_Frontal, EOS_Lateral, CT
    measurement_date = Column(DateTime, default=datetime.now, nullable=False)
    user = Column(String(100), nullable=True)
    comment = Column(Text, nullable=True)

    # Coordinate data
    x_coord = Column(Float, nullable=True)
    y_coord = Column(Float, nullable=True)
    z_coord = Column(Float, nullable=True)

    # Ellipse-specific data
    ellipse_center_x = Column(Float, nullable=True)
    ellipse_center_y = Column(Float, nullable=True)
    ellipse_major_axis = Column(Float, nullable=True)
    ellipse_minor_axis = Column(Float, nullable=True)
    ellipse_angle = Column(Float, nullable=True)  # degrees

    created_date = Column(DateTime, default=datetime.now, nullable=False)

    # Relationship to subject
    subject = relationship("Subject", back_populates="measurements")

    def __repr__(self):
        return (
            f"<Measurement(id={self.measurement_id}, "
            f"subject_id={self.subject_id}, "
            f"name='{self.measurement_name}', "
            f"value={self.measurement_value})>"
        )


class DatabaseManager:
    """
    Manages database connections and operations.

    This class provides a high-level interface for database operations including
    initialization, CRUD operations, and session management.
    """

    def __init__(self, database_url: str = "sqlite:///spinemodeling.db"):
        """
        Initialize database manager.

        Args:
            database_url: SQLAlchemy database URL (default: SQLite file)
        """
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
        self._session: Optional[Session] = None

    def initialize_database(self):
        """Create all tables in the database."""
        Base.metadata.create_all(bind=self.engine)

    def get_session(self) -> Session:
        """
        Get or create a database session.

        Returns:
            SQLAlchemy session object
        """
        if self._session is None:
            self._session = self.SessionLocal()
        return self._session

    def close_session(self):
        """Close the current database session."""
        if self._session is not None:
            self._session.close()
            self._session = None

    # Subject operations
    def create_subject(self, subject_code: str, name: str = None, **kwargs) -> Subject:
        """
        Create a new subject record.

        Args:
            subject_code: Unique subject code
            name: Subject's name
            **kwargs: Additional subject attributes

        Returns:
            Created Subject object
        """
        session = self.get_session()
        subject = Subject(subject_code=subject_code, name=name, **kwargs)
        session.add(subject)
        session.commit()
        session.refresh(subject)
        return subject

    def get_subject_by_code(self, subject_code: str) -> Optional[Subject]:
        """
        Get subject by code.

        Args:
            subject_code: Subject code to search for

        Returns:
            Subject object if found, None otherwise
        """
        session = self.get_session()
        return session.query(Subject).filter(Subject.subject_code == subject_code).first()

    def get_all_subjects(self):
        """Get all subjects."""
        session = self.get_session()
        return session.query(Subject).all()

    def update_subject(self, subject_id: int, **kwargs) -> Optional[Subject]:
        """
        Update subject record.

        Args:
            subject_id: Subject ID to update
            **kwargs: Attributes to update

        Returns:
            Updated Subject object if found, None otherwise
        """
        session = self.get_session()
        subject = session.query(Subject).filter(Subject.subject_id == subject_id).first()
        if subject:
            for key, value in kwargs.items():
                if hasattr(subject, key):
                    setattr(subject, key, value)
            session.commit()
            session.refresh(subject)
        return subject

    def delete_subject(self, subject_id: int) -> bool:
        """
        Delete subject and all associated measurements.

        Args:
            subject_id: Subject ID to delete

        Returns:
            True if deleted, False if not found
        """
        session = self.get_session()
        subject = session.query(Subject).filter(Subject.subject_id == subject_id).first()
        if subject:
            session.delete(subject)
            session.commit()
            return True
        return False

    # Measurement operations
    def create_measurement(
        self,
        subject_id: int,
        measurement_name: str,
        measurement_value: float = None,
        **kwargs
    ) -> Measurement:
        """
        Create a new measurement record.

        Args:
            subject_id: Foreign key to subject
            measurement_name: Name of the measurement
            measurement_value: Measurement value
            **kwargs: Additional measurement attributes

        Returns:
            Created Measurement object
        """
        session = self.get_session()
        measurement = Measurement(
            subject_id=subject_id,
            measurement_name=measurement_name,
            measurement_value=measurement_value,
            **kwargs
        )
        session.add(measurement)
        session.commit()
        session.refresh(measurement)
        return measurement

    def get_measurements_by_subject(self, subject_id: int):
        """
        Get all measurements for a subject.

        Args:
            subject_id: Subject ID

        Returns:
            List of Measurement objects
        """
        session = self.get_session()
        return session.query(Measurement).filter(Measurement.subject_id == subject_id).all()

    def get_all_measurements(self):
        """Get all measurements."""
        session = self.get_session()
        return session.query(Measurement).all()

    def update_measurement(self, measurement_id: int, **kwargs) -> Optional[Measurement]:
        """
        Update measurement record.

        Args:
            measurement_id: Measurement ID to update
            **kwargs: Attributes to update

        Returns:
            Updated Measurement object if found, None otherwise
        """
        session = self.get_session()
        measurement = session.query(Measurement).filter(
            Measurement.measurement_id == measurement_id
        ).first()
        if measurement:
            for key, value in kwargs.items():
                if hasattr(measurement, key):
                    setattr(measurement, key, value)
            session.commit()
            session.refresh(measurement)
        return measurement

    def delete_measurement(self, measurement_id: int) -> bool:
        """
        Delete measurement record.

        Args:
            measurement_id: Measurement ID to delete

        Returns:
            True if deleted, False if not found
        """
        session = self.get_session()
        measurement = session.query(Measurement).filter(
            Measurement.measurement_id == measurement_id
        ).first()
        if measurement:
            session.delete(measurement)
            session.commit()
            return True
        return False

    # PatientImage operations
    def create_patient_image(
        self,
        subject_id: int,
        image_type: str,
        file_path: str,
        file_name: str,
        vertebra_level: str = None,
        **kwargs
    ) -> PatientImage:
        """
        Create a new patient image record.

        Args:
            subject_id: Foreign key to subject
            image_type: Type of image (EOS_Frontal, EOS_Lateral, CT)
            file_path: Relative path to the image file
            file_name: Original filename
            vertebra_level: Vertebra level for CT images (optional)
            **kwargs: Additional image attributes

        Returns:
            Created PatientImage object
        """
        session = self.get_session()
        image = PatientImage(
            subject_id=subject_id,
            image_type=image_type,
            file_path=file_path,
            file_name=file_name,
            vertebra_level=vertebra_level,
            **kwargs
        )
        session.add(image)
        session.commit()
        session.refresh(image)
        return image

    def get_images_by_subject(self, subject_id: int):
        """
        Get all images for a subject.

        Args:
            subject_id: Subject ID

        Returns:
            List of PatientImage objects
        """
        session = self.get_session()
        return session.query(PatientImage).filter(PatientImage.subject_id == subject_id).all()

    def get_images_by_type(self, subject_id: int, image_type: str):
        """
        Get images of a specific type for a subject.

        Args:
            subject_id: Subject ID
            image_type: Image type (EOS_Frontal, EOS_Lateral, CT)

        Returns:
            List of PatientImage objects
        """
        session = self.get_session()
        return session.query(PatientImage).filter(
            PatientImage.subject_id == subject_id,
            PatientImage.image_type == image_type
        ).all()

    def get_images_by_vertebra(self, subject_id: int, vertebra_level: str):
        """
        Get CT images for a specific vertebra level.

        Args:
            subject_id: Subject ID
            vertebra_level: Vertebra level (e.g., "L2", "T12")

        Returns:
            List of PatientImage objects
        """
        session = self.get_session()
        return session.query(PatientImage).filter(
            PatientImage.subject_id == subject_id,
            PatientImage.vertebra_level == vertebra_level
        ).all()

    def delete_patient_image(self, image_id: int) -> bool:
        """
        Delete patient image record.

        Args:
            image_id: Image ID to delete

        Returns:
            True if deleted, False if not found
        """
        session = self.get_session()
        image = session.query(PatientImage).filter(PatientImage.image_id == image_id).first()
        if image:
            session.delete(image)
            session.commit()
            return True
        return False

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close_session()


# Example usage
if __name__ == "__main__":
    # Create database and test operations
    db = DatabaseManager("sqlite:///test_spinemodeling.db")
    db.initialize_database()

    # Create a test subject
    subject = db.create_subject(
        subject_code="ASD-043",
        name="Test Patient",
        gender="F",
        height=165.0,
        weight=58.0
    )
    print(f"Created: {subject}")

    # Create a test measurement
    measurement = db.create_measurement(
        subject_id=subject.subject_id,
        measurement_name="Pedicle Width L2",
        measurement_value=8.5,
        measurement_unit="mm",
        measurement_type="Ellipse",
        image_type="EOS_Frontal",
        user="TestUser"
    )
    print(f"Created: {measurement}")

    # Retrieve measurements
    measurements = db.get_measurements_by_subject(subject.subject_id)
    print(f"Measurements for subject {subject.subject_code}: {len(measurements)}")

    db.close_session()
