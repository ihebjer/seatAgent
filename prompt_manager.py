import os
from jinja2 import Environment, FileSystemLoader

class PromptManager:
    def __init__(self):
        # Set up Jinja2 environment
        template_dir = os.path.join(os.path.dirname(__file__), "prompts")
        self.env = Environment(loader=FileSystemLoader(template_dir))
        
    def get_system_prompt(self, current_metadata, tools_description):
        template = self.env.get_template("system_prompt.jinja2")
        return template.render(
            current_metadata=current_metadata,
            tools_description=tools_description
        )
        
    def get_final_response_prompt(self, user_query, tool_result, reasoning):
        template = self.env.get_template("final_response.jinja2")
        return template.render(
            user_query=user_query,
            tool_result=tool_result,
            reasoning=reasoning
        )