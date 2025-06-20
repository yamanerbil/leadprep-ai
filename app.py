"""
LeadPrep AI Web Interface

A simple Flask web app to test the LeadPrep AI functionality.
"""

from flask import Flask, render_template, request, jsonify
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
        
        # Validate the URL
        if not company_utils.validate_company_url(url):
            return jsonify({'error': 'Invalid company URL provided'}), 400
        
        # Get company information
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
        
        # Import interview search functionality
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

@app.route('/health')
def health():
    """Health check endpoint."""
    return jsonify({'status': 'healthy', 'service': 'LeadPrep AI'})

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    print("🚀 Starting LeadPrep AI Web Interface...")
    print("📱 Open your browser and go to: http://localhost:8080")
    print("🔍 Enter a company URL to test the functionality!")
    
    app.run(debug=True, host='0.0.0.0', port=8080) 