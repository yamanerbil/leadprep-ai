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
            '/team/leadership',
            '/about/leadership-team',
            '/about/executive-team'
        ]
        
        # Common leadership title patterns (expanded and improved)
        self.leadership_titles = [
            'CEO', 'Chief Executive Officer',
            'COO', 'Chief Operating Officer', 
            'CFO', 'Chief Financial Officer',
            'CTO', 'Chief Technology Officer',
            'CIO', 'Chief Information Officer',
            'CMO', 'Chief Marketing Officer',
            'CHRO', 'Chief Human Resources Officer',
            'CLO', 'Chief Legal Officer',
            'CDO', 'Chief Data Officer',
            'CSO', 'Chief Security Officer',
            'President',
            'Founder',
            'Co-Founder',
            'Executive Vice President',
            'Senior Vice President',
            'Vice President',
            'VP',
            'Director',
            'Managing Director',
            'General Manager',
            'Head of',
            'Senior Director',
            'Executive Director'
        ]
        
        # Common name patterns in HTML (improved)
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
                    leadership_indicators = ['leadership', 'executive', 'team', 'management', 'about us', 'officer', 'president', 'ceo', 'founder']
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
            
            # Method 3: Look for text patterns (improved)
            leaders.extend(self._extract_from_text_patterns(soup))
            
            # Method 4: Look for specific leadership sections
            leaders.extend(self._extract_from_leadership_sections(soup))
            
            # Remove duplicates and clean up
            unique_leaders = self._deduplicate_leaders(leaders)
            
            # Filter and validate leaders
            valid_leaders = self._validate_leaders(unique_leaders)
            
            return valid_leaders[:10]  # Return top 10 leaders
            
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
            '[class*="team"]', '[class*="officer"]', '[class*="president"]',
            '[class*="ceo"]', '[class*="founder"]', '[class*="director"]'
        ]
        
        for selector in leadership_selectors:
            elements = soup.select(selector)
            for element in elements:
                name, title = self._extract_name_title_from_element(element)
                if name and title:
                    leaders.append({'name': name, 'title': title})
                    
        return leaders

    def _extract_from_leadership_sections(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract leadership from specific leadership sections."""
        leaders = []
        
        # Look for sections that likely contain leadership info
        leadership_sections = [
            'h1', 'h2', 'h3', 'h4', 'h5', 'h6'
        ]
        
        for tag in leadership_sections:
            headings = soup.find_all(tag)
            for heading in headings:
                text = heading.get_text().strip()
                if any(title in text.upper() for title in self.leadership_titles):
                    # Look for name in the heading or nearby elements
                    name, title = self._extract_from_heading_context(heading)
                    if name and title:
                        leaders.append({'name': name, 'title': title})
                        
        return leaders

    def _extract_from_heading_context(self, heading) -> Tuple[Optional[str], Optional[str]]:
        """Extract name and title from heading context."""
        # Try to find name in the heading text
        heading_text = heading.get_text().strip()
        
        # Look for patterns like "Name - Title" or "Title: Name"
        patterns = [
            r'([A-Z][a-z]+ [A-Z][a-z]+)\s*[-–—]\s*(CEO|COO|CFO|CTO|President|Founder|VP|Director|Chief)',
            r'(CEO|COO|CFO|CTO|President|Founder|VP|Director|Chief)[\s:]*([A-Z][a-z]+ [A-Z][a-z]+)',
            r'([A-Z][a-z]+ [A-Z][a-z]+),\s*(CEO|COO|CFO|CTO|President|Founder|VP|Director|Chief)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, heading_text, re.IGNORECASE)
            if match:
                if match.group(1).upper() in self.leadership_titles:
                    return match.group(2), match.group(1)
                else:
                    return match.group(1), match.group(2)
                    
        # Look in nearby elements
        parent = heading.parent
        if parent:
            # Look for name in nearby paragraphs or divs
            nearby_elements = parent.find_all(['p', 'div', 'span'], limit=5)
            for element in nearby_elements:
                text = element.get_text().strip()
                if len(text) > 10 and len(text) < 100:  # Reasonable name length
                    # Check if this looks like a name
                    if re.match(r'^[A-Z][a-z]+ [A-Z][a-z]+$', text):
                        # Find title in heading
                        for title in self.leadership_titles:
                            if title.lower() in heading_text.lower():
                                return text, title
                                
        return None, None

    def _extract_from_text_patterns(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract leadership from text patterns (improved)."""
        leaders = []
        text = soup.get_text()
        
        # Improved patterns for name-title combinations
        patterns = [
            # "Name, Title" or "Name - Title"
            r'([A-Z][a-z]+ [A-Z][a-z]+)[,\s-]+(CEO|COO|CFO|CTO|President|Founder|VP|Director|Chief\s+\w+)',
            # "Title: Name" or "Title - Name"
            r'(CEO|COO|CFO|CTO|President|Founder|VP|Director|Chief\s+\w+)[:\s-]+([A-Z][a-z]+ [A-Z][a-z]+)',
            # "Name (Title)" or "Name - Title"
            r'([A-Z][a-z]+ [A-Z][a-z]+)\s*[\(-]\s*(CEO|COO|CFO|CTO|President|Founder|VP|Director|Chief\s+\w+)',
            # Full titles
            r'([A-Z][a-z]+ [A-Z][a-z]+)[,\s-]+(Chief\s+Executive\s+Officer|Chief\s+Operating\s+Officer|Chief\s+Financial\s+Officer|Chief\s+Technology\s+Officer|Executive\s+Vice\s+President|Senior\s+Vice\s+President)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match) == 2:
                    name = match[0].strip()
                    title = match[1].strip()
                    
                    # Validate name format
                    if self._is_valid_name(name) and self._is_valid_title(title):
                        if title.upper() in [t.upper() for t in self.leadership_titles]:
                            leaders.append({'name': name, 'title': title})
                        else:
                            # Check if title contains leadership keywords
                            if any(keyword in title.upper() for keyword in ['CEO', 'COO', 'CFO', 'CTO', 'PRESIDENT', 'FOUNDER', 'VP', 'DIRECTOR', 'CHIEF']):
                                leaders.append({'name': name, 'title': title})
                        
        return leaders

    def _is_valid_name(self, name: str) -> bool:
        """Check if a string looks like a valid person name."""
        if not name or len(name) < 4 or len(name) > 50:
            return False
            
        # Should contain at least two words (first and last name)
        words = name.split()
        if len(words) < 2:
            return False
            
        # Each word should start with capital letter
        for word in words:
            if not word[0].isupper():
                return False
                
        # Should not contain numbers or special characters (except hyphens for names like "Jean-Pierre")
        if re.search(r'[0-9!@#$%^&*()_+=]', name):
            return False
            
        return True

    def _is_valid_title(self, title: str) -> bool:
        """Check if a string looks like a valid job title."""
        if not title or len(title) < 2 or len(title) > 100:
            return False
            
        # Should contain at least one leadership keyword
        leadership_keywords = ['CEO', 'COO', 'CFO', 'CTO', 'PRESIDENT', 'FOUNDER', 'VP', 'DIRECTOR', 'CHIEF', 'OFFICER', 'MANAGER']
        title_upper = title.upper()
        
        return any(keyword in title_upper for keyword in leadership_keywords)

    def _extract_name_title_from_element(self, element) -> Tuple[Optional[str], Optional[str]]:
        """Extract name and title from an HTML element."""
        # Look for name and title in the element or its children
        name = None
        title = None
        
        # Common patterns for names and titles
        name_selectors = ['.name', '.executive-name', '.leader-name', 'h3', 'h4', 'h5']
        title_selectors = ['.title', '.job-title', '.position', '.role']
        
        # Try to find name
        for selector in name_selectors:
            name_elem = element.select_one(selector)
            if name_elem:
                name = name_elem.get_text().strip()
                if self._is_valid_name(name):
                    break
                else:
                    name = None
                    
        # Try to find title
        for selector in title_selectors:
            title_elem = element.select_one(selector)
            if title_elem:
                title = title_elem.get_text().strip()
                if self._is_valid_title(title):
                    break
                else:
                    title = None
                    
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
                    potential_name = name_elem.get_text().strip()
                    if self._is_valid_name(potential_name):
                        name = potential_name
                    
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

    def _validate_leaders(self, leaders: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Validate and filter leaders for quality."""
        valid_leaders = []
        
        for leader in leaders:
            name = leader.get('name', '')
            title = leader.get('title', '')
            
            # Apply validation filters
            if (self._is_valid_name(name) and 
                self._is_valid_title(title) and
                len(name) > 3 and
                len(title) > 2):
                valid_leaders.append(leader)
                
        return valid_leaders

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
            for i, leader in enumerate(leaders, 1):
                print(f"  {i}. {leader['name']} ({leader['title']})")
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
        "google.com",
        "amazon.com",
        "meta.com"
    ]
    
    for company in test_companies:
        print(f"\n{'='*60}")
        print(f"Testing: {company}")
        print(f"{'='*60}")
        
        leaders = get_company_leaders_from_web(company)
        
        if leaders:
            print(f"\nFound {len(leaders)} leaders:")
            for i, leader in enumerate(leaders, 1):
                print(f"  {i}. {leader['name']} ({leader['title']})")
        else:
            print("No leaders found") 