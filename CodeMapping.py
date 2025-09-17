"""
Medical Code Mapping Module - Step 2
====================================

This module handles mapping medical terms to official codes (ICD-10, CPT, SNOMED)
using APIs, databases, and manual mappings. It enriches extracted criteria with
standardized medical codes for integration into knowledge graphs.

Author: Policy Automation Pipeline
Date: 2025
"""

import re
import requests
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import logging
from urllib.parse import quote
import hashlib

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MedicalCode:
    """Represents a medical code with metadata"""
    code: str
    system: str  # 'ICD-10', 'CPT', 'SNOMED', etc.
    description: str
    category: Optional[str] = None
    version: Optional[str] = None
    confidence: float = 1.0
    source: str = "manual"  # 'api', 'manual', 'cache'
    mapped_at: str = ""
    
    def __post_init__(self):
        if not self.mapped_at:
            self.mapped_at = datetime.now().isoformat()

@dataclass
class CodeMapping:
    """Represents the mapping of a term to medical codes"""
    original_term: str
    normalized_term: str
    mapped_codes: List[MedicalCode]
    mapping_confidence: float
    mapping_source: str
    alternative_terms: List[str] = None
    
    def __post_init__(self):
        if self.alternative_terms is None:
            self.alternative_terms = []

class CodeMappingCache:
    """Simple file-based cache for code mappings"""
    
    def __init__(self, cache_file: str = "code_mapping_cache.json"):
        self.cache_file = cache_file
        self.cache = self._load_cache()
        self.hit_count = 0
        self.miss_count = 0
    
    def _load_cache(self) -> Dict[str, Any]:
        """Load cache from file"""
        try:
            with open(self.cache_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _save_cache(self):
        """Save cache to file"""
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")
    
    def get(self, term: str) -> Optional[CodeMapping]:
        """Get mapping from cache"""
        term_key = self._normalize_key(term)
        
        if term_key in self.cache:
            self.hit_count += 1
            data = self.cache[term_key]
            
            # Convert back to CodeMapping object
            mapped_codes = [MedicalCode(**code_data) for code_data in data['mapped_codes']]
            mapping = CodeMapping(
                original_term=data['original_term'],
                normalized_term=data['normalized_term'],
                mapped_codes=mapped_codes,
                mapping_confidence=data['mapping_confidence'],
                mapping_source=data['mapping_source'],
                alternative_terms=data.get('alternative_terms', [])
            )
            return mapping
        
        self.miss_count += 1
        return None
    
    def store(self, term: str, mapping: CodeMapping):
        """Store mapping in cache"""
        term_key = self._normalize_key(term)
        
        # Convert to serializable format
        cache_data = {
            'original_term': mapping.original_term,
            'normalized_term': mapping.normalized_term,
            'mapped_codes': [asdict(code) for code in mapping.mapped_codes],
            'mapping_confidence': mapping.mapping_confidence,
            'mapping_source': mapping.mapping_source,
            'alternative_terms': mapping.alternative_terms,
            'cached_at': datetime.now().isoformat()
        }
        
        self.cache[term_key] = cache_data
        self._save_cache()
    
    def _normalize_key(self, term: str) -> str:
        """Normalize term for cache key"""
        return re.sub(r'[^a-zA-Z0-9]', '_', term.lower().strip())
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.hit_count + self.miss_count
        hit_rate = self.hit_count / total_requests if total_requests > 0 else 0
        
        return {
            'total_entries': len(self.cache),
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'hit_rate': hit_rate,
            'cache_file': self.cache_file
        }

class ExternalAPIClient:
    """Base class for external medical API clients"""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None, rate_limit: int = 10):
        self.base_url = base_url
        self.api_key = api_key
        self.rate_limit = rate_limit  # requests per second
        self.last_request_time = 0
        self.request_count = 0
    
    def _rate_limit_wait(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        min_interval = 1.0 / self.rate_limit
        
        if time_since_last < min_interval:
            wait_time = min_interval - time_since_last
            time.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    def make_request(self, endpoint: str, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Make rate-limited API request"""
        try:
            self._rate_limit_wait()
            
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            self.request_count += 1
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"API request failed: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"API request error: {e}")
            return None

class ICD10APIClient(ExternalAPIClient):
    """Client for ICD-10 code lookup APIs"""
    
    def __init__(self):
        # Using free NIH Clinical Tables API
        super().__init__("https://clinicaltables.nlm.nih.gov/api/icd10cm/v3")
        
    def search_conditions(self, term: str, max_results: int = 10) -> List[MedicalCode]:
        """Search for ICD-10 codes by condition name"""
        params = {
            'sf': 'code,name',
            '