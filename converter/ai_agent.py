from openai import OpenAI
import base64
import io

class AIAgent:
    def __init__(self, api_key: str, model_name: str = 'gpt-4o'):
        self.api_key = api_key
        self.client = OpenAI(api_key=self.api_key)
        self.model_name = model_name

    def validate_key(self) -> bool:
        """
        Checks if the API key is valid by listing models.
        """
        try:
            self.client.models.list()
            return True, "API Key is valid."
        except Exception as e:
            return False, str(e)

    def convert_page(self, image_bytes: bytes) -> str:
        """
        Sends a page image to OpenAI and gets the Markdown transcription.
        """
        try:
            # Encode image to base64
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            
            prompt = """
            You are an expert document digitizer. 
            Transcribe this document page into clean Markdown.
            
            Rules:
            1. Use standard Markdown formatting.
            2. Represent tables using Markdown table syntax.
            3. If there are mathematical equations, transcribe them into LaTeX format enclosed in $ for inline and $$ for block.
            4. Do not add any introductory or concluding remarks. Just the content.
            5. If the image is blank or unreadable, return an empty string.
            6. IMPORTANT: Do NOT wrap the output in a markdown code block (i.e., do NOT use ```markdown ... ```). Return raw markdown text.
            """
            
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=4096
            )
            
            content = response.choices[0].message.content
            
            # Post-processing to remove potential markdown code blocks
            if content.startswith("```markdown"):
                content = content.replace("```markdown", "", 1)
            elif content.startswith("```"):
                content = content.replace("```", "", 1)
                
            if content.endswith("```"):
                content = content[:-3]
                
            return content.strip()
        except Exception as e:
            return f"<!-- AI Error: {str(e)} -->"
