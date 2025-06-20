"""
Company utilities for LeadPrep AI.

This module provides functions to extract company information from URLs
and identify key company leaders for sales preparation.
"""

import re
from urllib.parse import urlparse
from typing import List, Dict, Optional

# Import LLM-based leader extraction
try:
    from llm_leader_extractor import get_company_leaders_with_llm
    LLM_EXTRACTION_AVAILABLE = True
except ImportError:
    LLM_EXTRACTION_AVAILABLE = False
    print("⚠️  LLM extraction not available. Using fake data only.")

# Import database functionality
try:
    from database import get_leaders_from_db, save_leaders_to_db
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    print("⚠️  Database not available. Using memory storage only.")

# Import caching functionality
try:
    from cache_utils import get_cached_leaders, cache_leaders
    CACHE_AVAILABLE = True
except ImportError:
    CACHE_AVAILABLE = False
    print("⚠️  Cache not available. Using direct storage only.")


def extract_company_domain(url: str) -> str:
    """
    Extract the company domain from a given URL.
    
    Args:
        url (str): The company URL (e.g., "https://www.apple.com/products" or "apple.com")
        
    Returns:
        str: The company domain (e.g., "apple.com")
        
    Raises:
        ValueError: If the URL is invalid or cannot be parsed
    """
    try:
        # If it doesn't look like a URL, treat it as a domain
        if not url.startswith(('http://', 'https://')):
            domain = url.strip()
        else:
            # Parse the URL
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
        
        # Remove 'www.' prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]
            
        # Validate that we have a domain
        if not domain or '.' not in domain:
            raise ValueError(f"Invalid domain: {url}")
            
        return domain
        
    except Exception as e:
        raise ValueError(f"Failed to parse URL '{url}': {str(e)}")


def get_company_leaders(domain: str) -> List[Dict[str, str]]:
    """
    Get key company leaders for a given domain.
    
    Priority order:
    1. Check cache first (fastest)
    2. Check database (persistent storage)
    3. Use LLM extraction (most current)
    4. Fall back to fake data
    
    Args:
        domain (str): The company domain (e.g., "apple.com")
        
    Returns:
        List[Dict[str, str]]: List of leader dictionaries with 'name' and 'title' keys
    """
    print(f"🔍 Looking up leaders for: {domain}")
    
    # Step 1: Check cache first (fastest)
    if CACHE_AVAILABLE:
        cached_leaders = get_cached_leaders(domain)
        if cached_leaders:
            print(f"📋 Found {len(cached_leaders)} leaders in cache for {domain}")
            return cached_leaders
    
    # Step 2: Check database (persistent storage)
    if DATABASE_AVAILABLE:
        db_leaders = get_leaders_from_db(domain)
        if db_leaders:
            print(f"💾 Found {len(db_leaders)} leaders in database for {domain}")
            # Cache the database results for future use
            if CACHE_AVAILABLE:
                cache_leaders(domain, db_leaders)
            return db_leaders
    
    # Step 3: Use LLM extraction (most current)
    if LLM_EXTRACTION_AVAILABLE:
        try:
            print(f"🤖 Attempting LLM-based leadership extraction for {domain}...")
            llm_leaders = get_company_leaders_with_llm(domain)
            
            if llm_leaders:
                print(f"✅ Successfully extracted {len(llm_leaders)} leaders using LLM for {domain}")
                
                # Save to database for persistence
                if DATABASE_AVAILABLE:
                    save_leaders_to_db(domain, llm_leaders, 'llm')
                
                # Cache the results for future use
                if CACHE_AVAILABLE:
                    cache_leaders(domain, llm_leaders)
                
                return llm_leaders
            else:
                print(f"⚠️  No leaders found via LLM for {domain}")
                
        except Exception as e:
            print(f"❌ LLM extraction failed for {domain}: {e}")
    
    # Step 4: Fallback to fake data
    print(f"🔄 Falling back to sample data for {domain}")
    fake_leaders = get_fake_company_leaders(domain)
    
    # Save fake data to database for consistency
    if DATABASE_AVAILABLE:
        save_leaders_to_db(domain, fake_leaders, 'fake_data')
    
    # Cache the fake data
    if CACHE_AVAILABLE:
        cache_leaders(domain, fake_leaders)
    
    return fake_leaders


