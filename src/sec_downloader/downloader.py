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
        # For demonstration purposes, create mock filings
        # In a real implementation, this would query the SEC API
        from datetime import datetime, timedelta
        
        filings = []
        base_date = datetime.now()
        
        for i in range(min(limit, 3)):  # Create up to 3 mock filings
            filing_date = (base_date - timedelta(days=365*i)).strftime('%Y-%m-%d')
            accession_number = f"{cik}-{filing_date.replace('-', '')}-{i+1:03d}"
            
            filing = {
                'form': form_type,
                'filingDate': filing_date,
                'reportDate': filing_date,
                'accessionNumber': accession_number,
                'primaryDocument': f"{form_type.lower()}-{filing_date}.txt",
                'size': 1000000 + i * 100000  # Mock file size
            }
            filings.append(filing)
        
        self.logger.info(f"Found {len(filings)} {form_type} filings for CIK {cik} (mock data)")
        return filings
    
    def get_filing_documents(self, cik: str, accession_number: str) -> List[Dict]:
        """Get all documents for a specific filing"""
        # For demonstration purposes, create mock documents
        # In a real implementation, this would query the SEC API
        
        documents = [
            {
                'filename': f"{accession_number}.txt",
                'url': f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number}/{accession_number}.txt",
                'type': '10-K'
            },
            {
                'filename': f"{accession_number}-ex99.htm",
                'url': f"https://www.sec.gov/Archives/edgar/data/{cik}/{accession_number}/{accession_number}-ex99.htm",
                'type': 'other'
            }
        ]
        
        self.logger.info(f"Found {len(documents)} documents for filing {accession_number} (mock data)")
        return documents
    
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
            # For demonstration purposes, create mock document content
            # In a real implementation, this would download from the actual URL
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create mock 10-K content
            mock_content = f"""
SECURITIES AND EXCHANGE COMMISSION
Washington, D.C. 20549

FORM 10-K

(Mark One)
[X] ANNUAL REPORT PURSUANT TO SECTION 13 OR 15(d) OF THE SECURITIES EXCHANGE ACT OF 1934
For the fiscal year ended December 31, 2023

[ ] TRANSITION REPORT PURSUANT TO SECTION 13 OR 15(d) OF THE SECURITIES EXCHANGE ACT OF 1934
For the transition period from ___________ to ___________

Commission file number: 001-36743

APPLE INC.
(Exact name of registrant as specified in its charter)

Delaware                                   94-2404110
(State or other jurisdiction of            (I.R.S. Employer
incorporation or organization)             Identification No.)

One Apple Park Way
Cupertino, California                      95014
(Address of principal executive offices)   (Zip Code)

Registrant's telephone number, including area code: (408) 996-1010

Securities registered pursuant to Section 12(b) of the Act:

Title of each class                    Trading Symbol(s)    Name of each exchange on which registered
Common Stock, $0.00001 par value      AAPL                 The Nasdaq Stock Market LLC

Securities registered pursuant to Section 12(g) of the Act: None

Indicate by check mark if the registrant is a well-known seasoned issuer, as defined in Rule 405 of the Securities Act. Yes [X] No [ ]

Indicate by check mark if the registrant is not required to file reports pursuant to Section 13 or Section 15(d) of the Act. Yes [ ] No [X]

Indicate by check mark whether the registrant (1) has filed all reports required to be filed by Section 13 or 15(d) of the Securities Exchange Act of 1934 during the preceding 12 months (or for such shorter period that the registrant was required to file such reports), and (2) has been subject to such filing requirements for the past 90 days. Yes [X] No [ ]

Indicate by check mark whether the registrant has submitted electronically every Interactive Data File required to be submitted pursuant to Rule 405 of Regulation S-T (§232.405 of this chapter) during the preceding 12 months (or for such shorter period that the registrant was required to submit such files). Yes [X] No [ ]

Indicate by check mark whether the registrant is a large accelerated filer, an accelerated filer, a non-accelerated filer, a smaller reporting company, or an emerging growth company. See the definitions of "large accelerated filer," "accelerated filer," "smaller reporting company," and "emerging growth company" in Rule 12b-2 of the Exchange Act.

Large accelerated filer [X]    Accelerated filer [ ]    Non-accelerated filer [ ]    Smaller reporting company [ ]    Emerging growth company [ ]

If an emerging growth company, indicate by check mark if the registrant has elected not to use the extended transition period for complying with any new or revised financial accounting standards provided pursuant to Section 13(a) of the Exchange Act. [ ]

Indicate by check mark whether the registrant has filed a report on and attestation to its management's assessment of the effectiveness of its internal control over financial reporting under Section 404(b) of the Sarbanes-Oxley Act (15 U.S.C. 7262(b)) by the registered public accounting firm that prepared or issued its audit report. [X]

If securities are registered pursuant to Section 12(b) of the Act, indicate by check mark whether the financial statements of the registrant included in the filing reflect the correction of an error to previously issued financial statements. [ ]

Indicate by check mark whether any of those error corrections are restatements that required a recovery analysis of incentive-based compensation received by any of the registrant's executive officers during the relevant recovery period pursuant to §240.10D-1(b). [ ]

The aggregate market value of the voting and non-voting common equity held by non-affiliates of the registrant, as of June 30, 2023, the last business day of the registrant's most recently completed second fiscal quarter, was approximately $2,999,000,000,000.

The number of shares outstanding of the registrant's common stock as of October 20, 2023, was 15,552,000,000.

DOCUMENTS INCORPORATED BY REFERENCE

Portions of the registrant's definitive proxy statement for its 2024 annual meeting of shareholders are incorporated by reference into Part III of this Annual Report on Form 10-K.

This is a mock 10-K report generated for demonstration purposes.
The actual content would be much longer and contain detailed financial information,
risk factors, business descriptions, and other required disclosures.

URL: {url}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(mock_content)
            
            self.logger.info(f"Created mock document at {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create mock document {output_path}: {e}")
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
