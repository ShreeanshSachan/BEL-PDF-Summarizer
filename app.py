# app.py

import sys
import os
import io
import PyPDF2
import replicate
import threading
import re
from config import REPLICATE_API_TOKEN, GPT_NANO_MODEL 

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QPushButton, QTextEdit, QRadioButton, QComboBox,
    QButtonGroup, QFileDialog, QMessageBox, QFrame, QSizePolicy, QProgressBar
)
from PySide6.QtCore import Qt, Signal, QObject, QThread

# --- Replicate API Configuration ---


# Fixed model
GPT_NANO_MODEL = "openai/gpt-4.1-nano"

# --- Enhanced Token Estimation ---
def count_words(text):
    """Count words more accurately"""
    return len(text.split())

def estimate_tokens(text):
    """Improved token estimation"""
    word_count = count_words(text)
    # More accurate token estimation: 1 word ≈ 1.3 tokens for English
    return int(word_count * 1.3)

def estimate_words_from_tokens(tokens):
    """Convert tokens back to word estimate"""
    return int(tokens / 1.3)

# --- PDF Text Extraction with Validation ---
class PdfTextExtractor(QObject):
    """Worker to extract text from PDF in a separate thread with comprehensive validation."""
    finished = Signal(str, str)  # Emits (filename, extracted_text)
    error = Signal(str)          # Emits error message
    progress = Signal(int)       # Progress updates
    validation_failed = Signal(str)  # Emits validation failure message

    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path
        self.MIN_WORDS = 500
        self.MIN_PAGES = 1
        self.MAX_EMPTY_PAGES_RATIO = 0.7  # Allow up to 70% empty pages

    def run(self):
        try:
            # Step 1: Validate file extension
            if not self._validate_file_extension():
                return
            
            # Step 2: Validate file size and readability
            if not self._validate_file_size():
                return
            
            # Step 3: Extract and validate PDF content
            with open(self.file_path, 'rb') as file:
                pdf_content = file.read()
           
            pdf_file = io.BytesIO(pdf_content)
            reader = PyPDF2.PdfReader(pdf_file)
            
            # Step 4: Validate PDF structure
            if not self._validate_pdf_structure(reader):
                return
            
            # Step 5: Extract text with validation
            text, extraction_stats = self._extract_and_validate_text(reader)
            
            # Step 6: Final validation
            if not self._validate_extracted_text(text, extraction_stats):
                return
           
            self.finished.emit(os.path.basename(self.file_path), text.strip())
            
        except PyPDF2.errors.PdfReadError:
            self.validation_failed.emit("Invalid PDF file or corrupted content. Please ensure the file is a valid PDF.")
        except Exception as e:
            self.validation_failed.emit(f"Error processing PDF: {str(e)}")

    def _validate_file_extension(self):
        """Validate that the file has a PDF extension"""
        file_extension = os.path.splitext(self.file_path)[1].lower()
        if file_extension != '.pdf':
            self.validation_failed.emit(f"Invalid file format. Only PDF files are supported.\nFile type detected: {file_extension or 'Unknown'}")
            return False
        return True

    def _validate_file_size(self):
        """Validate file size is reasonable"""
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
        """Validate PDF structure and page count"""
        try:
            total_pages = len(reader.pages)
            
            if total_pages < self.MIN_PAGES:
                self.validation_failed.emit(f"PDF must have at least {self.MIN_PAGES} page(s). This PDF has {total_pages} page(s).")
                return False
            
            # Check if PDF is encrypted
            if reader.is_encrypted:
                self.validation_failed.emit("PDF is password-protected. Please provide an unencrypted PDF file.")
                return False
            
            return True
        except Exception as e:
            self.validation_failed.emit(f"Cannot read PDF structure: {str(e)}")
            return False

    def _extract_and_validate_text(self, reader):
        """Extract text and gather statistics"""
        text = ""
        total_pages = len(reader.pages)
        pages_with_text = 0
        empty_pages = 0
        extraction_stats = {
            'total_pages': total_pages,
            'pages_with_text': 0,
            'pages_with_substantial_text': 0,
            'empty_pages': 0,
            'total_characters': 0,
            'average_chars_per_page': 0
        }
        
        for page_num in range(total_pages):
            try:
                page = reader.pages[page_num]
                extracted = page.extract_text()
                
                if extracted and extracted.strip():
                    text += extracted + "\n\n"
                    pages_with_text += 1
                    extraction_stats['pages_with_text'] += 1
                    
                    # Check for substantial text (more than just headers/footers)
                    clean_text = re.sub(r'\s+', ' ', extracted.strip())
                    if len(clean_text) > 100:  # More than 100 characters
                        extraction_stats['pages_with_substantial_text'] += 1
                else:
                    empty_pages += 1
                    extraction_stats['empty_pages'] += 1
                    print(f"WARNING: Page {page_num+1} contains no extractable text (may be scanned or image-only)")
                
                # Emit progress
                progress = int((page_num + 1) / total_pages * 80)  # 80% for extraction
                self.progress.emit(progress)
                
            except Exception as e:
                print(f"Error extracting text from page {page_num+1}: {str(e)}")
                empty_pages += 1
                extraction_stats['empty_pages'] += 1
        
        extraction_stats['total_characters'] = len(text)
        extraction_stats['average_chars_per_page'] = extraction_stats['total_characters'] / total_pages if total_pages > 0 else 0
        
        return text, extraction_stats

    def _validate_extracted_text(self, text, stats):
        """Validate the extracted text meets minimum requirements"""
        self.progress.emit(85)
        
        # Check for completely empty document
        if not text or not text.strip():
            self.validation_failed.emit("No text could be extracted from this PDF. The file may contain only images or scanned content without OCR.")
            return False
        
        # Check minimum word count
        word_count = len(text.split())
        if word_count < self.MIN_WORDS:
            self.validation_failed.emit(f"PDF contains insufficient text for summarization.\nMinimum required: {self.MIN_WORDS} words\nFound: {word_count} words")
            return False
        
        # Check ratio of empty pages
        empty_page_ratio = stats['empty_pages'] / stats['total_pages']
        if empty_page_ratio > self.MAX_EMPTY_PAGES_RATIO:
            self.validation_failed.emit(f"Too many pages without text ({stats['empty_pages']}/{stats['total_pages']} pages are empty).\nThis PDF may contain primarily images or scanned content.")
            return False
        
        # Check for substantial content
        if stats['pages_with_substantial_text'] == 0:
            self.validation_failed.emit("No pages contain substantial text content. The PDF may contain only headers, footers, or minimal text.")
            return False
        
        # Check average characters per page
        if stats['average_chars_per_page'] < 200:
            self.validation_failed.emit(f"Average text per page is too low ({stats['average_chars_per_page']:.0f} characters/page).\nThis suggests the PDF contains primarily non-text content.")
            return False
        
        self.progress.emit(100)
        return True

