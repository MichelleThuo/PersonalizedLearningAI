"""Schema definitions for search-related API endpoints."""
from typing import List, Optional
from pydantic import BaseModel, Field


class SearchQuery(BaseModel):
    """Schema for search query request."""
    query: str = Field(..., description="Search query string")
    course_id: Optional[int] = Field(None, description="Filter by course ID")
    limit: int = Field(10, description="Maximum number of results to return")


class SearchResult(BaseModel):
    """Schema for a single search result."""
    id: int = Field(..., description="Content ID")
    title: str = Field(..., description="Content title")
    content_type: str = Field(..., description="Content type (document, video, quiz, etc.)")
    snippet: str = Field(..., description="Content snippet/preview")
    course_id: int = Field(..., description="Course ID")
    course_title: str = Field(..., description="Course title")
    url: Optional[str] = Field(None, description="URL to content if available")
    relevance_score: float = Field(..., description="Search relevance score")


class SearchResponse(BaseModel):
    """Schema for search response."""
    query: str = Field(..., description="Original search query")
    results: List[SearchResult] = Field(default_factory=list, description="Search results")
    total_count: int = Field(..., description="Total number of results")
    filtered_by_course: Optional[int] = Field(None, description="Course ID filter if applied")


class VectorSearchQuery(SearchQuery):
    """Schema for vector search query."""
    use_hybrid_search: bool = Field(True, description="Whether to use hybrid search (vector + keyword)")
    semantic_weight: float = Field(0.7, description="Weight for semantic/vector search (0-1)")


class VectorSearchResponse(SearchResponse):
    """Schema for vector search response."""
    vector_search_enabled: bool = Field(True, description="Whether vector search was enabled")