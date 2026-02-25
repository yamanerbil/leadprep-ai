"""
LLM-based company leadership extraction for LeadPrep AI.

This module uses Claude to intelligently extract company leadership information
using the model's knowledge rather than web scraping.
"""

import requests
import json
from typing import List, Dict, Optional
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LLMLeaderExtractor:
    """LLM-based extractor for company leadership information."""

    def __init__(self):
        self.api_key = os.getenv('ANTHROPIC_API_KEY')
        if not self.api_key:
            print("⚠️  ANTHROPIC_API_KEY not found in environment variables")
            print("   Please set your Anthropic API key in a .env file")

    def extract_leaders_with_llm(self, company_url: str) -> List[Dict[str, str]]:
        """
        Extract company leaders using Claude's knowledge.

        Args:
            company_url (str): Company URL or domain

        Returns:
            List[Dict[str, str]]: List of leaders with name and title
        """
        if not self.api_key:
            print("❌ Anthropic API key not available")
            return []

        print(f"🔍 Using Claude to find leadership for: {company_url}")

        # Use Claude to extract leaders from its knowledge
        leaders = self._call_claude_for_leaders(company_url)

        if leaders:
            print(f"✅ Found {len(leaders)} leaders using Claude")
            for i, leader in enumerate(leaders, 1):
                print(f"  {i}. {leader['name']} ({leader['title']})")
        else:
            print(f"❌ No leaders found using Claude")

        return leaders

    def _call_claude_for_leaders(self, company_url: str) -> List[Dict[str, str]]:
        """
        Call Claude API to extract leaders using its knowledge.

        Args:
            company_url (str): Company URL or domain

        Returns:
            List[Dict[str, str]]: List of leaders
        """
        try:
            # Clean the company URL to get domain
            if company_url.startswith(('http://', 'https://')):
                from urllib.parse import urlparse
                parsed = urlparse(company_url)
                domain = parsed.netloc
            else:
                domain = company_url

            # Remove 'www.' prefix if present
            if domain.startswith('www.'):
                domain = domain[4:]

            # Prepare the prompt
            prompt = f"""Given the company domain: {domain}

Please provide the top 15 most important current company leaders (executives, founders, key management) for this company.

Focus on finding:
- CEOs, Presidents, Founders
- C-level executives (CFO, CTO, COO, CMO, etc.)
- Senior Vice Presidents
- Key Directors and Managers
- Board members (if they are key executives)
- Other senior leadership positions

Use your knowledge to provide the most current and accurate information available. If you're not certain about current positions, indicate that in the title.

Return ONLY a JSON array of objects with "name" and "title" fields. For example:
[
    {{"name": "John Smith", "title": "CEO"}},
    {{"name": "Jane Doe", "title": "CFO"}},
    {{"name": "Bob Johnson", "title": "CTO"}}
]

If you cannot find reliable leadership information for this company, return an empty array [].

Be as comprehensive as possible and include up to 15 leaders if available."""

            # Call Anthropic API
            headers = {
                'x-api-key': self.api_key,
                'anthropic-version': '2023-06-01',
                'Content-Type': 'application/json'
            }

            data = {
                'model': 'claude-sonnet-4-20250514',
                'max_tokens': 2000,
                'messages': [
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'system': 'You are a helpful assistant that extracts company leadership information and returns it in JSON format. Always return valid JSON arrays.',
                'temperature': 0.1
            }

            response = requests.post(
                'https://api.anthropic.com/v1/messages',
                headers=headers,
                json=data,
                timeout=30
            )

            if response.status_code == 200:
                result = response.json()
                content = result['content'][0]['text']

                # Try to parse JSON response
                try:
                    # Clean up the response to extract JSON
                    content = content.strip()
                    if content.startswith('```json'):
                        content = content[7:]
                    if content.endswith('```'):
                        content = content[:-3]
                    content = content.strip()

                    leaders = json.loads(content)

                    # Validate the structure
                    if isinstance(leaders, list):
                        valid_leaders = []
                        for leader in leaders:
                            if isinstance(leader, dict) and 'name' in leader and 'title' in leader:
                                valid_leaders.append({
                                    'name': leader['name'].strip(),
                                    'title': leader['title'].strip()
                                })
                        return valid_leaders[:15]  # Return top 15

                except json.JSONDecodeError as e:
                    print(f"❌ Failed to parse JSON response: {e}")
                    print(f"Response: {content}")

            else:
                print(f"❌ API call failed: {response.status_code}")
                print(f"Response: {response.text}")

        except Exception as e:
            print(f"❌ Error calling Claude: {e}")

        return []

    def get_company_leaders(self, company_url: str) -> List[Dict[str, str]]:
        """
        Main function to get company leaders using LLM.

        Args:
            company_url (str): Company URL or domain

        Returns:
            List[Dict[str, str]]: List of leaders with name and title
        """
        return self.extract_leaders_with_llm(company_url)


# Global extractor instance
llm_extractor = LLMLeaderExtractor()


def get_company_leaders_with_llm(company_url: str) -> List[Dict[str, str]]:
    """
    Get company leaders using LLM analysis.

    Args:
        company_url (str): Company URL or domain

    Returns:
        List[Dict[str, str]]: List of leaders with name and title
    """
    try:
        return llm_extractor.get_company_leaders(company_url)
    except Exception as e:
        print(f"Error extracting leaders with LLM for {company_url}: {e}")
        return []


if __name__ == "__main__":
    # Test the LLM extractor
    test_companies = [
        "apple.com",
        "microsoft.com",
        "google.com",
        "amazon.com",
        "meta.com"
    ]

    for company in test_companies:
        print(f"\n{'='*60}")
        print(f"Testing LLM extraction: {company}")
        print(f"{'='*60}")

        leaders = get_company_leaders_with_llm(company)

        if leaders:
            print(f"\nFound {len(leaders)} leaders:")
            for i, leader in enumerate(leaders, 1):
                print(f"  {i}. {leader['name']} ({leader['title']})")
        else:
            print("No leaders found")