# --- Enhanced Summarizer Worker ---
class ReplicateSummarizerWorker(QObject):
    """Enhanced worker for Replicate API with improved summarization logic."""
    finished = Signal(str)  # Emits the summary text
    error = Signal(str)     # Emits error message
    progress = Signal(int)  # Progress updates

    def __init__(self, text_to_summarize, summary_level, api_token):
        super().__init__()
        self.text_to_summarize = text_to_summarize
        self.summary_level = summary_level
        self.api_token = api_token

    def run(self):
        if not self.api_token or self.api_token == "YOUR_HARDCODED_REPLICATE_API_TOKEN_HERE":
            self.error.emit("Error: Replicate API Token is not correctly set.")
            return

        try:
            # Enhanced summary level configurations
            if self.summary_level == "low":  # Comprehensive
                target_words = 5000
                compression_ratio = 0.4
                detail_level = "extremely comprehensive and detailed"
                prompt_instruction = "Provide an extremely comprehensive, detailed, and thorough summary. Include all key arguments, evidence, examples, data points, and nuances. Maintain the depth and richness of the original content."
            elif self.summary_level == "medium":  # Balanced
                target_words = 2500
                compression_ratio = 0.25
                detail_level = "balanced and substantial"
                prompt_instruction = "Provide a balanced, substantial summary that covers all main points, key arguments, and important details while maintaining readability and flow."
            else:  # "high" - Concise
                target_words = 800
                compression_ratio = 0.15
                detail_level = "concise but complete"
                prompt_instruction = "Provide a concise summary focusing on the most critical points, main arguments, and key takeaways while ensuring completeness."

            # Calculate token targets
            target_tokens = int(target_words * 1.3)
            input_tokens = estimate_tokens(self.text_to_summarize)
            
            self.progress.emit(10)
            
            # Enhanced chunking strategy
            chunks = self._create_intelligent_chunks(self.text_to_summarize)
            self.progress.emit(20)
            
            # Process chunks with improved logic
            chunk_summaries = []
            for i, chunk in enumerate(chunks):
                summary = self._process_chunk(chunk, detail_level, prompt_instruction)
                chunk_summaries.append(summary)
                
                # Update progress
                progress = 20 + int((i + 1) / len(chunks) * 60)
                self.progress.emit(progress)
            
            self.progress.emit(80)
            
            # Final synthesis
            final_summary = self._synthesize_final_summary(
                chunk_summaries, 
                target_tokens, 
                detail_level, 
                prompt_instruction
            )
            
            self.progress.emit(100)
            self.finished.emit(final_summary)

        except Exception as e:
            self.error.emit(f"Summarization error: {str(e)}")

    def _create_intelligent_chunks(self, text):
        """Create chunks that preserve semantic coherence"""
        # Split by double newlines first (paragraphs)
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
        
        # If no clear paragraphs, split by sentences
        if len(paragraphs) <= 2:
            sentences = re.split(r'[.!?]+', text)
            paragraphs = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        current_chunk = []
        current_tokens = 0
        max_chunk_tokens = 8000  # Increased for better context
        
        for paragraph in paragraphs:
            paragraph_tokens = estimate_tokens(paragraph)
            
            if current_tokens + paragraph_tokens > max_chunk_tokens and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [paragraph]
                current_tokens = paragraph_tokens
            else:
                current_chunk.append(paragraph)
                current_tokens += paragraph_tokens
        
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks

    def _process_chunk(self, chunk, detail_level, prompt_instruction):
        """Process individual chunk with enhanced prompting"""
        client = replicate.Client(api_token=self.api_token)
        
        chunk_tokens = estimate_tokens(chunk)
        # Aim for 50% compression in intermediate summaries
        target_output_tokens = min(int(chunk_tokens * 0.5), 4000)
        
        system_prompt = f"""You are an expert summarizer specializing in creating {detail_level} summaries. 
        Your task is to process this text segment while preserving all important information, 
        key arguments, supporting evidence, and relevant details. This is part of a multi-stage 
        summarization process, so thoroughness is crucial."""
        
        prompt = f"""{prompt_instruction}
        
        Text to summarize:
        {chunk}
        
        Create a detailed summary that preserves the essence and important details of this section:"""
        
        try:
            output = client.run(
                GPT_NANO_MODEL,
                input={
                    "prompt": prompt,
                    "system_prompt": system_prompt,
                    "temperature": 0.3,  # Lower for more focused output
                    "top_p": 0.9,
                    "max_completion_tokens": target_output_tokens,
                    "presence_penalty": 0,
                    "frequency_penalty": 0.1
                }
            )
            return "".join(output)
        except Exception as e:
            return f"Error processing chunk: {str(e)}"

    def _synthesize_final_summary(self, chunk_summaries, target_tokens, detail_level, prompt_instruction):
        """Synthesize final summary from chunk summaries"""
        client = replicate.Client(api_token=self.api_token)
        
        combined_summaries = "\n\n=== SECTION ===\n\n".join(chunk_summaries)
        
        system_prompt = f"""You are a master synthesizer capable of creating {detail_level} summaries. 
        Your task is to integrate multiple detailed section summaries into one cohesive, 
        comprehensive final summary that flows naturally and maintains the depth of the original content."""
        
        final_prompt = f"""{prompt_instruction}
        
        Below are detailed summaries of different sections of a document. Your task is to synthesize 
        these into a single, cohesive, and comprehensive summary that:
        
        1. Maintains all key information and arguments
        2. Flows naturally as a unified document
        3. Eliminates redundancy while preserving important details
        4. Achieves approximately {estimate_words_from_tokens(target_tokens)} words
        
        Section Summaries:
        {combined_summaries}
        
        Create a comprehensive final summary:"""
        
        try:
            output = client.run(
                GPT_NANO_MODEL,
                input={
                    "prompt": final_prompt,
                    "system_prompt": system_prompt,
                    "temperature": 0.4,
                    "top_p": 0.95,
                    "max_completion_tokens": min(target_tokens, 16000),  # Increased max
                    "presence_penalty": 0,
                    "frequency_penalty": 0.1
                }
            )
            return "".join(output)
        except Exception as e:
            return f"Error in final synthesis: {str(e)}"

