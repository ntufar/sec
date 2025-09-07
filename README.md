# SEC 10-K Report Downloader

A comprehensive Python package for downloading and converting SEC 10-K reports to PDF and HTML formats. This tool provides an easy-to-use interface for accessing SEC filings and converting them into readable PDF documents or clean HTML files.

## Features

- 📥 **Download 10-K Reports**: Automatically download SEC 10-K filings for any publicly traded company
- 📄 **PDF Conversion**: Convert downloaded reports to professionally formatted PDF documents
- 🌐 **HTML Extraction**: Extract clean, readable HTML from SEC 10-K documents
- 🔍 **Company Search**: Search and list available company tickers from the SEC database
- ⚙️ **Configurable**: Highly configurable with YAML configuration files
- 📊 **Batch Processing**: Download multiple companies' reports in a single operation
- 🚀 **CLI Interface**: Easy-to-use command-line interface
- 📝 **Comprehensive Logging**: Detailed logging for monitoring and debugging

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)
- **macOS users**: Homebrew (for WeasyPrint system libraries)

### Install from Source

1. Clone the repository:
```bash
git clone https://github.com/ntufar/sec-downloader.git
cd sec-downloader
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install the package:
```bash
pip install -e .
```

4. **macOS users - Install WeasyPrint system libraries:**
```bash
brew install cairo pango gdk-pixbuf libffi
```

5. **Set up environment variables (macOS only):**
```bash
source setup_env.sh
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Optional: Install wkhtmltopdf for Better PDF Conversion

For optimal PDF conversion quality, install wkhtmltopdf:

**macOS:**
```bash
brew install wkhtmltopdf
```

**Ubuntu/Debian:**
```bash
sudo apt-get install wkhtmltopdf
```

