"""
Document Processor Module
Handles text extraction and chunking strategies
"""
import re
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class DocumentProcessor:
    """
    Processes documents by extracting text and chunking it.
    """

    def __init__(self, chunk_size: int = 2048, chunk_overlap: int = 512):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        logger.info(
            f"DocumentProcessor initialized with chunk_size={chunk_size}, overlap={chunk_overlap}"
        )

    def extract_text(self, content: bytes, file_type: str) -> str:
        try:
            if file_type == '.txt':
                return self._extract_from_txt(content)
            elif file_type == '.pdf':
                return self._extract_from_pdf(content)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")
        except Exception as e:
            logger.error(f"Error extracting text: {str(e)}")
            raise

    def _extract_from_txt(self, content: bytes) -> str:
        try:
            try:
                text = content.decode("utf-8")
            except UnicodeDecodeError:
                text = content.decode("latin-1")
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting text from TXT: {str(e)}")
            raise

    def _extract_from_pdf(self, content: bytes) -> str:
        """Extract text from PDF file using pypdf"""
        try:
            import io
            from pypdf import PdfReader
        except ImportError:
            logger.error("pypdf not installed. PDF text extraction skipped.")
            return ""

        try:
            pdf_file = io.BytesIO(content)
            reader = PdfReader(pdf_file)

            text_parts = []
            for page_num, page in enumerate(reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text and page_text.strip():
                        text_parts.append(page_text)
                except Exception as e:
                    logger.warning(
                        f"Error extracting text from page {page_num}: {str(e)}"
                    )

            return "\n\n".join(text_parts).strip()

        except Exception as e:
            logger.error(f"Error extracting text from PDF: {str(e)}")
            return ""

    def chunk_text(self, text: str, document_id: str, filename: str) -> List[Dict]:
        text = self._clean_text(text)
        if not text:
            return []

        sentences = self._split_into_sentences(text)

        chunks = []
        current_chunk = []
        current_length = 0
        chunk_index = 0

        for sentence in sentences:
            sentence_length = len(sentence)

            if current_length + sentence_length > self.chunk_size and current_chunk:
                chunk_text = " ".join(current_chunk)
                chunks.append(
                    self._create_chunk_dict(
                        text=chunk_text,
                        document_id=document_id,
                        filename=filename,
                        chunk_index=chunk_index,
                    )
                )
                current_chunk = []
                current_length = 0
                chunk_index += 1

            current_chunk.append(sentence)
            current_length += sentence_length

        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append(
                self._create_chunk_dict(
                    text=chunk_text,
                    document_id=document_id,
                    filename=filename,
                    chunk_index=chunk_index,
                )
            )

        return chunks

    def _clean_text(self, text: str) -> str:
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"[^\w\s\.\,\!\?\;\:\-\(\)\[\]\{\}\"\'\/]", "", text)
        return text.strip()

    def _split_into_sentences(self, text: str) -> List[str]:
        sentences = re.split(r"[.!?]+\s+", text)
        return [s.strip() for s in sentences if s.strip()]

    def _create_chunk_dict(
        self, text: str, document_id: str, filename: str, chunk_index: int
    ) -> Dict:
        return {
            "text": text,
            "metadata": {
                "document_id": document_id,
                "filename": filename,
                "chunk_id": f"{document_id}_chunk_{chunk_index}",
                "chunk_index": chunk_index,
                "char_count": len(text),
                "word_count": len(text.split()),
            },
        }
