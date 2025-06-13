from fastapi import FastAPI
from fastmcp import FastMCP
import uvicorn
import logging
from typing import Dict, List, Any

# Logging setup
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

app = FastAPI(title="Motor MCP Server")
mcp = FastMCP(app)

# === Motor bounds ===
MOTOR_MIN = 0
MOTOR_MAX = 100
MOTOR_STEP = 10

def clamp(value: int, min_value: int = MOTOR_MIN, max_value: int = MOTOR_MAX) -> int:
    return max(min_value, min(value, max_value))

# === Thermal and Ventilation Controls ===

@mcp.tool()
def adjust_thermal(heatingLevel: int):
    """
    Adjust the thermal/heating level in the vehicle.
    
    Args:
        heatingLevel: Heating level from 0 to 100
    """
    heatingLevel = clamp(heatingLevel)
    logging.info("🔥 Adjusting thermal level to %d", heatingLevel)
    return {
        "status": "thermal adjusted",
        "heatingLevel": heatingLevel,
        "message": f"Thermal level set to {heatingLevel}"
    }

@mcp.tool()
def adjust_ventilation(ventilationLevel: int):
    """
    Adjust the ventilation level in the vehicle.
    
    Args:
        ventilationLevel: Ventilation level from 0 to 100
    """
    ventilationLevel = clamp(ventilationLevel)
    logging.info("💨 Adjusting ventilation level to %d", ventilationLevel)
    return {
        "status": "ventilation adjusted",
        "ventilationLevel": ventilationLevel,
        "message": f"Ventilation level set to {ventilationLevel}"
    }

# === Preset Experiences ===

@mcp.tool()
def adjust_highway_experience(backrest: int, track: int, tilt: int):
    """
    Activate highway driving experience with optimized seat position.
    
    Args:
        backrest: Backrest position (0-100)
        track: Track/forward-backward position (0-100)  
        tilt: Seat tilt angle (0-100)
    """
    backrest = clamp(backrest)
    track = clamp(track)
    tilt = clamp(tilt)
    
    logging.info("🛣️ Activating highway experience: backrest=%d, track=%d, tilt=%d",
                 backrest, track, tilt)
    return {
        "status": "highway experience activated",
        "motors": {
            "backrest": backrest,
            "track": track,
            "seatTilt": tilt
        },
        "message": f"Highway experience activated with backrest at {backrest}, track at {track}, tilt at {tilt}"
    }

@mcp.tool()
def adjust_city_experience(backrest: int, track: int, tilt: int):
    """
    Activate city driving experience with optimized seat position.
    
    Args:
        backrest: Backrest position (0-100)
        track: Track/forward-backward position (0-100)
        tilt: Seat tilt angle (0-100)
    """
    backrest = clamp(backrest)
    track = clamp(track)
    tilt = clamp(tilt)
    
    logging.info("🏙️ Activating city experience: backrest=%d, track=%d, tilt=%d",
                 backrest, track, tilt)
    return {
        "status": "city experience activated",
        "motors": {
            "backrest": backrest,
            "track": track,
            "tilt": tilt
        },
        "message": f"City experience activated with backrest at {backrest}, track at {track}, tilt at {tilt}"
    }

# === Individual Motor Controls ===

# Track Motor Controls
@mcp.tool()
def move_track_forward(current_value: int, step: int = MOTOR_STEP, new_value: int = None):
    """
    Move the seat track forward (away from steering wheel).
    
    Args:
        current_value: Current track position (0-100)
        step: Movement step size (fixed at 10)
        new_value: Target position (0-100)
    """
    # Force step to be MOTOR_STEP
    step = MOTOR_STEP
    
    if new_value is None:
        new_value = current_value + step
    new_value = clamp(new_value)
    logging.info(f"➡️ Moving Track forward from {current_value} to {new_value}")
    return {
        "status": "Track moved forward",
        "motor": "Track",
        "previous_value": current_value,
        "new_value": new_value,
        "step": step,
        "message": f"Track moved forward from {current_value} to {new_value}"
    }

