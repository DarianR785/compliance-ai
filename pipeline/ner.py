"""
ner.py — Named Entity Recognition for Small Business Compliance Intake

Extracts structured entities from freeform business descriptions:
  - BUSINESS_TYPE: restaurant, salon, food_truck, contractor, retail
  - LOCATION: city, neighborhood, address
  - FEATURE: liquor, outdoor dining, live entertainment, etc.
  - CAPACITY: seating count, square footage
  - BUSINESS_NAME: the user's business name (if provided)

Uses spaCy with a custom EntityRuler for domain-specific pattern matching
layered on top of the base en_core_web_sm model for general NER (locations,
organizations, etc.).

Falls back to a regex/keyword-based extractor if spaCy model is unavailable.
"""

import re
import sys
from typing import Optional

# Import the knowledge graph to pull aliases and triggers dynamically
sys.path.insert(0, ".")
from pipeline.knowledge_graph import get_business_aliases, get_feature_triggers


# Try loading spaCy — fall back to rule-based if unavailable
try:
    import spacy
    from spacy.language import Language
    from spacy.tokens import Span

    # Verify the model is actually installed
    spacy.load("en_core_web_sm")
    SPACY_AVAILABLE = True
except (ImportError, OSError):
    SPACY_AVAILABLE = False
    print("[ner.py] spaCy model not available — using rule-based fallback")


def _build_spacy_pipeline():
    """
    Build the spaCy NLP pipeline with custom EntityRuler patterns.
    """
    nlp = spacy.load("en_core_web_sm")

    # Create the EntityRuler and add it BEFORE the default NER
    # so our domain patterns take priority
    ruler = nlp.add_pipe("entity_ruler", before="ner")

    patterns = []

    # Business type patterns
    aliases = get_business_aliases()
    for btype_id, alias_list in aliases.items():
        for alias in alias_list:
            # Exact token match (case-insensitive via LOWER)
            tokens = alias.lower().split()
            pattern = {
                "label": "BUSINESS_TYPE",
                "pattern": [{"LOWER": t} for t in tokens],
                "id": btype_id,
            }
            patterns.append(pattern)

    # Feature / condition patterns
    feature_keywords = {
        "liquor": [
            "liquor", "alcohol", "alcoholic", "beer", "wine", "cocktail",
            "cocktails", "bar", "drinks", "spirits", "brewery", "taproom",
            "happy hour", "full bar", "beer and wine",
        ],
        "outdoor_dining": [
            "outdoor dining", "outdoor seating", "patio", "rooftop",
            "sidewalk dining", "al fresco", "terrace", "outdoor area",
            "beer garden", "rooftop patio", "outdoor patio",
        ],
        "live_entertainment": [
            "live music", "live entertainment", "dj", "karaoke",
            "dancing", "live band", "live performance", "comedy",
            "open mic", "trivia night",
        ],
        "home_based": [
            "home based", "home business", "from home", "from my home",
            "garage", "home office", "residential", "work from home",
            "out of my house", "out of my apartment",
        ],
        "employees": [
            "employees", "hire", "hiring", "staff", "workers", "team members",
        ],
        "signage": [
            "sign", "signage", "neon sign", "awning", "banner", "marquee",
        ],
        "construction": [
            "renovation", "remodel", "build out", "buildout", "tenant improvement",
            "construction", "new build", "convert", "converting",
        ],
    }

    for feature_id, keywords in feature_keywords.items():
        for kw in keywords:
            tokens = kw.lower().split()
            pattern = {
                "label": "FEATURE",
                "pattern": [{"LOWER": t} for t in tokens],
                "id": feature_id,
            }
            patterns.append(pattern)

    # Capacity patterns (number + seats/sqft/etc.)
    capacity_indicators = [
        "seats", "seat", "seating", "capacity", "people", "guests",
        "sqft", "sq ft", "square feet", "square foot",
    ]
    for indicator in capacity_indicators:
        tokens = indicator.lower().split()
        # Pattern: NUMBER + indicator (e.g., "80 seats")
        pattern = {
            "label": "CAPACITY",
            "pattern": [{"LIKE_NUM": True}] + [{"LOWER": t} for t in tokens],
        }
        patterns.append(pattern)
        # Pattern: indicator + NUMBER (e.g., "seats 80" or "capacity: 80")
        pattern_rev = {
            "label": "CAPACITY",
            "pattern": [{"LOWER": t} for t in tokens]
                       + [{"IS_PUNCT": True, "OP": "?"}]
                       + [{"LIKE_NUM": True}],
        }
        patterns.append(pattern_rev)

    # LA neighborhood / area patterns
    la_neighborhoods = [
        "koreatown", "hollywood", "west hollywood", "silver lake",
        "echo park", "downtown la", "downtown los angeles", "dtla",
        "venice", "santa monica", "culver city", "pasadena",
        "glendale", "burbank", "long beach", "inglewood",
        "highland park", "eagle rock", "los feliz", "atwater village",
        "arts district", "chinatown", "little tokyo", "boyle heights",
        "east la", "east los angeles", "westwood", "brentwood",
        "mar vista", "playa del rey", "el segundo", "torrance",
        "redondo beach", "hermosa beach", "manhattan beach",
    ]
    for neighborhood in la_neighborhoods:
        tokens = neighborhood.lower().split()
        pattern = {
            "label": "LOCATION",
            "pattern": [{"LOWER": t} for t in tokens],
        }
        patterns.append(pattern)

    ruler.add_patterns(patterns)
    return nlp


