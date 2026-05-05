"""
app.py — ComplianceCheck FastAPI Backend

Pipeline flow:
  1. NER (ner.py) — extract business_type, location, features from user text
  2. Knowledge Graph (knowledge_graph.py) — query structured permit requirements
  3a. [Modern] Tavily live search — real government sources, cited URLs (USE_TAVILY=True)
  3b. [Legacy] search.py + summarizer.py — local embeddings over regulations.json

USE_TAVILY=True by default. Set to False to use the legacy embedding pipeline.
Falls back to hardcoded mock data if all steps fail.
"""

import json
import os
import sys
from datetime import datetime

# Feature flag — True routes Step 3 through TavilySearchClient (live gov sources).
# Set USE_TAVILY=false in your environment to fall back to the local embedding pipeline.
USE_TAVILY = os.getenv("USE_TAVILY", "true").lower() != "false"

sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# NER loads independently — it has its own regex fallback if spaCy is missing
NER_AVAILABLE = False
SEARCH_AVAILABLE = False
KG_AVAILABLE = False
TAVILY_AVAILABLE = False

try:
    from pipeline.ner import extract_entities, entities_to_graph_input
    NER_AVAILABLE = True
    print("[app.py] NER loaded successfully")
except Exception as e:
    print(f"[app.py] NER unavailable ({e})")

try:
    from pipeline.search import retrieve_relevant_regulations
    from pipeline.summarizer import generate_output
    SEARCH_AVAILABLE = True
    print("[app.py] Search + summarizer loaded successfully")
except Exception as e:
    print(f"[app.py] Search/summarizer unavailable ({e}) — install sentence-transformers + transformers")

try:
    from pipeline.knowledge_graph import build_knowledge_graph, query_permits
    KG_AVAILABLE = True
    _kg = build_knowledge_graph()
    print("[app.py] Knowledge graph loaded successfully")
except Exception as e:
    print(f"[app.py] Knowledge graph unavailable ({e})")
    _kg = None

if USE_TAVILY:
    try:
        from apis import TavilySearchClient
        _tavily = TavilySearchClient()
        TAVILY_AVAILABLE = True
        print("[app.py] Tavily search loaded successfully (modern mode)")
    except Exception as e:
        print(f"[app.py] Tavily unavailable ({e}) — falling back to legacy search")
        _tavily = None
else:
    _tavily = None
    print("[app.py] USE_TAVILY=false — using legacy embedding pipeline")


