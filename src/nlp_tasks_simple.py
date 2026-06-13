"""
Lightweight NLP Tasks: Intent Classification and Entity Extraction
Optimized for fast execution without large model downloads
"""

from typing import Dict, List, Tuple
from dataclasses import dataclass
import re
import json
from enum import Enum


class Intent(Enum):
    """E-commerce intent types"""
    SEARCH = "search"       # Product search/discovery
    PURCHASE = "purchase"   # Intent to buy
    REVIEW = "review"       # Want to rate/comment
    COMPLAINT = "complaint" # Report issue/refund
    INQUIRY = "inquiry"     # General question


class EntityType(Enum):
    """Entity types in e-commerce"""
    PRODUCT = "product"
    QUANTITY = "quantity"
    PRICE = "price"
    BRAND = "brand"
    COLOR = "color"
    SIZE = "size"
    LOCATION = "location"


@dataclass
class IntentPrediction:
    """Intent classification result"""
    text: str
    intent: str
    confidence: float
    reasoning: str


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


class RuleBasedIntentClassifier:
    """
    Rule-based intent classifier for e-commerce
    Uses keyword matching and linguistic patterns
    """

    # Intent keywords
    INTENT_PATTERNS = {
        Intent.SEARCH.value: [
            r'\b(looking for|search|find|where.*can.*get|do.*have|stock|available)\b',
            r'\b(show me|tell me about|what.*product)\b',
            r'\b(looking|want|need).*\w+(shoes|shirt|phone|laptop)',
        ],
        Intent.PURCHASE.value: [
            r'\b(buy|purchase|order|want to buy|checkout)\b',
            r'\b(add to|cart|proceed to payment|payment)\b',
            r'\b(i\'ll take it|sold|interested in buying)\b',
        ],
        Intent.COMPLAINT.value: [
            r'\b(complain|complaint|issue|problem|defect|broken|damaged)\b',
            r'\b(refund|return|money back|exchange)\b',
            r'\b(bad quality|poor|doesn\'t work|not as described)\b',
            r'\b(disappointed|upset|unsatisfied|wrong)\b',
        ],
        Intent.REVIEW.value: [
            r'\b(rate|review|rating|star|excellent|amazing|terrible|awful)\b',
            r'\b(recommend|don\'t recommend|opinion|thoughts)\b',
            r'\b(feedback|experience|my thoughts)\b',
        ],
        Intent.INQUIRY.value: [
            r'\b(how|why|when|what|where|can you|could you|would you)\b',
            r'\b(warranty|return policy|shipping|delivery)\b',
            r'\b(more information|details|specifications)\b',
        ]
    }

    def classify(self, text: str) -> IntentPrediction:
        """Classify intent using rule-based matching"""
        text_lower = text.lower()
        scores = {intent: 0.0 for intent in Intent}

        # Score each intent
        for intent_name, patterns in self.INTENT_PATTERNS.items():
            matches = 0
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    matches += 1
            scores[intent_name] = matches / len(patterns) if patterns else 0

        # Get top intent
        top_intent = max(scores.items(), key=lambda x: x[1])[0]
        confidence = scores[top_intent]

        # Boost confidence for strong matches
        if confidence == 0:
            top_intent = Intent.INQUIRY.value
            confidence = 0.5

        return IntentPrediction(
            text=text,
            intent=top_intent,
            confidence=min(confidence, 1.0),
            reasoning=f"Matched {int(scores[top_intent] * len(self.INTENT_PATTERNS[top_intent]))} patterns"
        )

    def classify_batch(self, texts: List[str]) -> List[IntentPrediction]:
        """Classify multiple texts"""
        return [self.classify(text) for text in texts]


