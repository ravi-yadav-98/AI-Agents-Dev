# AI Real Estate Agent Team - Modular Structure

This application has been refactored into a modular structure for better maintainability and readability.

## File Structure

```
real_estate_agents/
├── __init__.py              # Package initialization and exports
├── models.py                # Pydantic data models and schemas
├── config.py                # Configuration settings and environment variables
├── agents.py                # AI agent classes and creation functions
├── analysis.py              # Market analysis and property valuation functions
├── ui.py                    # Streamlit UI components and display functions
├── main.py                  # Main application orchestration
├── run_app.py               # Entry point for running the application
├── ai_real_estate_agents.py # Backward compatibility wrapper
└── local_ai_real_estate_agents.py # Original local version (unchanged)
```

## Module Descriptions

### `models.py`
- **PropertyDetails**: Pydantic model for individual property data
- **PropertyListing**: Pydantic model for property search results

### `config.py`
- Environment variable loading
- Default API keys and model configuration
- Available real estate websites configuration

### `agents.py`
- **DirectFirecrawlAgent**: Agent with direct Firecrawl integration for property search
- **create_sequential_agents()**: Function to create specialized AI agents

### `analysis.py`
- **run_sequential_analysis()**: Main analysis orchestration function
- **extract_property_valuation()**: Helper function for property-specific valuations

### `ui.py`
- **display_properties_professionally()**: Professional property display with tabs
- **render_sidebar()**: Sidebar configuration and API key inputs
- **render_property_form()**: Main property search form
- **render_progress_section()**: Progress tracking UI

### `main.py`
- **main()**: Main application entry point that orchestrates all components

## Usage

### Running the Application

```bash
# Run the modular version
streamlit run real_estate_agents/run_app.py

# Or run the backward-compatible version
streamlit run real_estate_agents/ai_real_estate_agents.py
```

### Importing and Using Components

```python
# Import the main function
from real_estate_agents import main

# Run the application
main()

# Import specific components
from real_estate_agents import DirectFirecrawlAgent, PropertyDetails
from real_estate_agents.analysis import run_sequential_analysis
from real_estate_agents.ui import display_properties_professionally
```

## Benefits of Modular Structure

1. **Maintainability**: Each module has a single responsibility
2. **Readability**: Code is organized by functionality
3. **Reusability**: Components can be imported and used independently
4. **Testing**: Individual modules can be tested in isolation
5. **Scalability**: Easy to add new features or modify existing ones

## Configuration

The application uses environment variables for API keys:
- `OPENAI_API_KEY`: Your OpenAI API key
- `FIRECRAWL_API_KEY`: Your Firecrawl API key

These can be set in a `.env` file or through the Streamlit UI.

## Dependencies

The modular structure maintains the same dependencies as the original:
- streamlit
- agno
- firecrawl
- pydantic
- python-dotenv
