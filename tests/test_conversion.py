import sys
import os
import fitz # PyMuPDF
import pathlib

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from converter.engine import PDFConverter

def create_test_pdf(filename):
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "Hello World! This is a test PDF.", fontsize=20)
    page.insert_text((50, 100), "Table test:", fontsize=14)
    
    # Simple table simulation (just text for now as pymupdf creation is low level)
    page.insert_text((50, 130), "Col1   Col2", fontsize=12)
    page.insert_text((50, 150), "Val1   Val2", fontsize=12)
    
    doc.save(filename)
    doc.close()
    return filename

def test_conversion():
    pdf_path = "test_doc.pdf"
    try:
        # 1. Create PDF
        create_test_pdf(pdf_path)
        print(f"Created {pdf_path}")
        
        # 2. Convert
        converter = PDFConverter()
        result = converter.convert(pdf_path)
        print(result)
        
        # 3. Verify
        md_path = "test_doc.md"
        if os.path.exists(md_path):
            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()
            print("Markdown content preview:")
            print(content[:200])
            
            if "Hello World" in content:
                print("TEST PASSED: Content found.")
            else:
                print("TEST FAILED: Content not found.")
        else:
            print("TEST FAILED: Output file not found.")
            
    except Exception as e:
        print(f"TEST FAILED: Exception {e}")
    finally:
        # Cleanup
        if os.path.exists(pdf_path):
            os.remove(pdf_path)
        if os.path.exists("test_doc.md"):
            os.remove("test_doc.md")

if __name__ == "__main__":
    test_conversion()
