"""
Muscle actuator line visualization property for OpenSim models.

This module provides a property class that creates VTK line actors to visualize
muscle paths between control points in OpenSim biomechanical models.
"""

from typing import Optional

try:
    import vtk
except ImportError:
    vtk = None


class OsimMuscleActuatorLineProperty:
    """
    Property class for muscle line visualization in VTK.
    
    This class creates and manages a VTK line actor that connects two control
    points, representing a muscle actuator path in an OpenSim model. The line
    is rendered between two OsimControlPointProperty objects.
    
    Attributes:
        muscle_actor (vtkActor): The VTK actor for the muscle line
        cp1 (OsimControlPointProperty): First control point
        cp2 (OsimControlPointProperty): Second control point
        color_r (float): Red color component (0-1)
        color_g (float): Green color component (0-1)
        color_b (float): Blue color component (0-1)
    
    Example:
        >>> line_prop = OsimMuscleActuatorLineProperty()
        >>> line_prop.cp1 = control_point_1
        >>> line_prop.cp2 = control_point_2
        >>> line_prop.make_muscle_line_actor()
        >>> renderer.AddActor(line_prop.muscle_actor)
    """
    
    def __init__(self):
        """Initialize a muscle line property with default red color."""
        if vtk is None:
            raise ImportError(
                "VTK package is required but not installed. "
                "Install with: pip install vtk"
            )
        
        self._muscle_actor = vtk.vtkActor()
        self.cp1: Optional[object] = None  # OsimControlPointProperty
        self.cp2: Optional[object] = None  # OsimControlPointProperty
        self.color_r: float = 1.0
        self.color_g: float = 0.01
        self.color_b: float = 0.0
        self._line_source = vtk.vtkLineSource()
        self._mapper = vtk.vtkPolyDataMapper()
    
    @property
    def muscle_actor(self) -> object:
        """
        Get the VTK actor for the muscle line.
        
        Returns:
            vtkActor: The muscle line actor
        """
        return self._muscle_actor
    
    @muscle_actor.setter
    def muscle_actor(self, value: object):
        """Set the muscle actor."""
        self._muscle_actor = value
    
    def make_muscle_line_actor(self) -> None:
        """
        Create the VTK line actor between two control points.
        
        Constructs a VTK line connecting cp1 and cp2, applies the muscle
        color, and configures the actor's mapper. The line endpoints are
        taken from the control point transforms.
        
        Raises:
            ValueError: If cp1 or cp2 is not set
            
        Example:
            >>> line_prop = OsimMuscleActuatorLineProperty()
            >>> line_prop.cp1 = start_control_point
            >>> line_prop.cp2 = end_control_point
            >>> line_prop.make_muscle_line_actor()
        """
        if self.cp1 is None or self.cp2 is None:
            raise ValueError("Both cp1 and cp2 must be set before creating actor")
        
        # Get position from first control point
        pos1 = self.cp1.control_point_transform.GetPosition()
        
        # Set line source endpoints
        self._line_source.SetPoint1(pos1[0], pos1[1], pos1[2])
        
        # Get position from second control point
        pos2 = self.cp2.control_point_transform.GetPosition()
        self._line_source.SetPoint2(pos2[0], pos2[1], pos2[2])
        
        # Note: Tube filter commented out in original C# code
        # Could be enabled for thicker muscle lines:
        # tube_filter = vtk.vtkTubeFilter()
        # tube_filter.SetInputConnection(self._line_source.GetOutputPort())
        # tube_filter.SetRadius(0.001)
        # tube_filter.SetNumberOfSides(8)
        # self._mapper.SetInputConnection(tube_filter.GetOutputPort())
        
        # Set mapper input (use line directly, not tube)
        self._mapper.SetInputConnection(self._line_source.GetOutputPort())
        
        # Configure actor
        self._muscle_actor.SetMapper(self._mapper)
        self._muscle_actor.GetProperty().SetDiffuseColor(
            self.color_r, self.color_g, self.color_b
        )
    
    def scale_muscle_line_actor(self, value: float) -> None:
        """
        Scale the muscle line actor.
        
        Note: The original C# code indicates this does not work as expected.
        Scaling a line actor may not produce the desired visual effect.
        
        Args:
            value: Scale factor
        """
        # NOTE: Original C# comment: "THIS DOES NOT WORK!"
        # Scaling line actors may not work as expected
        self._muscle_actor.SetScale(value)
    
    def update_muscle_line_actor(self) -> None:
        """
        Update the muscle line actor with current control point positions.
        
        Retrieves the current positions from the control point transforms
        and updates the line endpoints. This should be called when control
        points move to keep the line synchronized.
        
        Example:
            >>> # After moving control points:
            >>> line_prop.update_muscle_line_actor()
            >>> render_window.Render()  # Re-render to see changes
        """
        if self.cp1 is None or self.cp2 is None:
            return
        
        # Get transform from first control point actor
        trans1 = self.cp1.control_point_actor.GetUserTransform()
        if trans1 is not None:
            pos1 = trans1.GetPosition()
            self._line_source.SetPoint1(pos1[0], pos1[1], pos1[2])
        
        # Get transform from second control point actor
        trans2 = self.cp2.control_point_actor.GetUserTransform()
        if trans2 is not None:
            pos2 = trans2.GetPosition()
            self._line_source.SetPoint2(pos2[0], pos2[1], pos2[2])
        
        # Update mapper
        self._mapper.SetInputConnection(self._line_source.GetOutputPort())
        
        # Refresh actor
        self._muscle_actor.SetMapper(self._mapper)
        self._muscle_actor.GetProperty().SetDiffuseColor(
            self.color_r, self.color_g, self.color_b
        )
    
    def __repr__(self) -> str:
        """Return string representation of the muscle line property."""
        return (
            f"OsimMuscleActuatorLineProperty("
            f"cp1={'set' if self.cp1 else 'None'}, "
            f"cp2={'set' if self.cp2 else 'None'}, "
            f"color=({self.color_r:.2f}, {self.color_g:.2f}, {self.color_b:.2f}))"
        )
