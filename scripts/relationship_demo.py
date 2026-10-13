"""Extracts relationships from sample text into the knowledge graph (calls the LLM)."""
from src.entity_resolution.relationship_extractor import run_extraction

run_extraction("""
Microsoft and Google are competitors in cloud computing.
OpenAI partners with Microsoft on AI research.
Google acquired DeepMind in AI development.
""")