def _extract_with_spacy(text: str, nlp) -> dict:
    """Extract entities using the spaCy pipeline."""
    doc = nlp(text)

    entities = {
        "business_type": [],
        "location": [],
        "features": [],
        "capacity": [],
        "business_name": [],
        "raw_entities": [],  # All entities for debugging
    }

    seen_features = set()

    for ent in doc.ents:
        entity_record = {
            "text": ent.text,
            "label": ent.label_,
            "start": ent.start_char,
            "end": ent.end_char,
            "ent_id": ent.ent_id_ if ent.ent_id_ else None,
        }
        entities["raw_entities"].append(entity_record)

        if ent.label_ == "BUSINESS_TYPE":
            entities["business_type"].append({
                "text": ent.text,
                "id": ent.ent_id_,
                "confidence": "rule-matched",
            })
        elif ent.label_ == "FEATURE":
            if ent.ent_id_ not in seen_features:
                seen_features.add(ent.ent_id_)
                entities["features"].append({
                    "text": ent.text,
                    "id": ent.ent_id_,
                    "confidence": "rule-matched",
                })
        elif ent.label_ == "CAPACITY":
            # Extract the numeric value
            nums = re.findall(r"\d+", ent.text)
            if nums:
                entities["capacity"].append({
                    "text": ent.text,
                    "value": int(nums[0]),
                    "confidence": "rule-matched",
                })
        elif ent.label_ in ("GPE", "LOC", "LOCATION"):
            entities["location"].append({
                "text": ent.text,
                "label": ent.label_,
                "confidence": "model" if ent.label_ in ("GPE", "LOC") else "rule-matched",
            })
        elif ent.label_ == "ORG":
            # Potential business name — heuristic: if it's not a known
            # government agency or common entity, treat as business name
            known_orgs = {"fda", "usda", "irs", "sba", "osha", "abc", "ladbs"}
            if ent.text.lower() not in known_orgs:
                entities["business_name"].append({
                    "text": ent.text,
                    "confidence": "model-inferred",
                })

    return entities


def _extract_with_regex(text: str) -> dict:
    """
    Fallback regex/keyword-based entity extraction.
    Used when spaCy is not available.
    """
    text_lower = text.lower()
    entities = {
        "business_type": [],
        "location": [],
        "features": [],
        "capacity": [],
        "business_name": [],
        "raw_entities": [],
    }

    # Business type
    aliases = get_business_aliases()
    for btype_id, alias_list in aliases.items():
        # Sort by length (longest first) to match multi-word aliases first
        sorted_aliases = sorted(alias_list, key=len, reverse=True)
        for alias in sorted_aliases:
            pattern = r"\b" + re.escape(alias.lower()) + r"\b"
            if re.search(pattern, text_lower):
                if not any(b["id"] == btype_id for b in entities["business_type"]):
                    entities["business_type"].append({
                        "text": alias,
                        "id": btype_id,
                        "confidence": "keyword-matched",
                    })
                break  # Only match one alias per business type

    # Features
    feature_keywords = {
        "liquor": [
            "liquor", "alcohol", "beer", "wine", "cocktail", "bar",
            "drinks", "spirits", "full bar", "happy hour",
        ],
        "outdoor_dining": [
            "outdoor dining", "outdoor seating", "patio", "rooftop",
            "sidewalk dining", "al fresco", "terrace", "beer garden",
        ],
        "live_entertainment": [
            "live music", "live entertainment", "dj", "karaoke",
            "dancing", "live band", "comedy", "open mic",
        ],
        "home_based": [
            "home based", "home business", "from home", "from my home",
            "garage", "home office", "residential",
        ],
        "employees": ["employees", "hire", "hiring", "staff", "workers"],
        "signage": ["sign", "signage", "neon sign", "awning", "banner"],
        "construction": [
            "renovation", "remodel", "build out", "buildout",
            "tenant improvement", "construction", "converting",
        ],
    }

    for feature_id, keywords in feature_keywords.items():
        sorted_kw = sorted(keywords, key=len, reverse=True)
        for kw in sorted_kw:
            pattern = r"\b" + re.escape(kw.lower()) + r"\b"
            if re.search(pattern, text_lower):
                entities["features"].append({
                    "text": kw,
                    "id": feature_id,
                    "confidence": "keyword-matched",
                })
                break

    # Capacity
    cap_patterns = [
        r"(\d+)\s*(?:seats?|seating|capacity|people|guests)",
        r"(?:seats?|seating|capacity)\s*(?:of|:)?\s*(\d+)",
        r"(\d+)\s*(?:sq\.?\s*ft|square\s*feet|sqft)",
    ]
    for pat in cap_patterns:
        match = re.search(pat, text_lower)
        if match:
            val = int(match.group(1))
            entities["capacity"].append({
                "text": match.group(0),
                "value": val,
                "confidence": "regex-matched",
            })
            break

    # Location (LA neighborhoods)
    la_neighborhoods = [
        "koreatown", "hollywood", "west hollywood", "silver lake",
        "echo park", "downtown la", "downtown los angeles", "dtla",
        "venice", "santa monica", "culver city", "pasadena",
        "glendale", "burbank", "long beach", "inglewood",
        "highland park", "eagle rock", "los feliz", "atwater village",
        "arts district", "chinatown", "little tokyo", "boyle heights",
        "east la", "east los angeles", "westwood", "brentwood",
        "los angeles", "la",
    ]
    # Sort longest first
    for neighborhood in sorted(la_neighborhoods, key=len, reverse=True):
        pattern = r"\b" + re.escape(neighborhood) + r"\b"
        if re.search(pattern, text_lower):
            entities["location"].append({
                "text": neighborhood.title(),
                "label": "GPE",
                "confidence": "keyword-matched",
            })
            break  # Take the most specific match

    return entities


