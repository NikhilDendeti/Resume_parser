import fitz  # PyMuPDF
import docx
import mammoth
import magic
import io
from PIL import Image
import paddleocr
import aiofiles
import asyncio
from typing import Tuple, Optional

class TextExtractor:
    def __init__(self):
        self.ocr = paddleocr.PaddleOCR(use_angle_cls=True, lang='en')
    
    async def extract_text(self, file_content: bytes, filename: str) -> Tuple[str, str]:
        """Extract text from various file formats"""
        try:
            file_type = self._detect_file_type(file_content, filename)
            
            if file_type == 'pdf':
                return await self._extract_from_pdf(file_content)
            elif file_type in ['docx', 'doc']:
                return await self._extract_from_docx(file_content)
            elif file_type in ['png', 'jpg', 'jpeg']:
                return await self._extract_from_image(file_content)
            elif file_type == 'txt':
                return file_content.decode('utf-8', errors='ignore'), 'text'
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
                
        except Exception as e:
            raise Exception(f"Text extraction failed: {str(e)}")
    
    def _detect_file_type(self, file_content: bytes, filename: str) -> str:
        """Detect file type using python-magic and filename"""
        try:
            mime_type = magic.from_buffer(file_content, mime=True)
            
            if mime_type == 'application/pdf':
                return 'pdf'
            elif mime_type in ['application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
                return 'docx'
            elif mime_type in ['application/msword']:
                return 'doc'
            elif mime_type.startswith('image/'):
                return filename.split('.')[-1].lower()
            elif mime_type == 'text/plain':
                return 'txt'
            else:
                # Fallback to filename extension
                return filename.split('.')[-1].lower()
        except:
            return filename.split('.')[-1].lower()
    
    async def _extract_from_pdf(self, file_content: bytes) -> Tuple[str, str]:
        """Extract text from PDF using PyMuPDF"""
        try:
            doc = fitz.open(stream=file_content, filetype="pdf")
            text = ""
            has_text = False
            
            for page in doc:
                page_text = page.get_text()
                if page_text.strip():
                    text += page_text + "\n"
                    has_text = True
            
            doc.close()
            
            if not has_text or len(text.strip()) < 100:
                # Fallback to OCR for scanned PDFs
                return await self._extract_from_pdf_ocr(file_content)
            
            return text.strip(), 'pdf_text'
            
        except Exception as e:
            # Fallback to OCR
            return await self._extract_from_pdf_ocr(file_content)
    
    async def _extract_from_pdf_ocr(self, file_content: bytes) -> Tuple[str, str]:
        """Extract text from PDF using OCR"""
        try:
            doc = fitz.open(stream=file_content, filetype="pdf")
            text = ""
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                pix = page.get_pixmap()
                img_data = pix.tobytes("png")
                
                # Run OCR in thread pool to avoid blocking
                ocr_result = await asyncio.get_event_loop().run_in_executor(
                    None, self._run_ocr, img_data
                )
                text += ocr_result + "\n"
            
            doc.close()
            return text.strip(), 'pdf_ocr'
            
        except Exception as e:
            raise Exception(f"PDF OCR extraction failed: {str(e)}")
    
    async def _extract_from_docx(self, file_content: bytes) -> Tuple[str, str]:
        """Extract text from DOCX files"""
        try:
            # Try python-docx first
            doc = docx.Document(io.BytesIO(file_content))
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            if text.strip():
                return text.strip(), 'docx'
            
            # Fallback to mammoth for better formatting
            with io.BytesIO(file_content) as docx_file:
                result = mammoth.extract_raw_text(docx_file)
                return result.value.strip(), 'docx_mammoth'
                
        except Exception as e:
            raise Exception(f"DOCX extraction failed: {str(e)}")
    
    async def _extract_from_image(self, file_content: bytes) -> Tuple[str, str]:
        """Extract text from image using OCR"""
        try:
            # Run OCR in thread pool
            text = await asyncio.get_event_loop().run_in_executor(
                None, self._run_ocr, file_content
            )
            return text.strip(), 'image_ocr'
            
        except Exception as e:
            raise Exception(f"Image OCR extraction failed: {str(e)}")
    
    def _run_ocr(self, image_data: bytes) -> str:
        """Run OCR on image data"""
        try:
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # Run PaddleOCR
            result = self.ocr.ocr(image_data)
            
            # Extract text from OCR result
            text = ""
            if result and result[0]:
                for line in result[0]:
                    if len(line) > 1:
                        text += line[1][0] + "\n"
            
            return text
        except Exception as e:
            return f"OCR failed: {str(e)}"