**Windows:**
Download from [wkhtmltopdf.org](https://wkhtmltopdf.org/downloads.html)

## Quick Start

### 1. Initialize Configuration

```bash
python -m sec_downloader config --init
```

### 2. Download 10-K Reports

Download reports for specific companies:
```bash
python -m sec_downloader download AAPL MSFT GOOGL
```

Download and convert to PDF:
```bash
python -m sec_downloader download --pdf AAPL MSFT
```

### 3. List Available Companies

Search for companies:
```bash
python -m sec_downloader list-tickers --search "Apple"
```

List all companies (limited to 50):
```bash
python -m sec_downloader list-tickers
```

### 4. Convert Existing Files

Convert text files to PDF:
```bash
python -m sec_downloader convert ./data/reports/AAPL/
```

## Usage

### Command Line Interface

The tool provides a comprehensive CLI with the following commands:

#### Download Command
```bash
python -m sec_downloader download [OPTIONS] TICKERS...

Options:
  -o, --output-dir PATH     Output directory for reports
  -p, --pdf                Convert downloaded reports to PDF
  --html                   Convert downloaded reports to HTML (much faster than PDF)
  --max-reports INTEGER    Maximum number of reports per company (default: 5)
  --config PATH            Path to configuration file
```

#### List Tickers Command
```bash
python -m sec_downloader list-tickers [OPTIONS]

Options:
  -s, --search TEXT        Search for specific ticker or company name
  --limit INTEGER          Maximum number of results (default: 50)
  --config PATH            Path to configuration file
```

#### Convert Command
```bash
python -m sec_downloader convert [OPTIONS] INPUT_PATH

Options:
  -o, --output-dir PATH    Output directory for PDFs
  --config PATH            Path to configuration file
```

#### Extract HTML Command
```bash
python -m sec_downloader extract-html [OPTIONS] INPUT_PATH

Options:
  -o, --output-dir PATH    Output directory for HTML files
  --config PATH            Path to configuration file
```

#### Config Command
```bash
python -m sec_downloader config [OPTIONS]

Options:
  --init                   Initialize default configuration
  --show                   Show current configuration
  --config PATH            Path to configuration file
```

### Configuration

The tool uses YAML configuration files. Initialize a default configuration:

```bash
python -m sec_downloader config --init
```

This creates a `config/config.yaml` file with the following structure:

```yaml
sec:
  base_url: 'https://www.sec.gov'
  api_url: 'https://data.sec.gov/api/xbrl/companyconcept'
  edgar_url: 'https://www.sec.gov/Archives/edgar'
  user_agent: 'ntufar@gmail.com'
  rate_limit_delay: 0.1

download:
  output_dir: 'data/reports'
  form_types: ['10-K', '10-Q']
  max_reports_per_company: 5
  years_back: 5

conversion:
  output_format: 'pdf'
  include_attachments: true
  quality: 'high'

logging:
  level: 'INFO'
  file: 'data/logs/sec_downloader.log'
  max_size: '10MB'
  backup_count: 5
```

### Python API

You can also use the package programmatically:

```python
from sec_downloader import SECDownloader, PDFConverter, Config

# Load configuration
config = Config('config/config.yaml')

# Initialize downloader
downloader = SECDownloader(config)

# Download reports
reports = downloader.download_10k_reports(['AAPL', 'MSFT'])

# Convert to PDF
converter = PDFConverter(config)
for ticker, files in reports.items():
    pdf_files = converter.batch_convert(files)
    print(f"Converted {len(pdf_files)} files for {ticker}")
```

## Project Structure

```
sec-downloader/
├── src/
│   └── sec_downloader/
│       ├── __init__.py
│       ├── cli.py              # Command-line interface
│       ├── config.py           # Configuration management
│       ├── converter.py        # PDF conversion
│       └── downloader.py       # SEC data downloading
├── docs/                       # Documentation
├── tests/                      # Unit tests
├── examples/                   # Example scripts
├── config/                     # Configuration files
├── data/                       # Data directories
│   ├── reports/               # Downloaded reports
│   └── logs/                  # Log files
├── requirements.txt           # Python dependencies
├── setup.py                   # Package setup
├── pyproject.toml            # Modern Python packaging
└── README.md                 # This file
```

## Examples

### Example 1: Download Apple's Recent 10-K Reports

```bash
python -m sec_downloader download --pdf --max-reports 3 AAPL
```

### Example 2: Search for Technology Companies

```bash
python -m sec_downloader list-tickers --search "technology" --limit 20
```

### Example 3: Batch Download Multiple Companies

```bash
python -m sec_downloader download --pdf AAPL MSFT GOOGL AMZN TSLA
```

### Example 4: Convert Existing Files

```bash
python -m sec_downloader convert ./data/reports/ --output-dir ./pdf_reports/
```

### Example 5: Extract HTML from SEC Documents

```bash
python -m sec_downloader extract-html ./data/reports/AAPL/AAPL_2024-11-01_10K.txt
```

## Development

### Setting Up Development Environment

1. Clone the repository and create a virtual environment:
```bash
git clone https://github.com/ntufar/sec-downloader.git
cd sec-downloader
python -m venv .venv
source .venv/bin/activate
```

2. Install development dependencies:
```bash
pip install -e ".[dev]"
```

3. Install pre-commit hooks (optional):
```bash
pre-commit install
```

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black src/ tests/
```

### Type Checking

```bash
mypy src/
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [SEC EDGAR Database](https://www.sec.gov/edgar) for providing public access to company filings
- [SEC API Documentation](https://www.sec.gov/edgar/sec-api-documentation) for API reference
- The Python community for excellent libraries like `requests`, `pandas`, and `plotly`

## Troubleshooting

### Common Issues

1. **Rate Limiting**: The SEC API has rate limits. If you encounter 429 errors, increase the `rate_limit_delay` in your configuration.

2. **PDF Conversion Issues**: If PDF conversion fails, ensure you have the required dependencies installed:
   ```bash
   pip install weasyprint reportlab
   ```

3. **Permission Errors**: Ensure the output directories are writable:
   ```bash
   chmod 755 data/reports data/logs
   ```

4. **Network Issues**: Check your internet connection and SEC website accessibility.

### Getting Help

- Check the [Issues](https://github.com/ntufar/sec-downloader/issues) page
- Review the logs in `data/logs/sec_downloader.log`
- Ensure you're using the latest version

## Changelog

### Version 1.0.0
- Initial release
- SEC 10-K report downloading
- PDF conversion capabilities
- Command-line interface
- Configuration management
- Comprehensive logging