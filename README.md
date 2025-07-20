Enhanced PDF Summarizer
📝 Project Overview
In today's information-rich world, professionals and individuals are often overwhelmed by lengthy PDF documents like reports, research papers, legal documents, and educational materials. Manually sifting through these extensive texts to extract key information, grasp core concepts, or identify actionable insights is incredibly time-consuming, leading to information overload, decreased productivity, and missed critical details. This challenge is further exacerbated when users need to quickly understand the essence of multiple documents or require different levels of detail from the same source.

The Enhanced PDF Summarizer is a desktop application designed to tackle this problem. It provides an intuitive graphical user interface (GUI) that allows users to upload PDF documents and generate concise, balanced, or comprehensive summaries using advanced Large Language Models (LLMs) via the Replicate API. The application is built with responsiveness in mind, performing heavy tasks like PDF parsing and AI summarization in separate threads to ensure a smooth user experience.

✨ Key Features
Intelligent PDF Upload & Robust Validation:

Supports only PDF files.

Performs comprehensive pre-processing and content validation (file type, size, encryption, extractable text, minimum word count, minimum pages, and acceptable ratio of empty pages).

Provides detailed feedback messages for any validation failures.

Multi-Level AI Summarization:

Offers three distinct summarization detail levels:

Comprehensive (Target: ~5000 words): For in-depth understanding, retaining significant detail.

Balanced (Target: ~2500 words): A substantial summary covering main points and important details.

Concise (Target: ~800 words): Focuses on the most critical points and key takeaways.

Advanced LLM Integration:

Leverages the powerful openai/gpt-4.1-nano model via the Replicate API for high-quality, context-aware summarization.

Intelligent Chunking & Multi-Stage Synthesis:

Employs a sophisticated process to break down large documents into semantically coherent chunks.

Summarizes each chunk individually.

Synthesizes these intermediate summaries into a cohesive and comprehensive final output, ensuring context is maintained across the entire document.

Responsive User Interface:

Built with PySide6 (Qt for Python) to provide a modern and interactive desktop experience.

Utilizes multi-threading for PDF extraction and AI summarization to prevent UI freezing during long-running operations.

Real-time Progress Tracking:

Displays a progress bar to keep users informed about the status of PDF processing and summarization.

Summary Export:

Allows users to easily save the generated summary to a text file (.txt).

Dynamic Word Count Display:

Shows the real-time word count of the generated summary.

🏗️ Architecture
The application adopts a client-server-like architecture within a desktop environment.

Frontend (GUI): Developed using PySide6, providing the user interface and handling user interactions.

Backend (Local Processing): Python modules (pdf_processor.py, summarizer.py) running in separate threads manage PDF text extraction, validation, text chunking, and orchestration of API calls.

External LLM Service: The Replicate API hosts the openai/gpt-4.1-nano Large Language Model, which performs the actual AI summarization.

Enhanced PDF Summarizer
📝 Project Overview
In today's information-rich world, professionals and individuals are often overwhelmed by lengthy PDF documents like reports, research papers, legal documents, and educational materials. Manually sifting through these extensive texts to extract key information, grasp core concepts, or identify actionable insights is incredibly time-consuming, leading to information overload, decreased productivity, and missed critical details. This challenge is further exacerbated when users need to quickly understand the essence of multiple documents or require different levels of detail from the same source.

The Enhanced PDF Summarizer is a desktop application designed to tackle this problem. It provides an intuitive graphical user interface (GUI) that allows users to upload PDF documents and generate concise, balanced, or comprehensive summaries using advanced Large Language Models (LLMs) via the Replicate API. The application is built with responsiveness in mind, performing heavy tasks like PDF parsing and AI summarization in separate threads to ensure a smooth user experience.

✨ Key Features
Intelligent PDF Upload & Robust Validation:

Supports only PDF files.

Performs comprehensive pre-processing and content validation (file type, size, encryption, extractable text, minimum word count, minimum pages, and acceptable ratio of empty pages).

Provides detailed feedback messages for any validation failures.

Multi-Level AI Summarization:

Offers three distinct summarization detail levels:

Comprehensive (Target: ~5000 words): For in-depth understanding, retaining significant detail.

Balanced (Target: ~2500 words): A substantial summary covering main points and important details.

Concise (Target: ~800 words): Focuses on the most critical points and key takeaways.

Advanced LLM Integration:

Leverages the powerful openai/gpt-4.1-nano model via the Replicate API for high-quality, context-aware summarization.

Intelligent Chunking & Multi-Stage Synthesis:

Employs a sophisticated process to break down large documents into semantically coherent chunks.

Summarizes each chunk individually.

Synthesizes these intermediate summaries into a cohesive and comprehensive final output, ensuring context is maintained across the entire document.

Responsive User Interface:

Built with PySide6 (Qt for Python) to provide a modern and interactive desktop experience.

Utilizes multi-threading for PDF extraction and AI summarization to prevent UI freezing during long-running operations.

Real-time Progress Tracking:

Displays a progress bar to keep users informed about the status of PDF processing and summarization.

Summary Export:

Allows users to easily save the generated summary to a text file (.txt).

Dynamic Word Count Display:

Shows the real-time word count of the generated summary.

🏗️ Architecture
The application adopts a client-server-like architecture within a desktop environment.

Frontend (GUI): Developed using PySide6, providing the user interface and handling user interactions.

Backend (Local Processing): Python modules (pdf_processor.py, summarizer.py) running in separate threads manage PDF text extraction, validation, text chunking, and orchestration of API calls.

External LLM Service: The Replicate API hosts the openai/gpt-4.1-nano Large Language Model, which performs the actual AI summarization.



