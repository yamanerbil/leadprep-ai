"""
LeadPrep AI Web Interface

Flask web app for lead research, signal extraction, and opener generation.
"""

import csv
import io
import json
from flask import Flask, render_template, request, jsonify, Response
import company_utils
import os

app = Flask(__name__)


@app.route('/')
def index():
    """Main page with the LeadPrep AI interface."""
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
def analyze_company():
    """Analyze a company URL and return leader information."""
    try:
        data = request.get_json()
        url = data.get('url', '').strip()

        if not url:
            return jsonify({'error': 'Please provide a company URL'}), 400

        if not company_utils.validate_company_url(url):
            return jsonify({'error': 'Invalid company URL provided'}), 400

        company_info = company_utils.get_company_info(url)

        return jsonify({
            'success': True,
            'data': company_info
        })

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


@app.route('/search-interviews', methods=['POST'])
def search_interviews():
    """Search for interviews with selected leaders."""
    try:
        data = request.get_json()
        leaders = data.get('leaders', [])
        company_name = data.get('company_name', '')

        if not leaders:
            return jsonify({'error': 'Please select at least one leader'}), 400

        if not company_name:
            return jsonify({'error': 'Company name is required'}), 400

        try:
            from interview_search import search_interviews_for_leaders
            interview_results = search_interviews_for_leaders(leaders, company_name)

            return jsonify({
                'success': True,
                'data': {
                    'company_name': company_name,
                    'leaders': leaders,
                    'interviews': interview_results
                }
            })

        except ImportError:
            return jsonify({'error': 'Interview search module not available'}), 500

    except Exception as e:
        return jsonify({'error': f'An error occurred: {str(e)}'}), 500


@app.route('/research', methods=['POST'])
def research():
    """
    Deep research on a company + lead.

    Expects JSON:
    {
        "company_domain": "acme.com",
        "company_name": "Acme Corp",       // optional
        "lead_name": "Jane Smith",          // optional
        "lead_title": "VP of People"        // optional
    }
    """
    try:
        data = request.get_json()
        company_domain = data.get('company_domain', '').strip()

        if not company_domain:
            return jsonify({'error': 'company_domain is required'}), 400

        from signal_researcher import research_lead
        result = research_lead(
            company_domain=company_domain,
            lead_name=data.get('lead_name'),
            lead_title=data.get('lead_title'),
            company_name=data.get('company_name'),
        )

        # Strip internal fields from response
        clean = {k: v for k, v in result.items() if not k.startswith('_')}

        return jsonify({'success': True, 'data': clean})

    except Exception as e:
        return jsonify({'error': f'Research failed: {str(e)}'}), 500


@app.route('/generate-opener', methods=['POST'])
def generate_opener():
    """
    Generate personalized openers from research.

    Expects JSON:
    {
        "research": { ... },         // output from /research
        "lead_name": "Jane Smith",
        "lead_title": "VP of People",
        "company_name": "Acme Corp",
        "product_context": "..."     // optional override
    }
    """
    try:
        data = request.get_json()

        required = ['research', 'lead_name', 'company_name']
        for field in required:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400

        from opener_generator import generate_opener as gen
        opener = gen(
            research=data['research'],
            lead_name=data['lead_name'],
            lead_title=data.get('lead_title', ''),
            company_name=data['company_name'],
            product_context=data.get('product_context'),
        )

        return jsonify({'success': True, 'data': {'opener': opener}})

    except Exception as e:
        return jsonify({'error': f'Opener generation failed: {str(e)}'}), 500


