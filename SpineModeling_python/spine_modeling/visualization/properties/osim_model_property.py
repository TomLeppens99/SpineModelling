"""
OpenSim Model Property wrapper for property grid display.

This module provides a property class that wraps OpenSim Model objects,
exposing key model properties for display and editing in property grids/panels.
"""

from typing import Optional

try:
    import opensim
except ImportError:
    opensim = None


class OsimModelProperty:
    """
    Property wrapper for OpenSim Model objects.
    
    This class encapsulates model-level properties such as name, credits,
    publications, and unit systems. It provides a structured interface for
    displaying and modifying model metadata in property grids.
    
    Attributes:
        object_name (str): Name of the musculoskeletal model
        object_type (str): Type of the selected node (read-only)
        credits (str): Model credits (read-only)
        publications (str): Related publications
        length_units (str): Length measurement units (read-only)
        force_units (str): Force measurement units (read-only)
    
    Example:
        >>> model = opensim.Model("path/to/model.osim")
        >>> prop = OsimModelProperty()
        >>> prop.read_model_properties(model)
        >>> print(prop.object_name)
        'GaitModel2392'
    """
    
    def __init__(self):
        """Initialize an empty OsimModelProperty instance."""
        self._object_name: str = ""
        self._object_type: str = ""
        self._credits: str = ""
        self._publications: str = ""
        self._length_units: str = ""
        self._force_units: str = ""
        self._model: Optional[object] = None  # opensim.Model
    
    @property
    def object_name(self) -> str:
        """
        Get or set the model name.
        
        When set, updates the underlying OpenSim model's name.
        
        Returns:
            str: The model name
        """
        return self._object_name
    
    @object_name.setter
    def object_name(self, value: str):
        """Set the model name and update the OpenSim model."""
        self._object_name = value
        if self._model is not None and opensim is not None:
            self._model.setName(value)
    
    @property
    def object_type(self) -> str:
        """
        Get the object type (read-only).
        
        Returns:
            str: The type name of the object
        """
        return self._object_type
    
    @object_type.setter
    def object_type(self, value: str):
        """Set the object type (internal use only)."""
        self._object_type = value
    
    @property
    def credits(self) -> str:
        """
        Get the model credits (read-only).
        
        Returns:
            str: Model credits/authors
        """
        return self._credits
    
    @credits.setter
    def credits(self, value: str):
        """Set the credits (internal use only)."""
        self._credits = value
    
    @property
    def publications(self) -> str:
        """
        Get or set related publications.
        
        When set, updates the underlying OpenSim model's publications.
        
        Returns:
            str: Related publications
        """
        return self._publications
    
    @publications.setter
    def publications(self, value: str):
        """Set the publications and update the OpenSim model."""
        self._publications = value
        if self._model is not None and opensim is not None:
            self._model.setPublications(value)
    
    @property
    def length_units(self) -> str:
        """
        Get the length units (read-only).
        
        Returns:
            str: Length measurement units (e.g., 'meters', 'mm')
        """
        return self._length_units
    
    @length_units.setter
    def length_units(self, value: str):
        """Set the length units (internal use only)."""
        self._length_units = value
    
    @property
    def force_units(self) -> str:
        """
        Get the force units (read-only).
        
        Returns:
            str: Force measurement units (e.g., 'N', 'Newtons')
        """
        return self._force_units
    
    @force_units.setter
    def force_units(self, value: str):
        """Set the force units (internal use only)."""
        self._force_units = value
    
    def read_model_properties(self, model: object) -> None:
        """
        Read properties from an OpenSim Model.
        
        Extracts metadata from the OpenSim Model object and populates
        this property instance with the model's name, type, credits,
        publications, and unit systems.
        
        Args:
            model: An opensim.Model instance
            
        Example:
            >>> model = opensim.Model("gait2392.osim")
            >>> prop = OsimModelProperty()
            >>> prop.read_model_properties(model)
            >>> print(f"{prop.object_name} uses {prop.length_units}")
            'Gait2392 uses meters'
        """
        if opensim is None:
            raise ImportError(
                "OpenSim package is required but not installed. "
                "Install with: pip install opensim"
            )
        
        self._model = model
        self._object_name = model.getName()
        self._object_type = str(type(model))
        self._credits = model.getCredits()
        self._publications = model.getPublications()
        self._length_units = model.getLengthUnits().getLabel()
        self._force_units = model.getForceUnits().getLabel()
    
    def __repr__(self) -> str:
        """Return string representation of the property object."""
        return (
            f"OsimModelProperty(name='{self._object_name}', "
            f"type='{self._object_type}', "
            f"units={self._length_units}/{self._force_units})"
        )
