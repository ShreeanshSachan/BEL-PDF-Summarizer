# config.py
import os

# --- Replicate API Configuration ---
# IMPORTANT: For security, the Replicate API token should be loaded from an environment variable.
# NEVER hardcode sensitive keys directly in your repository, especially if it's public.
#
# How to set the environment variable:
# On Linux/macOS (in your terminal, before running the app):
#   export REPLICATE_API_TOKEN="r8_YOUR_ACTUAL_REPLICATE_API_TOKEN_HERE"
#
# On Windows (Command Prompt, before running the app):
#   set REPLICATE_API_TOKEN="r8_YOUR_ACTUAL_REPLICATE_API_TOKEN_HERE"
#
# On Windows (PowerShell, before running the app):
#   $env:REPLICATE_API_TOKEN="r8_YOUR_ACTUAL_REPLICATE_API_TOKEN_HERE"
#
# Replace "r8_YOUR_ACTUAL_REPLICATE_API_TOKEN_HERE" with your real Replicate API token.
#
# The second argument to os.getenv is a fallback. In production, you might want to
# remove this fallback or make it raise an error if the variable isn't set.
REPLICATE_API_TOKEN = os.getenv("REPLICATE_API_TOKEN", "PLEASE_SET_YOUR_REPLICATE_API_TOKEN_ENVIRONMENT_VARIABLE")

# Fixed AI model to be used for summarization
GPT_NANO_MODEL = "openai/gpt-4.1-nano"
