from typing import Dict, Any

def get_seat_adjustment_tool() -> Dict[str, Any]:
    """Return the complete seat adjustment tool definition"""
    return {
        "name": "seat_adjustment",
        "description": "Full seat adjustment command",
        "parameters": {
            "type": "object",
            "properties": {
                "vibe": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "integer", "description": "Vibration action (0=off, 1=on)"},
                        "navigationTime": {"type": "string", "description": "Duration for navigation vibration"},
                        "mainVolume": {"type": "integer", "description": "Main vibration volume (0-100)"},
                        "vibeVolume": {"type": "integer", "description": "Vibration intensity (0-100)"},
                        "audioVolume": {"type": "integer", "description": "Audio-linked vibration volume (0-100)"},
                        "cushionVolume": {"type": "integer", "description": "Cushion vibration volume (0-100)"},
                        "backrestVolume": {"type": "integer", "description": "Backrest vibration volume (0-100)"}
                    }
                },
                "pneumatic": {
                    "type": "object",
                    "properties": {
                        "adjustement": {
                            "type": "object",
                            "properties": {
                                "lumbar": {
                                    "type": "object",
                                    "properties": {
                                        "direction": {"type": "string", "enum": ["increase", "decrease", "neutral"]},
                                        "percentage": {"type": "integer", "minimum": 0, "maximum": 100}
                                    }
                                },
                                "neckrest": {
                                    "type": "object",
                                    "properties": {
                                        "direction": {"type": "string", "enum": ["increase", "decrease", "neutral"]},
                                        "percentage": {"type": "integer", "minimum": 0, "maximum": 100}
                                    }
                                }
                            }
                        },
                        "massage": {
                            "type": "object",
                            "properties": {
                                "is_active": {"type": "boolean"},
                                "experience": {"type": "string", "enum": ["none", "relax", "energize", "circulation"]},
                                "intensity": {"type": "string", "enum": ["off", "low", "medium", "high"]}
                            }
                        }
                    }
                },
                "thermal": {
                    "type": "object",
                    "properties": {
                        "heatingLevel": {"type": "integer", "minimum": 0, "maximum": 100},
                        "ventilationLevel": {"type": "integer", "minimum": 0, "maximum": 100}
                    }
                },
                "motors": {
                    "type": "object",
                    "properties": {
                        "Track": {
                            "type": "object",
                            "properties": {
                                "percentage": {"type": "integer", "minimum": 0, "maximum": 100},
                                "type": {"type": "string", "enum": ["relative", "absolute"]},
                                "direction": {"type": "string", "enum": ["forward", "backward", "neutral"]}
                            }
                        },
                        "Backrest": {
                            "type": "object",
                            "properties": {
                                "percentage": {"type": "integer", "minimum": 0, "maximum": 100},
                                "type": {"type": "string", "enum": ["relative", "absolute"]},
                                "direction": {"type": "string", "enum": ["forward", "backward", "neutral"]}
                            }
                        },
                        "Height": {
                            "type": "object",
                            "properties": {
                                "percentage": {"type": "integer", "minimum": 0, "maximum": 100},
                                "type": {"type": "string", "enum": ["relative", "absolute"]},
                                "direction": {"type": "string", "enum": ["up", "down", "neutral"]}
                            }
                        },
                        "Tilt": {
                            "type": "object",
                            "properties": {
                                "percentage": {"type": "integer", "minimum": 0, "maximum": 100},
                                "type": {"type": "string", "enum": ["relative", "absolute"]},
                                "direction": {"type": "string", "enum": ["forward", "backward", "neutral"]}
                            }
                        },
                        "UBA": {
                            "type": "object",
                            "properties": {
                                "percentage": {"type": "integer", "minimum": 0, "maximum": 100},
                                "type": {"type": "string", "enum": ["relative", "absolute"]},
                                "direction": {"type": "string", "enum": ["forward", "backward", "neutral"]}
                            }
                        },
                        "Headrest": {
                            "type": "object",
                            "properties": {
                                "percentage": {"type": "integer", "minimum": 0, "maximum": 100},
                                "type": {"type": "string", "enum": ["relative", "absolute"]},
                                "direction": {"type": "string", "enum": ["forward", "backward", "neutral"]}
                            }
                        },
                        "CLA": {
                            "type": "object",
                            "properties": {
                                "percentage": {"type": "integer", "minimum": 0, "maximum": 100},
                                "type": {"type": "string", "enum": ["relative", "absolute"]},
                                "direction": {"type": "string", "enum": ["forward", "backward", "neutral"]}
                            }
                        }
                    }
                },
                "seatbelt": {
                    "type": "object",
                    "properties": {
                        "percentage": {"type": "integer", "minimum": 0, "maximum": 100}
                    }
                }
            }
        }
    }

def get_thermal_tool() -> Dict[str, Any]:
    """Return the thermal adjustment tool definition"""
    return {
        "name": "adjust_thermal",
        "description": "Adjust thermal level",
        "parameters": {
            "type": "object",
            "properties": {
                "heatingLevel": {
                    "type": "integer",
                    "description": "heating level (0-100)",
                    "minimum": 0,
                    "maximum": 100
                }
            },
            "required": ["heatingLevel"]
        }
    }

def get_ventilation_tool() -> Dict[str, Any]:
    """Return the ventilation adjustment tool definition"""
    return {
        "name": "adjust_ventilation",
        "description": "Adjust ventilation level",
        "parameters": {
            "type": "object",
            "properties": {
                "ventilationLevel": {
                    "type": "integer",
                    "description": "ventilation level (0-100)",
                    "minimum": 0,
                    "maximum": 100
                }
            },
            "required": ["ventilationLevel"]
        }
    }

def get_pelvis_drift_tool() -> Dict[str, Any]:
    """Return the pelvis drift adjustment tool definition"""
    return {
        "name": "adjustSeat_onPelvisdrift_city",
        "description": "Preset adjustment for pelvis drift posture in city driving (seat tilt +10, seatbelt +10)",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }