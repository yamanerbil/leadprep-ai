"""
Cache utilities for LeadPrep AI.

This module provides caching functionality to store company leadership data
locally and avoid repeated API calls to GPT-4.
"""

import json
import os
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import pickle

class LeadershipCache:
    """Cache for company leadership data."""
    
    def __init__(self, cache_dir: str = "data/cache", max_age_days: int = 30):
        """
        Initialize the cache.
        
        Args:
            cache_dir (str): Directory to store cache files
            max_age_days (int): Maximum age of cached data in days
        """
        self.cache_dir = cache_dir
        self.max_age_days = max_age_days
        self.cache_file = os.path.join(cache_dir, "leadership_cache.json")
        
        # Create cache directory if it doesn't exist
        os.makedirs(cache_dir, exist_ok=True)
        
        # Load existing cache
        self.cache = self._load_cache()
    
    def _load_cache(self) -> Dict[str, Any]:
        """Load cache from file."""
        try:
            if os.path.exists(self.cache_file):
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    
                # Clean expired entries
                current_time = datetime.now()
                cleaned_cache = {}
                
                for key, entry in cache_data.items():
                    cached_time = datetime.fromisoformat(entry['timestamp'])
                    if current_time - cached_time < timedelta(days=self.max_age_days):
                        cleaned_cache[key] = entry
                    else:
                        print(f"🗑️  Removing expired cache entry: {key}")
                
                return cleaned_cache
            else:
                return {}
        except Exception as e:
            print(f"⚠️  Error loading cache: {e}")
            return {}
    
    def _save_cache(self):
        """Save cache to file."""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️  Error saving cache: {e}")
    
    def _get_cache_key(self, company_url: str) -> str:
        """Generate a cache key for a company URL."""
        # Normalize the URL
        if company_url.startswith(('http://', 'https://')):
            from urllib.parse import urlparse
            parsed = urlparse(company_url)
            domain = parsed.netloc
        else:
            domain = company_url
            
        # Remove 'www.' prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]
            
        # Create a hash of the domain
        return hashlib.md5(domain.encode()).hexdigest()
    
    def get(self, company_url: str) -> Optional[List[Dict[str, str]]]:
        """
        Get cached leadership data for a company.
        
        Args:
            company_url (str): Company URL or domain
            
        Returns:
            Optional[List[Dict[str, str]]]: Cached leaders if available and not expired
        """
        cache_key = self._get_cache_key(company_url)
        
        if cache_key in self.cache:
            entry = self.cache[cache_key]
            cached_time = datetime.fromisoformat(entry['timestamp'])
            
            # Check if cache is still valid
            if datetime.now() - cached_time < timedelta(days=self.max_age_days):
                print(f"📋 Using cached data for {company_url} (cached {cached_time.strftime('%Y-%m-%d %H:%M')})")
                return entry['leaders']
            else:
                print(f"⏰ Cache expired for {company_url}")
                del self.cache[cache_key]
                self._save_cache()
        
        return None
    
    def set(self, company_url: str, leaders: List[Dict[str, str]]):
        """
        Cache leadership data for a company.
        
        Args:
            company_url (str): Company URL or domain
            leaders (List[Dict[str, str]]): List of leaders to cache
        """
        cache_key = self._get_cache_key(company_url)
        
        self.cache[cache_key] = {
            'leaders': leaders,
            'timestamp': datetime.now().isoformat(),
            'company_url': company_url
        }
        
        self._save_cache()
        print(f"💾 Cached {len(leaders)} leaders for {company_url}")
    
    def clear(self):
        """Clear all cached data."""
        self.cache = {}
        self._save_cache()
        print("🗑️  Cache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_entries = len(self.cache)
        total_leaders = sum(len(entry['leaders']) for entry in self.cache.values())
        
        # Calculate cache size
        cache_size = 0
        if os.path.exists(self.cache_file):
            cache_size = os.path.getsize(self.cache_file)
        
        return {
            'total_entries': total_entries,
            'total_leaders': total_leaders,
            'cache_size_bytes': cache_size,
            'cache_size_mb': round(cache_size / (1024 * 1024), 2),
            'max_age_days': self.max_age_days
        }


# Global cache instance
leadership_cache = LeadershipCache()


def get_cached_leaders(company_url: str) -> Optional[List[Dict[str, str]]]:
    """
    Get cached leadership data for a company.
    
    Args:
        company_url (str): Company URL or domain
        
    Returns:
        Optional[List[Dict[str, str]]]: Cached leaders if available
    """
    return leadership_cache.get(company_url)


def cache_leaders(company_url: str, leaders: List[Dict[str, str]]):
    """
    Cache leadership data for a company.
    
    Args:
        company_url (str): Company URL or domain
        leaders (List[Dict[str, str]]): List of leaders to cache
    """
    leadership_cache.set(company_url, leaders)


def clear_cache():
    """Clear all cached data."""
    leadership_cache.clear()


def get_cache_stats() -> Dict[str, Any]:
    """
    Get cache statistics.
    
    Returns:
        Dict[str, Any]: Cache statistics
    """
    return leadership_cache.get_stats()


if __name__ == "__main__":
    # Test the cache
    print("🧪 Testing Leadership Cache...")
    
    # Test data
    test_leaders = [
        {"name": "Tim Cook", "title": "CEO"},
        {"name": "Jeff Williams", "title": "COO"}
    ]
    
    # Test caching
    cache_leaders("apple.com", test_leaders)
    
    # Test retrieval
    cached = get_cached_leaders("apple.com")
    print(f"Cached leaders: {cached}")
    
    # Show stats
    stats = get_cache_stats()
    print(f"Cache stats: {stats}")