app = FastAPI(title="ComplianceCheck API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        os.getenv("FRONTEND_URL", ""),
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    description: str
    business_type: str = ""
    location: str = ""
    business_name: str = ""


MOCK_RESPONSE = {
    "business_type": "restaurant",
    "business_label": "Restaurant",
    "location": "Koreatown",
    "features": ["liquor", "outdoor_dining"],
    "summary": (
        "A restaurant with alcohol service and outdoor dining in Koreatown requires "
        "permits from multiple city, county, and state agencies. The ABC liquor license "
        "can take 2–6 months — start this application early. A Public Health Permit is "
        "required before opening, and an Outdoor Dining Permit is needed for any patio "
        "or sidewalk seating. A Certificate of Occupancy must be obtained before "
        "opening to the public."
    ),
    "checklist": [
        {
            "id": "business_tax_registration",
            "title": "Business Tax Registration Certificate (BTRC)",
            "status": "required",
            "priority": "critical",
            "category": "licenses",
            "detail": "Required for all businesses operating within the City of Los Angeles.",
            "agency": "City of Los Angeles",
            "fee": "$0–$500/year",
            "timeline": "1–2 weeks",
            "renewal": "Annual",
        },
        {
            "id": "ein",
            "title": "Employer Identification Number (EIN)",
            "status": "required",
            "priority": "critical",
            "category": "licenses",
            "detail": "Federal tax ID required for bank accounts, hiring, and tax filings. Free from IRS.",
            "agency": "Federal Government",
            "fee": "Free",
            "timeline": "Immediate (online)",
            "renewal": "None — permanent",
        },
        {
            "id": "health_permit",
            "title": "Health Permit (Public Health)",
            "status": "required",
            "priority": "critical",
            "category": "permits",
            "detail": "Required before serving food. LA County Department of Public Health inspects sanitation, ventilation, and food storage.",
            "agency": "LA County",
            "fee": "$700–$2,000",
            "timeline": "4–8 weeks",
            "renewal": "Annual",
        },
        {
            "id": "fire_clearance",
            "title": "Fire Department Clearance",
            "status": "pending",
            "priority": "critical",
            "category": "inspections",
            "detail": "LAFD inspects fire safety, occupancy capacity, exit signage, and sprinkler systems.",
            "agency": "City of Los Angeles",
            "fee": "$200–$500",
            "timeline": "2–4 weeks",
            "renewal": "Annual inspection",
        },
        {
            "id": "certificate_of_occupancy",
            "title": "Certificate of Occupancy",
            "status": "pending",
            "priority": "critical",
            "category": "zoning",
            "detail": "Required before opening. Confirms compliance with zoning, building code, and safety requirements.",
            "agency": "City of Los Angeles",
            "fee": "Included with building permit",
            "timeline": "2–6 weeks after final inspection",
            "renewal": "Per change of use",
        },
        {
            "id": "abc_license",
            "title": "ABC Liquor License",
            "status": "required",
            "priority": "high",
            "category": "licenses",
            "detail": "Required to sell or serve alcoholic beverages. Type 41 (beer/wine) or Type 47 (full liquor). Start this application early — it takes months.",
            "agency": "State of California",
            "fee": "$1,000–$15,000+",
            "timeline": "2–6 months",
            "renewal": "Annual",
        },
        {
            "id": "outdoor_dining_permit",
            "title": "Sidewalk/Outdoor Dining Permit",
            "status": "required",
            "priority": "medium",
            "category": "permits",
            "detail": "Required for dining on public sidewalks or rights-of-way. Requires site plan showing pedestrian clearance and ADA compliance.",
            "agency": "City of Los Angeles",
            "fee": "$500–$2,000",
            "timeline": "4–8 weeks",
            "renewal": "Annual",
        },
        {
            "id": "sellers_permit",
            "title": "Seller's Permit",
            "status": "required",
            "priority": "critical",
            "category": "licenses",
            "detail": "Required by CDTFA for collecting California sales tax on food sales.",
            "agency": "State of California",
            "fee": "Free",
            "timeline": "1–2 weeks",
            "renewal": "None unless business changes",
        },
    ],
    "sources": [
        {"title": "LA County Food Facility Health Permit", "agency": "LACDPH", "score": 0.91},
        {"title": "ABC Retail License Types", "agency": "CA Dept of Alcoholic Beverage Control", "score": 0.87},
        {"title": "Outdoor Dining Permit Requirements", "agency": "City of LA LADOT", "score": 0.83},
    ],
    "mock": True,
}


def _priority_to_status(priority: str) -> str:
    """Map knowledge graph priority to frontend status."""
    if priority in ("critical", "high"):
        return "required"
    return "pending"


def _load_regulations(business_type: str, features: list) -> list:
    """Load and filter regulations.json by business_type and features."""
    try:
        reg_path = os.path.join(os.path.dirname(__file__), "data", "regulations.json")
        with open(reg_path, "r") as f:
            all_regs = json.load(f)
    except Exception:
        return []

    results = []
    for reg in all_regs:
        bt = reg.get("business_type", [])
        if isinstance(bt, str):
            bt = [bt]
        if business_type and business_type not in bt:
            continue
        reg_features = reg.get("features", [])
        # Include if no feature requirement, or if user has the required feature
        if reg_features and not any(f in features for f in reg_features):
            continue
        results.append(reg)
    return results


def _match_tavily_url(reg: dict, tavily_results: list) -> str:
    """Find the best matching Tavily URL for a regulation by keyword overlap."""
    reg_words = set(
        (reg.get("title", "") + " " + reg.get("agency", "")).lower().split()
    )
    best_url, best_score = "", 0
    for r in tavily_results:
        result_words = set((r.title + " " + r.content[:200]).lower().split())
        score = len(reg_words & result_words)
        if score > best_score:
            best_score = score
            best_url = r.url
    return best_url


def _regulations_to_checklist(regulations: list, tavily_results: list) -> list:
    """Convert regulations.json entries into structured checklist items, enriched with Tavily URLs."""
    priority_map = {"permits": "high", "licenses": "critical", "inspections": "high", "zoning": "medium"}
    items = []
    for reg in regulations:
        category = reg.get("category", "permits")
        priority = priority_map.get(category, "high")
        url = _match_tavily_url(reg, tavily_results) if tavily_results else ""
        items.append({
            "id": reg.get("id", ""),
            "title": reg.get("title", ""),
            "status": "required" if priority in ("critical", "high") else "pending",
            "priority": priority,
            "category": category,
            "detail": reg.get("text", ""),
            "agency": reg.get("agency", ""),
            "fee": reg.get("fee", ""),
            "timeline": reg.get("timeline", ""),
            "renewal": "",
            "url": url,
        })
    return items


def _label_to_category(label: str, permit_id: str) -> str:
    """Infer checklist category from permit label and ID."""
    label_lower = label.lower()
    if any(w in label_lower for w in ["inspect", "fire", "clearance"]):
        return "inspections"
    if any(w in label_lower for w in ["zoning", "occupancy", "building permit", "conditional use"]):
        return "zoning"
    if any(w in label_lower for w in ["license", "seller", "registration", "ein", "abc", "cslb", "cosmetology", "handler", "manager cert", "workers"]):
        return "licenses"
    return "permits"


@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "ner_loaded": NER_AVAILABLE,
    "search_loaded": SEARCH_AVAILABLE,
        "kg_loaded": KG_AVAILABLE,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/api/analyze")
def analyze(request: AnalyzeRequest):
    description = request.description.strip()
    if not description:
        raise HTTPException(status_code=400, detail="Description is required")

    if not NER_AVAILABLE and not KG_AVAILABLE and not TAVILY_AVAILABLE:
        return MOCK_RESPONSE

    try:
        # Step 1: NER — extract features/capacity from text, but override
        # business_type and location with explicit form values if provided
        if NER_AVAILABLE:
            entities = extract_entities(description)
            graph_input = entities_to_graph_input(entities)
        else:
            graph_input = {"business_type": None, "features": [], "location": "Los Angeles", "capacity": None}

        # Explicit form fields always win over NER extraction
        business_type = request.business_type.strip() or graph_input.get("business_type")
        location = request.location.strip() or graph_input.get("location") or "Los Angeles"
        features = graph_input.get("features") or []

        checklist_items = []
        kg_summary = ""
        kg_sources = []
        business_label = business_type or "business"

        # Step 2: Knowledge Graph — only used when Tavily is unavailable
        if not TAVILY_AVAILABLE and KG_AVAILABLE and _kg and business_type and business_type in _kg.nodes:
            kg_result = query_permits(_kg, business_type, features)
            kg_summary = kg_result.get("summary", "")
            business_label = kg_result.get("business_label", business_type)

            for permit in kg_result.get("all_permits", []):
                checklist_items.append({
                    "id": permit.get("id", ""),
                    "title": permit.get("label", ""),
                    "status": _priority_to_status(permit.get("priority", "medium")),
                    "priority": permit.get("priority", "medium"),
                    "category": _label_to_category(permit.get("label", ""), permit.get("id", "")),
                    "detail": permit.get("description", ""),
                    "agency": permit.get("issued_by", ""),
                    "fee": permit.get("est_cost", ""),
                    "timeline": permit.get("processing_time", ""),
                    "renewal": permit.get("renewal", ""),
                })

        # Step 3: Search — Tavily (default) or local embeddings (legacy fallback)
        nlp_summary = kg_summary
        if TAVILY_AVAILABLE and _tavily:
            try:
                tavily_resp = _tavily.search_regulations(
                    topic=f"required permits licenses {business_type} {location}",
                    business_type=business_type,
                    location=location,
                )
                if tavily_resp.succeeded:
                    nlp_summary = tavily_resp.summary or kg_summary
                    kg_sources = [
                        {
                            "title": r.title,
                            "agency": r.source_domain,
                            "score": r.score,
                            "url": r.url,
                        }
                        for r in tavily_resp.results
                    ]

                # Build checklist from regulations.json (clean permit names/descriptions)
                # enriched with matched Tavily URLs as sources
                if not checklist_items and business_type:
                    regulations = _load_regulations(business_type, features)
                    checklist_items = _regulations_to_checklist(
                        regulations,
                        tavily_resp.results if tavily_resp.succeeded else [],
                    )
            except Exception as e:
                print(f"[app.py] Tavily error: {e}")

        elif SEARCH_AVAILABLE:
            try:
                regulations = retrieve_relevant_regulations(
                    query=description,
                    filters=graph_input,
                    top_k=5,
                )
                if regulations:
                    output = generate_output(regulations)
                    nlp_summary = output.get("summary", kg_summary) or kg_summary
                    kg_sources = output.get("sources", [])
                    if not checklist_items:
                        for i, item_text in enumerate(output.get("checklist", []), start=1):
                            checklist_items.append({
                                "id": str(i),
                                "title": item_text.replace("Review requirement: ", "").strip(),
                                "status": "required",
                                "priority": "high",
                                "category": "permits",
                                "detail": "",
                                "agency": "",
                                "fee": "",
                                "timeline": "",
                                "renewal": "",
                            })
            except Exception as e:
                print(f"[app.py] Search/summarizer error: {e}")

        if not checklist_items and not nlp_summary:
            return MOCK_RESPONSE

        return {
            "business_name": request.business_name.strip(),
            "business_type": business_type or "business",
            "business_label": business_label,
            "location": location,
            "features": features,
            "description": description,
            "summary": nlp_summary or kg_summary,
            "checklist": checklist_items,
            "sources": kg_sources,
            "mock": False,
        }

    except Exception as e:
        print(f"[app.py] Error: {e} — returning mock data")
        return MOCK_RESPONSE


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