📂 Project Structure
The project is organized into modular Python files for better maintainability and readability:

pdf-summarizer-app/
├── main.py             # Main application entry point, GUI setup, and thread orchestration
├── pdf_processor.py    # Handles PDF text extraction, validation, and utility functions
├── summarizer.py       # Manages AI summarization logic, chunking, and Replicate API calls
├── config.py           # Stores application-wide configuration (e.g., API token, model name)
├── .gitignore          # Specifies files/directories to be ignored by Git
├── README.md           # This file
└── requirements.txt    # Lists all Python dependencies

🚀 Getting Started
Follow these steps to set up and run the Enhanced PDF Summarizer on your local machine.

Prerequisites
Python 3.9+ installed.

A Replicate API Token. You can obtain one by signing up at replicate.com.

Installation
Clone the repository:

git clone https://github.com/ShreeanshSachan/BEL-PDF-Summarizer.git
cd BEL-PDF-Summarizer

Create a virtual environment (recommended):

python -m venv venv

Activate the virtual environment:

On Windows:

.\venv\Scripts\activate

On macOS/Linux:

source venv/bin/activate

Install dependencies:

pip install -r requirements.txt

API Key Configuration (Crucial for Security!)
NEVER hardcode your API key directly in code that might be pushed to a public repository. This project is configured to load the Replicate API token from an environment variable.

Set your Replicate API Token as an environment variable:

On Windows (Command Prompt - for current session):

set REPLICATE_API_TOKEN="r8_YOUR_ACTUAL_REPLICATE_API_TOKEN_HERE"

On Windows (PowerShell - for current session):

$env:REPLICATE_API_TOKEN="r8_YOUR_ACTUAL_REPLICATE_API_TOKEN_HERE"

On macOS/Linux (for current session):

export REPLICATE_API_TOKEN="r8_YOUR_ACTUAL_REPLICATE_API_TOKEN_HERE"

Replace r8_YOUR_ACTUAL_REPLICATE_API_TOKEN_HERE with your actual token obtained from replicate.com.

For persistent environment variables (across terminal sessions), refer to your operating system's documentation.

🏃 How to Run
Ensure your virtual environment is activated and the REPLICATE_API_TOKEN environment variable is set.

Navigate to the project's root directory in your terminal where main.py is located.

Run the application:

python main.py

🛠️ Dependencies
The application relies on the following Python packages:

PySide6

PyPDF2

replicate

These are listed in requirements.txt.

🤝 Contributing
Contributions are welcome! If you have suggestions for improvements, bug fixes, or new features, please open an issue or submit a pull request.

🙏 Acknowledgements
Developed as an enhanced solution for Bharat Electronics Limited (BEL).

Powered by the openai/gpt-4.1-nano model via the Replicate API.

GUI built with PySide6.

PDF processing handled by PyPDF2.

📂 Project Structure
The project is organized into modular Python files for better maintainability and readability:

pdf-summarizer-app/
├── main.py             # Main application entry point, GUI setup, and thread orchestration
├── pdf_processor.py    # Handles PDF text extraction, validation, and utility functions
├── summarizer.py       # Manages AI summarization logic, chunking, and Replicate API calls
├── config.py           # Stores application-wide configuration (e.g., API token, model name)
├── .gitignore          # Specifies files/directories to be ignored by Git
├── README.md           # This file
└── requirements.txt    # Lists all Python dependencies

🚀 Getting Started
Follow these steps to set up and run the Enhanced PDF Summarizer on your local machine.

Prerequisites
Python 3.9+ installed.

A Replicate API Token. You can obtain one by signing up at replicate.com.

Installation
Clone the repository:

git clone https://github.com/ShreeanshSachan/BEL-PDF-Summarizer.git
cd BEL-PDF-Summarizer

Create a virtual environment (recommended):

python -m venv venv

Activate the virtual environment:

On Windows:

.\venv\Scripts\activate

On macOS/Linux:

source venv/bin/activate

Install dependencies:

pip install -r requirements.txt

API Key Configuration (Crucial for Security!)
NEVER hardcode your API key directly in code that might be pushed to a public repository. This project is configured to load the Replicate API token from an environment variable.

Set your Replicate API Token as an environment variable:

On Windows (Command Prompt - for current session):

set REPLICATE_API_TOKEN="r8_YOUR_ACTUAL_REPLICATE_API_TOKEN_HERE"

On Windows (PowerShell - for current session):

$env:REPLICATE_API_TOKEN="r8_YOUR_ACTUAL_REPLICATE_API_TOKEN_HERE"

On macOS/Linux (for current session):

export REPLICATE_API_TOKEN="r8_YOUR_ACTUAL_REPLICATE_API_TOKEN_HERE"

Replace r8_YOUR_ACTUAL_REPLICATE_API_TOKEN_HERE with your actual token obtained from replicate.com.

For persistent environment variables (across terminal sessions), refer to your operating system's documentation.

🏃 How to Run
Ensure your virtual environment is activated and the REPLICATE_API_TOKEN environment variable is set.

Navigate to the project's root directory in your terminal where main.py is located.

Run the application:

python main.py

🛠️ Dependencies
The application relies on the following Python packages:

PySide6

PyPDF2

replicate

These are listed in requirements.txt.

🤝 Contributing
Contributions are welcome! If you have suggestions for improvements, bug fixes, or new features, please open an issue or submit a pull request.

🙏 Acknowledgements
Developed as an enhanced solution for Bharat Electronics Limited (BEL).

Powered by the openai/gpt-4.1-nano model via the Replicate API.

GUI built with PySide6.

PDF processing handled by PyPDF2.