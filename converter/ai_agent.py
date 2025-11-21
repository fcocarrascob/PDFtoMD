from openai import OpenAI
import base64
import io

import re

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

    def convert_page(self, image_bytes: bytes, page_num: int = 0) -> str:
        """
        Sends a page image to OpenAI and gets the Markdown transcription.
        """
        try:
            # Encode image to base64
            base64_image = base64.b64encode(image_bytes).decode('utf-8')
            
            # Dynamic instructions based on page number
            metadata_instruction = ""
            if page_num == 0:
                metadata_instruction = """
            0. METADATA (YAML FRONTMATTER):
               - Since this is the first page, analyze the content to extract metadata.
               - Output a YAML block at the VERY TOP of the response.
               - Fields: title, type (e.g., Manual, Standard, Paper), chapter (if applicable), tags (list of keywords).
               - Format:
                 ---
                 title: "Document Title"
                 type: "Document Type"
                 tags: [tag1, tag2]
                 ---
            """

            prompt = f"""
            You are an expert document digitizer. 
            Transcribe this document page into clean Markdown.
            
            Rules:
            {metadata_instruction}
            1. CLEANING:
               - IGNORE page headers and footers (e.g., page numbers, repeated chapter titles, dates).
               - Do not transcribe them. Keep only the main content.
            2. Use standard Markdown formatting.
            3. Represent tables using Markdown table syntax.
            4. MATHEMATICAL EQUATIONS:
               - STRICTLY use $ for inline math (e.g., $E=mc^2$).
               - STRICTLY use $$ for block math (e.g., $$ E=mc^2 $$).
               - Do NOT use \\( ... \\) or \\[ ... \\].
               - Pay close attention to SUBSCRIPTS and SUPERSCRIPTS. Ensure no terms are omitted.
               - VARIABLE DEFINITIONS: If an equation is presented with undefined variables in the immediate context, explicitly list the variable definitions below the equation as a bulleted list (e.g., "- $E$: Energy").
            5. IMAGES AND FIGURES:
               - Do NOT try to insert images using markdown syntax (like ![...](...)). 
               - Instead, provide a detailed description of the image, chart, or diagram in the following format:
                 > [IMAGE DESCRIPTION: A detailed description of what the image shows...]
            6. Do not add any introductory or concluding remarks. Just the content.
            7. If the image is blank or unreadable, return an empty string.
            8. IMPORTANT: Do NOT wrap the output in a markdown code block (i.e., do NOT use ```markdown ... ```). Return raw markdown text.
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
            
            # Post-processing: Fix LaTeX delimiters
            # Replace \[ ... \] with $$ ... $$
            content = re.sub(r'\\\[(.*?)\\\]', r'$$\1$$', content, flags=re.DOTALL)
            # Replace \( ... \) with $ ... $
            content = re.sub(r'\\\((.*?)\\\)', r'$\1$', content, flags=re.DOTALL)
                
            return content.strip()
        except Exception as e:
            return f"<!-- AI Error: {str(e)} -->"
