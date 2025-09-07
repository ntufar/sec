# User Guide

This guide provides step-by-step instructions for using the SEC 10-K Report Downloader.

## Table of Contents

1. [Installation](#installation)
2. [First Steps](#first-steps)
3. [Basic Usage](#basic-usage)
4. [Advanced Usage](#advanced-usage)
5. [Configuration](#configuration)
6. [Troubleshooting](#troubleshooting)
7. [Best Practices](#best-practices)

## Installation

### Prerequisites

Before installing the SEC Downloader, ensure you have:

- Python 3.8 or higher
- pip (Python package installer)
- Internet connection
- Sufficient disk space (reports can be large)
- **macOS users**: Homebrew (for WeasyPrint system libraries)

### Step 1: Download the Package

```bash
git clone https://github.com/ntufar/sec-downloader.git
cd sec-downloader
```

### Step 2: Create Virtual Environment

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Install the Package

```bash
pip install -e .
```

### Step 5: macOS Users - Install WeasyPrint System Libraries

For PDF conversion functionality, WeasyPrint requires system libraries:

```bash
brew install cairo pango gdk-pixbuf libffi
```

### Step 6: Set Up Environment Variables (macOS Only)

WeasyPrint requires a specific environment variable on macOS:

```bash
source setup_env.sh
```

This sets the `DYLD_FALLBACK_LIBRARY_PATH` environment variable needed for WeasyPrint to find the system libraries.

## First Steps

### 1. Initialize Configuration

Create a default configuration file:

```bash
python -m sec_downloader config --init
```

This creates `config/config.yaml` with default settings.

### 2. Test Installation

Verify the installation works:

```bash
python -m sec_downloader list-tickers --limit 5
```

You should see a list of 5 companies with their ticker symbols and names.

### 3. Download Your First Report

Download Apple's most recent 10-K report:

```bash
python -m sec_downloader download AAPL
```

Check the `data/reports/AAPL/` directory for the downloaded file.

## Basic Usage

### Downloading Reports

#### Download Single Company

```bash
python -m sec_downloader download AAPL
```

#### Download Multiple Companies

```bash
python -m sec_downloader download AAPL MSFT GOOGL
```

#### Download and Convert to PDF

```bash
python -m sec_downloader download --convert AAPL MSFT
```

#### Limit Number of Reports

```bash
python -m sec_downloader download --max-reports 3 AAPL
```

### Searching for Companies

#### Search by Company Name

```bash
python -m sec_downloader list-tickers --search "Apple"
```

#### Search by Ticker Symbol

```bash
python -m sec_downloader list-tickers --search "AAPL"
```

#### List All Companies (Limited)

```bash
python -m sec_downloader list-tickers --limit 20
```

### Converting Files

#### Convert Single File

```bash
python -m sec_downloader convert data/reports/AAPL/AAPL_2023-12-31_10K.txt
```

#### Convert Directory

```bash
python -m sec_downloader convert data/reports/AAPL/
```

#### Convert with Custom Output Directory

```bash
python -m sec_downloader convert data/reports/AAPL/ --output-dir pdf_reports/
```

## Advanced Usage

### Custom Configuration

#### Create Custom Config

1. Copy the default configuration:
```bash
cp config/config.yaml config/my_config.yaml
```

2. Edit the configuration file:
```yaml
sec:
  user_agent: 'your-email@example.com'  # Use your email
  rate_limit_delay: 0.2  # Slower requests

download:
  output_dir: 'my_reports'
  max_reports_per_company: 10
  years_back: 10

conversion:
  quality: 'high'
```

3. Use the custom configuration:
```bash
python -m sec_downloader download --config config/my_config.yaml AAPL
```

### Batch Processing

#### Download Large Number of Companies

Create a text file with ticker symbols:

```bash
echo "AAPL
MSFT
GOOGL
AMZN
TSLA
META
NVDA
NFLX
ADBE
CRM" > companies.txt
```

Download all companies:

```bash
python -m sec_downloader download --convert $(cat companies.txt)
```

### Automated Scripts

#### Python Script Example

Create `download_tech_companies.py`:

```python
#!/usr/bin/env python3

from sec_downloader import SECDownloader, PDFConverter, Config

def main():
    # Load configuration
    config = Config('config/config.yaml')
    
    # Tech companies
    tech_companies = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA']
    
    # Initialize downloader and converter
    downloader = SECDownloader(config)
    converter = PDFConverter(config)
    
    # Download reports
    print("Downloading tech company reports...")
    reports = downloader.download_10k_reports(tech_companies)
    
    # Convert to PDF
    print("Converting to PDF...")
    for ticker, files in reports.items():
        if files:
            pdf_files = converter.batch_convert(files)
            print(f"Converted {len(pdf_files)} reports for {ticker}")

if __name__ == "__main__":
    main()
```

Run the script:

```bash
python download_tech_companies.py
```

## Configuration

### Configuration File Location

The default configuration file is located at `config/config.yaml`. You can specify a different location:

```bash
python -m sec_downloader download --config /path/to/config.yaml AAPL
```

### Key Configuration Options

#### SEC API Settings

```yaml
sec:
  user_agent: 'your-email@example.com'  # Required: Your email address
  rate_limit_delay: 0.1  # Delay between requests (seconds)
```

#### Download Settings

```yaml
download:
  output_dir: 'data/reports'  # Where to save reports
  max_reports_per_company: 5  # Maximum reports per company
  years_back: 5  # How many years of historical data
```

#### Conversion Settings

```yaml
conversion:
  output_format: 'pdf'  # Output format
  quality: 'high'  # Conversion quality
  include_attachments: true  # Include attachments
```

#### Logging Settings

```yaml
logging:
  level: 'INFO'  # Logging level (DEBUG, INFO, WARNING, ERROR)
  file: 'data/logs/sec_downloader.log'  # Log file location
```

### Environment Variables

You can override configuration using environment variables:

```bash
export SEC_USER_AGENT="your-email@example.com"
export SEC_OUTPUT_DIR="/path/to/reports"
python -m sec_downloader download AAPL
```

## Troubleshooting

### Common Issues

#### 1. Rate Limiting Errors

**Problem:** Getting 429 (Too Many Requests) errors

**Solution:** Increase the rate limit delay in configuration:

```yaml
sec:
  rate_limit_delay: 0.5  # Increase from 0.1 to 0.5
```

#### 2. Permission Errors

**Problem:** Cannot write to output directory

**Solution:** Check directory permissions:

```bash
chmod 755 data/reports
mkdir -p data/logs
chmod 755 data/logs
```

#### 3. PDF Conversion Fails

**Problem:** PDF conversion not working

**Solution:** Install required dependencies:

```bash
pip install weasyprint reportlab beautifulsoup4
```

**macOS-specific WeasyPrint issues:**

If you get `cannot load library 'libgobject-2.0-0'` errors:

1. Install system libraries:
```bash
brew install cairo pango gdk-pixbuf libffi
```

2. Set environment variable:
```bash
export DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib:$DYLD_FALLBACK_LIBRARY_PATH
```

3. Or use the provided setup script:
```bash
source setup_env.sh
```

**For better quality, install wkhtmltopdf:**

```bash
# macOS
brew install wkhtmltopdf

# Ubuntu/Debian
sudo apt-get install wkhtmltopdf
```

**PDF Conversion Strategy:**
- **WeasyPrint**: Used for smaller files (<10MB) with excellent quality
- **wkhtmltopdf**: Used for large files if available (discontinued upstream)
- **ReportLab**: Robust fallback that handles any file size with chunking
- **Memory optimization**: Large files are processed in chunks to prevent memory issues

#### 4. Network Issues

**Problem:** Cannot connect to SEC servers

**Solution:** Check internet connection and try again. The SEC servers might be temporarily unavailable.

#### 5. Invalid Ticker Symbol

**Problem:** Ticker symbol not found

**Solution:** Verify the ticker symbol:

```bash
python -m sec_downloader list-tickers --search "company_name"
```

### Debug Mode

Enable debug logging for detailed information:

1. Edit `config/config.yaml`:
```yaml
logging:
  level: 'DEBUG'
```

2. Run your command:
```bash
python -m sec_downloader download AAPL
```

3. Check the log file:
```bash
tail -f data/logs/sec_downloader.log
```

### Log Files

Log files are stored in `data/logs/sec_downloader.log`. Check this file for detailed error information:

```bash
# View recent logs
tail -n 50 data/logs/sec_downloader.log

# Search for errors
grep ERROR data/logs/sec_downloader.log

# Follow logs in real-time
tail -f data/logs/sec_downloader.log
```

## Best Practices

### 1. Respect Rate Limits

- Use appropriate delays between requests
- Don't overwhelm the SEC servers
- Consider running downloads during off-peak hours

### 2. Organize Your Data

- Use meaningful directory structures
- Keep track of downloaded reports
- Regularly clean up old files

### 3. Monitor Disk Space

- SEC reports can be large (several MB each)
- Plan for sufficient storage space
- Consider archiving old reports

### 4. Use Version Control

- Track your configuration files
- Document your download scripts
- Keep track of what you've downloaded

### 5. Error Handling

- Always check for errors in your scripts
- Implement retry logic for network issues
- Log important operations

### 6. Security

- Use a valid email address as User-Agent
- Don't share your configuration files
- Be mindful of data retention policies

### 7. Performance

- Use SSD storage for better I/O performance
- Consider parallel processing for large batches
- Monitor memory usage during PDF conversion

## Examples

### Example 1: Download S&P 500 Companies

```bash
# Create list of S&P 500 companies
echo "AAPL MSFT GOOGL AMZN TSLA META NVDA NFLX ADBE CRM" > sp500.txt

# Download all reports
python -m sec_downloader download --convert $(cat sp500.txt)
```

### Example 2: Download Specific Year

```bash
# Download reports from 2023
python -m sec_downloader download --max-reports 1 AAPL
```

### Example 3: Convert Existing Reports

```bash
# Convert all existing reports to PDF
python -m sec_downloader convert data/reports/ --output-dir pdf_reports/
```

### Example 4: Search and Download

```bash
# Search for technology companies
python -m sec_downloader list-tickers --search "technology" --limit 10

# Download the first 5 results
python -m sec_downloader download --convert AAPL MSFT GOOGL AMZN TSLA
```

## Getting Help

If you encounter issues not covered in this guide:

1. Check the [API Reference](API.md) for detailed technical information
2. Review the log files for error details
3. Search existing issues on GitHub
4. Create a new issue with detailed information about your problem

## Contributing

We welcome contributions! Please see the main README for information on how to contribute to this project.
