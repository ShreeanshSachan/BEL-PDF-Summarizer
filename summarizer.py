import replicate
import re
from PySide6.QtCore import Signal, QObject

from pdf_processor import estimate_tokens, estimate_words_from_tokens
from config import GPT_NANO_MODEL

class ReplicateSummarizerWorker(QObject):
    """
    Worker class for interacting with the Replicate API to generate summaries.
    Implements intelligent chunking and a multi-stage summarization process
    to handle large documents effectively.
    """
    finished = Signal(str)  # Emits the final summary text
    error = Signal(str)     # Emits error message if summarization fails
    progress = Signal(int)  # Emits integer (0-100) for progress updates

    def __init__(self, text_to_summarize, summary_level, api_token):
        """
        Initializes the summarizer worker with the text, desired summary level, and API token.
        """
        super().__init__()
        self.text_to_summarize = text_to_summarize
        self.summary_level = summary_level # 'low', 'medium', 'high'
        self.api_token = api_token
        self.client = replicate.Client(api_token=self.api_token)

    def run(self):
        """
        Main execution method for the worker thread.
        Orchestrates the multi-stage summarization process.
        """
        if not self.api_token or self.api_token == "YOUR_HARDCODED_REPLICATE_API_TOKEN_HERE":
            self.error.emit("Error: Replicate API Token is not correctly set.")
            return

        try:
            # Configure summarization parameters based on the selected level
            if self.summary_level == "low":  # Comprehensive summary
                target_words = 5000
                detail_level = "extremely comprehensive and detailed"
                prompt_instruction = "Provide an extremely comprehensive, detailed, and thorough summary. Include all key arguments, evidence, examples, data points, and nuances. Maintain the depth and richness of the original content."
            elif self.summary_level == "medium":  # Balanced summary
                target_words = 2500
                detail_level = "balanced and substantial"
                prompt_instruction = "Provide a balanced, substantial summary that covers all main points, key arguments, and important details while maintaining readability and flow."
            else:  # "high" - Concise summary
                target_words = 800
                detail_level = "concise but complete"
                prompt_instruction = "Provide a concise summary focusing on the most critical points, main arguments, and key takeaways while ensuring completeness."

            # Calculate target tokens for the final summary
            target_tokens = int(target_words * 1.3)
            
            self.progress.emit(10) # Initial progress update

            # Step 1: Create intelligent chunks from the input text
            chunks = self._create_intelligent_chunks(self.text_to_summarize)
            self.progress.emit(20) # Progress after chunking

            # Step 2: Process each chunk to get intermediate summaries
            chunk_summaries = []
            for i, chunk in enumerate(chunks):
                summary = self._process_chunk(chunk, detail_level, prompt_instruction)
                chunk_summaries.append(summary)
                
                # Update progress for chunk processing (20% to 80% of total progress)
                progress = 20 + int((i + 1) / len(chunks) * 60)
                self.progress.emit(progress)
            
            self.progress.emit(80) # Progress after all chunks are processed

            # Step 3: Synthesize the final summary from intermediate summaries
            final_summary = self._synthesize_final_summary(
                chunk_summaries, 
                target_tokens, 
                detail_level, 
                prompt_instruction
            )
            
            self.progress.emit(100) # Final progress update
            self.finished.emit(final_summary)

        except Exception as e:
            self.error.emit(f"Summarization error: {str(e)}")

    def _create_intelligent_chunks(self, text):
        """
        Divides the input text into chunks that attempt to preserve semantic coherence.
        Prioritizes splitting by paragraphs, then by sentences if paragraphs are not distinct.
        Ensures chunks are within a maximum token limit suitable for the LLM.
        """
        # First, try to split by double newlines (paragraphs)
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
        
        # If paragraph splitting doesn't yield many distinct units, try splitting by sentences
        if len(paragraphs) <= 2 and len(text) > 500: # Only if text is substantial and few paragraphs
            sentences = re.split(r'[.!?]+', text)
            paragraphs = [s.strip() for s in sentences if s.strip()]
        
        chunks = []
        current_chunk = []
        current_tokens = 0
        max_chunk_tokens = 8000  # Max tokens per chunk for LLM input (adjust based on model context window)
        
        for paragraph in paragraphs:
            paragraph_tokens = estimate_tokens(paragraph)
            
            # If adding the current paragraph exceeds max_chunk_tokens and there's already content in current_chunk,
            # finalize the current chunk and start a new one.
            if current_tokens + paragraph_tokens > max_chunk_tokens and current_chunk:
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [paragraph]
                current_tokens = paragraph_tokens
            else:
                # Otherwise, add the paragraph to the current chunk
                current_chunk.append(paragraph)
                current_tokens += paragraph_tokens
        
        # Add any remaining content as the last chunk
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks

    def _process_chunk(self, chunk, detail_level, prompt_instruction):
        """
        Sends an individual text chunk to the LLM for intermediate summarization.
        Constructs specific system and user prompts for this stage.
        """
        chunk_tokens = estimate_tokens(chunk)
        # Aim for about 50% compression for intermediate summaries, max 4000 tokens output
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
            output = self.client.run(
                GPT_NANO_MODEL,
                input={
                    "prompt": prompt,
                    "system_prompt": system_prompt,
                    "temperature": 0.3,  # Lower temperature for more focused, less creative output
                    "top_p": 0.9,        # Top-p sampling for diverse but coherent responses
                    "max_completion_tokens": target_output_tokens,
                    "presence_penalty": 0,
                    "frequency_penalty": 0.1
                }
            )
            return "".join(output)
        except Exception as e:
            # Return an error message for the chunk if processing fails
            return f"Error processing chunk: {str(e)}"

    def _synthesize_final_summary(self, chunk_summaries, target_tokens, detail_level, prompt_instruction):
        """
        Synthesizes the final summary by combining and refining the intermediate chunk summaries.
        Sends the combined summaries to the LLM with a final synthesis prompt.
        """
        # Join intermediate summaries with a clear separator for the LLM
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
            output = self.client.run(
                GPT_NANO_MODEL,
                input={
                    "prompt": final_prompt,
                    "system_prompt": system_prompt,
                    "temperature": 0.4,  # Slightly higher temperature for more creative synthesis
                    "top_p": 0.95,       # Broader sampling for better flow
                    "max_completion_tokens": min(target_tokens, 16000), # Cap max tokens for safety
                    "presence_penalty": 0,
                    "frequency_penalty": 0.1
                }
            )
            return "".join(output)
        except Exception as e:
            return f"Error in final synthesis: {str(e)}"

