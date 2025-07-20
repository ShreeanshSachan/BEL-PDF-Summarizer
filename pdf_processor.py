import os
import io
import PyPDF2
import re
from PySide6.QtCore import Signal, QObject

# --- Helper Functions for Token Estimation ---
def count_words(text):
    """
    Counts words in a given text string more accurately by splitting and counting.
    """
    return len(text.split())

def estimate_tokens(text):
    """
    Estimates the number of tokens from a given text.
    Uses a common heuristic: 1 word ≈ 1.3 tokens for English text.
    """
    word_count = count_words(text)
    return int(word_count * 1.3)

def estimate_words_from_tokens(tokens):
    """
    Converts an estimated token count back to an approximate word count.
    Inverse of the estimate_tokens heuristic.
    """
    return int(tokens / 1.3)

# --- PDF Text Extraction with Validation ---
class PdfTextExtractor(QObject):
    """
    Worker class to extract text from a PDF file in a separate thread.
    Includes comprehensive validation steps to ensure the PDF is suitable for processing.
    """
    finished = Signal(str, str)  # Emits (filename, extracted_text) upon successful extraction
    error = Signal(str)          # Emits error message for general processing failures
    progress = Signal(int)       # Emits integer (0-100) for progress updates
    validation_failed = Signal(str) # Emits detailed message when validation fails

    def __init__(self, file_path):
        """
        Initializes the PdfTextExtractor with the path to the PDF file.
        Defines minimum requirements for PDF content.
        """
        super().__init__()
        self.file_path = file_path
        self.MIN_WORDS = 500  # Minimum words required in the entire PDF for summarization
        self.MIN_PAGES = 1    # Minimum pages required in the PDF
        self.MAX_EMPTY_PAGES_RATIO = 0.7 # Maximum allowed ratio of empty pages (70%)

    def run(self):
        """
        Main execution method for the worker thread.
        Performs sequential validation and text extraction.
        """
        try:
            # Step 1: Validate file extension to ensure it's a PDF
            if not self._validate_file_extension():
                return
            
            # Step 2: Validate file size and basic readability/accessibility
            if not self._validate_file_size():
                return
            
            # Step 3: Read PDF content into a BytesIO object for PyPDF2
            with open(self.file_path, 'rb') as file:
                pdf_content = file.read()
            
            pdf_file = io.BytesIO(pdf_content)
            reader = PyPDF2.PdfReader(pdf_file)
            
            # Step 4: Validate PDF structure (e.g., page count, encryption)
            if not self._validate_pdf_structure(reader):
                return
            
            # Step 5: Extract text from pages and gather extraction statistics
            text, extraction_stats = self._extract_and_validate_text(reader)
            
            # Step 6: Perform final validation on the extracted text content
            if not self._validate_extracted_text(text, extraction_stats):
                return
            
            # If all validations pass and text is extracted, emit the finished signal
            self.finished.emit(os.path.basename(self.file_path), text.strip())
            
        except PyPDF2.errors.PdfReadError:
            # Catch specific PyPDF2 errors for invalid or corrupted PDFs
            self.validation_failed.emit("Invalid PDF file or corrupted content. Please ensure the file is a valid PDF.")
        except Exception as e:
            # Catch any other unexpected errors during processing
            self.validation_failed.emit(f"Error processing PDF: {str(e)}")

    def _validate_file_extension(self):
        """
        Validates that the selected file has a .pdf extension.
        """
        file_extension = os.path.splitext(self.file_path)[1].lower()
        if file_extension != '.pdf':
            self.validation_failed.emit(f"Invalid file format. Only PDF files are supported.\nFile type detected: {file_extension or 'Unknown'}")
            return False
        return True

    def _validate_file_size(self):
        """
        Validates the file size to prevent processing of empty or excessively large files.
        Checks if the file is accessible.
        """
        try:
            file_size = os.path.getsize(self.file_path)
            if file_size == 0:
                self.validation_failed.emit("File is empty. Please select a valid PDF file.")
                return False
            elif file_size < 1024:  # Less than 1KB
                self.validation_failed.emit("File is too small to contain meaningful content. Please select a larger PDF file.")
                return False
            elif file_size > 100 * 1024 * 1024:  # Larger than 100MB
                self.validation_failed.emit("File is too large (>100MB). Please select a smaller PDF file.")
                return False
            return True
        except Exception as e:
            self.validation_failed.emit(f"Cannot access file: {str(e)}")
            return False

    def _validate_pdf_structure(self, reader):
        """
        Validates the internal structure of the PDF, including page count and encryption status.
        """
        try:
            total_pages = len(reader.pages)
            
            if total_pages < self.MIN_PAGES:
                self.validation_failed.emit(f"PDF must have at least {self.MIN_PAGES} page(s). This PDF has {total_pages} page(s).")
                return False
            
            # Check if PDF is encrypted (PyPDF2 cannot extract text from encrypted PDFs without password)
            if reader.is_encrypted:
                self.validation_failed.emit("PDF is password-protected. Please provide an unencrypted PDF file.")
                return False
            
            return True
        except Exception as e:
            self.validation_failed.emit(f"Cannot read PDF structure: {str(e)}")
            return False

    def _extract_and_validate_text(self, reader):
        """
        Extracts text from each page of the PDF and gathers statistics about the extraction.
        Emits progress updates during extraction.
        """
        text = ""
        total_pages = len(reader.pages)
        extraction_stats = {
            'total_pages': total_pages,
            'pages_with_text': 0,
            'pages_with_substantial_text': 0, # Pages with more than minimal text (e.g., headers/footers)
            'empty_pages': 0,
            'total_characters': 0,
            'average_chars_per_page': 0
        }
        
        for page_num in range(total_pages):
            try:
                page = reader.pages[page_num]
                extracted = page.extract_text()
                
                if extracted and extracted.strip():
                    text += extracted + "\n\n" # Add double newline for paragraph separation
                    extraction_stats['pages_with_text'] += 1
                    
                    # Check for substantial text (more than just headers/footers/page numbers)
                    clean_text = re.sub(r'\s+', ' ', extracted.strip()) # Normalize whitespace
                    if len(clean_text) > 100:  # Arbitrary threshold for "substantial" text
                        extraction_stats['pages_with_substantial_text'] += 1
                else:
                    extraction_stats['empty_pages'] += 1
                    # print(f"WARNING: Page {page_num+1} contains no extractable text (may be scanned or image-only)")
                
                # Emit progress (80% of total progress for extraction phase)
                progress = int((page_num + 1) / total_pages * 80)
                self.progress.emit(progress)
                
            except Exception as e:
                # Log error for specific page but continue if possible
                print(f"Error extracting text from page {page_num+1}: {str(e)}")
                extraction_stats['empty_pages'] += 1 # Treat as empty if extraction fails
        
        extraction_stats['total_characters'] = len(text)
        extraction_stats['average_chars_per_page'] = extraction_stats['total_characters'] / total_pages if total_pages > 0 else 0
        
        return text, extraction_stats

    def _validate_extracted_text(self, text, stats):
        """
        Performs final validation on the aggregated extracted text and statistics.
        Ensures the content is sufficient and meaningful for summarization.
        """
        self.progress.emit(85) # Update progress after extraction, before final validation
        
        # Check for completely empty document after extraction attempts
        if not text or not text.strip():
            self.validation_failed.emit("No text could be extracted from this PDF. The file may contain only images or scanned content without OCR.")
            return False
        
        # Check minimum word count in the extracted text
        word_count = len(text.split())
        if word_count < self.MIN_WORDS:
            self.validation_failed.emit(f"PDF contains insufficient text for summarization.\nMinimum required: {self.MIN_WORDS} words\nFound: {word_count} words")
            return False
        
        # Check ratio of empty pages to total pages
        empty_page_ratio = stats['empty_pages'] / stats['total_pages']
        if empty_page_ratio > self.MAX_EMPTY_PAGES_RATIO:
            self.validation_failed.emit(f"Too many pages without text ({stats['empty_pages']}/{stats['total_pages']} pages are empty).\nThis PDF may contain primarily images or scanned content.")
            return False
        
        # Ensure there's at least some substantial content, not just sparse text
        if stats['pages_with_substantial_text'] == 0 and stats['total_pages'] > 0:
            self.validation_failed.emit("No pages contain substantial text content. The PDF may contain only headers, footers, or minimal text.")
            return False
        
        # Check average characters per page to catch PDFs with very little actual content
        if stats['average_chars_per_page'] < 200 and stats['total_pages'] > 0: # Arbitrary threshold
            self.validation_failed.emit(f"Average text per page is too low ({stats['average_chars_per_page']:.0f} characters/page).\nThis suggests the PDF contains primarily non-text content.")
            return False
        
        self.progress.emit(100) # Full progress upon successful validation
        return True

