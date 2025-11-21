import pymupdf4llm
import pathlib
import fitz # PyMuPDF
from converter.ai_agent import AIAgent

class PDFConverter:
    def convert(self, pdf_path: str, output_path: str = None, progress_callback=None, ai_api_key: str = None, ai_model: str = 'gpt-4o') -> str:
        """
        Converts a PDF file to Markdown.
        If ai_api_key is provided, uses AI Agent for conversion.
        Otherwise, uses pymupdf4llm.
        """
        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            md_text = ""
            
            ai_agent = None
            if ai_api_key:
                ai_agent = AIAgent(ai_api_key, model_name=ai_model)
            
            for i in range(total_pages):
                if ai_agent:
                    # AI Mode: Get page as image
                    page = doc.load_page(i)
                    pix = page.get_pixmap()
                    img_bytes = pix.tobytes("png")
                    
                    page_md = ai_agent.convert_page(img_bytes)
                    md_text += f"## Page {i+1}\n\n{page_md}\n\n"
                else:
                    # Local Mode
                    page_md = pymupdf4llm.to_markdown(doc, pages=[i])
                    md_text += page_md + "\n\n"
                
                if progress_callback:
                    progress = int((i + 1) / total_pages * 100)
                    progress_callback(progress)
            
            doc.close()
            
            # Determine output path if not provided
            if output_path is None:
                pdf_path_obj = pathlib.Path(pdf_path)
                output_path = pdf_path_obj.with_suffix('.md')
            
            # Save the file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(md_text)
                
            return f"Success! Saved to: {output_path}"
        except Exception as e:
            raise e
