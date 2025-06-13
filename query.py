import os
import yaml
import requests

# Read config file
parent_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
config_path = os.path.join(parent_folder, "MCP", "config.yaml")
with open(config_path, 'r') as file:
    config = yaml.safe_load(file)

server_port = config["server"]["port"]
query = "What is the primary function of Forvia's AI-based seat comfort system?"

response = requests.post(f"http://localhost:{server_port}/query", json={"query": query})

print("Response from app.py:")
print(response.json())