# Public API

# Cache the pipeline so we only load once
_nlp_pipeline = None

def extract_entities(text: str) -> dict:
    """
    Extract structured entities from a freeform business description.

    Args:
        text: Natural language business description
              e.g. "I'm opening a Korean BBQ restaurant with a full bar
                    and rooftop patio in Koreatown, about 80 seats"

    Returns:
        dict with keys:
            business_type: list of detected business types with IDs
            location: list of detected locations
            features: list of detected features (liquor, patio, etc.)
            capacity: list of detected capacity values
            business_name: list of potential business names
            raw_entities: all entities for debugging
            method: 'spacy' or 'regex' indicating which extractor was used
    """
    global _nlp_pipeline

    if SPACY_AVAILABLE:
        if _nlp_pipeline is None:
            print("[ner.py] Loading spaCy pipeline (first call)...")
            _nlp_pipeline = _build_spacy_pipeline()
        entities = _extract_with_spacy(text, _nlp_pipeline)
        entities["method"] = "spacy"
    else:
        entities = _extract_with_regex(text)
        entities["method"] = "regex"

    return entities


def entities_to_graph_input(entities: dict) -> dict:
    """
    Convert extracted entities into the format expected by
    knowledge_graph.query_permits().

    Returns:
        dict with:
            business_type: str (first detected type ID, or None)
            features: list[str] (feature IDs)
            location: str (first detected location text, or 'Los Angeles')
            capacity: int or None
    """
    business_type = None
    if entities["business_type"]:
        business_type = entities["business_type"][0]["id"]

    features = [f["id"] for f in entities["features"]]

    location = "Los Angeles"
    if entities["location"]:
        location = entities["location"][0]["text"]

    capacity = None
    if entities["capacity"]:
        capacity = entities["capacity"][0]["value"]

    return {
        "business_type": business_type,
        "features": features,
        "location": location,
        "capacity": capacity,
    }

# Test
if __name__ == "__main__":
    test_inputs = [
        "I'm opening a Korean BBQ restaurant with a full bar and rooftop patio in Koreatown, about 80 seats",
        "Starting a hair salon in Silver Lake, planning to do some renovation on the space",
        "I want to launch a food truck selling tacos in downtown LA",
        "Opening a small boutique clothing store in Santa Monica with a neon sign out front",
        "I'm a general contractor based in Pasadena, planning to hire 5 employees",
        "Converting my garage into a home bakery in Echo Park",
    ]

    for text in test_inputs:
        print(f"\n{'='*70}")
        print(f"INPUT: {text}")
        print(f"{'='*70}")

        entities = extract_entities(text)
        graph_input = entities_to_graph_input(entities)

        print(f"  Method: {entities['method']}")
        print(f"  Business Type: {entities['business_type']}")
        print(f"  Location:      {entities['location']}")
        print(f"  Features:      {entities['features']}")
        print(f"  Capacity:      {entities['capacity']}")
        print(f"\n  → Graph Input: {graph_input}")