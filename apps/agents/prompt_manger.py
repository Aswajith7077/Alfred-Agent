from jinja2 import Environment
from jinja2 import FileSystemLoader
from pathlib import Path
from text_to_speech import Voice
from typing import Dict
from typing import Optional


class PromptManager:
    def __init__(self, templates_dir: str):

        self.templates_path = Path(templates_dir)
        if not self.templates_path.exists():
            raise FileNotFoundError(f"Directory: {templates_dir} Cannot be located.")

        path_string = str(self.templates_path)
        self.environment = Environment(loader=FileSystemLoader(path_string))

    def get_system_prompt(self, voice: Voice, data: Optional[Dict] = None):

        if data is None:
            data = {}

        template_name = f"system_prompts/{voice.name}.jinja2"
        template = self.environment.get_template(template_name)
        prompt = template.render(data)

        return prompt
