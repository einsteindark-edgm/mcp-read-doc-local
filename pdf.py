"""PDF loader with validation and text extraction."""
import asyncio
import os
from pathlib import Path
from typing import List

import pdfplumber
from dotenv import load_dotenv

from app.exceptions import DocumentLoadError, ValidationError

# Load environment variables
load_dotenv()


class PDFLoader:
    """Handles PDF loading and text extraction."""
    
    def __init__(self):
        """Initialize the PDF loader with configuration."""
        self.max_size_kb = int(os.getenv("MAX_PDF_SIZE_KB", "350"))
        self.pdf_dir = Path(os.getenv("PDF_DIR", "./data/pdfs"))
    
    async def load_pdf(self, filename: str) -> str:
        """Load PDF and extract text asynchronously.
        
        Args:
            filename: PDF filename (without path)
            
        Returns:
            Extracted text from all pages
            
        Raises:
            ValidationError: If filename is invalid or file is too large
            DocumentLoadError: If PDF file doesn't exist or cannot be read
        """
        # Validate filename (no path traversal)
        if "/" in filename or "\\" in filename:
            raise ValidationError("Invalid filename - path traversal not allowed")
        
        # Check file exists
        pdf_path = self.pdf_dir / filename
        if not pdf_path.exists():
            raise DocumentLoadError(f"PDF not found: {filename}")
        
        # Validate file has .pdf extension
        if not pdf_path.suffix.lower() == ".pdf":
            raise ValidationError(f"File must be a PDF: {filename}")
        
        # Validate size
        size_kb = pdf_path.stat().st_size / 1024
        if size_kb > self.max_size_kb:
            raise ValidationError(
                f"PDF too large: {size_kb:.1f}KB > {self.max_size_kb}KB"
            )
        
        # Extract text in thread (pdfplumber is sync)
        def extract_sync() -> str:
            """Synchronous text extraction from PDF."""
            try:
                with pdfplumber.open(pdf_path) as pdf:
                    pages_text = []
                    for page in pdf.pages:
                        if text := page.extract_text():
                            pages_text.append(text)
                    
                    if not pages_text:
                        raise DocumentLoadError(
                            f"No text content found in PDF: {filename}"
                        )
                    
                    return "\n\n".join(pages_text)
            except Exception as e:
                raise DocumentLoadError(
                    f"Failed to read PDF {filename}: {str(e)}"
                ) from e
        
        return await asyncio.to_thread(extract_sync)
    
    async def list_available_pdfs(self) -> List[str]:
        """List all available PDF files in the configured directory.
        
        Returns:
            List of PDF filenames
        """
        if not self.pdf_dir.exists():
            return []
        
        pdf_files = [f.name for f in self.pdf_dir.glob("*.pdf") if f.is_file()]
        return sorted(pdf_files)