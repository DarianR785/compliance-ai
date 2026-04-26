"""
knowledge_graph.py — Regulatory Knowledge Graph for Small Business Compliance

Builds a NetworkX directed graph encoding relationships between:
  - Business types (restaurant, salon, food_truck, contractor, retail)
  - Permit/license types (health_permit, fire_permit, ABC_license, etc.)
  - Jurisdictions (city_of_la, la_county, state_of_california, federal)
  - Features/conditions that trigger additional requirements

Edges encode REQUIRES, ISSUED_BY, and TRIGGERED_BY relationships with
metadata like estimated cost, processing time, and renewal period.
"""

import networkx as nx
from typing import Optional


def build_knowledge_graph() -> nx.DiGraph:
    """
    Construct and return the full regulatory knowledge graph.
    Scoped to Los Angeles for MVP.
    """
    G = nx.DiGraph()

    # JURISDICTION NODES
    jurisdictions = {
        "city_of_la": {
            "label": "City of Los Angeles",
            "type": "jurisdiction",
            "level": "city",
        },
        "la_county": {
            "label": "Los Angeles County",
            "type": "jurisdiction",
            "level": "county",
        },
        "state_of_california": {
            "label": "State of California",
            "type": "jurisdiction",
            "level": "state",
        },
        "federal": {
            "label": "Federal Government",
            "type": "jurisdiction",
            "level": "federal",
        },
    }
    for node_id, attrs in jurisdictions.items():
        G.add_node(node_id, **attrs)

    # BUSINESS TYPE NODES
    business_types = {
        "restaurant": {
            "label": "Restaurant",
            "type": "business_type",
            "description": "Food service establishment with dine-in seating",
            "aliases": [
                "restaurant", "eatery", "diner", "cafe", "bistro",
                "pizzeria", "grill", "bbq", "barbeque", "barbecue",
                "sushi", "taqueria", "bakery", "coffee shop",
            ],
        },
        "salon": {
            "label": "Hair/Beauty Salon",
            "type": "business_type",
            "description": "Personal care and beauty services",
            "aliases": [
                "salon", "hair salon", "beauty salon", "barbershop",
                "barber shop", "nail salon", "spa", "waxing",
                "aesthetics", "cosmetology", "beauty parlor",
            ],
        },
        "food_truck": {
            "label": "Food Truck / Mobile Food",
            "type": "business_type",
            "description": "Mobile food vending operation",
            "aliases": [
                "food truck", "food cart", "mobile food", "food stand",
                "catering truck", "taco truck", "street food",
            ],
        },
        "contractor": {
            "label": "General Contractor",
            "type": "business_type",
            "description": "Construction and building trades",
            "aliases": [
                "contractor", "general contractor", "construction",
                "builder", "remodeling", "renovation", "plumber",
                "electrician", "hvac", "roofing", "painting",
            ],
        },
        "retail": {
            "label": "Retail Store",
            "type": "business_type",
            "description": "Retail sales of goods to consumers",
            "aliases": [
                "retail", "store", "shop", "boutique", "clothing store",
                "gift shop", "convenience store", "grocery", "market",
            ],
        },
    }
    for node_id, attrs in business_types.items():
        G.add_node(node_id, **attrs)

    # PERMIT / LICENSE NODES
    permits = {
        # Universal permits (most businesses need these)
        "business_tax_registration": {
            "label": "Business Tax Registration Certificate (BTRC)",
            "type": "permit",
            "description": "Required for all businesses operating within the City of Los Angeles. Registers the business with the Office of Finance for tax purposes.",
            "est_cost": "$0–$500/year (varies by gross receipts)",
            "processing_time": "1–2 weeks",
            "renewal": "Annual",
            "priority": "critical",
        },
        "ein": {
            "label": "Employer Identification Number (EIN)",
            "type": "permit",
            "description": "Federal tax identification number required to open business bank accounts, hire employees, and file taxes. Free to obtain from the IRS.",
            "est_cost": "Free",
            "processing_time": "Immediate (online)",
            "renewal": "None — permanent",
            "priority": "critical",
        },
        "sellers_permit": {
            "label": "Seller's Permit",
            "type": "permit",
            "description": "Required by the California Department of Tax and Fee Administration (CDTFA) for businesses selling tangible goods. Enables collection and remittance of sales tax.",
            "est_cost": "Free (security deposit may apply)",
            "processing_time": "1–2 weeks",
            "renewal": "None unless business changes",
            "priority": "critical",
        },
        # Food / Restaurant specific
        "health_permit": {
            "label": "Health Permit (Public Health)",
            "type": "permit",
            "description": "Required for any business that prepares, handles, or serves food. Issued by the LA County Department of Public Health after facility inspection. Covers sanitation, ventilation, food storage, and hygiene.",
            "est_cost": "$700–$2,000",
            "processing_time": "4–8 weeks (includes plan check + inspection)",
            "renewal": "Annual",
            "priority": "critical",
        },
        "food_handler_card": {
            "label": "Food Handler's Card / Certificate",
            "type": "permit",
            "description": "All employees who handle food must obtain a California Food Handler Card through an approved training program (e.g., ServSafe). The owner must also hold this certification.",
            "est_cost": "$10–$15 per person",
            "processing_time": "Same day (online exam)",
            "renewal": "Every 3 years",
            "priority": "high",
        },
        "food_manager_cert": {
            "label": "Certified Food Protection Manager",
            "type": "permit",
            "description": "At least one certified food protection manager must be on staff at all times during food service operations. Requires passing an ANSI-accredited exam.",
            "est_cost": "$80–$200",
            "processing_time": "1–2 weeks",
            "renewal": "Every 5 years",
            "priority": "high",
        },
        # Fire / Safety
        "fire_clearance": {
            "label": "Fire Department Clearance",
            "type": "permit",
            "description": "Required for businesses open to the public or using flammable materials. The LAFD inspects for fire safety, occupancy capacity, exit signage, sprinkler systems, and extinguisher placement.",
            "est_cost": "$200–$500",
            "processing_time": "2–4 weeks",
            "renewal": "Annual inspection",
            "priority": "critical",
        },
        # Building / Zoning 
        "building_permit": {
            "label": "Building Permit (LADBS)",
            "type": "permit",
            "description": "Required before making structural changes, tenant improvements, or new construction. Issued by the LA Department of Building and Safety (LADBS). Requires architectural plans and a site survey.",
            "est_cost": "$200–$5,000+ (varies by scope)",
            "processing_time": "4–12 weeks",
            "renewal": "Per project",
            "priority": "high",
        },
        "certificate_of_occupancy": {
            "label": "Certificate of Occupancy",
            "type": "permit",
            "description": "Confirms that the building meets all zoning, building code, and safety requirements for its intended use. Required before opening to the public.",
            "est_cost": "Included with building permit",
            "processing_time": "2–6 weeks after final inspection",
            "renewal": "Per change of use",
            "priority": "critical",
        },
        "sign_permit": {
            "label": "Sign Permit",
            "type": "permit",
            "description": "Required for any exterior signage, awnings, or projecting signs. Governed by LAMC Section 14.4. Size, illumination, and placement restrictions vary by zone.",
            "est_cost": "$100–$500",
            "processing_time": "2–4 weeks",
            "renewal": "Per sign installation",
            "priority": "medium",
        },
        # Conditional / Feature-triggered
        "abc_license": {
            "label": "ABC Liquor License",
            "type": "permit",
            "description": "Required to sell or serve alcoholic beverages. Issued by the California Department of Alcoholic Beverage Control (ABC). Type 41 (On-Sale Beer/Wine for restaurants) or Type 47 (On-Sale General) are most common.",
            "est_cost": "$1,000–$15,000+ (varies by license type)",
            "processing_time": "2–6 months",
            "renewal": "Annual",
            "priority": "high",
            "triggered_by": ["liquor", "alcohol", "beer", "wine", "bar", "cocktail"],
        },
        "conditional_use_permit": {
            "label": "Conditional Use Permit (CUP)",
            "type": "permit",
            "description": "Required for land uses not normally permitted in a zoning district but allowed under special conditions. Common triggers include outdoor dining, live entertainment, and late-night operation.",
            "est_cost": "$15,000–$30,000+",
            "processing_time": "3–12 months",
            "renewal": "Varies — may include conditions review",
            "priority": "high",
            "triggered_by": ["outdoor dining", "patio", "rooftop", "live music", "late night"],
        },
        "entertainment_permit": {
            "label": "Entertainment / Police Commission Permit",
            "type": "permit",
            "description": "Required for businesses offering live entertainment, DJs, karaoke, dancing, or amplified music. Issued by the LAPD/Board of Police Commissioners.",
            "est_cost": "$500–$3,000",
            "processing_time": "4–8 weeks",
            "renewal": "Annual",
            "priority": "medium",
            "triggered_by": ["live music", "dj", "karaoke", "dancing", "entertainment", "live band"],
        },
        "outdoor_dining_permit": {
            "label": "Sidewalk/Outdoor Dining Permit",
            "type": "permit",
            "description": "Required for dining on public sidewalks or rights-of-way. Issued by the Bureau of Engineering. Requires a site plan showing pedestrian clearance and ADA compliance.",
            "est_cost": "$500–$2,000",
            "processing_time": "4–8 weeks",
            "renewal": "Annual",
            "priority": "medium",
            "triggered_by": ["outdoor dining", "sidewalk dining", "patio", "al fresco", "outdoor seating"],
        },
        "home_occupation_permit": {
            "label": "Home Occupation Permit",
            "type": "permit",
            "description": "Required if operating a business from a residential property. Restricts signage, customer visits, noise, and employee count. Issued by the Department of City Planning.",
            "est_cost": "$100–$300",
            "processing_time": "2–4 weeks",
            "renewal": "Annual",
            "priority": "high",
            "triggered_by": ["home based", "home business", "garage", "residential", "work from home"],
        },
        "commissary_agreement": {
            "label": "Commissary Agreement",
            "type": "permit",
            "description": "Food trucks and mobile food vendors must have a written agreement with a licensed commissary kitchen for food storage, preparation, and vehicle servicing.",
            "est_cost": "$500–$2,000/month",
            "processing_time": "1–2 weeks (once commissary is secured)",
            "renewal": "Ongoing agreement",
            "priority": "critical",
        },
        "mobile_food_facility_permit": {
            "label": "Mobile Food Facility Permit (MFF)",
            "type": "permit",
            "description": "Annual permit from LA County Department of Public Health specifically for food trucks, carts, and mobile vending. Requires vehicle inspection and commissary documentation.",
            "est_cost": "$800–$1,200",
            "processing_time": "4–6 weeks",
            "renewal": "Annual",
            "priority": "critical",
        },
        # Salon specific
        "cosmetology_license": {
            "label": "Cosmetology / Barbering License",
            "type": "permit",
            "description": "State-issued license required for all individuals performing hair, skin, or nail services. Requires completion of approved cosmetology school hours and passing the California Board of Barbering and Cosmetology exam.",
            "est_cost": "$50–$100 (exam + license fee)",
            "processing_time": "2–6 weeks after exam",
            "renewal": "Every 2 years",
            "priority": "critical",
        },
        "salon_establishment_license": {
            "label": "Salon Establishment License",
            "type": "permit",
            "description": "The physical salon location must be separately licensed by the California Board of Barbering and Cosmetology. Requires facility inspection for sanitation, ventilation, and equipment standards.",
            "est_cost": "$100–$200",
            "processing_time": "2–4 weeks (includes inspection)",
            "renewal": "Every 2 years",
            "priority": "critical",
        },
        # Contractor specific
        "cslb_license": {
            "label": "Contractors State License (CSLB)",
            "type": "permit",
            "description": "Required for any construction project valued over $500 (including labor and materials). Issued by the California Contractors State License Board. Requires experience verification, trade exam, law exam, and a surety bond.",
            "est_cost": "$450 (application + exam) + $15,000 bond",
            "processing_time": "8–12 weeks",
            "renewal": "Every 2 years",
            "priority": "critical",
        },
        "workers_comp_insurance": {
            "label": "Workers' Compensation Insurance",
            "type": "permit",
            "description": "California requires all employers to carry workers' compensation insurance. Contractors without employees must file a Certificate of Exemption.",
            "est_cost": "Varies by payroll and trade classification",
            "processing_time": "1–2 weeks",
            "renewal": "Annual policy",
            "priority": "critical",
        },
    }
    for node_id, attrs in permits.items():
        G.add_node(node_id, **attrs)

    # FEATURE / CONDITION NODES
    features = {
        "liquor": {"label": "Alcohol Sales/Service", "type": "feature"},
        "outdoor_dining": {"label": "Outdoor/Patio Dining", "type": "feature"},
        "live_entertainment": {"label": "Live Music/Entertainment", "type": "feature"},
        "home_based": {"label": "Home-Based Operation", "type": "feature"},
        "employees": {"label": "Has Employees", "type": "feature"},
        "signage": {"label": "Exterior Signage", "type": "feature"},
        "construction": {"label": "Tenant Improvements/Build-out", "type": "feature"},
    }
    for node_id, attrs in features.items():
        G.add_node(node_id, **attrs)

    # EDGES: REQUIRES (business_type → permit)

    # Universal requirements (all business types)
    for btype in business_types:
        G.add_edge(btype, "business_tax_registration", relation="REQUIRES", condition="always")
        G.add_edge(btype, "ein", relation="REQUIRES", condition="always")

    # Restaurant
    restaurant_permits = [
        ("sellers_permit", "always"),
        ("health_permit", "always"),
        ("food_handler_card", "always"),
        ("food_manager_cert", "always"),
        ("fire_clearance", "always"),
        ("certificate_of_occupancy", "always"),
    ]
    for permit, condition in restaurant_permits:
        G.add_edge("restaurant", permit, relation="REQUIRES", condition=condition)

    # Salon
    salon_permits = [
        ("cosmetology_license", "always"),
        ("salon_establishment_license", "always"),
        ("fire_clearance", "always"),
        ("certificate_of_occupancy", "always"),
    ]
    for permit, condition in salon_permits:
        G.add_edge("salon", permit, relation="REQUIRES", condition=condition)

    # Food Truck
    food_truck_permits = [
        ("sellers_permit", "always"),
        ("health_permit", "always"),
        ("food_handler_card", "always"),
        ("mobile_food_facility_permit", "always"),
        ("commissary_agreement", "always"),
    ]
    for permit, condition in food_truck_permits:
        G.add_edge("food_truck", permit, relation="REQUIRES", condition=condition)

    # Contractor
    contractor_permits = [
        ("cslb_license", "always"),
        ("workers_comp_insurance", "always"),
    ]
    for permit, condition in contractor_permits:
        G.add_edge("contractor", permit, relation="REQUIRES", condition=condition)

    # Retail
    retail_permits = [
        ("sellers_permit", "always"),
        ("fire_clearance", "always"),
        ("certificate_of_occupancy", "always"),
    ]
    for permit, condition in retail_permits:
        G.add_edge("retail", permit, relation="REQUIRES", condition=condition)

    # EDGES: TRIGGERED_BY (feature → permit)
    G.add_edge("liquor", "abc_license", relation="TRIGGERS")
    G.add_edge("outdoor_dining", "outdoor_dining_permit", relation="TRIGGERS")
    G.add_edge("outdoor_dining", "conditional_use_permit", relation="TRIGGERS")
    G.add_edge("live_entertainment", "entertainment_permit", relation="TRIGGERS")
    G.add_edge("live_entertainment", "conditional_use_permit", relation="TRIGGERS")
    G.add_edge("home_based", "home_occupation_permit", relation="TRIGGERS")
    G.add_edge("signage", "sign_permit", relation="TRIGGERS")
    G.add_edge("construction", "building_permit", relation="TRIGGERS")

    # EDGES: ISSUED_BY (permit → jurisdiction)
    issued_by_mapping = {
        "business_tax_registration": "city_of_la",
        "ein": "federal",
        "sellers_permit": "state_of_california",
        "health_permit": "la_county",
        "food_handler_card": "state_of_california",
        "food_manager_cert": "state_of_california",
        "fire_clearance": "city_of_la",
        "building_permit": "city_of_la",
        "certificate_of_occupancy": "city_of_la",
        "sign_permit": "city_of_la",
        "abc_license": "state_of_california",
        "conditional_use_permit": "city_of_la",
        "entertainment_permit": "city_of_la",
        "outdoor_dining_permit": "city_of_la",
        "home_occupation_permit": "city_of_la",
        "commissary_agreement": "la_county",
        "mobile_food_facility_permit": "la_county",
        "cosmetology_license": "state_of_california",
        "salon_establishment_license": "state_of_california",
        "cslb_license": "state_of_california",
        "workers_comp_insurance": "state_of_california",
    }
    for permit, jurisdiction in issued_by_mapping.items():
        G.add_edge(permit, jurisdiction, relation="ISSUED_BY")

    return G


