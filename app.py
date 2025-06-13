import os
import threading
import logging
import urllib3
import yaml
import requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage
from utils.metadata_handler import MetadataHandler
import time
import json

# === Initialization ===
load_dotenv()
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

parent_folder = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
config_path = os.path.join(parent_folder, "MCP", "config.yaml")
with open(config_path, 'r') as file:
    config = yaml.safe_load(file)

config.update({
    "server_port": config["server"]["port"],
    "motor_mcp_host": "http://localhost:5051",
    "knowledge_mcp_host": "http://localhost:5052",
    "metadata_path": os.path.abspath(config["metadata"])
})

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class DynamicMCPClient:
    def __init__(self, config):
        self.config = config
        self.llm = None
        self.metadata_handler = None
        self.cached_metadata = None
        self.last_metadata_update = 0
        self.available_tools = {}
        self.mcp_servers = {
            "motor": config["motor_mcp_host"],
            "knowledge": config["knowledge_mcp_host"]
        }

    def initialize(self):
        """Initialize the LLM and metadata handler"""
        logging.info("Initializing Dynamic MCP Client...")
        try:
            self.llm = ChatOpenAI(
                model="gpt-4o",
                openai_api_key=os.getenv("OPENAI_API_KEY"),
                temperature=0.1
            )
            self.metadata_handler = MetadataHandler(self.config["metadata_path"])
            self.refresh_metadata_cache()
            self.discover_tools()
            logging.info("✅ Dynamic MCP Client ready!")
        except Exception as e:
            logging.error(f"Failed to initialize client: {str(e)}")
            raise

    def discover_tools(self):
        """Discover available tools from all MCP servers"""
        logging.info("🔍 Discovering available tools from MCP servers...")
        self.available_tools = {}
        
        for server_name, server_url in self.mcp_servers.items():
            try:
                # Get tools list from MCP server
                response = requests.get(f"{server_url}/mcp/tools")
                if response.status_code == 200:
                    tools_data = response.json()
                    self.available_tools[server_name] = {
                        "url": f"{server_url}/mcp/execute",
                        "tools": tools_data.get("tools", [])
                    }
                    logging.info(f"✅ Discovered {len(tools_data.get('tools', []))} tools from {server_name} server")
                else:
                    logging.warning(f"⚠️ Could not get tools from {server_name} server: {response.status_code}")
            except Exception as e:
                logging.error(f"❌ Error discovering tools from {server_name}: {str(e)}")

    def refresh_metadata_cache(self):
        """Refresh the metadata cache"""
        try:
            if self.metadata_handler:
                self.cached_metadata = self.metadata_handler.load_latest_metadata()
                if self.cached_metadata:
                    self.last_metadata_update = time.time()
                    logging.info("✅ Metadata cache refreshed")
        except Exception as e:
            logging.error(f"❌ Error refreshing metadata cache: {str(e)}")

    def get_current_metadata(self):
        """Get current driving metadata"""
        try:
            # Refresh cache if older than 5 seconds
            if time.time() - self.last_metadata_update > 5:
                self.refresh_metadata_cache()
            
            if self.cached_metadata:
                return self.metadata_handler.format_metadata_for_prompt(self.cached_metadata)
            return "Metadata unavailable"
        except Exception as e:
            logging.warning(f"Could not retrieve metadata: {e}")
            return "Metadata unavailable"

    def create_tools_description(self):
        """Create a description of all available tools for the LLM"""
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
        """Create system prompt with current metadata and available tools"""
        current_metadata = self.get_current_metadata()
        tools_description = self.create_tools_description()
        
        return f"""You are an intelligent car seat assistant with access to MCP (Model Context Protocol) tools.

CURRENT VEHICLE STATE:
{current_metadata}

{tools_description}

Your responsibilities:
1. Analyze the user's request and current vehicle state
2. Choose the most appropriate tool(s) to fulfill the request
3. Generate proper tool calls with correct parameters
4. Provide helpful responses based on tool results

Guidelines:
- For seat adjustments, use individual motor controls or preset experiences
- For knowledge queries, use the RAG system (get_knowledge tool)
- For thermal/ventilation, use the appropriate adjustment tools
- Always consider current motor positions when making adjustments
- Provide clear, conversational responses

When you decide to use a tool, respond with a JSON object containing:
{{
    "action": "call_tool",
    "server": "motor" or "knowledge",
    "tool": "tool_name",
    "args": {{parameter_name: value}},
    "reasoning": "Why you chose this tool"
}}

If no tool is needed, respond with:
{{
    "action": "direct_response",
    "response": "Your direct response to the user"
}}
"""

    def send_mcp_command(self, server_name, tool_name, args):
        """Send command to specified MCP server"""
        try:
            if server_name not in self.available_tools:
                return 400, {"error": f"Server {server_name} not available"}
            
            server_url = self.available_tools[server_name]["url"]
            payload = {
                "tool": tool_name,
                "args": args
            }
            
            logging.info(f"Sending to {server_name}: {tool_name} with args {args}")
            response = requests.post(server_url, json=payload)
            return response.status_code, response.json()
        except Exception as e:
            logging.error(f"Failed to call MCP server {server_name}: {str(e)}")
            return 500, {"error": f"Failed to reach {server_name} server"}

    def process_query(self, user_query):
        """Process user query using LLM and MCP tools"""
        try:
            system_prompt = self.create_system_prompt()
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_query)
            ]
            
            # Get LLM decision
            llm_response = self.llm.invoke(messages)
            decision_text = llm_response.content.strip()
            
            logging.info(f"LLM Decision: {decision_text}")
            
            try:
                # Try to parse as JSON
                decision = json.loads(decision_text)
            except json.JSONDecodeError:
                # If not JSON, treat as direct response
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
            
            elif decision.get("action") == "call_tool":
                server_name = decision.get("server")
                tool_name = decision.get("tool")
                args = decision.get("args", {})
                reasoning = decision.get("reasoning", "")
                
                # Execute the tool
                status_code, tool_result = self.send_mcp_command(server_name, tool_name, args)
                
                if status_code == 200:
                    # Generate final response based on tool result
                    final_response = self.generate_final_response(user_query, tool_result, reasoning)
                    
                    return {
                        "status": "success",
                        "response": final_response,
                        "tool_used": f"{server_name}.{tool_name}",
                        "tool_result": tool_result,
                        "metadata": self.get_current_metadata()
                    }, 200
                else:
                    return {
                        "status": "error",
                        "error": f"Tool execution failed: {tool_result}",
                        "metadata": self.get_current_metadata()
                    }, status_code
            
            else:
                return {
                    "status": "error",
                    "error": "Invalid action from LLM",
                    "metadata": self.get_current_metadata()
                }, 400
                
        except Exception as e:
            logging.error(f"Error processing query: {str(e)}")
            return {
                "status": "error",
                "error": f"Failed to process query: {str(e)}"
            }, 500

    def generate_final_response(self, user_query, tool_result, reasoning):
        """Generate a natural language response based on tool results"""
        try:
            context_prompt = f"""
Based on this tool execution:
- User asked: "{user_query}"
- Tool reasoning: {reasoning}
- Tool result: {json.dumps(tool_result, indent=2)}

Generate a natural, conversational response that:
1. Confirms what action was taken
2. Explains the result in user-friendly terms
3. Mentions any relevant current state information
4. Is helpful and concise

Respond as if you're a helpful car assistant talking directly to the driver.
"""
            
            response = self.llm.invoke([HumanMessage(content=context_prompt)])
            return response.content.strip()
            
        except Exception as e:
            logging.error(f"Error generating final response: {str(e)}")
            return f"Action completed. Tool result: {tool_result}"

