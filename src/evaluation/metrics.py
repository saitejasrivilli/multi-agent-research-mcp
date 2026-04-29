"""
RAG Evaluation Metrics using RAGAS and DeepEval concepts
"""
from typing import Dict, List
import re

class RAGEvaluator:
    """Evaluate RAG pipeline quality using standard metrics."""
    
    def __init__(self):
        self.weights = {
            "relevancy": 0.25,
            "faithfulness": 0.25,
            "coherence": 0.20,
            "completeness": 0.15,
            "citation_accuracy": 0.15
        }
    
    def calculate_relevancy(self, query: str, findings: List[Dict]) -> float:
        """Measure how relevant findings are to the query."""
        if not findings:
            return 0.0
        
        query_terms = set(query.lower().split())
        relevant_count = 0
        
        for finding in findings:
            finding_text = finding.get("finding", "").lower()
            evidence_text = finding.get("evidence", "").lower()
            combined = finding_text + " " + evidence_text
            
            matches = sum(1 for term in query_terms if term in combined)
            if matches >= len(query_terms) * 0.3:  # 30% term overlap
                relevant_count += 1
        
        return min(1.0, relevant_count / max(len(findings), 1))
    
    def calculate_faithfulness(self, synthesis: Dict, sources: List[Dict]) -> float:
        """Measure if synthesis is faithful to sources."""
        if not sources or not synthesis:
            return 0.0
        
        source_content = " ".join([s.get("content", s.get("snippet", ""))[:500] for s in sources]).lower()
        summary = synthesis.get("executive_summary", "").lower()
        
        # Check if key claims in summary can be found in sources
        sentences = re.split(r'[.!?]', summary)
        supported = 0
        
        for sentence in sentences:
            if len(sentence.strip()) < 20:
                continue
            words = sentence.strip().split()[:5]  # First 5 words as key phrase
            phrase = " ".join(words)
            if any(word in source_content for word in words if len(word) > 4):
                supported += 1
        
        total_sentences = len([s for s in sentences if len(s.strip()) >= 20])
        return supported / max(total_sentences, 1)
    
    def calculate_coherence(self, synthesis: Dict) -> float:
        """Measure logical flow and structure."""
        score = 0.0
        
        # Has title
        if synthesis.get("title"):
            score += 0.15
        
        # Has summary
        summary = synthesis.get("executive_summary", "")
        if len(summary) > 100:
            score += 0.25
        elif len(summary) > 50:
            score += 0.15
        
        # Has sections
        sections = synthesis.get("sections", [])
        if len(sections) >= 3:
            score += 0.25
        elif len(sections) >= 1:
            score += 0.15
        
        # Has takeaways
        takeaways = synthesis.get("key_takeaways", [])
        if len(takeaways) >= 3:
            score += 0.20
        elif len(takeaways) >= 1:
            score += 0.10
        
        # Has limitations/further research
        if synthesis.get("limitations"):
            score += 0.075
        if synthesis.get("further_research"):
            score += 0.075
        
        return min(1.0, score)
    
    def calculate_completeness(self, synthesis: Dict, sources: List[Dict]) -> float:
        """Measure how complete the research is."""
        score = 0.0
        
        # Word count
        word_count = synthesis.get("word_count", 0)
        if word_count >= 500:
            score += 0.3
        elif word_count >= 200:
            score += 0.2
        elif word_count >= 100:
            score += 0.1
        
        # Source coverage
        num_sources = len(sources)
        if num_sources >= 5:
            score += 0.3
        elif num_sources >= 3:
            score += 0.2
        elif num_sources >= 1:
            score += 0.1
        
        # Section depth
        sections = synthesis.get("sections", [])
        total_section_words = sum(len(s.get("content", "").split()) for s in sections)
        if total_section_words >= 300:
            score += 0.25
        elif total_section_words >= 100:
            score += 0.15
        
        # Takeaways coverage
        if len(synthesis.get("key_takeaways", [])) >= 3:
            score += 0.15
        
        return min(1.0, score)
    
    def calculate_citation_accuracy(self, synthesis: Dict, sources: List[Dict]) -> float:
        """Measure citation coverage."""
        if not sources:
            return 0.0
        
        source_urls = set(s.get("url", "") for s in sources)
        
        # Check if sections reference sources
        sections = synthesis.get("sections", [])
        referenced = 0
        
        for section in sections:
            content = section.get("content", "").lower()
            for url in source_urls:
                domain = url.split("/")[2] if len(url.split("/")) > 2 else ""
                if domain and domain.split(".")[-2] in content:
                    referenced += 1
                    break
        
        # Base score on source count
        base_score = min(1.0, len(sources) / 5)
        
        return base_score
    
    def evaluate(self, query: str, findings: List[Dict], synthesis: Dict, sources: List[Dict]) -> Dict:
        """Run full evaluation and return scores."""
        scores = {
            "relevancy": self.calculate_relevancy(query, findings),
            "faithfulness": self.calculate_faithfulness(synthesis, sources),
            "coherence": self.calculate_coherence(synthesis),
            "completeness": self.calculate_completeness(synthesis, sources),
            "citation_accuracy": self.calculate_citation_accuracy(synthesis, sources)
        }
        
        # Calculate weighted overall score
        overall = sum(scores[k] * self.weights[k] for k in self.weights)
        scores["overall"] = overall
        
        # Add grade
        if overall >= 0.85:
            scores["grade"] = "A"
        elif overall >= 0.70:
            scores["grade"] = "B"
        elif overall >= 0.55:
            scores["grade"] = "C"
        else:
            scores["grade"] = "D"
        
        return scores
