import os
import threading
import logging
import urllib3
import yaml
import requests
import json
import time
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from utils.metadata_handler import MetadataHandler
from prompt_manager import PromptManager


class DynamicMCPHost:
    """Main MCP Host application that coordinates between LLM and MCP servers."""
    
    def __init__(self):
        """Initialize the MCP Host with configuration and services."""
        self._load_configuration()
        self._setup_environment()
        self._initialize_services()
        self._create_flask_app()
        self.prompt_manager = PromptManager()  # Add this line
        
    def _load_configuration(self):
        """Load configuration from YAML file."""
        load_dotenv()
        parent_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        config_path = os.path.join(parent_folder, "MCP", "config.yaml")
        
        with open(config_path, 'r') as file:
            self.config = yaml.safe_load(file)
            
        self.config.update({
            "server_port": self.config["server"]["port"],
            "motor_mcp_host": "http://localhost:5051",
            "knowledge_mcp_host": "http://localhost:5052",
            "metadata_path": os.path.abspath(self.config["metadata"])
        })
    
    def _setup_environment(self):
        """Configure environment settings and logging."""
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
        
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger(__name__)
    
    def _initialize_services(self):
        """Initialize all required services."""
        self.llm = None
        self.metadata_handler = MetadataHandler(self.config["metadata_path"])
        self.cached_metadata = None
        self.last_metadata_update = 0
        self.available_tools = {}
        self.mcp_servers = {
            "motor": self.config["motor_mcp_host"],
            "knowledge": self.config["knowledge_mcp_host"]
        }
    
    def _create_flask_app(self):
        """Create and configure the Flask application."""
        self.app = Flask(__name__)
        self._register_routes()
    
    def _register_routes(self):
        """Register all API endpoints."""
        self.app.route("/query", methods=["POST"])(self.query_endpoint)
        self.app.route("/tools", methods=["GET"])(self.get_available_tools)
        self.app.route("/metadata", methods=["GET"])(self.get_metadata)
        self.app.route("/refresh", methods=["POST"])(self.refresh_tools)
        self.app.route("/debug/servers", methods=["GET"])(self.debug_servers)
    
    def initialize(self):
        """Initialize the LLM and discover available tools."""
        self.logger.info("Initializing Dynamic MCP Client...")
        try:
            self.llm = ChatOpenAI(
                model="gpt-4o",
                openai_api_key=os.getenv("OPENAI_API_KEY"),
                temperature=0.1
            )
            self.refresh_metadata_cache()
            self.discover_tools()
            self.logger.info("✅ Dynamic MCP Client ready!")
        except Exception as e:
            self.logger.error(f"Failed to initialize client: {str(e)}")
            raise
    
    def debug_servers(self):
        """Debug endpoint to check server connectivity."""
        results = {}
        for server_name, server_url in self.mcp_servers.items():
            try:
                response = requests.get(f"{server_url}/mcp/tools", timeout=5)
                results[server_name] = {
                    "status": response.status_code,
                    "reachable": True,
                    "response": response.json() if response.status_code == 200 else response.text
                }
            except Exception as e:
                results[server_name] = {
                    "status": "error",
                    "reachable": False,
                    "error": str(e)
                }
        return jsonify(results)
    
    def discover_tools(self):
        """Discover available tools from all MCP servers."""
        self.logger.info("🔍 Discovering available tools from MCP servers...")
        self.available_tools = {}
        
        for server_name, server_url in self.mcp_servers.items():
            try:
                response = requests.get(f"{server_url}/mcp/tools", timeout=5)
                if response.status_code == 200:
                    tools_data = response.json()
                    self.available_tools[server_name] = {
                        "url": f"{server_url}/mcp/execute",
                        "tools": tools_data.get("tools", [])
                    }
                    self.logger.info(f"✅ Discovered {len(tools_data.get('tools', []))} tools from {server_name} server")
                else:
                    self.logger.warning(f"⚠️ Could not get tools from {server_name} server: {response.status_code}")
            except Exception as e:
                self.logger.error(f"❌ Error discovering tools from {server_name}: {str(e)}")
    
    def refresh_metadata_cache(self):
        """Refresh the cached metadata from file."""
        try:
            self.cached_metadata = self.metadata_handler.load_latest_metadata()
            if self.cached_metadata:
                self.last_metadata_update = time.time()
                self.logger.info("✅ Metadata cache refreshed")
        except Exception as e:
            self.logger.error(f"❌ Error refreshing metadata cache: {str(e)}")
    
    def get_current_metadata(self):
        """Get current driving metadata with caching."""
        if time.time() - self.last_metadata_update > 5:  # Refresh cache if older than 5 seconds
            self.refresh_metadata_cache()
        
        if self.cached_metadata:
            return self.metadata_handler.format_metadata_for_prompt(self.cached_metadata)
        return "Metadata unavailable"
    
    def create_tools_description(self):
        """Generate a description of all available tools for the LLM."""
        tools_desc = "Available MCP Tools:\n\n"
        
        for server_name, server_info in self.available_tools.items():
            tools_desc += f"=== {server_name.upper()} SERVER ===\n"
            for tool in server_info["tools"]:
                tools_desc += f"- {tool['name']}: {tool.get('description', 'No description')}\n"
                if tool.get('parameters'):
                    params = []
                    for param_name, param_info in tool['parameters'].get('properties', {}).items():
                        param_type = param_info.get('type', 'unknown')
                        param_desc = param_info.get('description', '')
                        params.append(f"{param_name} ({param_type}): {param_desc}")
                    if params:
                        tools_desc += f"  Parameters: {', '.join(params)}\n"
                tools_desc += "\n"
        
        return tools_desc
    
    def create_system_prompt(self):
        """Create the system prompt for the LLM with current context."""
        current_metadata = self.get_current_metadata()
        tools_description = self.create_tools_description()
        return self.prompt_manager.get_system_prompt(current_metadata, tools_description)
        
    def send_mcp_command(self, server_name, tool_name, args):
        """Send command to specified MCP server."""
        try:
            if server_name not in self.available_tools:
                return 400, {"error": f"Server {server_name} not available"}
            
            server_url = self.available_tools[server_name]["url"]
            payload = {"tool": tool_name, "args": args}
            
            self.logger.info(f"Sending to {server_name}: {tool_name} with args {args}")
            response = requests.post(server_url, json=payload)
            return response.status_code, response.json()
        except Exception as e:
            self.logger.error(f"Failed to call MCP server {server_name}: {str(e)}")
            return 500, {"error": f"Failed to reach {server_name} server"}
        
    
    def process_query(self, user_query):
        """Process user query using LLM and MCP tools."""
        try:
            messages = [
                SystemMessage(content=self.create_system_prompt()),
                HumanMessage(content=user_query)
            ]
            
            llm_response = self.llm.invoke(messages)
            decision_text = llm_response.content.strip()
            
            self.logger.info(f"User Query: {user_query}")
            self.logger.info(f"LLM Decision: {decision_text}")
            
            try:
                decision = json.loads(decision_text)
            except json.JSONDecodeError:
                return {
                    "status": "success",
                    "response": decision_text,
                    "metadata": self.get_current_metadata()
                }, 200
            
            if decision.get("action") == "direct_response":
                return {
                    "status": "success",
                    "response": decision.get("response"),
                    "metadata": self.get_current_metadata()
                }, 200
            
            elif "seatCommand" in decision:  # Motor command case
                status_code, tool_result = self.send_mcp_command(
                    "motor",
                    "seat_adjustment",
                    decision.get("seatCommand", {})
                )
                
                if status_code == 200:
                    final_response = self.generate_final_response(
                        user_query,
                        tool_result,
                        decision.get("reasoning", "")
                    )
                    return {
                        "status": "success",
                        "response": final_response,
                        "tool_used": "motor.seat_adjustment",
                        "tool_result": tool_result,
                        "metadata": self.get_current_metadata()
                    }, 200
                else:
                    return {
                        "status": "error",
                        "error": f"Tool execution failed: {tool_result}",
                        "metadata": self.get_current_metadata()
                    }, status_code
            
            return {
                "status": "error",
                "error": "Invalid action from LLM",
                "metadata": self.get_current_metadata()
            }, 400
                
        except Exception as e:
            self.logger.error(f"Error processing query: {str(e)}")
            return {
                "status": "error",
                "error": f"Failed to process query: {str(e)}"
            }, 500
    
    def generate_final_response(self, user_query, tool_result, reasoning):
        """Generate natural language response based on tool results."""
        context_prompt = self.prompt_manager.get_final_response_prompt(
            user_query,
            json.dumps(tool_result, indent=2),
            reasoning
        )
        response = self.llm.invoke([HumanMessage(content=context_prompt)])
        return response.content.strip()
    
    def query_endpoint(self):
        """Main query endpoint handler."""
        data = request.json
        user_query = data.get("query", "").strip()
        
        if not user_query:
            return jsonify({"error": "No query provided"}), 400
        
        response, status_code = self.process_query(user_query)
        return jsonify(response), status_code
    
    def get_available_tools(self):
        """Endpoint to get available tools."""
        return jsonify({
            "status": "success",
            "servers": self.available_tools
        })
    
    def get_metadata(self):
        """Endpoint to get current metadata."""
        return jsonify({
            "status": "success",
            "metadata": self.get_current_metadata(),
            "raw_metadata": self.cached_metadata
        })
    
    def refresh_tools(self):
        """Endpoint to refresh tools and metadata."""
        try:
            self.discover_tools()
            self.refresh_metadata_cache()
            return jsonify({
                "status": "success",
                "message": "Tools and metadata refreshed",
                "tools_count": sum(len(server["tools"]) for server in self.available_tools.values())
            })
        except Exception as e:
            return jsonify({
                "status": "error",
                "error": f"Failed to refresh: {str(e)}"
            }), 500
    
    def run(self):
        """Run the Flask application."""
        self.logger.info(f"🚀 Starting Dynamic MCP Client on port {self.config['server_port']}")
        self.app.run(
            host="0.0.0.0",
            port=self.config['server_port'],
            debug=False,
            threaded=True
        )

if __name__ == "__main__":
    mcp_host = DynamicMCPHost()
    
    # Initialize in a separate thread
    init_thread = threading.Thread(target=mcp_host.initialize, daemon=True)
    init_thread.start()
    init_thread.join()
    
    # Start the Flask app
    mcp_host.run()