class RuleBasedEntityExtractor:
    """
    Rule-based entity extractor for e-commerce
    Uses regex patterns for common entity types
    """

    # Entity patterns
    ENTITY_PATTERNS = {
        EntityType.PRICE.value: [
            (r'\$\d+\.?\d*', 'price_dollar'),
            (r'£\d+\.?\d*', 'price_pound'),
            (r'€\d+\.?\d*', 'price_euro'),
            (r'₹\d+\.?\d*', 'price_rupee'),
            (r'\d+\s*(dollars|pounds|euros|rupees|USD|GBP|EUR|INR)', 'price_named'),
        ],
        EntityType.QUANTITY.value: [
            (r'\b(\d+)\s*(pieces|pcs|items|units|qty|quantity|pack)\b', 'quantity_explicit'),
            (r'\b(one|two|three|four|five|six|seven|eight|nine|ten)\b', 'quantity_word'),
            (r'\b(\d+)\s*x\s*(\w+)', 'quantity_multiplier'),
        ],
        EntityType.BRAND.value: [
            (r'\b(Nike|Apple|Samsung|Microsoft|Sony|Google|Intel|AMD|HP|Dell|Lenovo|Adidas|Puma|Jordan|BMW|Audi|Mercedes)\b', 'brand_known'),
        ],
        EntityType.COLOR.value: [
            (r'\b(red|blue|green|yellow|black|white|gray|grey|pink|purple|orange|brown|silver|gold|turquoise|navy|beige)\b', 'color_basic'),
            (r'\b(dark|light|bright)\s+\w+', 'color_modifier'),
        ],
        EntityType.SIZE.value: [
            (r'\b(XS|S|M|L|XL|XXL|XXXL)\b', 'size_clothing'),
            (r'\b(\d+)\s*(cm|inch|inches|ft|feet|mm)\b', 'size_numeric'),
            (r'\b(small|medium|large|extra\s+large)\b', 'size_word'),
        ],
        EntityType.LOCATION.value: [
            (r'\b(New York|Los Angeles|Chicago|Houston|Phoenix|Philadelphia|San Antonio|San Diego|Dallas|San Jose|Austin|Seattle|Boston|Miami|Atlanta)\b', 'location_city'),
            (r'\b(USA|UK|Canada|Australia|Germany|France|Japan|India|China)\b', 'location_country'),
        ],
    }

    def extract(self, text: str) -> EntityExtractionResult:
        """Extract entities from text"""
        entities = []
        seen_spans = set()  # Avoid overlapping entities

        # Find all matches for each entity type
        for entity_type, patterns in self.ENTITY_PATTERNS.items():
            for pattern, pattern_name in patterns:
                for match in re.finditer(pattern, text, re.IGNORECASE):
                    span = (match.start(), match.end())

                    # Skip if overlaps with existing entity
                    if any(s <= span[0] < e or s < span[1] <= e for s, e in seen_spans):
                        continue

                    entity = Entity(
                        text=match.group(),
                        type=entity_type,
                        start=match.start(),
                        end=match.end(),
                        confidence=0.9  # Regex matches are high confidence
                    )
                    entities.append(entity)
                    seen_spans.add(span)

        # Sort by position
        entities.sort(key=lambda e: e.start)

        return EntityExtractionResult(
            text=text,
            entities=entities
        )

    def extract_batch(self, texts: List[str]) -> List[EntityExtractionResult]:
        """Extract entities from multiple texts"""
        return [self.extract(text) for text in texts]


