import os
import logging
from typing import Dict, Any
from fastapi import FastAPI
from fastmcp import FastMCP
import uvicorn

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
        # Thermal/Ventilation
        self.mcp.tool()(self.adjust_thermal)
        self.mcp.tool()(self.adjust_ventilation)
        
        # Preset Experiences
        self.mcp.tool()(self.adjust_highway_experience)
        self.mcp.tool()(self.adjust_city_experience)
        
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
        """Dynamically create motor control methods."""
        def motor_method(
            current_value: int, 
            step: int = self.MOTOR_STEP, 
            new_value: int = None
        ) -> Dict[str, Any]:
            """Generated motor control method."""
            step = self.MOTOR_STEP  # Force fixed step size
            
            if new_value is None:
                new_value = current_value + step if 'forward' in direction or 'up' in direction else current_value - step
            
            new_value = self._clamp(new_value)
            action = direction.replace('_', ' ')
            
            self.logger.info(f"🔄 Moving {motor} {action} from {current_value} to {new_value}")
            
            return {
                "status": f"{motor} moved {action}",
                "motor": motor,
                "previous_value": current_value,
                "new_value": new_value,
                "step": step,
                "message": f"{motor.capitalize()} moved {action} from {current_value} to {new_value}"
            }
        
        # Add docstring
        doc_action = "closer to" if "forward" in direction else "away from" if "backward" in direction else direction
        motor_method.__doc__ = f"""
        Move the {motor} {direction} ({doc_action} {'steering wheel' if motor == 'track' else 'head' if motor == 'headrest' else 'default position'})
        
        Args:
            current_value: Current {motor} position (0-100)
            step: Movement step size (fixed at 10)
            new_value: Target position (0-100)
        """
        return motor_method

    # Thermal/Ventilation Controls
    def adjust_thermal(self, heatingLevel: int) -> Dict[str, Any]:
        """Adjust the thermal/heating level in the vehicle."""
        heatingLevel = self._clamp(heatingLevel)
        self.logger.info("🔥 Adjusting thermal level to %d", heatingLevel)
        return {
            "status": "thermal adjusted",
            "heatingLevel": heatingLevel,
            "message": f"Thermal level set to {heatingLevel}"
        }

    def adjust_ventilation(self, ventilationLevel: int) -> Dict[str, Any]:
        """Adjust the ventilation level in the vehicle."""
        ventilationLevel = self._clamp(ventilationLevel)
        self.logger.info("💨 Adjusting ventilation level to %d", ventilationLevel)
        return {
            "status": "ventilation adjusted",
            "ventilationLevel": ventilationLevel,
            "message": f"Ventilation level set to {ventilationLevel}"
        }

    # Preset Experiences
    def adjust_highway_experience(self, backrest: int, track: int, tilt: int) -> Dict[str, Any]:
        """Activate highway driving experience with optimized seat position."""
        backrest = self._clamp(backrest)
        track = self._clamp(track)
        tilt = self._clamp(tilt)
        
        self.logger.info("🛣️ Activating highway experience: backrest=%d, track=%d, tilt=%d",
                         backrest, track, tilt)
        return {
            "status": "highway experience activated",
            "motors": {"backrest": backrest, "track": track, "seatTilt": tilt},
            "message": f"Highway experience with backrest={backrest}, track={track}, tilt={tilt}"
        }

    def adjust_city_experience(self, backrest: int, track: int, tilt: int) -> Dict[str, Any]:
        """Activate city driving experience with optimized seat position."""
        backrest = self._clamp(backrest)
        track = self._clamp(track)
        tilt = self._clamp(tilt)
        
        self.logger.info("🏙️ Activating city experience: backrest=%d, track=%d, tilt=%d",
                         backrest, track, tilt)
        return {
            "status": "city experience activated",
            "motors": {"backrest": backrest, "track": track, "tilt": tilt},
            "message": f"City experience with backrest={backrest}, track={track}, tilt={tilt}"
        }

    def get_available_tools(self) -> Dict[str, Any]:
        """Return all available tools with descriptions."""
        tools = [
            self._create_tool_definition("adjust_thermal", "Adjust thermal level", {"heatingLevel": (0, 100)}),
            self._create_tool_definition("adjust_ventilation", "Adjust ventilation level", {"ventilationLevel": (0, 100)}),
            self._create_tool_definition(
                "adjust_highway_experience",
                "Activate highway driving experience",
                {"backrest": (0, 100), "track": (0, 100), "tilt": (0, 100)}
            ),
            self._create_tool_definition(
                "adjust_city_experience",
                "Activate city driving experience",
                {"backrest": (0, 100), "track": (0, 100), "tilt": (0, 100)}
            )
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