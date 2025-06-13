import json
from typing import Union

DEFAULT_RESPONSE_STRUCTURE = {
    "seatCommand": {
        "vibe": {
            "action": 0,
            "navigationTime": "00:00:00:000",
            "mainVolume": 0,
            "vibeVolume": 0,
            "audioVolume": 0,
            "cushionVolume": 0,
            "backrestVolume": 0
        },
        "pneumatic": {
            "adjustement": {
                "lumbar": {
                    "direction": "neutral",
                    "percentage": 0
                },
                "neckrest": {
                    "direction": "neutral",
                    "percentage": 0
                }
            },
            "massage": {
                "is_active": False,
                "experience": "none",
                "intensity": "off"
            }
        },
        "thermal": {
            "heatingLevel": 0,
            "ventilationLevel": 0
        },
        "motors": {
            "Track": {
                "percentage": 0,
                "type": "relative",
                "direction": "neutral"
            },
            "Backrest": {
                "percentage": 0,
                "type": "relative",
                "direction": "neutral"
            },
            "Height": {
                "percentage": 0,
                "type": "relative",
                "direction": "neutral"
            },
            "Tilt": {
                "percentage": 0,
                "type": "relative",
                "direction": "neutral"
            },
            "UBA": {
                "percentage": 0,
                "type": "relative",
                "direction": "neutral"
            },
            "Headrest": {
                "percentage": 0,
                "type": "relative",
                "direction": "neutral"
            },
            "CLA": {
                "percentage": 0,
                "type": "relative",
                "direction": "neutral"
            }
        },
        "seatbelt": {
            "percentage": 0
        }
    }
}

def extract_json_from_response(response: Union[str, dict]) -> dict:
    """Extract JSON from response which could be either string or dict."""
    if isinstance(response, dict):
        if "answer" in response:
            if isinstance(response["answer"], str):
                try:
                    json_start = response["answer"].find('{')
                    json_end = response["answer"].rfind('}') + 1
                    if json_start >= 0 and json_end > json_start:
                        return json.loads(response["answer"][json_start:json_end])
                except:
                    pass
        return response.get("seatCommand", {})
    elif isinstance(response, str):
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                parsed = json.loads(response[json_start:json_end])
                return parsed.get("seatCommand", {})
        except:
            pass
    return {}

def is_section_active(section_data, section_name):
    """Check if a section should be considered active based on its content."""
    if not section_data:
        return False
        
    if section_name == "massage":
        return section_data.get("is_active", False)
    elif section_name == "thermal":
        return section_data.get("heatingLevel", 0) > 0 or \
               section_data.get("ventilationLevel", 0) > 0
    elif section_name == "vibe":
        return section_data.get("action", 0) > 0
    elif section_name == "pneumatic_adjustment":
        return (section_data.get("lumbar", {}).get("percentage", 0) > 0 or
               section_data.get("neckrest", {}).get("percentage", 0) > 0)
    elif section_name == "motors":
        return any(motor.get("percentage", 0) > 0 for motor in section_data.values() if isinstance(motor, dict))
    elif section_name == "seatbelt":
        return section_data.get("percentage", 0) > 0
    return False

def handle_legacy_fields(actions, result):
    """Handle backward compatibility for simple boolean fields from older format."""
    if isinstance(actions.get("ventilation"), bool):
        result["thermal"]["ventilationLevel"] = 3 if actions["ventilation"] else 0
    
    if isinstance(actions.get("vibe"), bool) and actions["vibe"]:
        result["vibe"]["action"] = 1
        result["vibe"]["mainVolume"] = 5
        
    if isinstance(actions.get("massage"), bool):
        result["pneumatic"]["massage"]["is_active"] = actions["massage"]

def process_llm_response(response: Union[str, dict]) -> dict:
    """
    Process the LLM response and extract the JSON structure.
    Initialize missing sections with default values and ensure non-requested
    features are set to zero/false.
    """
    try:
        actions = extract_json_from_response(response)
        if not actions:
            return DEFAULT_RESPONSE_STRUCTURE.copy()
            
        result = DEFAULT_RESPONSE_STRUCTURE.copy()
        active_sections = set()

        # Process each section
        if "vibe" in actions and is_section_active(actions["vibe"], "vibe"):
            active_sections.add("vibe")
            result["seatCommand"]["vibe"].update(actions["vibe"])

        if "thermal" in actions and is_section_active(actions["thermal"], "thermal"):
            active_sections.add("thermal")
            result["seatCommand"]["thermal"].update(actions["thermal"])

        if "motors" in actions and is_section_active(actions["motors"], "motors"):
            active_sections.add("motors")
            for motor, settings in actions["motors"].items():
                if motor in result["seatCommand"]["motors"]:
                    result["seatCommand"]["motors"][motor].update(settings)

        if "pneumatic" in actions:
            if "massage" in actions["pneumatic"] and is_section_active(actions["pneumatic"]["massage"], "massage"):
                active_sections.add("massage")
                result["seatCommand"]["pneumatic"]["massage"].update(actions["pneumatic"]["massage"])

            if "adjustement" in actions["pneumatic"] and is_section_active(actions["pneumatic"]["adjustement"], "pneumatic_adjustment"):
                active_sections.add("pneumatic_adjustment")
                result["seatCommand"]["pneumatic"]["adjustement"].update(actions["pneumatic"]["adjustement"])

        if "seatbelt" in actions and is_section_active(actions["seatbelt"], "seatbelt"):
            active_sections.add("seatbelt")
            result["seatCommand"]["seatbelt"].update(actions["seatbelt"])

        handle_legacy_fields(actions, result)

        return result
        
    except json.JSONDecodeError as e:
        print(f"Failed to parse JSON in LLM response: {str(e)}")
    except ValueError as e:
        print(f"Error processing response: {str(e)}")
    except Exception as e:
        print(f"Unexpected error processing LLM response: {str(e)}")
    
    return DEFAULT_RESPONSE_STRUCTURE.copy()