"""
NLP Task Modules: Intent Classification and Entity Extraction
For e-commerce conversations (buyer-seller interactions)
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass
import json
from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer
import numpy as np


@dataclass
class IntentPrediction:
    """Intent classification result"""
    text: str
    intent: str
    confidence: float
    all_scores: Dict[str, float]


@dataclass
class Entity:
    """Extracted entity"""
    text: str
    type: str
    start: int
    end: int
    confidence: float


@dataclass
class EntityExtractionResult:
    """Entity extraction result"""
    text: str
    entities: List[Entity]
    raw_entities: list  # Original NER output


class IntentClassifier:
    """
    Intent classification for e-commerce queries
    Supports 5 intent classes: search, purchase, review, complaint, inquiry
    """

    INTENT_LABELS = {
        0: "search",     # Looking for products
        1: "purchase",   # Intent to buy
        2: "review",     # Want to review/rate
        3: "complaint",  # Report issue
        4: "inquiry"     # General question
    }

    def __init__(self, model_name: str = "distilbert-base-uncased-finetuned-sst-2-english"):
        """
        Initialize intent classifier
        Uses zero-shot classification for flexibility
        """
        self.zero_shot = pipeline(
            "zero-shot-classification",
            model="facebook/bart-large-mnli",
            device=-1  # CPU
        )
        self.intent_candidates = list(self.INTENT_LABELS.values())

    def classify(self, text: str) -> IntentPrediction:
        """
        Classify intent of input text

        Args:
            text: Input query

        Returns:
            IntentPrediction with intent and confidence
        """
        result = self.zero_shot(text, self.intent_candidates, multi_class=False)

        # Build scores dict
        scores = {label: 0.0 for label in self.intent_candidates}
        for label, score in zip(result['labels'], result['scores']):
            scores[label] = score

        top_intent = result['labels'][0]
        confidence = result['scores'][0]

        return IntentPrediction(
            text=text,
            intent=top_intent,
            confidence=confidence,
            all_scores=scores
        )

    def classify_batch(self, texts: List[str]) -> List[IntentPrediction]:
        """Classify multiple texts"""
        return [self.classify(text) for text in texts]


class EntityExtractor:
    """
    Named Entity Recognition for e-commerce
    Extracts: product, quantity, price, brand, color, size, etc.
    """

    ENTITY_TYPES = {
        'PRODUCT': 'Product/Item',
        'QUANTITY': 'Quantity/Number',
        'PRICE': 'Price/Cost',
        'BRAND': 'Brand',
        'COLOR': 'Color',
        'SIZE': 'Size',
        'LOCATION': 'Location',
        'ORG': 'Organization'
    }

    def __init__(self, model_name: str = "dbmdz/bert-base-multilingual-cased"):
        """
        Initialize entity extractor with multilingual NER
        """
        self.ner = pipeline(
            "ner",
            model="bert-base-multilingual-cased",
            aggregation_strategy="simple",
            device=-1  # CPU
        )

    def extract(self, text: str) -> EntityExtractionResult:
        """
        Extract entities from text

        Args:
            text: Input text

        Returns:
            EntityExtractionResult with list of entities
        """
        raw_entities = self.ner(text)

        # Convert NER output to Entity objects
        entities = []
        for entity in raw_entities:
            # Normalize entity type
            entity_type = entity['entity_group']

            entities.append(Entity(
                text=entity['word'],
                type=entity_type,
                start=entity.get('start', -1),
                end=entity.get('end', -1),
                confidence=entity['score']
            ))

        return EntityExtractionResult(
            text=text,
            entities=entities,
            raw_entities=raw_entities
        )

    def extract_batch(self, texts: List[str]) -> List[EntityExtractionResult]:
        """Extract entities from multiple texts"""
        return [self.extract(text) for text in texts]


class ConversationAnalyzer:
    """
    Combined intent + entity analysis for e-commerce conversations
    Analyzes buyer-seller interactions
    """

    def __init__(self):
        self.intent_classifier = IntentClassifier()
        self.entity_extractor = EntityExtractor()

    def analyze(self, text: str) -> Dict:
        """
        Analyze a single message for intent and entities

        Args:
            text: Single message

        Returns:
            Dict with intent and entities
        """
        intent_result = self.intent_classifier.classify(text)
        entity_result = self.entity_extractor.extract(text)

        return {
            'text': text,
            'intent': {
                'label': intent_result.intent,
                'confidence': float(intent_result.confidence),
                'all_scores': {k: float(v) for k, v in intent_result.all_scores.items()}
            },
            'entities': [
                {
                    'text': e.text,
                    'type': e.type,
                    'confidence': float(e.confidence),
                    'start': e.start,
                    'end': e.end
                }
                for e in entity_result.entities
            ],
            'entity_count': len(entity_result.entities)
        }

    def analyze_conversation(self, messages: List[str]) -> List[Dict]:
        """
        Analyze a full conversation (list of messages)

        Args:
            messages: List of message texts

        Returns:
            List of analysis results
        """
        return [self.analyze(msg) for msg in messages]

    def summarize_conversation(self, messages: List[str]) -> Dict:
        """
        Generate summary of conversation

        Args:
            messages: List of message texts

        Returns:
            Conversation summary
        """
        analyses = self.analyze_conversation(messages)

        # Count intents
        intent_counts = {}
        for analysis in analyses:
            intent = analysis['intent']['label']
            intent_counts[intent] = intent_counts.get(intent, 0) + 1

        # Aggregate entities
        entity_types = {}
        all_entities = []
        for analysis in analyses:
            for entity in analysis['entities']:
                entity_types[entity['type']] = entity_types.get(entity['type'], 0) + 1
                all_entities.append(entity)

        return {
            'total_messages': len(messages),
            'intent_distribution': intent_counts,
            'entity_types': entity_types,
            'entities_found': len(all_entities),
            'dominant_intent': max(intent_counts.items(), key=lambda x: x[1])[0] if intent_counts else None,
            'conversation_type': self._classify_conversation_type(intent_counts)
        }

    @staticmethod
    def _classify_conversation_type(intent_counts: Dict[str, int]) -> str:
        """Classify conversation type based on intent distribution"""
        if not intent_counts:
            return 'unknown'

        total = sum(intent_counts.values())
        dominant = max(intent_counts.items(), key=lambda x: x[1])[0]

        dominance = intent_counts[dominant] / total

        if dominance > 0.6:
            return f'primarily_{dominant}'
        elif intent_counts.get('purchase', 0) > 0:
            return 'transactional'
        elif intent_counts.get('complaint', 0) > 0:
            return 'support'
        else:
            return 'inquiry'


# Demo/Test Functions
def demo_intent_classification():
    """Demo intent classification"""
    print("\n" + "=" * 70)
    print("INTENT CLASSIFICATION DEMO")
    print("=" * 70)

    classifier = IntentClassifier()

    test_queries = [
        "I'm looking for red Nike running shoes",
        "I want to buy this product",
        "This item has a defect, I need a refund",
        "Can you tell me more about the warranty?",
        "This product is amazing, I give it 5 stars"
    ]

    for query in test_queries:
        result = classifier.classify(query)
        print(f"\nQuery: {query}")
        print(f"Intent: {result.intent} (confidence: {result.confidence:.3f})")
        print(f"Scores: {json.dumps({k: f'{v:.3f}' for k, v in result.all_scores.items()}, indent=2)}")


def demo_entity_extraction():
    """Demo entity extraction"""
    print("\n" + "=" * 70)
    print("ENTITY EXTRACTION DEMO")
    print("=" * 70)

    extractor = EntityExtractor()

    test_texts = [
        "I want to buy 2 red Nike Air Max 90 shoes for $150",
        "Do you have the iPhone 15 in blue?",
        "This Adidas jacket is defective, I bought it last week"
    ]

    for text in test_texts:
        result = extractor.extract(text)
        print(f"\nText: {text}")
        print(f"Entities found: {len(result.entities)}")
        for entity in result.entities:
            print(f"  - {entity.text} ({entity.type}) - confidence: {entity.confidence:.3f}")


def demo_conversation_analysis():
    """Demo full conversation analysis"""
    print("\n" + "=" * 70)
    print("CONVERSATION ANALYSIS DEMO")
    print("=" * 70)

    analyzer = ConversationAnalyzer()

    # Sample e-commerce conversation
    conversation = [
        "Hi, do you have the iPhone 15 Pro in silver?",
        "I'm interested in buying one",
        "What's the price and warranty?",
        "Can you ship it to New York?",
        "Great! I'll take it. This is exactly what I needed!"
    ]

    print("\n📝 Conversation:")
    for i, msg in enumerate(conversation, 1):
        print(f"  {i}. {msg}")

    print("\n🔍 Detailed Analysis:")
    analyses = analyzer.analyze_conversation(conversation)
    for i, analysis in enumerate(analyses, 1):
        print(f"\n  Message {i}: {analysis['text'][:50]}...")
        print(f"    Intent: {analysis['intent']['label']} ({analysis['intent']['confidence']:.3f})")
        print(f"    Entities: {analysis['entity_count']}")
        for entity in analysis['entities']:
            print(f"      - {entity['text']} ({entity['type']})")

    print("\n📊 Conversation Summary:")
    summary = analyzer.summarize_conversation(conversation)
    print(f"  Total messages: {summary['total_messages']}")
    print(f"  Dominant intent: {summary['dominant_intent']}")
    print(f"  Conversation type: {summary['conversation_type']}")
    print(f"  Intent distribution: {json.dumps(summary['intent_distribution'], indent=4)}")
    print(f"  Entities by type: {json.dumps(summary['entity_types'], indent=4)}")


if __name__ == '__main__':
    print("NLP Task Modules Demo")
    demo_intent_classification()
    demo_entity_extraction()
    demo_conversation_analysis()