def query_permits(
    G: nx.DiGraph,
    business_type: str,
    features: Optional[list[str]] = None,
) -> dict:
    """
    Given a business type and optional features, traverse the knowledge graph
    to return all required permits organized by priority.

    Args:
        G: The regulatory knowledge graph
        business_type: One of 'restaurant', 'salon', 'food_truck', 'contractor', 'retail'
        features: List of feature strings like ['liquor', 'outdoor_dining', 'live_entertainment']

    Returns:
        dict with keys 'base_permits', 'feature_permits', 'all_permits', 'summary'
    """
    if features is None:
        features = []

    # Collect base permits from business type edges
    base_permits = []
    for _, target, data in G.out_edges(business_type, data=True):
        if data.get("relation") == "REQUIRES":
            node_data = G.nodes[target].copy()
            node_data["id"] = target
            base_permits.append(node_data)

    # Collect feature-triggered permits
    feature_permits = []
    matched_features = []
    for feature in features:
        if feature in G.nodes:
            matched_features.append(feature)
            for _, target, data in G.out_edges(feature, data=True):
                if data.get("relation") == "TRIGGERS":
                    node_data = G.nodes[target].copy()
                    node_data["id"] = target
                    node_data["triggered_by_feature"] = feature
                    # Avoid duplicates
                    if not any(p["id"] == target for p in feature_permits + base_permits):
                        feature_permits.append(node_data)

    all_permits = base_permits + feature_permits

    # Add issuing jurisdiction to each permit
    for permit in all_permits:
        for _, target, data in G.out_edges(permit["id"], data=True):
            if data.get("relation") == "ISSUED_BY":
                permit["issued_by"] = G.nodes[target]["label"]
                break

    # Sort by priority
    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    all_permits.sort(key=lambda p: priority_order.get(p.get("priority", "low"), 3))

    # Build summary
    business_label = G.nodes[business_type].get("label", business_type)
    summary = (
        f"A {business_label} in Los Angeles requires {len(base_permits)} base "
        f"permit(s)/license(s)."
    )
    if feature_permits:
        feat_labels = [G.nodes[f]["label"] for f in matched_features]
        summary += (
            f" The following features trigger {len(feature_permits)} additional "
            f"requirement(s): {', '.join(feat_labels)}."
        )

    return {
        "business_type": business_type,
        "business_label": business_label,
        "base_permits": base_permits,
        "feature_permits": feature_permits,
        "all_permits": all_permits,
        "matched_features": matched_features,
        "summary": summary,
    }


