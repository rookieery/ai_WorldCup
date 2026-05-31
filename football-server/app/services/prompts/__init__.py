"""Extracted prompt templates for the PromptBuilder service."""

from app.services.prompts.championship_prompts import get_championship_instruction
from app.services.prompts.system_prompts import ANALYSIS_PROMPTS, SYSTEM_FRAGMENTS

__all__ = [
    "ANALYSIS_PROMPTS",
    "SYSTEM_FRAGMENTS",
    "get_championship_instruction",
]
