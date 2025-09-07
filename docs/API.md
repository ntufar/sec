# API Reference

This document provides detailed information about the SEC Downloader API.

## Core Classes

### Config

Configuration management class for the SEC Downloader.

```python
from sec_downloader import Config

config = Config('config/config.yaml')
```

#### Methods

##### `__init__(config_file: str = "config/config.yaml")`
Initialize configuration from YAML file or create default configuration.

**Parameters:**
- `config_file` (str): Path to configuration file

##### `get(key: str, default: Any = None) -> Any`
Get configuration value by dot-separated key.

**Parameters:**
- `key` (str): Dot-separated configuration key (e.g., 'sec.user_agent')
- `default` (Any): Default value if key not found

**Returns:**
- Configuration value or default

**Example:**
```python
user_agent = config.get('sec.user_agent', 'default@example.com')
```

##### `save()`
Save current configuration to file.

### SECDownloader

Main class for downloading SEC filings.

```python
from sec_downloader import SECDownloader, Config

config = Config()
downloader = SECDownloader(config)
```

#### Methods

##### `get_company_tickers() -> Dict[str, Dict]`
Get mapping of ticker symbols to CIK numbers.

**Returns:**
- Dictionary mapping ticker symbols to company information

**Example:**
```python
tickers = downloader.get_company_tickers()
print(tickers['AAPL'])  # {'cik': '0000320193', 'title': 'Apple Inc.'}
```

##### `get_company_filings(cik: str, form_type: str = "10-K", limit: int = 5) -> List[Dict]`
Get recent filings for a company.

**Parameters:**
- `cik` (str): Company CIK number
- `form_type` (str): Type of filing (default: "10-K")
- `limit` (int): Maximum number of filings to retrieve

**Returns:**
- List of filing dictionaries

**Example:**
```python
filings = downloader.get_company_filings('0000320193', '10-K', 3)
```

##### `download_10k_reports(tickers: List[str], output_dir: str = None) -> Dict[str, List[Path]]`
Download 10-K reports for specified tickers.

**Parameters:**
- `tickers` (List[str]): List of ticker symbols
- `output_dir` (str, optional): Output directory for reports

**Returns:**
- Dictionary mapping ticker symbols to list of downloaded file paths

**Example:**
```python
reports = downloader.download_10k_reports(['AAPL', 'MSFT'])
```

### PDFConverter

Class for converting text documents to PDF format.

```python
from sec_downloader import PDFConverter, Config

config = Config()
converter = PDFConverter(config)
```

#### Methods

##### `convert_to_pdf(input_file: Path, output_file: Path = None) -> bool`
Convert a text file to PDF.

**Parameters:**
- `input_file` (Path): Path to input text file
- `output_file` (Path, optional): Path for output PDF file

**Returns:**
- True if conversion successful, False otherwise

**Example:**
```python
from pathlib import Path

success = converter.convert_to_pdf(Path('report.txt'), Path('report.pdf'))
```

##### `batch_convert(input_files: List[Path], output_dir: Path = None) -> List[Path]`
Convert multiple files to PDF.

**Parameters:**
- `input_files` (List[Path]): List of input file paths
- `output_dir` (Path, optional): Output directory for PDF files

**Returns:**
- List of successfully converted PDF file paths

**Example:**
```python
input_files = [Path('file1.txt'), Path('file2.txt')]
pdf_files = converter.batch_convert(input_files, Path('pdf_output/'))
```

## Configuration Schema

The configuration file uses YAML format with the following structure:

```yaml
sec:
  base_url: 'https://www.sec.gov'                    # SEC base URL
  api_url: 'https://data.sec.gov/api/xbrl/companyconcept'  # SEC API URL
  edgar_url: 'https://www.sec.gov/Archives/edgar'    # EDGAR archives URL
  user_agent: 'your-email@example.com'               # User agent for requests
  rate_limit_delay: 0.1                              # Delay between requests (seconds)

download:
  output_dir: 'data/reports'                         # Output directory for reports
  form_types: ['10-K', '10-Q']                      # Types of forms to download
  max_reports_per_company: 5                        # Max reports per company
  years_back: 5                                     # Years of historical data

conversion:
  output_format: 'pdf'                              # Output format
  include_attachments: true                         # Include attachments
  quality: 'high'                                   # Conversion quality

logging:
  level: 'INFO'                                     # Logging level
  file: 'data/logs/sec_downloader.log'             # Log file path
  max_size: '10MB'                                  # Max log file size
  backup_count: 5                                   # Number of backup files
```

## Error Handling

The package includes comprehensive error handling:

### Common Exceptions

- `requests.RequestException`: Network-related errors
- `FileNotFoundError`: Missing files or directories
- `PermissionError`: File permission issues
- `ValueError`: Invalid configuration values

### Example Error Handling

```python
from sec_downloader import SECDownloader, Config
import logging

config = Config()
downloader = SECDownloader(config)

try:
    reports = downloader.download_10k_reports(['AAPL'])
except requests.RequestException as e:
    logging.error(f"Network error: {e}")
except Exception as e:
    logging.error(f"Unexpected error: {e}")
```

## Logging

The package uses Python's built-in logging module. Configure logging through the configuration file or programmatically:

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sec_downloader.log'),
        logging.StreamHandler()
    ]
)
```

## Rate Limiting

The SEC API has rate limits. The package includes built-in rate limiting:

- Default delay: 0.1 seconds between requests
- Configurable through `sec.rate_limit_delay`
- Automatic retry on rate limit errors

## Data Formats

### Filing Data Structure

```python
{
    'form': '10-K',
    'filingDate': '2023-12-31',
    'reportDate': '2023-12-31',
    'accessionNumber': '0000320193-23-000077',
    'primaryDocument': 'aapl-20231231.htm',
    'size': 1234567
}
```

### Company Data Structure

```python
{
    'cik': '0000320193',
    'title': 'Apple Inc.'
}
```

## Performance Considerations

- Use appropriate rate limiting to avoid API throttling
- Consider disk space for large batch downloads
- Monitor memory usage for large PDF conversions
- Use SSD storage for better I/O performance

## Security Considerations

- Always use a valid email address as User-Agent
- Respect SEC's terms of service
- Implement proper error handling for production use
- Consider data retention policies for downloaded reports
