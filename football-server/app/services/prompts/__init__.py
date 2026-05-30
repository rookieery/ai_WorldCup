"""Extracted prompt templates for the PromptBuilder service."""

from app.services.prompts.championship_prompts import CHAMPIONSHIP_INSTRUCTION
from app.services.prompts.system_prompts import ANALYSIS_PROMPTS, SYSTEM_FRAGMENTS

__all__ = [
    "ANALYSIS_PROMPTS",
    "CHAMPIONSHIP_INSTRUCTION",
    "SYSTEM_FRAGMENTS",
]
