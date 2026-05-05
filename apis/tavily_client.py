"""
apis/tavily_client.py — Live regulatory search via Tavily

Tavily is a search API purpose-built for RAG: it returns clean extracted text
(not raw HTML) with source URLs, making it easy to cite authoritative sources.

Free tier: 1,000 searches/month — sufficient for an MVP.
Sign up at https://tavily.com to get an API key.

Usage:
    client = TavilySearchClient(api_key="tvly-...")
    results = client.search_regulations("restaurant liquor license Los Angeles")
    print(results.summary)
    for r in results.results:
        print(r.title, r.url, r.content)
"""

import os
from dataclasses import dataclass, field
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

try:
    from tavily import TavilyClient as _TavilySDKClient
    _TAVILY_AVAILABLE = True
except ImportError:
    _TAVILY_AVAILABLE = False


# Authoritative LA/CA government domains — restricting to these ensures
# results come from real regulatory sources, not third-party summaries.
COMPLIANCE_DOMAINS = [
    "lacity.gov",
    "lacdph.lacounty.gov",
    "lacounty.gov",
    "abc.ca.gov",
    "cdtfa.ca.gov",
    "dir.ca.gov",
    "cslb.ca.gov",
    "cdph.ca.gov",
    "irs.gov",
    "sba.gov",
    "ladbs.org",
    "planning.lacity.org",
]


@dataclass
class SearchResult:
    title: str
    url: str
    content: str
    score: float
    source_domain: str = ""

    def __post_init__(self):
        if not self.source_domain and self.url:
            # Extract just the domain for display
            try:
                from urllib.parse import urlparse
                self.source_domain = urlparse(self.url).netloc.replace("www.", "")
            except Exception:
                self.source_domain = self.url


@dataclass
class SearchResponse:
    query: str
    summary: str
    results: list[SearchResult] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def succeeded(self) -> bool:
        return self.error is None and bool(self.results)


class TavilySearchClient:
    """
    Wraps Tavily search for LA/CA regulatory compliance queries.

    Restricts searches to authoritative government domains by default,
    so returned sources are citable and authentic.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        restrict_to_gov: bool = True,
        max_results: int = 5,
    ):
        """
        Args:
            api_key: Tavily API key. Falls back to TAVILY_API_KEY env var.
            restrict_to_gov: If True, only searches COMPLIANCE_DOMAINS.
                             Set False to broaden to all web sources.
            max_results: Number of results to return per query (1–10).
        """
        self.api_key = api_key or os.getenv("TAVILY_API_KEY", "")
        self.restrict_to_gov = restrict_to_gov
        self.max_results = max_results
        self._client: Optional[TavilyClient] = None

        if not _TAVILY_AVAILABLE:
            raise ImportError(
                "tavily-python is not installed. Run: pip install tavily-python"
            )
        if not self.api_key:
            raise ValueError(
                "Tavily API key required. Pass api_key= or set TAVILY_API_KEY env var."
            )

        self._client = _TavilySDKClient(api_key=self.api_key)

    def _build_query(
        self,
        topic: str,
        business_type: Optional[str] = None,
        location: str = "Los Angeles",
    ) -> str:
        parts = []
        if business_type:
            parts.append(business_type)
        parts.append(topic)
        parts.append(location)
        parts.append("permit OR license OR regulation requirement")
        return " ".join(parts)

    def search_regulations(
        self,
        topic: str,
        business_type: Optional[str] = None,
        location: str = "Los Angeles",
    ) -> SearchResponse:
        """
        Search for compliance regulations matching a topic.

        Args:
            topic: What to search for, e.g. "health permit food service"
            business_type: Optional business category to narrow results
            location: City/region context (default: Los Angeles)

        Returns:
            SearchResponse with summary and list of SearchResult objects
        """
        query = self._build_query(topic, business_type, location)

        kwargs = {
            "query": query,
            "search_depth": "advanced",
            "max_results": self.max_results,
            "include_answer": True,
        }
        if self.restrict_to_gov:
            kwargs["include_domains"] = COMPLIANCE_DOMAINS

        try:
            raw = self._client.search(**kwargs)
        except Exception as e:
            return SearchResponse(query=query, summary="", error=str(e))

        results = [
            SearchResult(
                title=r.get("title", ""),
                url=r.get("url", ""),
                content=r.get("content", ""),
                score=round(r.get("score", 0.0), 4),
            )
            for r in raw.get("results", [])
        ]

        summary = raw.get("answer") or ""

        return SearchResponse(query=query, summary=summary, results=results)

    def search_permit(
        self,
        permit_name: str,
        business_type: Optional[str] = None,
        location: str = "Los Angeles",
    ) -> SearchResponse:
        """Convenience wrapper for searching a specific named permit."""
        return self.search_regulations(
            topic=permit_name,
            business_type=business_type,
            location=location,
        )

    def batch_search(
        self,
        topics: list[str],
        business_type: Optional[str] = None,
        location: str = "Los Angeles",
    ) -> list[SearchResponse]:
        """
        Run multiple searches, one per topic. Useful for augmenting a
        knowledge graph permit list with live regulatory detail.

        Each topic counts as one Tavily API call.
        """
        return [
            self.search_regulations(topic, business_type, location)
            for topic in topics
        ]
