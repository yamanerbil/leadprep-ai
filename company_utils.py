"""
Company utilities for LeadPrep AI.

This module provides functions to extract company information from URLs
and identify key company leaders for sales preparation.
"""

import re
from urllib.parse import urlparse
from typing import List, Dict, Optional

# Import web scraping functionality
try:
    from web_scraper import get_company_leaders_from_web
    WEB_SCRAPING_AVAILABLE = True
except ImportError:
    WEB_SCRAPING_AVAILABLE = False
    print("⚠️  Web scraping not available. Using fake data only.")


def extract_company_domain(url: str) -> str:
    """
    Extract the company domain from a given URL.
    
    Args:
        url (str): The company URL (e.g., "https://www.apple.com/products")
        
    Returns:
        str: The company domain (e.g., "apple.com")
        
    Raises:
        ValueError: If the URL is invalid or cannot be parsed
    """
    try:
        # Parse the URL
        parsed_url = urlparse(url)
        
        # Extract the netloc (domain)
        domain = parsed_url.netloc
        
        # Remove 'www.' prefix if present
        if domain.startswith('www.'):
            domain = domain[4:]
            
        # Validate that we have a domain
        if not domain or '.' not in domain:
            raise ValueError(f"Invalid URL: {url}")
            
        return domain
        
    except Exception as e:
        raise ValueError(f"Failed to parse URL '{url}': {str(e)}")


def get_company_leaders(domain: str) -> List[Dict[str, str]]:
    """
    Get key company leaders for a given domain.
    
    First tries web scraping, then falls back to fake data.
    
    Args:
        domain (str): The company domain (e.g., "apple.com")
        
    Returns:
        List[Dict[str, str]]: List of leader dictionaries with 'name' and 'title' keys
    """
    # Try web scraping first if available
    if WEB_SCRAPING_AVAILABLE:
        try:
            print(f"🔍 Attempting to scrape leadership data for {domain}...")
            scraped_leaders = get_company_leaders_from_web(domain)
            
            if scraped_leaders:
                print(f"✅ Successfully scraped {len(scraped_leaders)} leaders from {domain}")
                return scraped_leaders
            else:
                print(f"⚠️  No leaders found via web scraping for {domain}, using fallback data")
                
        except Exception as e:
            print(f"❌ Web scraping failed for {domain}: {e}")
            print("🔄 Falling back to fake data...")
    
    # Fallback to fake leader data
    return get_fake_company_leaders(domain)


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
            {"name": "Jeff Williams", "title": "COO"}
        ],
        "microsoft.com": [
            {"name": "Satya Nadella", "title": "CEO"},
            {"name": "Brad Smith", "title": "President"}
        ],
        "google.com": [
            {"name": "Sundar Pichai", "title": "CEO"},
            {"name": "Ruth Porat", "title": "CFO"}
        ],
        "amazon.com": [
            {"name": "Andy Jassy", "title": "CEO"},
            {"name": "Brian Olsavsky", "title": "CFO"}
        ],
        "meta.com": [
            {"name": "Mark Zuckerberg", "title": "CEO"},
            {"name": "Sheryl Sandberg", "title": "COO"}
        ]
    }
    
    # Return fake leaders if we have data for this domain
    if domain in fake_leaders:
        return fake_leaders[domain]
    
    # Default fake leaders for unknown companies
    return [
        {"name": f"John Smith", "title": "CEO"},
        {"name": f"Sarah Johnson", "title": "CTO"}
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
    
    return {
        "domain": domain,
        "leaders": leaders,
        "source_url": url,
        "data_source": "web_scraping" if WEB_SCRAPING_AVAILABLE and leaders and not any("John Smith" in leader["name"] for leader in leaders) else "fake_data"
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
                print("Leaders:")
                for leader in company_info['leaders']:
                    print(f"  - {leader['name']} ({leader['title']})")
            else:
                print("Invalid company URL")
        except Exception as e:
            print(f"Error: {e}")