# Initialize the client
client = DynamicMCPClient(config)
app = Flask(__name__)

@app.route("/query", methods=["POST"])
def query_endpoint():
    """Main query endpoint"""
    data = request.json
    user_query = data.get("query", "").strip()
    
    if not user_query:
        return jsonify({"error": "No query provided"}), 400
    
    response, status_code = client.process_query(user_query)
    return jsonify(response), status_code

@app.route("/tools", methods=["GET"])
def get_available_tools():
    """Get list of available tools from all servers"""
    return jsonify({
        "status": "success",
        "servers": client.available_tools
    })

@app.route("/metadata", methods=["GET"])
def get_metadata():
    """Get current driving metadata"""
    return jsonify({
        "status": "success",
        "metadata": client.get_current_metadata(),
        "raw_metadata": client.cached_metadata
    })

@app.route("/refresh", methods=["POST"])
def refresh_tools():
    """Refresh available tools from MCP servers"""
    try:
        client.discover_tools()
        client.refresh_metadata_cache()
        return jsonify({
            "status": "success",
            "message": "Tools and metadata refreshed",
            "tools_count": sum(len(server["tools"]) for server in client.available_tools.values())
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "error": f"Failed to refresh: {str(e)}"
        }), 500

def run_app():
    """Run the Flask application"""
    logging.info(f"🚀 Starting Dynamic MCP Client on port {config['server_port']}")
    app.run(host="0.0.0.0", port=config['server_port'], debug=False, threaded=True)

if __name__ == "__main__":
    # Initialize in a separate thread
    init_thread = threading.Thread(target=client.initialize, daemon=True)
    init_thread.start()
    
    # Wait a moment for initialization
    time.sleep(2)
    
    # Start the Flask app
    run_app()