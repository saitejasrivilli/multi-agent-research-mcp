"""
Citation Generator - APA, MLA, Chicago formats
"""
from datetime import datetime
from typing import List, Dict

class CitationGenerator:
    """Generate citations in various formats."""
    
    @staticmethod
    def generate_apa(source: Dict) -> str:
        """Generate APA format citation."""
        title = source.get("title", "Untitled")
        url = source.get("url", "")
        date = datetime.now().strftime("%Y, %B %d")
        
        return f"{title}. Retrieved {date}, from {url}"
    
    @staticmethod
    def generate_mla(source: Dict) -> str:
        """Generate MLA format citation."""
        title = source.get("title", "Untitled")
        url = source.get("url", "")
        date = datetime.now().strftime("%d %b. %Y")
        
        return f'"{title}." Web. {date}. <{url}>'
    
    @staticmethod
    def generate_chicago(source: Dict) -> str:
        """Generate Chicago format citation."""
        title = source.get("title", "Untitled")
        url = source.get("url", "")
        date = datetime.now().strftime("%B %d, %Y")
        
        return f'"{title}." Accessed {date}. {url}.'
    
    @classmethod
    def generate_all(cls, sources: List[Dict], format: str = "apa") -> List[str]:
        """Generate citations for all sources."""
        generators = {
            "apa": cls.generate_apa,
            "mla": cls.generate_mla,
            "chicago": cls.generate_chicago
        }
        
        gen_fn = generators.get(format.lower(), cls.generate_apa)
        return [gen_fn(source) for source in sources]
    
    @classmethod
    def format_bibliography(cls, sources: List[Dict], format: str = "apa") -> str:
        """Generate formatted bibliography."""
        citations = cls.generate_all(sources, format)
        
        header = f"References ({format.upper()})\n" + "=" * 40 + "\n\n"
        body = "\n\n".join([f"[{i+1}] {c}" for i, c in enumerate(citations)])
        
        return header + body
