"""
Web scraping utilities for LeadPrep AI.

This module provides functions to extract company leadership information
from company websites by scraping their About/Leadership pages.
"""

import requests
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Optional, Tuple
import time
import random


class WebScraper:
    """Web scraper for extracting company leadership information."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Common leadership page patterns
        self.leadership_paths = [
            '/about',
            '/about-us',
            '/about/leadership',
            '/about/team',
            '/leadership',
            '/team',
            '/executives',
            '/management',
            '/about/management',
            '/company',
            '/company/leadership',
            '/about/executives',
            '/about/management-team',
            '/leadership-team',
            '/executive-team',
            '/management-team',
            '/about/our-team',
            '/team/leadership'
        ]
        
        # Common leadership title patterns
        self.leadership_titles = [
            'CEO', 'Chief Executive Officer',
            'COO', 'Chief Operating Officer', 
            'CFO', 'Chief Financial Officer',
            'CTO', 'Chief Technology Officer',
            'CIO', 'Chief Information Officer',
            'CMO', 'Chief Marketing Officer',
            'CHRO', 'Chief Human Resources Officer',
            'CLO', 'Chief Legal Officer',
            'President',
            'Founder',
            'Co-Founder',
            'Executive Vice President',
            'Senior Vice President',
            'Vice President',
            'Director',
            'Managing Director',
            'General Manager'
        ]
        
        # Common name patterns in HTML
        self.name_patterns = [
            r'<h[1-6][^>]*>([^<]*?(?:CEO|COO|CFO|CTO|President|Founder|VP|Director)[^<]*)</h[1-6]>',
            r'<div[^>]*class="[^"]*(?:name|title|executive|leader)[^"]*"[^>]*>([^<]+)</div>',
            r'<span[^>]*class="[^"]*(?:name|title|executive|leader)[^"]*"[^>]*>([^<]+)</span>',
            r'<p[^>]*class="[^"]*(?:name|title|executive|leader)[^"]*"[^>]*>([^<]+)</p>'
        ]

    def find_leadership_page(self, base_url: str) -> Optional[str]:
        """
        Find the leadership/about page for a company.
        
        Args:
            base_url (str): The company's base URL
            
        Returns:
            Optional[str]: URL of the leadership page if found
        """
        # Clean the base URL
        if not base_url.startswith(('http://', 'https://')):
            base_url = 'https://' + base_url
            
        # Remove trailing slash
        base_url = base_url.rstrip('/')
        
        # Try each leadership path
        for path in self.leadership_paths:
            url = base_url + path
            try:
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    # Check if page contains leadership-related content
                    soup = BeautifulSoup(response.content, 'html.parser')
                    text = soup.get_text().lower()
                    
                    # Look for leadership indicators
                    leadership_indicators = ['leadership', 'executive', 'team', 'management', 'about us']
                    if any(indicator in text for indicator in leadership_indicators):
                        return url
                        
            except Exception as e:
                print(f"Error checking {url}: {e}")
                continue
                
        return None

    def extract_leadership_info(self, url: str) -> List[Dict[str, str]]:
        """
        Extract leadership information from a company page.
        
        Args:
            url (str): URL of the leadership page
            
        Returns:
            List[Dict[str, str]]: List of leaders with name and title
        """
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            leaders = []
            
            # Method 1: Look for structured data (JSON-LD)
            leaders.extend(self._extract_from_structured_data(soup))
            
            # Method 2: Look for common HTML patterns
            leaders.extend(self._extract_from_html_patterns(soup))
            
            # Method 3: Look for text patterns
            leaders.extend(self._extract_from_text_patterns(soup))
            
            # Remove duplicates and clean up
            unique_leaders = self._deduplicate_leaders(leaders)
            
            return unique_leaders[:5]  # Return top 5 leaders
            
        except Exception as e:
            print(f"Error extracting leadership from {url}: {e}")
            return []

    def _extract_from_structured_data(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract leadership from JSON-LD structured data."""
        leaders = []
        
        # Look for JSON-LD scripts
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                import json
                data = json.loads(script.string)
                
                # Handle different JSON-LD structures
                if isinstance(data, dict):
                    if data.get('@type') == 'Organization':
                        # Look for employees/people
                        employees = data.get('employee', [])
                        if not isinstance(employees, list):
                            employees = [employees]
                            
                        for employee in employees:
                            if isinstance(employee, dict):
                                name = employee.get('name', '')
                                title = employee.get('jobTitle', '')
                                if name and title and any(title_pattern in title.upper() for title_pattern in self.leadership_titles):
                                    leaders.append({'name': name, 'title': title})
                                    
            except (json.JSONDecodeError, AttributeError):
                continue
                
        return leaders

    def _extract_from_html_patterns(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract leadership from common HTML patterns."""
        leaders = []
        
        # Look for common leadership page structures
        leadership_selectors = [
            '.executive', '.leader', '.management', '.team-member',
            '[class*="executive"]', '[class*="leader"]', '[class*="management"]',
            '[class*="team"]', '[class*="officer"]'
        ]
        
        for selector in leadership_selectors:
            elements = soup.select(selector)
            for element in elements:
                name, title = self._extract_name_title_from_element(element)
                if name and title:
                    leaders.append({'name': name, 'title': title})
                    
        return leaders

    def _extract_from_text_patterns(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract leadership from text patterns."""
        leaders = []
        text = soup.get_text()
        
        # Look for patterns like "Name, Title" or "Title: Name"
        patterns = [
            r'([A-Z][a-z]+ [A-Z][a-z]+),?\s*(CEO|COO|CFO|CTO|President|Founder|VP|Director)',
            r'(CEO|COO|CFO|CTO|President|Founder|VP|Director):?\s*([A-Z][a-z]+ [A-Z][a-z]+)',
            r'([A-Z][a-z]+ [A-Z][a-z]+)\s*-\s*(CEO|COO|CFO|CTO|President|Founder|VP|Director)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match) == 2:
                    if match[0].upper() in self.leadership_titles:
                        # Title first, then name
                        leaders.append({'name': match[1], 'title': match[0]})
                    else:
                        # Name first, then title
                        leaders.append({'name': match[0], 'title': match[1]})
                        
        return leaders

    def _extract_name_title_from_element(self, element) -> Tuple[Optional[str], Optional[str]]:
        """Extract name and title from an HTML element."""
        # Look for name and title in the element or its children
        name = None
        title = None
        
        # Common patterns for names and titles
        name_selectors = ['.name', '.executive-name', '.leader-name', 'h3', 'h4']
        title_selectors = ['.title', '.job-title', '.position', '.role']
        
        # Try to find name
        for selector in name_selectors:
            name_elem = element.select_one(selector)
            if name_elem:
                name = name_elem.get_text().strip()
                break
                
        # Try to find title
        for selector in title_selectors:
            title_elem = element.select_one(selector)
            if title_elem:
                title = title_elem.get_text().strip()
                break
                
        # If we found one but not the other, try to extract from text
        if name and not title:
            text = element.get_text()
            for title_pattern in self.leadership_titles:
                if title_pattern.lower() in text.lower():
                    title = title_pattern
                    break
                    
        if title and not name:
            # Try to extract name from parent or sibling elements
            parent = element.parent
            if parent:
                name_elem = parent.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                if name_elem:
                    name = name_elem.get_text().strip()
                    
        return name, title

    def _deduplicate_leaders(self, leaders: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Remove duplicate leaders and clean up data."""
        seen = set()
        unique_leaders = []
        
        for leader in leaders:
            name = leader.get('name', '').strip()
            title = leader.get('title', '').strip()
            
            if name and title:
                # Create a key for deduplication
                key = f"{name.lower()}_{title.lower()}"
                if key not in seen:
                    seen.add(key)
                    unique_leaders.append({
                        'name': name,
                        'title': title
                    })
                    
        return unique_leaders

    def scrape_company_leadership(self, company_url: str) -> List[Dict[str, str]]:
        """
        Main function to scrape company leadership.
        
        Args:
            company_url (str): Company URL or domain
            
        Returns:
            List[Dict[str, str]]: List of leaders with name and title
        """
        print(f"🔍 Scraping leadership for: {company_url}")
        
        # Find the leadership page
        leadership_page = self.find_leadership_page(company_url)
        
        if not leadership_page:
            print(f"❌ No leadership page found for {company_url}")
            return []
            
        print(f"✅ Found leadership page: {leadership_page}")
        
        # Extract leadership information
        leaders = self.extract_leadership_info(leadership_page)
        
        if leaders:
            print(f"✅ Found {len(leaders)} leaders")
            for leader in leaders:
                print(f"  - {leader['name']} ({leader['title']})")
        else:
            print(f"❌ No leaders found on {leadership_page}")
            
        return leaders


# Global scraper instance
scraper = WebScraper()


def get_company_leaders_from_web(company_url: str) -> List[Dict[str, str]]:
    """
    Get company leaders by scraping the company website.
    
    Args:
        company_url (str): Company URL or domain
        
    Returns:
        List[Dict[str, str]]: List of leaders with name and title
    """
    try:
        return scraper.scrape_company_leadership(company_url)
    except Exception as e:
        print(f"Error scraping {company_url}: {e}")
        return []


if __name__ == "__main__":
    # Test the scraper
    test_companies = [
        "apple.com",
        "microsoft.com", 
        "google.com"
    ]
    
    for company in test_companies:
        print(f"\n{'='*50}")
        print(f"Testing: {company}")
        print(f"{'='*50}")
        
        leaders = get_company_leaders_from_web(company)
        
        if leaders:
            print(f"\nFound {len(leaders)} leaders:")
            for leader in leaders:
                print(f"  - {leader['name']} ({leader['title']})")
        else:
            print("No leaders found") 