@mcp.tool()
def move_track_backward(current_value: int,step: int = MOTOR_STEP, new_value: int = None):
    """
    Move the seat track backward (toward steering wheel).
    
    Args:
        current_value: Current track position (0-100)
    """
    if new_value is None:
        new_value = current_value - step
    new_value = clamp(new_value)
    logging.info(f"⬅️ Moving Track backward from {current_value} to {new_value}")
    return {
        "status": "Track moved backward",
        "motor": "Track",
        "previous_value": current_value,
        "new_value": new_value,
        "step": step,
        "message": f"Track moved backward from {current_value} to {new_value}"
    }

# Height Motor Controls
@mcp.tool()
def move_height_up(current_value: int, step: int = MOTOR_STEP, new_value: int = None):
    """
    Move the seat height up.
    
    Args:
        current_value: Current height position (0-100)
    """
    if new_value is None:
        new_value = current_value - step
    new_value = clamp(new_value)
    logging.info(f"⬅️ Moving Track up from {current_value} to {new_value}")
    return {
        "status": "height moved up",
        "motor": "height",
        "previous_value": current_value,
        "new_value": new_value,
        "step": step,
        "message": f"Track moved backward from {current_value} to {new_value}"
    }

@mcp.tool()
def move_height_down(current_value: int):
    """
    Move the seat height down.
    
    Args:
        current_value: Current height position (0-100)
    """
    new_value = clamp(current_value - MOTOR_STEP)
    logging.info(f"⬇️ Moving Height down from {current_value} to {new_value}")
    return {
        "status": "Height moved down",
        "motor": "Height",
        "previous_value": current_value,
        "new_value": new_value,
        "step": MOTOR_STEP,
        "message": f"Seat height lowered from {current_value} to {new_value}"
    }

# Backrest Motor Controls
@mcp.tool()
def move_backrest_forward(current_value: int):
    """
    Move the backrest forward (more upright position).
    
    Args:
        current_value: Current backrest position (0-100)
    """
    new_value = clamp(current_value + MOTOR_STEP)
    logging.info(f"➡️ Moving Backrest forward from {current_value} to {new_value}")
    return {
        "status": "Backrest moved forward",
        "motor": "Backrest",
        "previous_value": current_value,
        "new_value": new_value,
        "step": MOTOR_STEP,
        "message": f"Backrest moved to more upright position: {current_value} → {new_value}"
    }

@mcp.tool()
def move_backrest_backward(current_value: int):
    """
    Move the backrest backward (more reclined position).
    
    Args:
        current_value: Current backrest position (0-100)
    """
    new_value = clamp(current_value - MOTOR_STEP)
    logging.info(f"⬅️ Moving Backrest backward from {current_value} to {new_value}")
    return {
        "status": "Backrest moved backward",
        "motor": "Backrest",
        "previous_value": current_value,
        "new_value": new_value,
        "step": MOTOR_STEP,
        "message": f"Backrest reclined: {current_value} → {new_value}"
    }

# SeatTilt Motor Controls
@mcp.tool()
def move_seattilt_up(current_value: int):
    """
    Tilt the seat up (front edge higher).
    
    Args:
        current_value: Current seat tilt position (0-100)
    """
    new_value = clamp(current_value + MOTOR_STEP)
    logging.info(f"⬆️ Moving SeatTilt up from {current_value} to {new_value}")
    return {
        "status": "SeatTilt moved up",
        "motor": "SeatTilt",
        "previous_value": current_value,
        "new_value": new_value,
        "step": MOTOR_STEP,
        "message": f"Seat tilted up: {current_value} → {new_value}"
    }

@mcp.tool()
def move_seattilt_down(current_value: int):
    """
    Tilt the seat down (front edge lower).
    
    Args:
        current_value: Current seat tilt position (0-100)
    """
    new_value = clamp(current_value - MOTOR_STEP)
    logging.info(f"⬇️ Moving SeatTilt down from {current_value} to {new_value}")
    return {
        "status": "SeatTilt moved down",
        "motor": "SeatTilt",
        "previous_value": current_value,
        "new_value": new_value,
        "step": MOTOR_STEP,
        "message": f"Seat tilted down: {current_value} → {new_value}"
    }

