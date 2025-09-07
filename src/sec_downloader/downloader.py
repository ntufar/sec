"""
SEC EDGAR Downloader for 10-K reports
"""

import requests
import time
import logging
import random
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
            'User-Agent': 'SEC Downloader Tool (ntufar@gmail.com)',
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
                'User-Agent': 'SEC Downloader Tool (ntufar@gmail.com)',
                'Accept': 'application/json, text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive'
            }
            
            # Add random delay to respect SEC rate limits and avoid detection
            delay = random.uniform(0.5, 1.5)  # Random delay between 0.5-1.5 seconds
            time.sleep(delay)
            
            # Retry logic with exponential backoff
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.session.get(url, headers=headers, timeout=30)
                    response.raise_for_status()
                    break
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 403 and attempt < max_retries - 1:
                        wait_time = (2 ** attempt) * 2  # 2, 4, 8 seconds
                        self.logger.warning(f"403 error on attempt {attempt + 1}, retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise
            
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
    
    
    def get_complete_submission_text(self, cik: str, accession_number: str) -> Dict:
        """Get the complete submission text file which contains the full 10-K content"""
        try:
            # The complete submission text file URL format - remove dashes from accession number in directory path
            accession_no_dashes = accession_number.replace('-', '')
            url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_no_dashes}/{accession_number}.txt"
            
            headers = {
                'User-Agent': 'SEC Downloader Tool (ntufar@gmail.com)',
                'Accept': 'text/plain, */*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive'
            }
            
            # Add random delay to respect SEC rate limits
            delay = random.uniform(0.5, 1.5)
            time.sleep(delay)
            
            # Retry logic with exponential backoff
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.session.get(url, headers=headers, timeout=30)
                    response.raise_for_status()
                    break
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 403 and attempt < max_retries - 1:
                        wait_time = (2 ** attempt) * 2
                        self.logger.warning(f"403 error on attempt {attempt + 1}, retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise
            
            # Return the complete submission text
            return {
                'filename': f"{accession_number}.txt",
                'url': url,
                'type': 'Complete Submission Text',
                'content': response.text,
                'size': len(response.text)
            }
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to get complete submission text for {accession_number}: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error getting complete submission text for {accession_number}: {e}")
            raise

    def get_filing_documents(self, cik: str, accession_number: str) -> List[Dict]:
        """Get all documents for a specific filing"""
        try:
            # Use the correct SEC API endpoint for filing documents
            url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number}/{accession_number}-index.html"
            headers = {
                'User-Agent': 'SEC Downloader Tool (contact@example.com)',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive'
            }
            
            # Add random delay to respect SEC rate limits and avoid detection
            delay = random.uniform(0.5, 1.5)  # Random delay between 0.5-1.5 seconds
            time.sleep(delay)
            
            # Retry logic with exponential backoff
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.session.get(url, headers=headers, timeout=30)
                    response.raise_for_status()
                    break
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 403 and attempt < max_retries - 1:
                        wait_time = (2 ** attempt) * 2  # 2, 4, 8 seconds
                        self.logger.warning(f"403 error on attempt {attempt + 1}, retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise
            
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
                
                # Prioritize main 10-K document over exhibits
                main_10k_docs = []
                other_primary_docs = []
                exhibit_docs = []
                
                for doc in all_documents:
                    filename_lower = doc['filename'].lower()
                    doc_type_lower = doc['doc_type'].lower()
                    
                    # Check if it's an exhibit (EX-*)
                    if ('exhibit' in filename_lower or 
                        'ex-' in filename_lower or
                        doc_type_lower.startswith('ex-')):
                        exhibit_docs.append(doc)
                    # Check if it's the complete submission text file (main 10-K)
                    elif ('complete submission text file' in doc_type_lower or
                          (filename_lower.endswith('.txt') and not any(x in filename_lower for x in ['exhibit', 'ex-', 'cert', 'cover']))):
                        main_10k_docs.append(doc)
                    # Check if it's the main 10-K HTML document
                    elif (('10-k' in filename_lower and not any(x in filename_lower for x in ['exhibit', 'ex-', 'cert', 'cover', 'xbrl'])) or
                          (doc_type_lower == '10-k' and not any(x in filename_lower for x in ['exhibit', 'ex-', 'cert', 'cover', 'xbrl'])) or
                          (filename_lower.endswith('.htm') and not any(x in filename_lower for x in ['exhibit', 'ex-', 'cert', 'cover', 'xbrl']))):
                        main_10k_docs.append(doc)
                    # Other primary documents
                    elif (filename_lower.endswith('.htm') or 
                          filename_lower.endswith('.html') or
                          filename_lower.endswith('.txt')):
                        other_primary_docs.append(doc)
                    else:
                        exhibit_docs.append(doc)
                
                # Add main 10-K documents first, then other primary docs, then exhibits
                documents.extend(main_10k_docs)
                documents.extend(other_primary_docs)
                documents.extend(exhibit_docs)
                
                # Log document selection for debugging
                self.logger.info(f"Document selection for {accession_number}:")
                self.logger.info(f"  Main 10-K docs: {len(main_10k_docs)}")
                self.logger.info(f"  Other primary docs: {len(other_primary_docs)}")
                self.logger.info(f"  Exhibit docs: {len(exhibit_docs)}")
                if main_10k_docs:
                    self.logger.info(f"  Selected main doc: {main_10k_docs[0]['filename']}")
                elif other_primary_docs:
                    self.logger.info(f"  Selected primary doc: {other_primary_docs[0]['filename']}")
            
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
                'User-Agent': 'SEC Downloader Tool (contact@example.com)',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive'
            }
            
            # Add random delay to respect SEC rate limits and avoid detection
            delay = random.uniform(0.5, 1.5)  # Random delay between 0.5-1.5 seconds
            time.sleep(delay)
            
            # Retry logic with exponential backoff
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.session.get(url, headers=headers, timeout=30)
                    response.raise_for_status()
                    break
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 403 and attempt < max_retries - 1:
                        wait_time = (2 ** attempt) * 2  # 2, 4, 8 seconds
                        self.logger.warning(f"403 error on attempt {attempt + 1}, retrying in {wait_time} seconds...")
                        time.sleep(wait_time)
                        continue
                    else:
                        raise
            
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
                # Get the complete submission text file which contains the full 10-K content
                try:
                    complete_text = self.get_complete_submission_text(cik, filing['accessionNumber'])
                    
                    # Create filename: TICKER_YYYY-MM-DD_10K.txt
                    filing_date = filing['filingDate']
                    filename = f"{ticker}_{filing_date}_10K.txt"
                    file_path = output_path / ticker / filename
                    
                    # Ensure directory exists
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Write the complete submission text to file
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(complete_text['content'])
                    
                    self.logger.info(f"Downloaded complete 10-K report to {file_path} ({complete_text['size']:,} characters)")
                    ticker_reports.append(file_path)
                    
                except Exception as e:
                    self.logger.error(f"Failed to download complete submission text for {ticker} {filing['accessionNumber']}: {e}")
                    # Fallback to original method
                    try:
                        documents = self.get_filing_documents(cik, filing['accessionNumber'])
                        main_doc = documents[0] if documents else None
                        
                        if main_doc:
                            filing_date = filing['filingDate']
                            filename = f"{ticker}_{filing_date}_10K.txt"
                            file_path = output_path / ticker / filename
                            
                            if self.download_document(main_doc['url'], file_path):
                                ticker_reports.append(file_path)
                    except Exception as fallback_error:
                        self.logger.error(f"Fallback download also failed for {ticker}: {fallback_error}")
                
                # Rate limiting
                time.sleep(self.config.get('sec.rate_limit_delay'))
            
            downloaded_reports[ticker] = ticker_reports
            self.logger.info(f"Downloaded {len(ticker_reports)} reports for {ticker}")
        
        return downloaded_reports
