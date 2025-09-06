"""
SEC EDGAR Downloader for 10-K reports
"""

import requests
import time
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin
import json
from datetime import datetime, timedelta
import re

from .config import Config


class SECDownloader:
    """Downloads SEC 10-K reports from EDGAR database"""
    
    def __init__(self, config: Config):
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': config.get('sec.user_agent'),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        self.logger = logging.getLogger(__name__)
        
    def get_company_tickers(self) -> Dict[str, Dict]:
        """Get mapping of ticker symbols to CIK numbers"""
        url = f"{self.config.get('sec.base_url')}/files/company_tickers.json"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            data = response.json()
            
            # Convert to more usable format
            tickers = {}
            for item in data.values():
                if isinstance(item, dict) and 'ticker' in item and 'cik_str' in item:
                    tickers[item['ticker']] = {
                        'cik': str(item['cik_str']).zfill(10),
                        'title': item.get('title', 'Unknown Company')
                    }
            
            self.logger.info(f"Retrieved {len(tickers)} company tickers")
            return tickers
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to get company tickers: {e}")
            raise
    
    def get_company_filings(self, cik: str, form_type: str = "10-K", 
                          limit: int = 5) -> List[Dict]:
        """Get recent filings for a company"""
        try:
            # Use the correct SEC API endpoint for company submissions
            url = f"https://data.sec.gov/submissions/CIK{cik}.json"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1'
            }
            
            # Add delay to respect SEC rate limits
            time.sleep(0.1)
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract recent filings
            filings = []
            recent_filings = data.get('filings', {}).get('recent', {})
            
            if not recent_filings:
                self.logger.warning(f"No recent filings found for CIK {cik}")
                return []
            
            # Get the form types, filing dates, and accession numbers
            forms = recent_filings.get('form', [])
            filing_dates = recent_filings.get('filingDate', [])
            accession_numbers = recent_filings.get('accessionNumber', [])
            primary_documents = recent_filings.get('primaryDocument', [])
            file_numbers = recent_filings.get('fileNumber', [])
            
            # Filter for the requested form type and limit results
            count = 0
            for i, form in enumerate(forms):
                if count >= limit:
                    break
                    
                if form == form_type:
                    filing = {
                        'form': form,
                        'filingDate': filing_dates[i] if i < len(filing_dates) else '',
                        'reportDate': filing_dates[i] if i < len(filing_dates) else '',
                        'accessionNumber': accession_numbers[i] if i < len(accession_numbers) else '',
                        'primaryDocument': primary_documents[i] if i < len(primary_documents) else '',
                        'fileNumber': file_numbers[i] if i < len(file_numbers) else '',
                        'size': 0  # Size not available in this API response
                    }
                    filings.append(filing)
                    count += 1
            
            self.logger.info(f"Found {len(filings)} {form_type} filings for CIK {cik}")
            return filings
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to get filings for CIK {cik}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error getting filings for CIK {cik}: {e}")
            raise
    
    
    def get_filing_documents(self, cik: str, accession_number: str) -> List[Dict]:
        """Get all documents for a specific filing"""
        try:
            # Use the correct SEC API endpoint for filing documents
            url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number}/{accession_number}-index.html"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1'
            }
            
            # Add delay to respect SEC rate limits
            time.sleep(0.1)
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            # Parse the HTML to extract document information
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            documents = []
            
            # Find the table with document information
            table = soup.find('table', {'class': 'tableFile'})
            if table:
                rows = table.find_all('tr')[1:]  # Skip header row
                
                # First pass: collect all documents
                all_documents = []
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 4:
                        # Extract document information
                        doc_type = cells[1].get_text(strip=True)
                        doc_name = cells[2].get_text(strip=True)
                        doc_size = cells[3].get_text(strip=True)
                        
                        # Find the link to the document
                        link = cells[2].find('a')
                        if link:
                            doc_url = f"https://www.sec.gov{link.get('href')}"
                            
                            document = {
                                'filename': doc_name,
                                'url': doc_url,
                                'type': self._get_document_type(doc_name),
                                'size': doc_size,
                                'doc_type': doc_type
                            }
                            all_documents.append(document)
                
                # Prioritize 10-K documents over exhibits
                # Look for documents that contain "10-K" in the filename or type
                primary_docs = []
                exhibit_docs = []
                
                for doc in all_documents:
                    if ('10-k' in doc['filename'].lower() or 
                        '10-k' in doc['doc_type'].lower() or
                        doc['filename'].endswith('.htm') or 
                        doc['filename'].endswith('.html')):
                        if 'exhibit' in doc['filename'].lower() or 'ex-' in doc['filename'].lower():
                            exhibit_docs.append(doc)
                        else:
                            primary_docs.append(doc)
                    else:
                        exhibit_docs.append(doc)
                
                # Add primary documents first, then exhibits
                documents.extend(primary_docs)
                documents.extend(exhibit_docs)
            
            # If no documents found in table, create basic document entry
            if not documents:
                documents = [{
                    'filename': f"{accession_number}.txt",
                    'url': f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number}/{accession_number}.txt",
                    'type': '10-K',
                    'size': 'Unknown'
                }]
            
            self.logger.info(f"Found {len(documents)} documents for filing {accession_number}")
            return documents
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to get documents for filing {accession_number}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error getting documents for filing {accession_number}: {e}")
            raise
    
    
    def _get_document_type(self, filename: str) -> str:
        """Determine document type from filename"""
        if '10-k' in filename.lower():
            return '10-K'
        elif '10-q' in filename.lower():
            return '10-Q'
        elif '8-k' in filename.lower():
            return '8-K'
        else:
            return 'other'
    
    def download_document(self, url: str, output_path: Path) -> bool:
        """Download a document from URL to local path"""
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Set up headers for SEC requests
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
                'Upgrade-Insecure-Requests': '1'
            }
            
            # Add delay to respect SEC rate limits
            time.sleep(0.1)
            
            # Download the document
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            # Determine file extension based on content type or URL
            content_type = response.headers.get('content-type', '').lower()
            if 'html' in content_type or url.endswith('.htm') or url.endswith('.html'):
                file_extension = '.html'
            elif 'pdf' in content_type or url.endswith('.pdf'):
                file_extension = '.pdf'
            else:
                file_extension = '.txt'
            
            # Update output path with correct extension
            if not str(output_path).endswith(file_extension):
                output_path = output_path.with_suffix(file_extension)
            
            # Write the content to file
            with open(output_path, 'wb') as f:
                f.write(response.content)
            
            # If it's HTML, also create a text version for PDF conversion
            if file_extension == '.html':
                text_path = output_path.with_suffix('.txt')
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Remove script and style elements
                    for script in soup(["script", "style"]):
                        script.decompose()
                    
                    # Get text content
                    text_content = soup.get_text()
                    
                    # Clean up text
                    lines = (line.strip() for line in text_content.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    text_content = '\n'.join(chunk for chunk in chunks if chunk)
                    
                    with open(text_path, 'w', encoding='utf-8') as f:
                        f.write(text_content)
                        
                    self.logger.info(f"Created text version at {text_path}")
                    
                except Exception as e:
                    self.logger.warning(f"Failed to create text version: {e}")
            
            file_size = output_path.stat().st_size
            self.logger.info(f"Downloaded document to {output_path} ({file_size:,} bytes)")
            return True
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to download document from {url}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error downloading document {output_path}: {e}")
            return False
    
    
    
    
    def download_10k_reports(self, tickers: List[str], 
                           output_dir: str = None) -> Dict[str, List[Path]]:
        """Download 10-K reports for specified tickers"""
        if output_dir is None:
            output_dir = self.config.get('download.output_dir')
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Get company tickers mapping
        company_data = self.get_company_tickers()
        
        downloaded_reports = {}
        
        for ticker in tickers:
            if ticker not in company_data:
                self.logger.warning(f"Ticker {ticker} not found in SEC database")
                continue
            
            cik = company_data[ticker]['cik']
            company_name = company_data[ticker]['title']
            
            self.logger.info(f"Processing {ticker} ({company_name}) - CIK: {cik}")
            
            # Get recent 10-K filings
            filings = self.get_company_filings(cik, "10-K", 
                                             self.config.get('download.max_reports_per_company'))
            
            ticker_reports = []
            
            for filing in filings:
                # Get all documents for this filing
                documents = self.get_filing_documents(cik, filing['accessionNumber'])
                
                # Download the main 10-K document
                main_doc = next((doc for doc in documents if doc['type'] == '10-K'), None)
                
                if main_doc:
                    # Create filename: TICKER_YYYY-MM-DD_10K.txt
                    filing_date = filing['filingDate']
                    filename = f"{ticker}_{filing_date}_10K.txt"
                    file_path = output_path / ticker / filename
                    
                    if self.download_document(main_doc['url'], file_path):
                        ticker_reports.append(file_path)
                
                # Rate limiting
                time.sleep(self.config.get('sec.rate_limit_delay'))
            
            downloaded_reports[ticker] = ticker_reports
            self.logger.info(f"Downloaded {len(ticker_reports)} reports for {ticker}")
        
        return downloaded_reports
