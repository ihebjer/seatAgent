import os
import logging
from typing import Dict, Any
from fastapi import FastAPI
from fastmcp import FastMCP
import uvicorn
import yaml
from tools_definition import (
    get_seat_adjustment_tool,
    get_thermal_tool,
    get_ventilation_tool,
    get_pelvis_drift_tool
)
class MotorControlServer:
    """MCP Server for motor control with thermal and ventilation features."""
    
    # Constants
    MOTOR_MIN = 0
    MOTOR_MAX = 100
    MOTOR_STEP = 10
    
    def __init__(self):
        """Initialize the server with FastAPI and FastMCP."""
        self.app = FastAPI(title="Motor MCP Server")
        self.mcp = FastMCP(self.app)
        self._setup_logging()
        self._register_endpoints()
        
    def _setup_logging(self):
        """Configure logging settings."""
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger(__name__)
    
    def _register_endpoints(self):
        """Register all API endpoints."""
        # Main seat adjustment endpoint
        self.mcp.tool()(self.seat_adjustment)
        
        # Individual control endpoints (maintained for backward compatibility)
        # self.mcp.tool()(self.adjust_thermal)
        # self.mcp.tool()(self.adjust_ventilation)
        self.mcp.tool()(self.adjustSeat_onPelvisdrift_city)

        # Motor Controls
        motors = [
            ('track', ['forward', 'backward']),
            ('height', ['up', 'down']),
            ('backrest', ['forward', 'backward']),
            ('seattilt', ['up', 'down']),
            ('uba', ['forward', 'backward']),
            ('headrest', ['forward', 'backward'])
        ]
        
        for motor, directions in motors:
            for direction in directions:
                method_name = f"move_{motor}_{direction}"
                setattr(self, method_name, self._create_motor_method(motor, direction))
                self.mcp.tool()(getattr(self, method_name))
        
        # Tool discovery
        self.app.get("/mcp/tools")(self.get_available_tools)
    
    def _clamp(self, value: int, min_val: int = MOTOR_MIN, max_val: int = MOTOR_MAX) -> int:
        """Clamp value between min and max bounds."""
        return max(min_val, min(value, max_val))
    
    def _create_motor_method(self, motor: str, direction: str):
        """Dynamically create motor control methods that enforce relative movements."""
        def motor_method(
            current_value: int,
            percentage: int = None,  # How much to move (relative)
            move_fully: bool = False  # Special flag for full movement
        ) -> Dict[str, Any]:
            # Calculate movement percentage
            if move_fully:
                if direction in ['backward', 'down']:
                    percentage = current_value  # Move all the way to min (0)
                else:
                    percentage = 100 - current_value  # Move all the way to max (100)
            elif percentage is None:
                percentage = self.MOTOR_STEP  # Default step
                
            percentage = self._clamp(percentage, 0, 100)
            
            # Calculate new value for logging
            if direction in ['backward', 'down']:
                new_value = current_value - percentage
            else:
                new_value = current_value + percentage
            new_value = self._clamp(new_value)
            
            self.logger.info(
                f"🔄 Moving {motor} {direction} by {percentage}% "
                f"(from {current_value}% to {new_value}%)"
            )
            
            return {
                "seatCommand": {
                    "motors": {
                        motor.capitalize(): {
                            "percentage": percentage,
                            "type": "relative",
                            "direction": direction
                        }
                    }
                },
                "status": "success",
                "metadata": {
                    "motor": motor,
                    "from_position": current_value,
                    "movement": percentage,
                    "direction": direction,
                    "to_position": new_value
                }
            }
        
        # Update docstring
        motor_method.__doc__ = f"""
        Move the {motor} {direction} (relative movement)
        
        Args:
            current_value: Current position (0-100)
            percentage: How much to move (0-100), None for default step
            move_fully: If True, move fully in direction (to min/max)
        """
        return motor_method
    
    def _read_metadata(self):
        """Read the current metadata values."""
        try:
            metadata_path = "metadata.yaml"
            with open(metadata_path, 'r') as file:
                metadata = yaml.safe_load(file)
            return metadata
        except Exception as e:
            self.logger.error(f"Error reading metadata: {str(e)}")
            return None

    def seat_adjustment(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Full seat adjustment command that accepts the complete seat command JSON structure.
        Only processes the fields that are provided in the command.
        """
        self.logger.info(f"Received seat command: {command}")
        
        # Here you would normally process the command and send it to the seat hardware
        # For now, we'll just return the received command as confirmation
        
        return {
            "status": "success",
            "command": command,
            "message": "Seat command processed successfully"
        }

    def adjustSeat_onPelvisdrift_city(self) -> Dict[str, Any]:
        """
        Automatic adjustment for pelvis drift posture in city driving mode.
        Increases seat tilt by 10 and seatbelt tightness by 10 from current metadata values.
        Returns the newly calculated values in seat command format.
        """
        try:
            metadata = self._read_metadata()
            if not metadata:
                return {
                    "status": "error",
                    "message": "Could not read current metadata"
                }
            
            # Get current values from metadata
            current_seattilt = metadata.get('motors', {}).get('SeatTilt', 0)
            current_seatbelt = metadata.get('seatbelt_tightness', 0)
            
            # Calculate new values (clamped to valid ranges)
            new_seattilt = self._clamp(current_seattilt + 10)
            new_seatbelt = self._clamp(current_seatbelt + 10)
            
            self.logger.info(
                f"🔄 Auto-adjusting for pelvis drift (city mode): "
                f"SeatTilt {current_seattilt}→{new_seattilt}, "
                f"Seatbelt {current_seatbelt}→{new_seatbelt}"
            )
            
            return {
                "seatCommand": {
                    "motors": {
                        "Tilt": {
                            "percentage": new_seattilt,
                            "type": "relative",
                            "direction": "up" if new_seattilt > current_seattilt else "down"
                        }
                    },
                    "seatbelt": {
                        "percentage": new_seatbelt
                    }
                },
                "status": "success",
                "message": (
                    f"Auto-adjusted for pelvis drift: "
                    f"SeatTilt set to {new_seattilt}, "
                    f"Seatbelt tightness set to {new_seatbelt}"
                )
            }
        except Exception as e:
            self.logger.error(f"Error in adjustSeat_onPelvisdrift_city: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "message": "Failed to auto-adjust for pelvis drift"
            }

    # def adjust_thermal(self, heatingLevel: int = None) -> Dict[str, Any]:
    #     """
    #     Adjust the thermal/heating level in the vehicle based on cabin temperature.
    #     If heatingLevel is provided, it will be used directly (clamped to 0-5).
    #     If not provided, it will be calculated based on cabin temperature.
    #     """
    #     metadata = self._read_metadata()
    #     if not metadata:
    #         return {
    #             "status": "error",
    #             "message": "Could not read current metadata"
    #         }
        
    #     cabin_temp = metadata.get('cabin_temperature', 20)  # Default to 20 if not available
        
    #     if heatingLevel is None:
    #         # Auto-calculate heating level based on temperature
    #         if cabin_temp >= 20:
    #             heatingLevel = 0  # No heating needed
    #         elif 17 <= cabin_temp <= 19:
    #             heatingLevel = 1
    #         elif 14 <= cabin_temp <= 16:
    #             heatingLevel = 2
    #         elif 11 <= cabin_temp <= 13:
    #             heatingLevel = 3
    #         elif 8 <= cabin_temp <= 10:
    #             heatingLevel = 4
    #         else:  # Below 8
    #             heatingLevel = 5
        
    #     heatingLevel = self._clamp(heatingLevel, 0, 5)
    #     self.logger.info(f"🔥 Adjusting heating level to {heatingLevel} (Cabin temp: {cabin_temp}°C)")
        
    #     return {
    #         "seatCommand": {
    #             "thermal": {
    #                 "heatingLevel": heatingLevel,
    #                 "ventilationLevel": 0  # Turn off ventilation when heating
    #             }
    #         },
    #         "status": "thermal adjusted",
    #         "message": f"Heating level set to {heatingLevel} (Cabin temp: {cabin_temp}°C)",
    #         "metadata": {
    #             "cabin_temperature": cabin_temp,
    #             "calculated_heating": heatingLevel
    #         }
    #     }

    # def adjust_ventilation(self, ventilationLevel: int = None) -> Dict[str, Any]:
    #     """
    #     Adjust the ventilation level in the vehicle based on cabin temperature.
    #     If ventilationLevel is provided, it will be used directly (clamped to 0-5).
    #     If not provided, it will be calculated based on cabin temperature.
    #     """
    #     metadata = self._read_metadata()
    #     if not metadata:
    #         return {
    #             "status": "error",
    #             "message": "Could not read current metadata"
    #         }
        
    #     cabin_temp = metadata.get('cabin_temperature', 20)  # Default to 20 if not available
        
    #     if ventilationLevel is None:
    #         # Auto-calculate ventilation level based on temperature
    #         if cabin_temp < 20:
    #             ventilationLevel = 0  # No ventilation needed
    #         elif 20 <= cabin_temp <= 23:
    #             ventilationLevel = 0
    #         elif 24 <= cabin_temp <= 28:
    #             ventilationLevel = 1
    #         elif 29 <= cabin_temp <= 32:
    #             ventilationLevel = 2
    #         elif 33 <= cabin_temp <= 36:
    #             ventilationLevel = 3
    #         elif 37 <= cabin_temp <= 40:
    #             ventilationLevel = 4
    #         else:  # Above 40
    #             ventilationLevel = 5
        
    #     ventilationLevel = self._clamp(ventilationLevel, 0, 5)
    #     self.logger.info(f"💨 Adjusting ventilation level to {ventilationLevel} (Cabin temp: {cabin_temp}°C)")
        
    #     return {
    #         "seatCommand": {
    #             "thermal": {
    #                 "ventilationLevel": ventilationLevel,
    #                 "heatingLevel": 0  # Turn off heating when ventilating
    #             }
    #         },
    #         "status": "ventilation adjusted",
    #         "message": f"Ventilation level set to {ventilationLevel} (Cabin temp: {cabin_temp}°C)",
    #         "metadata": {
    #             "cabin_temperature": cabin_temp,
    #             "calculated_ventilation": ventilationLevel
    #         }
    #     }

    def get_available_tools(self) -> Dict[str, Any]:
        tools = [
            get_seat_adjustment_tool(),
            # get_thermal_tool(),
            # get_ventilation_tool(),
            get_pelvis_drift_tool()
        ]
        
        # Add motor controls
        motors = ['track', 'height', 'backrest', 'seattilt', 'uba', 'headrest']
        directions = {
            'track': ['forward', 'backward'],
            'height': ['up', 'down'],
            'backrest': ['forward', 'backward'],
            'seattilt': ['up', 'down'],
            'uba': ['forward', 'backward'],
            'headrest': ['forward', 'backward']
        }
        
        for motor in motors:
            for direction in directions[motor]:
                tools.append(
                    self._create_tool_definition(
                        f"move_{motor}_{direction}",
                        f"Move {motor} {direction}",
                        {"current_value": (0, 100), "step": (10, 10), "new_value": (0, 100)},
                        required=["current_value"]
                    )
                ) 

        return {"tools": tools}
    
    def _create_tool_definition(self, name: str, description: str, params: Dict[str, tuple], required=None):
        """Generate tool definition dictionary."""
        if required is None:
            required = list(params.keys())
            
        properties = {}
        for param, (min_val, max_val) in params.items():
            properties[param] = {
                "type": "integer",
                "description": f"{param.replace('_', ' ')} ({min_val}-{max_val})",
                "minimum": min_val,
                "maximum": max_val
            }
            if param == "step":
                properties[param]["default"] = 10
                properties[param]["enum"] = [10]
        
        return {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }

    def run(self, host: str = "0.0.0.0", port: int = 5051):
        """Run the FastAPI server."""
        self.logger.info(f"🚀 Starting Motor MCP Server on {host}:{port}...")
        uvicorn.run(self.app, host=host, port=port)

if __name__ == "__main__":
    server = MotorControlServer()
    server.run()