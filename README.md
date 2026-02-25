# LeadPrep AI 🚀

**Intelligent Sales Preparation Platform**

LeadPrep AI helps sales executives prepare deeply for high-value prospects by automatically extracting and analyzing company leadership information, finding public interviews/podcasts, and generating strategic insights.

## 🎯 **Project Vision**

Transform how sales teams prepare for high-value prospects by:

- **Automatically identifying** key company leaders
- **Finding public appearances** (interviews, podcasts, speeches)
- **Transcribing and analyzing** content using AI
- **Generating strategic insights** for sales conversations

## ✨ **Current Features (MVP)**

### ✅ **Company Leadership Extraction**

- **Web Scraping**: Automatically finds and extracts leadership from company websites
- **Smart Fallback**: Uses curated data when scraping isn't available
- **Multiple Sources**: Supports various website structures and patterns

### ✅ **Modern Web Interface**

- **Beautiful UI**: Clean, responsive design with real-time feedback
- **Flexible Input**: Accepts domains with or without `https://`
- **Live Analysis**: Real-time company analysis with progress indicators

### ✅ **Robust Architecture**

- **Modular Design**: Separate modules for different functionalities
- **Error Handling**: Graceful fallbacks and comprehensive error management
- **Extensible**: Easy to add new data sources and features

## 🚀 **Quick Start**

### **Prerequisites**

- Python 3.8+
- pip (Python package manager)

### **Installation**

1. **Clone the repository**

   ```bash
   git clone https://github.com/yourusername/leadprep-ai.git
   cd leadprep-ai
   ```

2. **Create virtual environment**

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**

   ```bash
   python app.py
   ```

5. **Open your browser**
   Navigate to: http://localhost:8080

## 🧪 **Testing the Application**

### **Try These Examples:**

- `apple.com` - Test with Apple's leadership
- `microsoft.com` - Microsoft executives
- `google.com` - Google leadership
- `amazon.com` - Amazon management
- Any other company domain

### **What You'll See:**

- **Company Domain**: Extracted from your input
- **Key Leaders**: Names and titles (real or fallback data)
- **Data Source**: Indicates if data came from web scraping or fallback

## 🏗️ **Project Structure**

```
leadprep-ai/
├── app.py                 # Main Flask web application
├── company_utils.py       # Company domain extraction & leadership data
├── web_scraper.py         # Web scraping for company leadership
├── youtube_utils.py       # YouTube search functionality (planned)
├── podcast_utils.py       # Podcast search functionality (planned)
├── summarization.py       # AI summarization (planned)
├── cache_utils.py         # Caching utilities (planned)
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html         # Web interface template
├── data/                  # Data storage directory
└── README.md             # This file
```

## 🔧 **Development Workflow**

### **Git/GitHub Best Practices**

1. **Create Feature Branches**

   ```bash
   git checkout -b feature/web-scraping
   git checkout -b feature/youtube-integration
   ```

2. **Make Regular Commits**

   ```bash
   git add .
   git commit -m "feat: add web scraping for company leadership"
   ```

3. **Push and Create Pull Requests**
   ```bash
   git push origin feature/web-scraping
   # Then create PR on GitHub
   ```

### **Commit Message Convention**

- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `style:` Code formatting
- `refactor:` Code refactoring
- `test:` Adding tests
- `chore:` Maintenance tasks

## 📋 **Roadmap**

### **Phase 1: Core Leadership (✅ Complete)**

- [x] Company domain extraction
- [x] Web scraping for leadership
- [x] Fallback data system
- [x] Web interface

### **Phase 2: Content Discovery (🔄 In Progress)**

- [ ] YouTube search for leader appearances
- [ ] Podcast search integration
- [ ] Content filtering and relevance scoring

### **Phase 3: AI Analysis (📅 Planned)**

- [ ] Audio transcription
- [ ] Claude content summarization
- [ ] Strategic insight generation
- [ ] Sales conversation preparation

### **Phase 4: Advanced Features (📅 Future)**

- [ ] LinkedIn API integration
- [ ] SEC filings analysis
- [ ] Real-time content monitoring
- [ ] Advanced analytics dashboard

## 🤝 **Contributing**

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes** and test thoroughly
4. **Commit your changes**: `git commit -m 'feat: add amazing feature'`
5. **Push to your branch**: `git push origin feature/amazing-feature`
6. **Create a Pull Request**

### **Development Guidelines**

- Follow PEP 8 style guidelines
- Add docstrings to all functions
- Include error handling
- Write tests for new features
- Update documentation

## 🔒 **Security & Privacy**

- **No API Keys in Code**: Use environment variables for sensitive data
- **Rate Limiting**: Respect website rate limits when scraping
- **Data Privacy**: Only collect publicly available information
- **Secure Storage**: Implement proper data encryption (future)

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 **Acknowledgments**

- **BeautifulSoup4** for web scraping
- **Flask** for the web framework
- **Anthropic Claude** for AI capabilities
- **YouTube Data API** for content discovery (planned)

## 📞 **Support**

- **Issues**: [GitHub Issues](https://github.com/yourusername/leadprep-ai/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/leadprep-ai/discussions)
- **Email**: your-email@example.com

---

**Built with ❤️ for sales professionals everywhere**
