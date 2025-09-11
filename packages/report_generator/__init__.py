"""
Pakiet do generowania raportów z LLM
"""

from .llm_report_generator import generate_comprehensive_report
from .pdf_generator import generate_pdf_report

__all__ = ['generate_comprehensive_report', 'generate_pdf_report']
