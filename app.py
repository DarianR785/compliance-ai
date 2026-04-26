"""
app.py — ComplianceCheck FastAPI Backend

Pipeline flow:
  1. NER (ner.py) — extract business_type, location, features from user text
  2. Knowledge Graph (knowledge_graph.py) — query structured permit requirements
  3. Semantic Search (search.py) — retrieve relevant regulation texts via embeddings
  4. Summarizer (summarizer.py) — BART/extractive summary of regulation texts

Falls back to hardcoded mock data if ML dependencies are not installed.
"""

import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Try to load the NLP pipeline — graceful fallback if dependencies missing
PIPELINE_AVAILABLE = False
KG_AVAILABLE = False

try:
    from pipeline.ner import extract_entities, entities_to_graph_input
    from pipeline.search import retrieve_relevant_regulations
    from pipeline.summarizer import generate_output
    PIPELINE_AVAILABLE = True
    print("[app.py] NLP pipeline loaded successfully")
except Exception as e:
    print(f"[app.py] NLP pipeline unavailable ({e})")

try:
    from pipeline.knowledge_graph import build_knowledge_graph, query_permits
    KG_AVAILABLE = True
    _kg = build_knowledge_graph()
    print("[app.py] Knowledge graph loaded successfully")
except Exception as e:
    print(f"[app.py] Knowledge graph unavailable ({e})")
    _kg = None


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
        "pipeline_loaded": PIPELINE_AVAILABLE,
        "kg_loaded": KG_AVAILABLE,
        "timestamp": datetime.utcnow().isoformat(),
    }


@app.post("/api/analyze")
def analyze(request: AnalyzeRequest):
    description = request.description.strip()
    if not description:
        raise HTTPException(status_code=400, detail="Description is required")

    # If neither the NLP pipeline nor knowledge graph is available, use mock
    if not PIPELINE_AVAILABLE and not KG_AVAILABLE:
        return MOCK_RESPONSE

    try:
        # Step 1: NER — extract structured entities from user text
        if PIPELINE_AVAILABLE:
            entities = extract_entities(description)
            graph_input = entities_to_graph_input(entities)
        else:
            graph_input = {"business_type": None, "features": [], "location": "Los Angeles", "capacity": None}

        business_type = graph_input.get("business_type")
        features = graph_input.get("features") or []
        location = graph_input.get("location") or "Los Angeles"

        # Step 2: Knowledge Graph — get structured permit requirements
        checklist_items = []
        kg_summary = ""
        kg_sources = []

        if KG_AVAILABLE and _kg and business_type and business_type in _kg.nodes:
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
        else:
            business_label = business_type or "business"

        # Step 3: Semantic Search — retrieve regulation texts using embeddings
        # and cosine similarity (SentenceTransformer from search.py)
        nlp_summary = kg_summary
        if PIPELINE_AVAILABLE:
            try:
                regulations = retrieve_relevant_regulations(
                    query=description,
                    filters=graph_input,
                    top_k=5,
                )
                if regulations:
                    # Step 4: Summarizer — BART/extractive summary of retrieved texts
                    output = generate_output(regulations)
                    nlp_summary = output.get("summary", kg_summary) or kg_summary
                    kg_sources = output.get("sources", [])

                    # If KG gave no results (unknown business type), use NLP checklist
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
                print(f"[app.py] NLP pipeline step error: {e}")

        if not checklist_items and not nlp_summary:
            return MOCK_RESPONSE

        return {
            "business_type": business_type or "business",
            "business_label": business_label,
            "location": location,
            "features": features,
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