# UBA Motor Controls
@mcp.tool()
def move_uba_forward(current_value: int):
    """
    Move the UBA (Upper Back Adjustment) forward.
    
    Args:
        current_value: Current UBA position (0-100)
    """
    new_value = clamp(current_value + MOTOR_STEP)
    logging.info(f"➡️ Moving UBA forward from {current_value} to {new_value}")
    return {
        "status": "UBA moved forward",
        "motor": "UBA",
        "previous_value": current_value,
        "new_value": new_value,
        "step": MOTOR_STEP,
        "message": f"Upper back support adjusted: {current_value} → {new_value}"
    }

@mcp.tool()
def move_uba_backward(current_value: int):
    """
    Move the UBA (Upper Back Adjustment) backward.
    
    Args:
        current_value: Current UBA position (0-100)
    """
    new_value = clamp(current_value - MOTOR_STEP)
    logging.info(f"⬅️ Moving UBA backward from {current_value} to {new_value}")
    return {
        "status": "UBA moved backward",
        "motor": "UBA", 
        "previous_value": current_value,
        "new_value": new_value,
        "step": MOTOR_STEP,
        "message": f"Upper back support adjusted: {current_value} → {new_value}"
    }

# Headrest Motor Controls
@mcp.tool()
def move_headrest_forward(current_value: int):
    """
    Move the headrest forward (closer to head).
    
    Args:
        current_value: Current headrest position (0-100)
    """
    new_value = clamp(current_value + MOTOR_STEP)
    logging.info(f"➡️ Moving Headrest forward from {current_value} to {new_value}")
    return {
        "status": "Headrest moved forward",
        "motor": "Headrest",
        "previous_value": current_value,
        "new_value": new_value,
        "step": MOTOR_STEP,
        "message": f"Headrest moved closer: {current_value} → {new_value}"
    }

@mcp.tool()
def move_headrest_backward(current_value: int):
    """
    Move the headrest backward (away from head).
    
    Args:
        current_value: Current headrest position (0-100)
    """
    new_value = clamp(current_value - MOTOR_STEP)
    logging.info(f"⬅️ Moving Headrest backward from {current_value} to {new_value}")
    return {
        "status": "Headrest moved backward",
        "motor": "Headrest",
        "previous_value": current_value,
        "new_value": new_value,
        "step": MOTOR_STEP,
        "message": f"Headrest moved away: {current_value} → {new_value}"
    }

# === Tool Discovery Endpoint ===

