"""
Export to PDF and Markdown
"""
from fpdf import FPDF
from typing import Dict
from datetime import datetime
from .citations import CitationGenerator

class PDFExporter:
    """Export research report to PDF."""
    
    def __init__(self):
        self.pdf = FPDF()
        self.pdf.set_auto_page_break(auto=True, margin=15)
    
    def generate(self, synthesis: Dict, research: Dict, evaluation: Dict) -> bytes:
        """Generate PDF report."""
        self.pdf.add_page()
        
        # Title
        self.pdf.set_font("Arial", "B", 20)
        title = synthesis.get("title", "Research Report")
        self.pdf.cell(0, 15, title.encode('latin-1', 'replace').decode('latin-1'), ln=True, align="C")
        
        # Metadata
        self.pdf.set_font("Arial", "I", 10)
        self.pdf.cell(0, 8, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ln=True, align="C")
        self.pdf.ln(10)
        
        # Executive Summary
        self.pdf.set_font("Arial", "B", 14)
        self.pdf.cell(0, 10, "Executive Summary", ln=True)
        self.pdf.set_font("Arial", "", 11)
        summary = synthesis.get("executive_summary", "N/A")
        self.pdf.multi_cell(0, 6, summary.encode('latin-1', 'replace').decode('latin-1'))
        self.pdf.ln(8)
        
        # Key Takeaways
        self.pdf.set_font("Arial", "B", 14)
        self.pdf.cell(0, 10, "Key Takeaways", ln=True)
        self.pdf.set_font("Arial", "", 11)
        for t in synthesis.get("key_takeaways", []):
            self.pdf.multi_cell(0, 6, f"• {t}".encode('latin-1', 'replace').decode('latin-1'))
        self.pdf.ln(8)
        
        # Sections
        for section in synthesis.get("sections", []):
            self.pdf.set_font("Arial", "B", 12)
            self.pdf.cell(0, 10, section.get("title", "Section").encode('latin-1', 'replace').decode('latin-1'), ln=True)
            self.pdf.set_font("Arial", "", 11)
            self.pdf.multi_cell(0, 6, section.get("content", "").encode('latin-1', 'replace').decode('latin-1'))
            self.pdf.ln(5)
        
        # Evaluation Scores
        self.pdf.add_page()
        self.pdf.set_font("Arial", "B", 14)
        self.pdf.cell(0, 10, "Quality Evaluation", ln=True)
        self.pdf.set_font("Arial", "", 11)
        for metric, score in evaluation.items():
            if isinstance(score, float):
                self.pdf.cell(0, 8, f"{metric.title()}: {score:.0%}", ln=True)
        self.pdf.ln(8)
        
        # Sources
        self.pdf.set_font("Arial", "B", 14)
        self.pdf.cell(0, 10, "Sources", ln=True)
        self.pdf.set_font("Arial", "", 10)
        for i, source in enumerate(research.get("sources", []), 1):
            title = source.get("title", "Source")
            url = source.get("url", "")
            self.pdf.multi_cell(0, 5, f"[{i}] {title}\n    {url}".encode('latin-1', 'replace').decode('latin-1'))
            self.pdf.ln(2)
        
        return bytes(self.pdf.output())


class MarkdownExporter:
    """Export research report to Markdown."""
    
    @staticmethod
    def generate(synthesis: Dict, research: Dict, evaluation: Dict, citation_format: str = "apa") -> str:
        """Generate Markdown report."""
        lines = []
        
        # Title
        lines.append(f"# {synthesis.get('title', 'Research Report')}")
        lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")
        
        # Evaluation Badge
        overall = evaluation.get("overall", 0)
        badge_color = "green" if overall >= 0.8 else "yellow" if overall >= 0.6 else "red"
        lines.append(f"![Quality Score](https://img.shields.io/badge/Quality-{overall:.0%}-{badge_color})\n")
        
        # Executive Summary
        lines.append("## �� Executive Summary\n")
        lines.append(synthesis.get("executive_summary", "N/A"))
        lines.append("")
        
        # Key Takeaways
        lines.append("## 🎯 Key Takeaways\n")
        for t in synthesis.get("key_takeaways", []):
            lines.append(f"- {t}")
        lines.append("")
        
        # Sections
        for section in synthesis.get("sections", []):
            lines.append(f"## 📑 {section.get('title', 'Section')}\n")
            lines.append(section.get("content", ""))
            lines.append("")
        
        # Evaluation
        lines.append("## 📊 Quality Metrics\n")
        lines.append("| Metric | Score |")
        lines.append("|--------|-------|")
        for metric, score in evaluation.items():
            if isinstance(score, float):
                lines.append(f"| {metric.title()} | {score:.0%} |")
        lines.append("")
        
        # Sources with Citations
        lines.append("## 📚 References\n")
        citations = CitationGenerator.generate_all(research.get("sources", []), citation_format)
        for i, citation in enumerate(citations, 1):
            lines.append(f"{i}. {citation}")
        lines.append("")
        
        # Limitations
        if synthesis.get("limitations"):
            lines.append("## ⚠️ Limitations\n")
            for l in synthesis["limitations"]:
                lines.append(f"- {l}")
            lines.append("")
        
        # Further Research
        if synthesis.get("further_research"):
            lines.append("## 🔮 Further Research\n")
            for f in synthesis["further_research"]:
                lines.append(f"- {f}")
        
        return "\n".join(lines)