class ConversationAnalyzer:
    """Combined intent + entity analysis for conversations"""

    def __init__(self):
        self.intent_classifier = RuleBasedIntentClassifier()
        self.entity_extractor = RuleBasedEntityExtractor()

    def analyze(self, text: str) -> Dict:
        """Analyze a single message"""
        intent_result = self.intent_classifier.classify(text)
        entity_result = self.entity_extractor.extract(text)

        return {
            'text': text,
            'intent': {
                'label': intent_result.intent,
                'confidence': float(intent_result.confidence),
                'reasoning': intent_result.reasoning
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
        """Analyze a full conversation"""
        return [self.analyze(msg) for msg in messages]

    def summarize_conversation(self, messages: List[str]) -> Dict:
        """Generate summary of conversation"""
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
        """Classify conversation type"""
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


# Demo Functions
def demo():
    """Run all demos"""
    print("\n" + "=" * 80)
    print("NLP TASKS DEMO: Intent Classification & Entity Extraction")
    print("=" * 80)

    analyzer = ConversationAnalyzer()

    # Test conversations
    print("\n" + "-" * 80)
    print("TEST 1: Product Search Conversation")
    print("-" * 80)

    conversation_1 = [
        "Hi, do you have the iPhone 15 Pro in silver?",
        "I'm interested in buying one",
        "What's the price and warranty?",
        "Can you ship it to New York?",
        "Great! I'll take it for $999. This is exactly what I needed!"
    ]

    print("\n📝 Messages:")
    for i, msg in enumerate(conversation_1, 1):
        print(f"  {i}. {msg}")

    print("\n🔍 Analysis:")
    analyses_1 = analyzer.analyze_conversation(conversation_1)
    for i, analysis in enumerate(analyses_1, 1):
        print(f"\n  Message {i}:")
        print(f"    Intent: {analysis['intent']['label']} (confidence: {analysis['intent']['confidence']:.2f})")
        print(f"    Reasoning: {analysis['intent']['reasoning']}")
        if analysis['entities']:
            print(f"    Entities:")
            for entity in analysis['entities']:
                print(f"      - '{entity['text']}' ({entity['type']})")

    summary_1 = analyzer.summarize_conversation(conversation_1)
    print(f"\n📊 Conversation Summary:")
    print(f"  Type: {summary_1['conversation_type']}")
    print(f"  Dominant Intent: {summary_1['dominant_intent']}")
    print(f"  Total Entities: {summary_1['entities_found']}")
    print(f"  Entity Types: {json.dumps(summary_1['entity_types'], indent=4)}")

    # Test with complaint
    print("\n" + "-" * 80)
    print("TEST 2: Complaint Conversation")
    print("-" * 80)

    conversation_2 = [
        "I purchased this Samsung Galaxy S24 for $800 last week",
        "But the screen has a defect, it's cracked",
        "I want a full refund or replacement",
        "The product is not as described in the listing"
    ]

    print("\n📝 Messages:")
    for i, msg in enumerate(conversation_2, 1):
        print(f"  {i}. {msg}")

    print("\n🔍 Analysis:")
    analyses_2 = analyzer.analyze_conversation(conversation_2)
    for i, analysis in enumerate(analyses_2, 1):
        print(f"\n  Message {i}:")
        print(f"    Intent: {analysis['intent']['label']} (confidence: {analysis['intent']['confidence']:.2f})")
        if analysis['entities']:
            entity_strs = [f"'{e['text']}' ({e['type']})" for e in analysis['entities']]
            print(f"    Entities: {', '.join(entity_strs)}")

    summary_2 = analyzer.summarize_conversation(conversation_2)
    print(f"\n📊 Conversation Summary:")
    print(f"  Type: {summary_2['conversation_type']}")
    print(f"  Dominant Intent: {summary_2['dominant_intent']}")
    print(f"  Total Entities: {summary_2['entities_found']}")

    # Test with complex query
    print("\n" + "-" * 80)
    print("TEST 3: Complex Product Query")
    print("-" * 80)

    complex_query = "I'm looking for 2 pairs of red Nike Air Max 90 shoes size 10 US, priced around $150 each, and I need them shipped to London"

    print(f"\n📝 Query: {complex_query}")
    analysis = analyzer.analyze(complex_query)

    print(f"\n🔍 Analysis:")
    print(f"  Intent: {analysis['intent']['label']} (confidence: {analysis['intent']['confidence']:.2f})")
    print(f"  Entities found: {analysis['entity_count']}")
    for entity in analysis['entities']:
        print(f"    - '{entity['text']}' ({entity['type']})")

    print("\n" + "=" * 80)
    print("✓ Demo Complete")
    print("=" * 80 + "\n")


if __name__ == '__main__':
    demo()
