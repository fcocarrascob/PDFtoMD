import pymupdf4llm
import pathlib
import fitz # PyMuPDF
from converter.ai_agent import AIAgent
import re

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
            
            # Try to detect start page from filename (e.g., "..._Start51.pdf")
            match = re.search(r"_Start(\d+)", pathlib.Path(pdf_path).stem)
            start_offset = int(match.group(1)) - 1 if match else 0
            
            ai_agent = None
            if ai_api_key:
                ai_agent = AIAgent(ai_api_key, model_name=ai_model)
            
            for i in range(total_pages):
                current_page_global = i + start_offset
                
                if ai_agent:
                    # AI Mode: Get page as image
                    page = doc.load_page(i)
                    # Increase resolution (zoom x2) for better equation detection
                    matrix = fitz.Matrix(2, 2)
                    pix = page.get_pixmap(matrix=matrix)
                    img_bytes = pix.tobytes("png")
                    
                    page_md = ai_agent.convert_page(img_bytes, page_num=current_page_global)
                    md_text += f"## Page {current_page_global + 1}\n\n{page_md}\n\n"
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

    def split_pdf(self, pdf_path: str, pages_per_chunk: int = 50) -> list[str]:
        """
        Splits a PDF into chunks of specified pages.
        Returns a list of paths to the created chunks.
        """
        try:
            doc = fitz.open(pdf_path)
            total_pages = len(doc)
            created_files = []
            
            pdf_path_obj = pathlib.Path(pdf_path)
            base_name = pdf_path_obj.stem
            parent_dir = pdf_path_obj.parent
            
            for i in range(0, total_pages, pages_per_chunk):
                start_page = i
                end_page = min(i + pages_per_chunk, total_pages)
                
                # Create new PDF for this chunk
                new_doc = fitz.open()
                new_doc.insert_pdf(doc, from_page=start_page, to_page=end_page - 1)
                
                chunk_name = f"{base_name}_Part{i//pages_per_chunk + 1}_Start{start_page + 1}.pdf"
                chunk_path = parent_dir / chunk_name
                
                new_doc.save(chunk_path)
                new_doc.close()
                created_files.append(str(chunk_path))
                
            doc.close()
            return created_files
        except Exception as e:
            raise e