@app.get("/mcp/tools")
def get_available_tools():
    """Return all available tools with their descriptions and parameters"""
    
    tools_definitions = [
        # --- Already defined tools, repeated for context ---
        {
            "name": "adjust_thermal",
            "description": "Adjust the thermal/heating level in the vehicle",
            "parameters": {
                "type": "object",
                "properties": {
                    "heatingLevel": {
                        "type": "integer",
                        "description": "Heating level from 0 to 100",
                        "minimum": 0,
                        "maximum": 100
                    }
                },
                "required": ["heatingLevel"]
            }
        },
        {
            "name": "adjust_ventilation", 
            "description": "Adjust the ventilation level in the vehicle",
            "parameters": {
                "type": "object",
                "properties": {
                    "ventilationLevel": {
                        "type": "integer",
                        "description": "Ventilation level from 0 to 100",
                        "minimum": 0,
                        "maximum": 100
                    }
                },
                "required": ["ventilationLevel"]
            }
        },
        {
            "name": "adjust_highway_experience",
            "description": "Activate highway driving experience with optimized seat position",
            "parameters": {
                "type": "object",
                "properties": {
                    "backrest": {"type": "integer", "description": "Backrest position (0-100)", "minimum": 0, "maximum": 100},
                    "track": {"type": "integer", "description": "Track/forward-backward position (0-100)", "minimum": 0, "maximum": 100},
                    "tilt": {"type": "integer", "description": "Seat tilt angle (0-100)", "minimum": 0, "maximum": 100}
                },
                "required": ["backrest", "track", "tilt"]
            }
        },
        {
            "name": "adjust_city_experience",
            "description": "Activate city driving experience with optimized seat position",
            "parameters": {
                "type": "object",
                "properties": {
                    "backrest": {"type": "integer", "description": "Backrest position (0-100)", "minimum": 0, "maximum": 100},
                    "track": {"type": "integer", "description": "Track/forward-backward position (0-100)", "minimum": 0, "maximum": 100},
                    "tilt": {"type": "integer", "description": "Seat tilt angle (0-100)", "minimum": 0, "maximum": 100}
                },
                "required": ["backrest", "track", "tilt"]
            }
        },
        # Track
        {
            "name": "move_track_forward",
            "description": "Move the seat track forward (toward  steering wheel)",
    "parameters": {
        "type": "object",
        "properties": {
            "current_value": {
                "type": "integer",
                "description": "Current track position (0-100)",
                "minimum": 0,
                "maximum": 100
            },
            "step": {
                "type": "integer",
                "description": "Movement step size",
                "default": 10,
                "minimum": 1,
                "maximum": 100
            },
            "new_value": {
                "type": "integer",
                "description": "Target position (0-100), calculated as current_value + step",
                "minimum": 0,
                "maximum": 100}
                },
                "required": ["current_value"]
            }
        },
{
    "name": "move_track_backward",
    "description": "Move the seat track backward (away steering wheel)",
    "parameters": {
        "type": "object",
        "properties": {
            "current_value": {
                "type": "integer",
                "description": "Current track position (0-100)",
                "minimum": 0,
                "maximum": 100
            },
            "step": {
                "type": "integer",
                "description": "Movement step size (fixed at 10)",
                "default": 10,
                "enum": [10]  # Only allow value of 10
            },
            "new_value": {
                "type": "integer",
                "description": "Target position (0-100), calculated as current_value - 10",
                "minimum": 0,
                "maximum": 100
            }
        },
        "required": ["current_value"]
    }
},
        # Height
        {
            "name": "move_height_up",
            "description": "Move the seat height up",
   "parameters": {
        "type": "object",
        "properties": {
            "current_value": {
                "type": "integer",
                "description": "Current height position (0-100)",
                "minimum": 0,
                "maximum": 100
            },
            "step": {
                "type": "integer",
                "description": "Movement step size (fixed at 10)",
                "default": 10,
                "enum": [10]  # Only allow value of 10
            },
            "new_value": {
                "type": "integer",
                "description": "Target position (0-100), calculated as current_value + 10",
                "minimum": 0,
                "maximum": 100
            }
        },
                "required": ["current_value"]
            }
        },
        {
            "name": "move_height_down",
            "description": "Move the seat height down",
   "parameters": {
        "type": "object",
        "properties": {
            "current_value": {
                "type": "integer",
                "description": "Current height position (0-100)",
                "minimum": 0,
                "maximum": 100
            },
            "step": {
                "type": "integer",
                "description": "Movement step size (fixed at 10)",
                "default": 10,
                "enum": [10]  # Only allow value of 10
            },
            "new_value": {
                "type": "integer",
                "description": "Target position (0-100), calculated as current_value - 10",
                "minimum": 0,
                "maximum": 100
            }
        },
                "required": ["current_value"]
            }
        },
        # Backrest
        {
            "name": "move_backrest_forward",
            "description": "Move the backrest forward (more upright position)",
   "parameters": {
        "type": "object",
        "properties": {
            "current_value": {
                "type": "integer",
                "description": "Current backrest position (0-100)",
                "minimum": 0,
                "maximum": 100
            },
            "step": {
                "type": "integer",
                "description": "Movement step size (fixed at 10)",
                "default": 10,
                "enum": [10]  # Only allow value of 10
            },
            "new_value": {
                "type": "integer",
                "description": "Target position (0-100), calculated as current_value + 10",
                "minimum": 0,
                "maximum": 100
            }
        },
                "required": ["current_value"]
            }
        },
        {
            "name": "move_backrest_backward",
            "description": "Move the backrest backward (more reclined position)",
        "parameters": {
        "type": "object",
        "properties": {
            "current_value": {
                "type": "integer",
                "description": "Current backrest position (0-100)",
                "minimum": 0,
                "maximum": 100
            },
            "step": {
                "type": "integer",
                "description": "Movement step size (fixed at 10)",
                "default": 10,
                "enum": [10]  
            },
            "new_value": {
                "type": "integer",
                "description": "Target position (0-100), calculated as current_value - 10",
                "minimum": 0,
                "maximum": 100
            }
        },
                "required": ["current_value"]
            }
        },
        # SeatTilt
        {
            "name": "move_seattilt_up",
            "description": "Tilt the seat up (front edge higher)",
        "parameters": {
        "type": "object",
        "properties": {
            "current_value": {
                "type": "integer",
                "description": "Current seat tilt position (0-100)",
                "minimum": 0,
                "maximum": 100
            },
            "step": {
                "type": "integer",
                "description": "Movement step size (fixed at 10)",
                "default": 10,
                "enum": [10]  
            },
            "new_value": {
                "type": "integer",
                "description": "Target position (0-100), calculated as current_value + 10",
                "minimum": 0,
                "maximum": 100
            }
        },
                "required": ["current_value"]
            }
        },
        {
            "name": "move_seattilt_down",
            "description": "Tilt the seat down (front edge lower)",
        "parameters": {
        "type": "object",
        "properties": {
            "current_value": {
                "type": "integer",
                "description": "Current seat tilt position (0-100)",
                "minimum": 0,
                "maximum": 100
            },
            "step": {
                "type": "integer",
                "description": "Movement step size (fixed at 10)",
                "default": 10,
                "enum": [10]  
            },
            "new_value": {
                "type": "integer",
                "description": "Target position (0-100), calculated as current_value - 10",
                "minimum": 0,
                "maximum": 100
            }
        },
                "required": ["current_value"]
            }
        },
        # UBA
        {
            "name": "move_uba_forward",
            "description": "Move the UBA (Upper Back Adjustment) forward",
        "parameters": {
        "type": "object",
        "properties": {
            "current_value": {
                "type": "integer",
                "description": "Current UBA position (0-100)",
                "minimum": 0,
                "maximum": 100
            },
            "step": {
                "type": "integer",
                "description": "Movement step size (fixed at 10)",
                "default": 10,
                "enum": [10]  
            },
            "new_value": {
                "type": "integer",
                "description": "Target position (0-100), calculated as current_value + 10",
                "minimum": 0,
                "maximum": 100
            }
        },
                "required": ["current_value"]
            }
        },
        {
            "name": "move_uba_backward",
            "description": "Move the UBA (Upper Back Adjustment) backward",
        "parameters": {
        "type": "object",
        "properties": {
            "current_value": {
                "type": "integer",
                "description": "Current UBA position (0-100)",
                "minimum": 0,
                "maximum": 100
            },
            "step": {
                "type": "integer",
                "description": "Movement step size (fixed at 10)",
                "default": 10,
                "enum": [10]  
            },
            "new_value": {
                "type": "integer",
                "description": "Target position (0-100), calculated as current_value - 10",
                "minimum": 0,
                "maximum": 100
            }
        },
                "required": ["current_value"]
            }
        },
        # Headrest
        {
            "name": "move_headrest_forward",
            "description": "Move the headrest forward (closer to head)",
        "parameters": {
        "type": "object",
        "properties": {
            "current_value": {
                "type": "integer",
                "description": "Current headrest position (0-100)",
                "minimum": 0,
                "maximum": 100
            },
            "step": {
                "type": "integer",
                "description": "Movement step size (fixed at 10)",
                "default": 10,
                "enum": [10]  
            },
            "new_value": {
                "type": "integer",
                "description": "Target position (0-100), calculated as current_value + 10",
                "minimum": 0,
                "maximum": 100
            }
        },
                "required": ["current_value"]
            }
        },
        {
            "name": "move_headrest_backward",
            "description": "Move the headrest backward (away from head)",
        "parameters": {
        "type": "object",
        "properties": {
            "current_value": {
                "type": "integer",
                "description": "Current headrest position (0-100)",
                "minimum": 0,
                "maximum": 100
            },
            "step": {
                "type": "integer",
                "description": "Movement step size (fixed at 10)",
                "default": 10,
                "enum": [10]  
            },
            "new_value": {
                "type": "integer",
                "description": "Target position (0-100), calculated as current_value - 10",
                "minimum": 0,
                "maximum": 100
            }
        },
                "required": ["current_value"]
            }
        }
    ]
    return {"tools": tools_definitions}


if __name__ == "__main__":
    uvicorn.run("mcp_server:app", host="0.0.0.0", port=5051, reload=True)
