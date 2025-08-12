import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys - must be set in environment variables
DEFAULT_OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DEFAULT_FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

# Default model configuration
DEFAULT_MODEL_ID = "gpt-4o"

# Available real estate websites
AVAILABLE_WEBSITES = ["Zillow", "Realtor.com", "Trulia", "Homes.com"]
DEFAULT_WEBSITES = ["Zillow", "Realtor.com"]
