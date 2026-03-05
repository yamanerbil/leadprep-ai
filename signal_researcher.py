"""
Signal Researcher for LeadPrep AI.

Deep, unconstrained web research on companies and leads.
Minimal scaffolding — let Claude search freely and synthesize what it finds.
"""

import json
import os
import requests
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('ANTHROPIC_API_KEY')
API_URL = 'https://api.anthropic.com/v1/messages'
MODEL = 'claude-sonnet-4-20250514'


def _call_anthropic(messages, tools=None, max_tokens=16000):
    """Make a raw API call to Anthropic with optional tool use."""
    headers = {
        'x-api-key': API_KEY,
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json',
    }

    body = {
        'model': MODEL,
        'max_tokens': max_tokens,
        'messages': messages,
    }
    if tools:
        body['tools'] = tools

    resp = requests.post(API_URL, headers=headers, json=body, timeout=120)
    resp.raise_for_status()
    return resp.json()


def _extract_text(response):
    """Pull all text blocks out of an Anthropic response."""
    parts = []
    for block in response.get('content', []):
        if block.get('type') == 'text':
            parts.append(block['text'])
    return '\n'.join(parts)


def _parse_json_from_text(text):
    """Best-effort JSON extraction from Claude's response."""
    # Try the whole thing first
    try:
        return json.loads(text.strip())
    except (json.JSONDecodeError, ValueError):
        pass

    # Try to find a JSON block in markdown fences
    import re
    fence_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', text, re.DOTALL)
    if fence_match:
        try:
            return json.loads(fence_match.group(1).strip())
        except (json.JSONDecodeError, ValueError):
            pass

    # Find the outermost { ... }
    start = text.find('{')
    end = text.rfind('}')
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except (json.JSONDecodeError, ValueError):
            pass

    return None


def research_lead(company_domain: str,
                  lead_name: Optional[str] = None,
                  lead_title: Optional[str] = None,
                  company_name: Optional[str] = None) -> Dict:
    """
    Deep research on a company and optional specific lead.

    Returns a dict with signals, pain hypotheses, conversation hooks, etc.
    The prompt is intentionally loose — Claude decides what matters.
    """
    if not API_KEY:
        return {'error': 'ANTHROPIC_API_KEY not configured'}

    # Build the context the model will work from
    who = company_name or company_domain
    target = ''
    if lead_name:
        target = f'\nSpecific person to research: {lead_name}'
        if lead_title:
            target += f' ({lead_title})'

    prompt = f"""You are a world-class sales researcher. A BDR is about to cold-call or email someone at this company and needs to sound like they actually know what's going on.

Company: {who} ({company_domain}){target}

Do thorough research. Search multiple times. Look for:
- Recent company news, funding, earnings, reorg, acquisitions, layoffs, product launches
- What this specific person has said publicly — LinkedIn posts, conference talks, podcast appearances, press quotes
- Job postings that reveal what teams are growing or what problems they're solving
- Glassdoor or Blind sentiment — especially around internal culture, feedback, performance reviews
- Competitor moves that might be creating pressure
- Industry trends affecting this company right now
- Leadership changes — new CHRO, VP People, Head of Talent — these are buying signals
- Anything surprising or non-obvious

Don't hold back. Surface raw facts. The BDR will decide what to use.

Return a JSON object:
{{
  "company_overview": "2-3 sentence snapshot of the company right now",
  "company_signals": [
    {{"signal": "what happened", "source": "where you found it", "date": "when", "relevance": "why a salesperson cares"}}
  ],
  "person_signals": [
    {{"signal": "what they said/did", "source": "where", "date": "when"}}
  ],
  "industry_context": "what's happening in their space that creates urgency",
  "pain_hypotheses": [
    "specific problem they might have based on what you found"
  ],
  "conversation_hooks": [
    "a specific thing to reference that shows you did your homework"
  ],
  "buying_signals": [
    "evidence they might be in-market for people/performance/review tools"
  ],
  "sources": ["url1", "url2"]
}}"""

    messages = [{'role': 'user', 'content': prompt}]

    # Try with web search first (server-side connector tool)
    tools = [
        {
            'type': 'web_search_20250305',
            'name': 'web_search',
            'max_uses': 15,
        }
    ]

    try:
        print(f'Researching {who}' + (f' / {lead_name}' if lead_name else '') + ' ...')
        response = _call_anthropic(messages, tools=tools)
        text = _extract_text(response)

        if not text:
            # Fallback: retry without web search
            print('Web search response empty, retrying without tools...')
            response = _call_anthropic(messages, tools=None, max_tokens=4000)
            text = _extract_text(response)

    except requests.exceptions.HTTPError as e:
        # If web search tool not supported, fall back to model knowledge
        print(f'Web search not available ({e}), using model knowledge...')
        fallback_messages = [{
            'role': 'user',
            'content': prompt.replace('Search multiple times. ', '')
        }]
        response = _call_anthropic(fallback_messages, tools=None, max_tokens=4000)
        text = _extract_text(response)

    # Parse structured output
    parsed = _parse_json_from_text(text)
    if parsed:
        parsed['_raw'] = text
        return parsed

    # If parsing failed, return raw research
    return {
        'company_overview': '',
        'company_signals': [],
        'person_signals': [],
        'industry_context': '',
        'pain_hypotheses': [],
        'conversation_hooks': [],
        'buying_signals': [],
        'sources': [],
        '_raw': text,
    }


def research_batch(leads: list) -> list:
    """
    Research a batch of leads.

    Each lead should be a dict with at least 'company_domain'.
    Optional keys: 'lead_name', 'lead_title', 'company_name'.

    Returns a list of research results in the same order.
    """
    results = []
    for i, lead in enumerate(leads):
        print(f'[{i+1}/{len(leads)}] Researching {lead.get("company_domain", "unknown")}...')
        try:
            result = research_lead(
                company_domain=lead.get('company_domain', ''),
                lead_name=lead.get('lead_name'),
                lead_title=lead.get('lead_title'),
                company_name=lead.get('company_name'),
            )
            result['_lead'] = lead
            results.append(result)
        except Exception as e:
            print(f'  Error: {e}')
            results.append({'error': str(e), '_lead': lead})
    return results


if __name__ == '__main__':
    # Quick test
    result = research_lead(
        company_domain='jellyfish.co',
        lead_name='Andrew Lau',
        lead_title='CEO',
        company_name='Jellyfish',
    )
    print(json.dumps(result, indent=2, default=str))
