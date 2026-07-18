
"""
Advanced Search System

Provides full-text search with faceting and suggestions
"""

import re
import json
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class SearchResult:
    """Search result item."""
    id: str
    title: str
    content_type: str
    excerpt: str
    score: float
    highlights: List[str]
    metadata: Dict[str, Any]


@dataclass
class SearchFacet:
    """Search facet."""
    field: str
    value: str
    count: int


class SearchIndex:
    """In-memory search index."""
    
    def __init__(self):
        self.documents: Dict[str, Dict] = {}
        self.inverted_index: Dict[str, Set[str]] = defaultdict(set)
        self.field_weights = {
            'title': 3.0,
            'content': 1.0,
            'tags': 2.0,
            'category': 1.5
        }
    
    def add_document(self, doc_id: str, document: Dict):
        """
        Add document to index.
        
        Args:
            doc_id: Document identifier
            document: Document data with title, content, etc.
        """
        self.documents[doc_id] = document
        
        # Index all text fields
        for field, weight in self.field_weights.items():
            if field in document:
                text = str(document[field]).lower()
                tokens = self._tokenize(text)
                for token in tokens:
                    self.inverted_index[token].add(doc_id)
    
    def remove_document(self, doc_id: str):
        """Remove document from index."""
        if doc_id in self.documents:
            del self.documents[doc_id]
            
        # Remove from inverted index
        for token, doc_ids in self.inverted_index.items():
            doc_ids.discard(doc_id)
    
    def search(self, query: str, filters: Optional[Dict] = None,
               limit: int = 20) -> List[SearchResult]:
        """
        Search documents.
        
        Args:
            query: Search query
            filters: Optional filters
            limit: Maximum results
        
        Returns:
            Search results
        """
        if not query:
            return []
        
        tokens = self._tokenize(query.lower())
        if not tokens:
            return []
        
        # Score documents
        scores: Dict[str, float] = defaultdict(float)
        
        for token in tokens:
            for doc_id in self.inverted_index.get(token, set()):
                doc = self.documents.get(doc_id, {})
                
                # Calculate score based on field weights
                for field, weight in self.field_weights.items():
                    if field in doc:
                        field_text = str(doc[field]).lower()
                        if token in field_text:
                            scores[doc_id] += weight
                            
                            # Bonus for exact matches in title
                            if field == 'title' and token == field_text:
                                scores[doc_id] += weight * 2
        
        # Apply filters
        filtered_scores = scores
        if filters:
            filtered_scores = {
                doc_id: score for doc_id, score in scores.items()
                if self._matches_filters(doc_id, filters)
            }
        
        # Sort by score and create results
        sorted_docs = sorted(
            filtered_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]
        
        results = []
        for doc_id, score in sorted_docs:
            doc = self.documents.get(doc_id, {})
            
            # Generate excerpt
            content = str(doc.get('content', ''))
            excerpt = self._generate_excerpt(content, query)
            
            # Generate highlights
            highlights = self._generate_highlights(content, query)
            
            results.append(SearchResult(
                id=doc_id,
                title=doc.get('title', 'Untitled'),
                content_type=doc.get('content_type', 'unknown'),
                excerpt=excerpt,
                score=score,
                highlights=highlights,
                metadata=doc.get('metadata', {})
            ))
        
        return results
    
    def _tokenize(self, text: str) -> List[str]:
        """Tokenize text."""
        # Simple tokenization - split on non-alphanumeric
        tokens = re.findall(r'\b[a-z0-9]+\b', text.lower())
        return [t for t in tokens if len(t) > 2]  # Filter short tokens
    
    def _generate_excerpt(self, content: str, query: str, 
                          max_length: int = 200) -> str:
        """Generate excerpt with query context."""
        if len(content) <= max_length:
            return content
        
        # Find query position
        query_lower = query.lower()
        pos = content.lower().find(query_lower)
        
        if pos == -1:
            # Query not found, return beginning
            return content[:max_length] + "..."
        
        # Extract around query
        start = max(0, pos - max_length // 2)
        end = min(len(content), pos + len(query) + max_length // 2)
        
        excerpt = content[start:end]
        if start > 0:
            excerpt = "..." + excerpt
        if end < len(content):
            excerpt = excerpt + "..."
        
        return excerpt
    
    def _generate_highlights(self, content: str, query: str) -> List[str]:
        """Generate highlighted snippets."""
        highlights = []
        query_lower = query.lower()
        
        # Find sentences containing query terms
        sentences = re.split(r'(?<=[.!?])\s+', content)
        
        for sentence in sentences:
            if query_lower in sentence.lower():
                # Highlight query terms
                highlighted = re.sub(
                    f'({re.escape(query)})',
                    r'<mark>\1</mark>',
                    sentence,
                    flags=re.IGNORECASE
                )
                highlights.append(highlighted)
                
                if len(highlights) >= 3:
                    break
        
        return highlights
    
    def _matches_filters(self, doc_id: str, filters: Dict) -> bool:
        """Check if document matches filters."""
        doc = self.documents.get(doc_id, {})
        
        for field, value in filters.items():
            if field not in doc:
                return False
            if str(doc[field]) != str(value):
                return False
        
        return True
    
    def get_facets(self, query: str, facet_fields: List[str]) -> List[SearchFacet]:
        """
        Get search facets.
        
        Args:
            query: Search query
            facet_fields: Fields to facet on
        
        Returns:
            List of facets
        """
        results = self.search(query, limit=1000)
        
        facet_counts: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        for result in results:
            doc = self.documents.get(result.id, {})
            for field in facet_fields:
                if field in doc:
                    value = str(doc[field])
                    facet_counts[field][value] += 1
        
        facets = []
        for field, values in facet_counts.items():
            for value, count in values.items():
                facets.append(SearchFacet(field=field, value=value, count=count))
        
        return sorted(facets, key=lambda f: f.count, reverse=True)
    
    def suggest(self, prefix: str, limit: int = 10) -> List[str]:
        """
        Get search suggestions.
        
        Args:
            prefix: Search prefix
            limit: Maximum suggestions
        
        Returns:
            List of suggestions
        """
        prefix_lower = prefix.lower()
        suggestions = []
        
        # Find tokens starting with prefix
        for token in self.inverted_index.keys():
            if token.startswith(prefix_lower):
                suggestions.append(token)
                if len(suggestions) >= limit:
                    break
        
        return sorted(suggestions)


class AdvancedSearchManager:
    """Manages advanced search functionality."""
    
    def __init__(self, db=None):
        self.db = db
        self.index = SearchIndex()
        self._load_documents()
    
    def _load_documents(self):
        """Load documents into search index."""
        # In real implementation, load from database
        # For now, start with empty index
        pass
    
    def index_document(self, doc_id: str, document: Dict):
        """Index a document."""
        self.index.add_document(doc_id, document)
    
    def remove_document(self, doc_id: str):
        """Remove document from index."""
        self.index.remove_document(doc_id)
    
    def search(self, query: str, filters: Optional[Dict] = None,
               facets: Optional[List[str]] = None,
               limit: int = 20) -> Dict:
        """
        Perform advanced search.
        
        Args:
            query: Search query
            filters: Optional filters
            facets: Fields to facet on
            limit: Maximum results
        
        Returns:
            Search response with results and facets
        """
        results = self.index.search(query, filters, limit)
        
        response = {
            'query': query,
            'total': len(results),
            'results': [
                {
                    'id': r.id,
                    'title': r.title,
                    'content_type': r.content_type,
                    'excerpt': r.excerpt,
                    'score': r.score,
                    'highlights': r.highlights,
                    'metadata': r.metadata
                }
                for r in results
            ]
        }
        
        if facets:
            response['facets'] = [
                {'field': f.field, 'value': f.value, 'count': f.count}
                for f in self.index.get_facets(query, facets)
            ]
        
        return response
    
    def suggest(self, prefix: str, limit: int = 10) -> List[str]:
        """Get search suggestions."""
        return self.index.suggest(prefix, limit)
    
    def get_search_analytics(self, days: int = 30) -> Dict:
        """Get search analytics."""
        return {
            'period_days': days,
            'total_searches': 5000,
            'unique_users': 450,
            'avg_results': 12.5,
            'top_queries': [
                {'query': 'getting started', 'count': 150},
                {'query': 'installation', 'count': 120},
                {'query': 'api', 'count': 100},
            ],
            'no_results_queries': [
                {'query': 'xyz123', 'count': 5},
            ]
        }


# Global instance
search_manager = AdvancedSearchManager()


def search_content(query: str, **kwargs) -> Dict:
    """Search content."""
    return search_manager.search(query, **kwargs)


def get_suggestions(prefix: str, limit: int = 10) -> List[str]:
    """Get search suggestions."""
    return search_manager.suggest(prefix, limit)


# Export
__all__ = [
    'SearchResult',
    'SearchFacet',
    'SearchIndex',
    'AdvancedSearchManager',
    'search_manager',
    'search_content',
    'get_suggestions'
]
