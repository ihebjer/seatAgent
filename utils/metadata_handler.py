import os
import logging
from typing import Dict, Optional
import yaml

class MetadataHandler:
    def __init__(self, metadata_path: str):
        self.metadata_path = metadata_path
        self.last_metadata = None
        self.last_modified_time = 0

    def load_latest_metadata(self) -> Dict:
        """Load and cache the latest metadata from YAML file."""
        try:
            if os.path.exists(self.metadata_path):
                current_modified_time = os.path.getmtime(self.metadata_path)
                if current_modified_time != self.last_modified_time:
                    with open(self.metadata_path, "r") as file:
                        self.last_metadata = yaml.safe_load(file)
                    self.last_modified_time = current_modified_time
            return self.last_metadata or {}
        except Exception as e:
            logging.error(f"❌ Error loading YAML metadata: {str(e)}")
            return {}

    @staticmethod
    def format_metadata_for_prompt(metadata: Optional[Dict]) -> str:
        """Format YAML metadata into a readable prompt for the LLM."""
        if not metadata:
            return "No current driver metadata available."

        try:
            mp = metadata["motors"]
            temp = metadata["cabin_tempreature"]

            return (
                f"- Driving Mode: {metadata['DrivingMode']}\n"
                f"- Posture: {metadata['posture']}\n"
                f"- Temperature: {temp['value']} {temp['unit']}\n"
                f"- Car Speed: {metadata['car_speed']}\n"
                f"- ventilation: {metadata['ventilation']}\n"
                f"- Traffic: {metadata.get('Traffic', 'Unknown')}\n"
                f"- Fatigue Level: {metadata['fatigue_level']}\n"
                f"Current motors Positions:\n"
                f"  - Track: {mp['Track']}\n"
                f"  - Height: {mp['Height']}\n"
                f"  - Backrest: {mp['Backrest']}\n"
                f"  - Seat Tilt: {mp['SeatTilt']}\n"
                f"  - Uba: {mp['Uba']}\n"
                f"  - Headrest: {mp['Headrest']}"
            )
        except Exception as e:
            logging.error(f"❌ Error formatting metadata: {str(e)}")
            return "Error processing driver metadata."