# --- Enhanced Main Application ---
class PdfSummarizerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BEL PDF Summarizer - Enhanced")
        self.setGeometry(100, 100, 1000, 800)

        self.extracted_pdf_text = ""
        self.current_filename = ""

        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        # Header
        header_label = QLabel("<b>Enhanced PDF Summarizer</b>")
        header_label.setAlignment(Qt.AlignCenter)
        header_label.setStyleSheet("font-size: 28px; color: #2c3e50; padding-bottom: 10px;")
        main_layout.addWidget(header_label)

        # Main content grid
        content_grid_layout = QGridLayout()
        content_grid_layout.setSpacing(15)
        main_layout.addLayout(content_grid_layout)

        row = 0

        # File Input Section with improved styling
        file_section_label = QLabel("<b>Choose PDF File:</b>")
        file_section_label.setStyleSheet("color: #2c3e50; font-size: 14px;")
        content_grid_layout.addWidget(file_section_label, row, 0, 1, 2)
        row += 1
        
        file_input_layout = QHBoxLayout()
        self.file_path_input = QLineEdit("No file selected")
        self.file_path_input.setReadOnly(True)
        self.file_path_input.setStyleSheet("padding: 8px; border: 1px solid #dcdcdc; border-radius: 5px; background-color: #f9f9f9;")
        self.browse_file_btn = QPushButton("Browse PDF")
        self.browse_file_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 8px 15px; border-radius: 5px; border: none; font-weight: bold;")
        file_input_layout.addWidget(self.file_path_input)
        file_input_layout.addWidget(self.browse_file_btn)
        content_grid_layout.addLayout(file_input_layout, row, 0, 1, 2)
        row += 1

        # Requirements info
        requirements_label = QLabel("📋 <b>Requirements:</b> PDF files only • Min 500 words • Min 1 page • Must contain extractable text")
        requirements_label.setStyleSheet("color: #666; font-size: 11px; font-style: italic; padding: 5px;")
        requirements_label.setWordWrap(True)
        content_grid_layout.addWidget(requirements_label, row, 0, 1, 2)
        row += 1

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("QProgressBar { border: 1px solid #dcdcdc; border-radius: 5px; text-align: center; }")
        content_grid_layout.addWidget(self.progress_bar, row, 0, 1, 2)
        row += 1

        # Summary Level Selection
        content_grid_layout.addWidget(QLabel("<b>Summary Detail Level:</b>"), row, 0, 1, 2)
        row += 1
        accuracy_layout = QHBoxLayout()
        self.accuracy_group = QButtonGroup(self)
        self.low_accuracy_radio = QRadioButton("Comprehensive (Target: ~5000 words)")
        self.medium_accuracy_radio = QRadioButton("Balanced (Target: ~2500 words)")
        self.high_accuracy_radio = QRadioButton("Concise (Target: ~800 words)")
        self.accuracy_group.addButton(self.low_accuracy_radio)
        self.accuracy_group.addButton(self.medium_accuracy_radio)
        self.accuracy_group.addButton(self.high_accuracy_radio)
        self.low_accuracy_radio.setChecked(True)
        accuracy_layout.addWidget(self.low_accuracy_radio)
        accuracy_layout.addWidget(self.medium_accuracy_radio)
        accuracy_layout.addWidget(self.high_accuracy_radio)
        content_grid_layout.addLayout(accuracy_layout, row, 0, 1, 2)
        row += 1

        # Model Display
        content_grid_layout.addWidget(QLabel("<b>AI Model:</b>"), row, 0)
        self.model_display_label = QLabel("GPT-4.1 Nano (Enhanced Logic)")
        self.model_display_label.setStyleSheet("font-weight: bold; color: #34495e;")
        content_grid_layout.addWidget(self.model_display_label, row, 1)
        row += 1

        # Summarize Button
        self.summarize_btn = QPushButton("Generate Enhanced Summary")
        self.summarize_btn.setStyleSheet("background-color: #007bff; color: white; padding: 12px 20px; border-radius: 8px; font-weight: bold; border: none;")
        self.summarize_btn.setEnabled(False)
        content_grid_layout.addWidget(self.summarize_btn, row, 0, 1, 2, alignment=Qt.AlignCenter)
        row += 1

        # Summary Display
        content_grid_layout.addWidget(QLabel("<b>Generated Summary:</b>"), row, 0, 1, 2)
        row += 1
        self.summary_textarea = QTextEdit("Upload a PDF and click 'Generate Enhanced Summary' to see the results.")
        self.summary_textarea.setReadOnly(True)
        self.summary_textarea.setStyleSheet("padding: 10px; border: 1px solid #dcdcdc; border-radius: 5px; background-color: #f8f8f8;")
        self.summary_textarea.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        content_grid_layout.addWidget(self.summary_textarea, row, 0, 1, 2)
        row += 1

        # Word Count Display
        self.word_count_label = QLabel("Word Count: 0")
        self.word_count_label.setStyleSheet("font-weight: bold; color: #555;")
        content_grid_layout.addWidget(self.word_count_label, row, 0, 1, 2)
        row += 1

        # Output Filename
        content_grid_layout.addWidget(QLabel("<b>Output Filename:</b>"), row, 0, 1, 2)
        row += 1
        self.output_filename_input = QLineEdit("enhanced_summary.txt")
        self.output_filename_input.setStyleSheet("padding: 8px; border: 1px solid #dcdcdc; border-radius: 5px;")
        content_grid_layout.addWidget(self.output_filename_input, row, 0, 1, 2)
        row += 1

        # Save Button
        self.save_file_button = QPushButton("Save Enhanced Summary")
        self.save_file_button.setStyleSheet("background-color: #6c757d; color: white; padding: 10px 20px; border-radius: 8px; font-weight: bold; border: none;")
        self.save_file_button.setEnabled(False)
        content_grid_layout.addWidget(self.save_file_button, row, 0, 1, 2, alignment=Qt.AlignCenter)
        row += 1

        # Footer
        footer_label = QLabel("© 2025 Bharat Electronics Limited - Enhanced Version")
        footer_label.setAlignment(Qt.AlignCenter)
        footer_label.setStyleSheet("font-size: 12px; color: #777;")
        main_layout.addWidget(footer_label)

    def connect_signals(self):
        self.browse_file_btn.clicked.connect(self.open_file_dialog)
        self.summarize_btn.clicked.connect(self.summarize_pdf)
        self.save_file_button.clicked.connect(self.save_summary_to_file)
        self.summary_textarea.textChanged.connect(self.update_word_count)

    def update_word_count(self):
        """Update word count display"""
        text = self.summary_textarea.toPlainText()
        if text and not text.startswith("Upload a PDF") and not text.startswith("Error"):
            word_count = len(text.split())
            self.word_count_label.setText(f"Word Count: {word_count:,}")
        else:
            self.word_count_label.setText("Word Count: 0")

    def open_file_dialog(self):
        file_dialog = QFileDialog(self)
        file_dialog.setNameFilter("PDF files (*.pdf)")
        if file_dialog.exec():
            selected_files = file_dialog.selectedFiles()
            if selected_files:
                file_path = selected_files[0]
                
                # Pre-validate file before processing
                if not self._pre_validate_file(file_path):
                    return
                
                self.file_path_input.setText(os.path.basename(file_path))
                self.summary_textarea.setPlainText("Validating and extracting text from PDF... Please wait.")
                self.summarize_btn.setEnabled(False)
                self.save_file_button.setEnabled(False)
                self.progress_bar.setVisible(True)
                self.progress_bar.setValue(0)

                self.extractor_worker = PdfTextExtractor(file_path)
                self.extractor_thread = QThread()
                self.extractor_worker.moveToThread(self.extractor_thread)

                self.extractor_thread.started.connect(self.extractor_worker.run)
                self.extractor_worker.finished.connect(self.handle_pdf_extracted)
                self.extractor_worker.error.connect(self.handle_pdf_error)
                self.extractor_worker.validation_failed.connect(self.handle_validation_failed)
                self.extractor_worker.progress.connect(self.progress_bar.setValue)
                self.extractor_worker.finished.connect(self.extractor_thread.quit)
                self.extractor_worker.error.connect(self.extractor_thread.quit)
                self.extractor_worker.validation_failed.connect(self.extractor_thread.quit)
                self.extractor_thread.finished.connect(self.extractor_thread.deleteLater)

                self.extractor_thread.start()

    def _pre_validate_file(self, file_path):
        """Pre-validate file before processing"""
        try:
            # Check if file exists
            if not os.path.exists(file_path):
                QMessageBox.critical(self, "File Not Found", "The selected file does not exist.")
                return False
            
            # Check file extension
            file_extension = os.path.splitext(file_path)[1].lower()
            if file_extension != '.pdf':
                QMessageBox.critical(self, "Invalid File Type", 
                                   f"Only PDF files are supported.\nSelected file type: {file_extension or 'Unknown'}")
                return False
            
            # Check if file is accessible
            try:
                with open(file_path, 'rb') as f:
                    f.read(1024)  # Try to read first 1KB
            except PermissionError:
                QMessageBox.critical(self, "Access Denied", "Cannot access the selected file. Please check file permissions.")
                return False
            except Exception as e:
                QMessageBox.critical(self, "File Error", f"Cannot read the selected file: {str(e)}")
                return False
                
            return True
        except Exception as e:
            QMessageBox.critical(self, "Validation Error", f"Error validating file: {str(e)}")
            return False

    def handle_pdf_extracted(self, filename, extracted_text):
        self.extracted_pdf_text = extracted_text
        self.current_filename = filename
        word_count = len(extracted_text.split())
        char_count = len(extracted_text)
        
        # Display success message with statistics
        success_message = f"""✅ PDF Successfully Processed!
        
File: "{filename}"
Statistics:
• Word count: {word_count:,} words
• Character count: {char_count:,} characters
• Status: Ready for enhanced summarization

The document meets all requirements for summarization."""
        
        self.summary_textarea.setPlainText(success_message)
        self.output_filename_input.setText(f"{os.path.splitext(filename)[0]}_enhanced_summary.txt")
        self.summarize_btn.setEnabled(True)
        self.save_file_button.setEnabled(False)
        self.progress_bar.setVisible(False)

    def handle_pdf_error(self, error_message):
        self.summary_textarea.setPlainText(f"❌ Processing Error:\n\n{error_message}")
        self.summarize_btn.setEnabled(False)
        self.save_file_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "PDF Processing Error", error_message)

    def handle_validation_failed(self, validation_message):
        """Handle validation failures with detailed feedback"""
        self.summary_textarea.setPlainText(f"❌ Validation Failed:\n\n{validation_message}\n\nPlease select a different PDF file that meets the requirements.")
        self.summarize_btn.setEnabled(False)
        self.save_file_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.file_path_input.setText("No valid file selected")
        
        # Show detailed validation failure dialog
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("File Validation Failed")
        msg.setText("The selected PDF file does not meet the requirements for summarization.")
        msg.setDetailedText(f"Validation Details:\n\n{validation_message}\n\nRequirements:\n• File must be a valid PDF\n• Must contain at least 500 words\n• Must have at least 1 page\n• Must contain extractable text (not just images)\n• Less than 70% of pages can be empty")
        msg.exec()

    def summarize_pdf(self):
        if not self.extracted_pdf_text:
            QMessageBox.warning(self, "No PDF Text", "Please extract text from a PDF file first.")
            return

        selected_radio = self.accuracy_group.checkedButton()
        if "Comprehensive" in selected_radio.text():
            summary_level = "low"
        elif "Balanced" in selected_radio.text():
            summary_level = "medium"
        else:
            summary_level = "high"

        self.summary_textarea.setPlainText("Generating enhanced summary... This may take several minutes for comprehensive summaries.")
        self.summarize_btn.setEnabled(False)
        self.save_file_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)

        self.summarizer_worker = ReplicateSummarizerWorker(self.extracted_pdf_text, summary_level, REPLICATE_API_TOKEN)
        self.summarizer_thread = QThread()
        self.summarizer_worker.moveToThread(self.summarizer_thread)

        self.summarizer_thread.started.connect(self.summarizer_worker.run)
        self.summarizer_worker.finished.connect(self.handle_summary_finished)
        self.summarizer_worker.error.connect(self.handle_summary_error)
        self.summarizer_worker.progress.connect(self.progress_bar.setValue)
        self.summarizer_worker.finished.connect(self.summarizer_thread.quit)
        self.summarizer_worker.error.connect(self.summarizer_thread.quit)
        self.summarizer_thread.finished.connect(self.summarizer_thread.deleteLater)

        self.summarizer_thread.start()

    def handle_summary_finished(self, summary_text):
        self.summary_textarea.setPlainText(summary_text)
        self.summarize_btn.setEnabled(True)
        self.save_file_button.setEnabled(True)
        self.progress_bar.setVisible(False)

    def handle_summary_error(self, error_message):
        self.summary_textarea.setPlainText(f"Error: {error_message}")
        self.summarize_btn.setEnabled(True)
        self.save_file_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Summarization Error", error_message)

    def save_summary_to_file(self):
        summary_content = self.summary_textarea.toPlainText()
        if not summary_content or "Upload a PDF" in summary_content or summary_content.startswith("Error:"):
            QMessageBox.warning(self, "No Summary", "There is no valid summary to save.")
            return

        default_filename = self.output_filename_input.text()
        if not default_filename.strip():
            default_filename = "enhanced_summary.txt"

        file_path, _ = QFileDialog.getSaveFileName(self, "Save Enhanced Summary", default_filename, "Text Files (*.txt);;All Files (*)")
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(summary_content)
                QMessageBox.information(self, "Save Successful", f"Enhanced summary saved to:\n{file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Save Error", f"Failed to save file: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PdfSummarizerApp()
    window.show()
    sys.exit(app.exec())