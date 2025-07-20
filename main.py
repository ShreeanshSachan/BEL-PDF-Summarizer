import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, \
    QLabel, QLineEdit, QPushButton, QTextEdit, QRadioButton, QButtonGroup, QFileDialog, QMessageBox, QProgressBar, QSizePolicy
from PySide6.QtCore import Qt, QThread

from pdf_processor import PdfTextExtractor
from summarizer import ReplicateSummarizerWorker
from config import REPLICATE_API_TOKEN

# --- Main Application ---
class PdfSummarizerApp(QMainWindow):
    """
    Main application window for the Enhanced PDF Summarizer.
    Manages UI, user interactions, and orchestrates PDF extraction and summarization
    by delegating tasks to worker threads.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BEL PDF Summarizer - Enhanced")
        self.setGeometry(100, 100, 1000, 800)

        self.extracted_pdf_text = ""
        self.current_filename = ""

        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        """Sets up the main user interface elements."""
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
        """Connects UI elements to their respective slots (event handlers)."""
        self.browse_file_btn.clicked.connect(self.open_file_dialog)
        self.summarize_btn.clicked.connect(self.summarize_pdf)
        self.save_file_button.clicked.connect(self.save_summary_to_file)
        self.summary_textarea.textChanged.connect(self.update_word_count)

    def update_word_count(self):
        """Updates the displayed word count of the summary text area."""
        text = self.summary_textarea.toPlainText()
        if text and not text.startswith("Upload a PDF") and not text.startswith("Error"):
            word_count = len(text.split())
            self.word_count_label.setText(f"Word Count: {word_count:,}")
        else:
            self.word_count_label.setText("Word Count: 0")

    def open_file_dialog(self):
        """
        Opens a file dialog for the user to select a PDF.
        Initiates PDF text extraction in a separate thread upon selection.
        """
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

                # Create and start the PDF extractor worker thread
                self.extractor_worker = PdfTextExtractor(file_path)
                self.extractor_thread = QThread()
                self.extractor_worker.moveToThread(self.extractor_thread)

                # Connect signals from worker to UI slots
                self.extractor_thread.started.connect(self.extractor_worker.run)
                self.extractor_worker.finished.connect(self.handle_pdf_extracted)
                self.extractor_worker.error.connect(self.handle_pdf_error)
                self.extractor_worker.validation_failed.connect(self.handle_validation_failed)
                self.extractor_worker.progress.connect(self.progress_bar.setValue)
                
                # Clean up thread upon completion or error
                self.extractor_worker.finished.connect(self.extractor_thread.quit)
                self.extractor_worker.error.connect(self.extractor_thread.quit)
                self.extractor_worker.validation_failed.connect(self.extractor_thread.quit)
                self.extractor_thread.finished.connect(self.extractor_thread.deleteLater)

                self.extractor_thread.start()

    def _pre_validate_file(self, file_path):
        """
        Performs initial, quick validations on the selected file path
        before starting the detailed PDF extraction process.
        """
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
        """
        Slot to handle the 'finished' signal from PdfTextExtractor.
        Updates UI with extracted text status and enables summarization.
        """
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
        """
        Slot to handle the 'error' signal from PdfTextExtractor.
        Displays an error message to the user.
        """
        self.summary_textarea.setPlainText(f"❌ Processing Error:\n\n{error_message}")
        self.summarize_btn.setEnabled(False)
        self.save_file_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "PDF Processing Error", error_message)

    def handle_validation_failed(self, validation_message):
        """
        Slot to handle the 'validation_failed' signal from PdfTextExtractor.
        Displays detailed validation feedback to the user.
        """
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
        """
        Initiates the PDF summarization process in a separate thread.
        Retrieves the selected summary level and extracted text.
        """
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

        # Create and start the summarizer worker thread
        self.summarizer_worker = ReplicateSummarizerWorker(self.extracted_pdf_text, summary_level, REPLICATE_API_TOKEN)
        self.summarizer_thread = QThread()
        self.summarizer_worker.moveToThread(self.summarizer_thread)

        # Connect signals from worker to UI slots
        self.summarizer_thread.started.connect(self.summarizer_worker.run)
        self.summarizer_worker.finished.connect(self.handle_summary_finished)
        self.summarizer_worker.error.connect(self.handle_summary_error)
        self.summarizer_worker.progress.connect(self.progress_bar.setValue)
        
        # Clean up thread upon completion or error
        self.summarizer_worker.finished.connect(self.summarizer_thread.quit)
        self.summarizer_worker.error.connect(self.summarizer_thread.quit)
        self.summarizer_thread.finished.connect(self.summarizer_thread.deleteLater)

        self.summarizer_thread.start()

    def handle_summary_finished(self, summary_text):
        """
        Slot to handle the 'finished' signal from ReplicateSummarizerWorker.
        Displays the generated summary and enables saving.
        """
        self.summary_textarea.setPlainText(summary_text)
        self.summarize_btn.setEnabled(True)
        self.save_file_button.setEnabled(True)
        self.progress_bar.setVisible(False)

    def handle_summary_error(self, error_message):
        """
        Slot to handle the 'error' signal from ReplicateSummarizerWorker.
        Displays an error message to the user.
        """
        self.summary_textarea.setPlainText(f"Error: {error_message}")
        self.summarize_btn.setEnabled(True)
        self.save_file_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Summarization Error", error_message)

    def save_summary_to_file(self):
        """
        Opens a file dialog for the user to save the generated summary to a text file.
        """
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