@app.route('/batch-research', methods=['POST'])
def batch_research():
    """
    Batch research + opener generation from CSV upload.

    Accepts multipart form with a CSV file.
    Required CSV columns: company_domain
    Optional columns: company_name, lead_name, lead_title, email, phone

    Returns JSON with research + openers for each row.
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No CSV file uploaded'}), 400

        file = request.files['file']
        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'File must be a CSV'}), 400

        # Parse CSV
        stream = io.StringIO(file.stream.read().decode('utf-8'))
        reader = csv.DictReader(stream)
        leads = list(reader)

        if not leads:
            return jsonify({'error': 'CSV is empty'}), 400

        # Validate required column
        if 'company_domain' not in leads[0]:
            # Try common alternative column names
            alt_names = {'domain': 'company_domain', 'company': 'company_name',
                         'name': 'lead_name', 'title': 'lead_title',
                         'Company Domain': 'company_domain', 'Domain': 'company_domain',
                         'Company': 'company_name', 'Name': 'lead_name',
                         'Title': 'lead_title', 'Email': 'email', 'Phone': 'phone',
                         'First Name': 'first_name', 'Last Name': 'last_name',
                         'Person Linkedin Url': 'linkedin_url',
                         'Company Name for Emails': 'company_name'}
            remapped = []
            for lead in leads:
                new_lead = {}
                for k, v in lead.items():
                    mapped_key = alt_names.get(k, k)
                    new_lead[mapped_key] = v
                # Handle first_name + last_name -> lead_name
                if 'first_name' in new_lead and 'last_name' in new_lead:
                    new_lead['lead_name'] = f"{new_lead['first_name']} {new_lead['last_name']}".strip()
                remapped.append(new_lead)
            leads = remapped

            if 'company_domain' not in leads[0]:
                return jsonify({
                    'error': 'CSV must have a "company_domain" column (or "domain", "Domain")',
                    'found_columns': list(reader.fieldnames or [])
                }), 400

        # Cap batch size
        max_batch = 25
        if len(leads) > max_batch:
            leads = leads[:max_batch]

        from signal_researcher import research_batch
        from opener_generator import generate_batch_openers

        # Phase 1: Research
        research_results = research_batch(leads)

        # Phase 2: Generate openers
        product_ctx = request.form.get('product_context', None)
        opener_results = generate_batch_openers(research_results, product_context=product_ctx)

        return jsonify({
            'success': True,
            'data': {
                'count': len(opener_results),
                'results': opener_results
            }
        })

    except Exception as e:
        return jsonify({'error': f'Batch processing failed: {str(e)}'}), 500


@app.route('/batch-research/csv', methods=['POST'])
def batch_research_csv():
    """
    Same as /batch-research but returns a CSV file with openers appended.
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No CSV file uploaded'}), 400

        file = request.files['file']
        stream = io.StringIO(file.stream.read().decode('utf-8'))
        reader = csv.DictReader(stream)
        original_rows = list(reader)
        fieldnames = list(reader.fieldnames or [])

        if not original_rows:
            return jsonify({'error': 'CSV is empty'}), 400

        # Remap columns (same logic as batch_research)
        alt_names = {'domain': 'company_domain', 'company': 'company_name',
                     'name': 'lead_name', 'title': 'lead_title',
                     'Company Domain': 'company_domain', 'Domain': 'company_domain',
                     'Company': 'company_name', 'Name': 'lead_name',
                     'Title': 'lead_title',
                     'First Name': 'first_name', 'Last Name': 'last_name',
                     'Company Name for Emails': 'company_name'}

        leads = []
        for row in original_rows:
            lead = {}
            for k, v in row.items():
                lead[alt_names.get(k, k)] = v
            if 'first_name' in lead and 'last_name' in lead:
                lead['lead_name'] = f"{lead['first_name']} {lead['last_name']}".strip()
            leads.append(lead)

        max_batch = 25
        leads = leads[:max_batch]
        original_rows = original_rows[:max_batch]

        from signal_researcher import research_batch
        from opener_generator import generate_batch_openers

        research_results = research_batch(leads)
        opener_results = generate_batch_openers(research_results)

        # Build output CSV
        out_fields = fieldnames + ['research_summary', 'opener']
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=out_fields)
        writer.writeheader()

        for orig_row, opener_data in zip(original_rows, opener_results):
            row = dict(orig_row)
            row['research_summary'] = opener_data.get('research_summary', '')
            row['opener'] = opener_data.get('opener', '')
            writer.writerow(row)

        csv_content = output.getvalue()
        return Response(
            csv_content,
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=leadprep_results.csv'}
        )

    except Exception as e:
        return jsonify({'error': f'Batch CSV failed: {str(e)}'}), 500


@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'service': 'LeadPrep AI'})


if __name__ == '__main__':
    os.makedirs('templates', exist_ok=True)

    print("Starting LeadPrep AI Web Interface...")
    print("Open your browser and go to: http://localhost:8080")

    app.run(debug=True, host='0.0.0.0', port=8080)