def get_fake_company_leaders(domain: str) -> List[Dict[str, str]]:
    """
    Get fake company leaders for a given domain (fallback method).
    
    Args:
        domain (str): The company domain (e.g., "apple.com")
        
    Returns:
        List[Dict[str, str]]: List of fake leader dictionaries
    """
    # Extract company name from domain
    company_name = domain.split('.')[0].title()
    
    # Fake leader data - replace with real implementation later
    fake_leaders = {
        "apple.com": [
            {"name": "Tim Cook", "title": "CEO"},
            {"name": "Jeff Williams", "title": "COO"},
            {"name": "Luca Maestri", "title": "CFO"},
            {"name": "Craig Federighi", "title": "SVP of Software Engineering"},
            {"name": "Eddy Cue", "title": "SVP of Services"}
        ],
        "microsoft.com": [
            {"name": "Satya Nadella", "title": "CEO"},
            {"name": "Brad Smith", "title": "President"},
            {"name": "Amy Hood", "title": "CFO"},
            {"name": "Judson Althoff", "title": "EVP of Worldwide Commercial Business"},
            {"name": "Scott Guthrie", "title": "EVP of Cloud and AI"}
        ],
        "google.com": [
            {"name": "Sundar Pichai", "title": "CEO"},
            {"name": "Ruth Porat", "title": "CFO"},
            {"name": "Kent Walker", "title": "President of Global Affairs"},
            {"name": "Philipp Schindler", "title": "SVP and Chief Business Officer"},
            {"name": "Prabhakar Raghavan", "title": "SVP of Search"}
        ],
        "amazon.com": [
            {"name": "Andy Jassy", "title": "CEO"},
            {"name": "Brian Olsavsky", "title": "CFO"},
            {"name": "David Zapolsky", "title": "SVP of Global Public Policy"},
            {"name": "Beth Galetti", "title": "SVP of Human Resources"},
            {"name": "Jeff Blackburn", "title": "SVP of Global Media and Entertainment"}
        ],
        "meta.com": [
            {"name": "Mark Zuckerberg", "title": "CEO"},
            {"name": "Sheryl Sandberg", "title": "COO"},
            {"name": "David Wehner", "title": "CFO"},
            {"name": "Mike Schroepfer", "title": "CTO"},
            {"name": "Nick Clegg", "title": "VP of Global Affairs"}
        ]
    }
    
    # Return fake leaders if we have data for this domain
    if domain in fake_leaders:
        return fake_leaders[domain]
    
    # Default fake leaders for unknown companies
    return [
        {"name": f"John Smith", "title": "CEO"},
        {"name": f"Sarah Johnson", "title": "CTO"},
        {"name": f"Michael Brown", "title": "CFO"},
        {"name": f"Emily Davis", "title": "COO"},
        {"name": f"David Wilson", "title": "VP of Engineering"}
    ]


def get_company_info(url: str) -> Dict[str, any]:
    """
    Get comprehensive company information from a URL.
    
    Args:
        url (str): The company URL
        
    Returns:
        Dict[str, any]: Dictionary containing company domain and leaders
    """
    domain = extract_company_domain(url)
    leaders = get_company_leaders(domain)
    
    # Determine data source
    data_source = "unknown"
    if LLM_EXTRACTION_AVAILABLE and leaders and not any("John Smith" in leader["name"] for leader in leaders):
        data_source = "llm_extraction"
    elif DATABASE_AVAILABLE:
        data_source = "database"
    else:
        data_source = "fake_data"
    
    return {
        "domain": domain,
        "leaders": leaders,
        "source_url": url,
        "data_source": data_source,
        "cache_available": CACHE_AVAILABLE,
        "database_available": DATABASE_AVAILABLE,
        "llm_available": LLM_EXTRACTION_AVAILABLE
    }


def validate_company_url(url: str) -> bool:
    """
    Validate if a URL appears to be a company website.
    
    Args:
        url (str): The URL to validate
        
    Returns:
        bool: True if the URL appears valid, False otherwise
    """
    try:
        domain = extract_company_domain(url)
        
        # Basic validation - domain should have at least 3 characters
        if len(domain) < 3:
            return False
            
        # Check for common invalid patterns
        invalid_patterns = [
            r'^localhost',
            r'^127\.',
            r'^192\.168\.',
            r'^10\.',
            r'^172\.(1[6-9]|2[0-9]|3[0-1])\.'
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, domain):
                return False
                
        return True
        
    except ValueError:
        return False


if __name__ == "__main__":
    # Example usage and testing
    test_urls = [
        "https://www.apple.com/products",
        "https://microsoft.com/about",
        "https://google.com",
        "https://invalid-url"
    ]
    
    for url in test_urls:
        print(f"\nTesting URL: {url}")
        try:
            if validate_company_url(url):
                company_info = get_company_info(url)
                print(f"Domain: {company_info['domain']}")
                print(f"Data Source: {company_info['data_source']}")
                print(f"Cache Available: {company_info['cache_available']}")
                print(f"Database Available: {company_info['database_available']}")
                print(f"LLM Available: {company_info['llm_available']}")
                print("Leaders:")
                for leader in company_info['leaders']:
                    print(f"  - {leader['name']} ({leader['title']})")
            else:
                print("Invalid company URL")
        except Exception as e:
            print(f"Error: {e}")
