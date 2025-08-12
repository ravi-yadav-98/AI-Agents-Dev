"""
AI Real Estate Agent Team

A modular Streamlit application that uses AI agents to search, analyze, and evaluate real estate properties.
"""

from .main import main
from .models import PropertyDetails, PropertyListing
from .agents import DirectFirecrawlAgent, create_sequential_agents
from .analysis import run_sequential_analysis, extract_property_valuation
from .ui import display_properties_professionally, render_sidebar, render_property_form

__version__ = "1.0.0"
__author__ = "AI Real Estate Team"

__all__ = [
    "main",
    "PropertyDetails", 
    "PropertyListing",
    "DirectFirecrawlAgent",
    "create_sequential_agents",
    "run_sequential_analysis",
    "extract_property_valuation",
    "display_properties_professionally",
    "render_sidebar",
    "render_property_form"
]
