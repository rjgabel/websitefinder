# 🕵 WebsiteFinder

**WebsiteFinder** is a Python script that runs daily to discover websites matching specific sets of **keywords** and **search visibility criteria**—ideal for SEO monitoring, content discovery, brand mention tracking, and more.  
[GitHub Repository](https://github.com/rjgabel/websitefinder)

---

## ✨ Features

- Automates daily web searches based on a **configurable list of keywords**
- Filters results using **search visibility** thresholds (e.g., search engine ranking, domain authority)
- Outputs exploration results in structured formats for easy analysis and follow-up
- Lightweight and easily configurable for personal or team use

---

## 🚀 Getting Started

### Prerequisites

- Python 3.7 or above
- Recommended packages (install via pip):

```bash
pip install requests beautifulsoup4 schedule

(Adjust based on actual package dependencies used in the script.)
Installation

    Clone the repository:

git clone https://github.com/rjgabel/websitefinder.git
cd websitefinder

    (Optional) Set up a virtual environment:

python3 -m venv venv
source venv/bin/activate  # macOS/Linux
.\venv\Scripts\activate   # Windows

    Install required dependencies:

pip install -r requirements.txt

(If a requirements.txt isn't included, use manual installation as shown above.)
⚙ Configuration

    Keywords: Define the search terms you're targeting in a configuration file (e.g., keywords.txt or a JSON/CSV).

    Filters: Set visibility thresholds—such as minimum domain authority, maximum search ranking, or other metrics you track.

    Scheduling: The script is intended to run daily (e.g., via cron jobs or task scheduler) to keep searches up to date.

▶ Usage

Run the script manually:

python websitefinder.py

Or schedule it to run daily with cron:

0 8 * * * cd /path/to/websitefinder && /usr/bin/python3 websitefinder.py >> run.log 2>&1

📊 Output & Results

The script produces:

    A log of websites discovered per keyword, with accompanying metadata (e.g., ranking, authority)

    Output saved in CSV or JSON formats for analysis

    (Optional) email or webhook integrations for alerts or reporting

💡 Examples

Command:

python websitefinder.py --keywords keywords.txt --output results.json --min_domain_authority 30

Sample Output (JSON):

[
  {
    "keyword": "artificial intelligence",
    "url": "https://example.com/ai-article",
    "domain_authority": 45,
    "rank": 3
  }
]

🤝 Contributing

Contributions are welcome! You can help by:

    Improving search/filter logic or integrating new visibility metrics

    Adding support for new output formats or integrations

    Enhancing scheduling, logging, or error handling

Feel free to open an issue or pull request to collaborate.

