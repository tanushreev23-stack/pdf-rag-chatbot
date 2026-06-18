import fitz
import hashlib
import io
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from typing import List
from app.utils.logger import logger

try:
    import pytesseract
    from PIL import Image
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    OCR_AVAILABLE = True
    logger.info("OCR ready via Tesseract")
except ImportError:
    OCR_AVAILABLE = False
    logger.warning("pytesseract not installed — OCR disabled")

def extract_text_normal(page) -> str:
    """Extract text from normal text-based PDF pages"""
    try:
        text = page.get_text()
        return text
    except Exception as e:
        logger.warning(f"Normal text extraction failed: {e}")
        return ""

def extract_text_with_ocr(page) -> str:
    """Extract text from scanned/image-based PDF pages using OCR"""
    try:
        mat = fitz.Matrix(2.5, 2.5)  # Higher zoom = better OCR quality
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("png")
        img = Image.open(io.BytesIO(img_bytes))
        text = pytesseract.image_to_string(img, lang='eng')
        logger.info(f"OCR extracted {len(text)} characters from page")
        return text
    except Exception as e:
        logger.warning(f"OCR failed: {e}")
        return ""

def extract_documents(pdf_bytes: bytes, filename: str) -> List[Document]:
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        total_pages = len(doc)
        logger.info(f"Opened PDF: {filename} | Pages: {total_pages}")

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=800,
            chunk_overlap=100,
            separators=["\n\n", "\n", ".", " "]
        )

        doc_hash = hashlib.md5(pdf_bytes).hexdigest()
        documents = []
        text_pages = 0
        ocr_pages = 0

        for page_num in range(total_pages):
            page = doc[page_num]

            # First try normal text extraction
            text = extract_text_normal(page)

            if text.strip():
                # Normal text-based page
                text_pages += 1
                logger.info(f"Page {page_num + 1}: text-based ✓")
            else:
                # No text found — try OCR for scanned/image page
                logger.warning(f"Page {page_num + 1}: no text — trying OCR")
                if OCR_AVAILABLE:
                    text = extract_text_with_ocr(page)
                    if text.strip():
                        ocr_pages += 1
                        logger.info(f"Page {page_num + 1}: OCR success ✓")
                    else:
                        logger.warning(f"Page {page_num + 1}: OCR found nothing — skipping")
                        continue
                else:
                    logger.warning(f"Page {page_num + 1}: OCR not available — skipping")
                    continue

            # Split text into chunks
            chunks = splitter.split_text(text)
            for i, chunk in enumerate(chunks):
                if len(chunk.strip()) < 20:
                    continue
                documents.append(Document(
                    page_content=chunk,
                    metadata={
                        "source": filename,
                        "page": page_num + 1,
                        "chunk_index": i,
                        "doc_hash": doc_hash,
                        "total_pages": total_pages,
                        "extraction_method": "ocr" if not page.get_text().strip() else "text"
                    }
                ))

        logger.info(f"Done | {len(documents)} chunks | {text_pages} text pages | {ocr_pages} OCR pages")
        return documents

    except Exception as e:
        logger.error(f"Failed to process PDF {filename}: {e}", exc_info=True)
        raise