def get_business_aliases() -> dict[str, list[str]]:
    """Return a mapping of business_type_id -> list of alias strings for NER."""
    G = build_knowledge_graph()
    aliases = {}
    for node_id, data in G.nodes(data=True):
        if data.get("type") == "business_type":
            aliases[node_id] = data.get("aliases", [])
    return aliases

def get_feature_triggers() -> dict[str, list[str]]:
    """Return a mapping of feature_id -> list of trigger keywords for NER."""
    G = build_knowledge_graph()
    triggers = {}
    for node_id, data in G.nodes(data=True):
        if data.get("type") == "permit":
            trigger_words = data.get("triggered_by", [])
            if trigger_words:
                # Find which feature node triggers this permit
                for source, target, edge_data in G.in_edges(node_id, data=True):
                    if edge_data.get("relation") == "TRIGGERS":
                        if source not in triggers:
                            triggers[source] = []
                        triggers[source].extend(trigger_words)
    # Deduplicate
    for key in triggers:
        triggers[key] = list(set(triggers[key]))
    return triggers


# Test
if __name__ == "__main__":
    G = build_knowledge_graph()
    print(f"Knowledge Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges\n")

    # Test query: restaurant with liquor and outdoor dining
    result = query_permits(G, "restaurant", ["liquor", "outdoor_dining"])
    print(result["summary"])
    print(f"\nAll required permits ({len(result['all_permits'])}):")
    for p in result["all_permits"]:
        triggered = f" [triggered by: {p['triggered_by_feature']}]" if "triggered_by_feature" in p else ""
        print(f"  [{p.get('priority', '?').upper():>8}] {p['label']}{triggered}")
        print(f"             Cost: {p.get('est_cost', 'N/A')} | Time: {p.get('processing_time', 'N/A')} | Issued by: {p.get('issued_by', 'N/A')}")