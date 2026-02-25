"""
Opener Generator for LeadPrep AI.

Takes research signals and generates cold outreach openers.
Intentionally unconstrained — Claude picks the best angle.
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


def generate_opener(research: Dict,
                    lead_name: str,
                    lead_title: str,
                    company_name: str,
                    product_context: Optional[str] = None) -> str:
    """
    Generate personalized cold outreach openers from research signals.

    Minimal prompt engineering. Let Claude read the research and figure
    out the most compelling angle on its own.
    """
    if not API_KEY:
        return 'Error: ANTHROPIC_API_KEY not configured'

    # Strip internal fields from research before sending
    clean_research = {k: v for k, v in research.items() if not k.startswith('_')}

    # Default product context if none provided
    if not product_context:
        product_context = (
            'We sell a performance management / people analytics platform. '
            'We help companies run better performance reviews, '
            'gather high-quality feedback, and make talent decisions with real data. '
            'Relevant case studies: GitHub (tech) found that AI-generated reviews '
            'were low-quality slop with no actionable feedback. '
            'Deloitte (professional services) had similar issues with review quality at scale.'
        )

    prompt = f"""Here is deep research on {lead_name} ({lead_title}) at {company_name}:

{json.dumps(clean_research, indent=2, default=str)}

Our product: {product_context}

Write cold outreach for a BDR. Give me 3 openers — each a different angle.

Rules:
- Use a SPECIFIC fact from the research. Don't be generic.
- 2-3 sentences max per opener. These are the first lines of an email or cold call script.
- Don't be sycophantic ("I was so impressed by..."). Be direct and peer-to-peer.
- Connect the signal to a pain point our product solves. Don't force it — if the connection is weak, say so.
- For each opener, note which signal you used and rate the strength of the angle (strong / medium / weak).

Format:
**Opener 1** [Signal: ... | Strength: ...]
<the opener text>

**Opener 2** [Signal: ... | Strength: ...]
<the opener text>

**Opener 3** [Signal: ... | Strength: ...]
<the opener text>"""

    headers = {
        'x-api-key': API_KEY,
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json',
    }

    body = {
        'model': MODEL,
        'max_tokens': 2000,
        'messages': [{'role': 'user', 'content': prompt}],
    }

    try:
        resp = requests.post(API_URL, headers=headers, json=body, timeout=60)
        resp.raise_for_status()
        result = resp.json()
        return result['content'][0]['text']
    except Exception as e:
        return f'Error generating opener: {e}'


def generate_batch_openers(research_results: list,
                           product_context: Optional[str] = None) -> list:
    """
    Generate openers for a batch of researched leads.

    Each item in research_results should have '_lead' with lead info
    plus the research signals.
    """
    openers = []
    for i, research in enumerate(research_results):
        lead = research.get('_lead', {})
        name = lead.get('lead_name', 'Unknown')
        title = lead.get('lead_title', '')
        company = lead.get('company_name', lead.get('company_domain', ''))

        print(f'[{i+1}/{len(research_results)}] Generating opener for {name} at {company}...')

        if 'error' in research and not research.get('company_signals'):
            openers.append({
                'lead': lead,
                'opener': f'Research failed: {research["error"]}',
            })
            continue

        opener = generate_opener(
            research=research,
            lead_name=name,
            lead_title=title,
            company_name=company,
            product_context=product_context,
        )
        openers.append({
            'lead': lead,
            'opener': opener,
            'research_summary': research.get('company_overview', ''),
        })
    return openers


if __name__ == '__main__':
    # Test with mock research
    mock_research = {
        'company_overview': 'Jellyfish is an engineering management platform that helps leaders understand and improve engineering productivity.',
        'company_signals': [
            {'signal': 'Raised $71M Series C in 2023', 'source': 'TechCrunch', 'relevance': 'Growing fast, scaling teams'},
            {'signal': 'Hiring 15 people ops roles', 'source': 'LinkedIn Jobs', 'relevance': 'Building out people function'},
        ],
        'person_signals': [
            {'signal': 'Andrew Lau spoke at SaaStr about engineering metrics', 'source': 'YouTube'},
        ],
        'pain_hypotheses': [
            'Rapidly scaling team means performance reviews are getting harder to do well',
            'As an engineering analytics company, they know the value of data — but may not have it for their own people processes',
        ],
        'conversation_hooks': [
            'His SaaStr talk about engineering metrics — bridge to people metrics',
        ],
    }

    result = generate_opener(
        research=mock_research,
        lead_name='Andrew Lau',
        lead_title='CEO',
        company_name='Jellyfish',
    )
    print(result)
