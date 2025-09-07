"""
Tests for SEC downloader functionality
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import tempfile
import json

from sec_downloader.config import Config
from sec_downloader.downloader import SECDownloader


class TestSECDownloader:
    """Test cases for SECDownloader class"""
    
    @pytest.fixture
    def config(self):
        """Create a test configuration"""
        config = Config()
        config.config['sec']['rate_limit_delay'] = 0.01  # Faster for tests
        return config
    
    @pytest.fixture
    def downloader(self, config):
        """Create a test downloader instance"""
        return SECDownloader(config)
    
    def test_init(self, config):
        """Test downloader initialization"""
        downloader = SECDownloader(config)
        
        assert downloader.config == config
        assert downloader.session is not None
        assert 'User-Agent' in downloader.session.headers
    
    @patch('requests.Session.get')
    def test_get_company_tickers(self, mock_get, downloader):
        """Test getting company tickers"""
        # Mock response data
        mock_response = Mock()
        mock_response.json.return_value = {
            '0': {'ticker': 'AAPL', 'cik': 320193, 'title': 'Apple Inc.'},
            '1': {'ticker': 'MSFT', 'cik': 789019, 'title': 'Microsoft Corporation'}
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test the method
        tickers = downloader.get_company_tickers()
        
        # Verify results
        assert len(tickers) == 2
        assert 'AAPL' in tickers
        assert 'MSFT' in tickers
        assert tickers['AAPL']['cik'] == '0000320193'
        assert tickers['AAPL']['title'] == 'Apple Inc.'
        assert tickers['MSFT']['cik'] == '0000789019'
        assert tickers['MSFT']['title'] == 'Microsoft Corporation'
    
    @patch('requests.Session.get')
    def test_get_company_tickers_error(self, mock_get, downloader):
        """Test error handling in get_company_tickers"""
        # Mock error response
        mock_get.side_effect = Exception("Network error")
        
        with pytest.raises(Exception):
            downloader.get_company_tickers()
    
    @patch('requests.Session.get')
    def test_get_company_filings(self, mock_get, downloader):
        """Test getting company filings"""
        # Mock response data
        mock_response = Mock()
        mock_response.json.return_value = {
            'filings': {
                'recent': {
                    'form': ['10-K', '10-K'],
                    'filingDate': ['2023-12-31', '2022-12-31'],
                    'reportDate': ['2023-12-31', '2022-12-31'],
                    'accessionNumber': ['0000320193-23-000077', '0000320193-22-000077'],
                    'primaryDocument': ['aapl-20231231.htm', 'aapl-20221231.htm'],
                    'size': [1234567, 1234567]
                }
            }
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test the method
        filings = downloader.get_company_filings('0000320193', '10-K', 2)
        
        # Verify results
        assert len(filings) == 2
        assert filings[0]['form'] == '10-K'
        assert filings[0]['filingDate'] == '2023-12-31'
        assert filings[0]['accessionNumber'] == '0000320193-23-000077'
    
    @patch('requests.Session.get')
    def test_get_filing_documents(self, mock_get, downloader):
        """Test getting filing documents"""
        # Mock HTML response with document links
        mock_response = Mock()
        mock_response.text = '''
        <html>
        <body>
        <a href="aapl-20231231.htm">10-K Report</a>
        <a href="aapl-20231231-ex99.htm">Exhibit 99</a>
        <a href="other.txt">Other Document</a>
        </body>
        </html>
        '''
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        # Test the method
        documents = downloader.get_filing_documents('0000320193', '0000320193-23-000077')
        
        # Verify results
        assert len(documents) >= 1
        assert any(doc['filename'] == 'aapl-20231231.htm' for doc in documents)
    
    def test_get_document_type(self, downloader):
        """Test document type detection"""
        assert downloader._get_document_type('aapl-10k-20231231.htm') == '10-K'
        assert downloader._get_document_type('aapl-10q-20231231.htm') == '10-Q'
        assert downloader._get_document_type('aapl-8k-20231231.htm') == '8-K'
        assert downloader._get_document_type('other-document.txt') == 'other'
    
    @patch('requests.Session.get')
    def test_download_document_success(self, mock_get, downloader):
        """Test successful document download"""
        # Mock response
        mock_response = Mock()
        mock_response.iter_content.return_value = [b'file content']
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / 'test_file.txt'
            
            # Test download
            result = downloader.download_document('http://example.com/file.txt', output_path)
            
            # Verify results
            assert result is True
            assert output_path.exists()
            assert output_path.read_text() == 'file content'
    
    @patch('requests.Session.get')
    def test_download_document_error(self, mock_get, downloader):
        """Test document download error handling"""
        # Mock error response
        mock_get.side_effect = Exception("Download error")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / 'test_file.txt'
            
            # Test download
            result = downloader.download_document('http://example.com/file.txt', output_path)
            
            # Verify results
            assert result is False
            assert not output_path.exists()
    
    @patch.object(SECDownloader, 'get_company_tickers')
    @patch.object(SECDownloader, 'get_company_filings')
    @patch.object(SECDownloader, 'get_filing_documents')
    @patch.object(SECDownloader, 'download_document')
    def test_download_10k_reports(self, mock_download, mock_get_docs, 
                                 mock_get_filings, mock_get_tickers, downloader):
        """Test downloading 10-K reports"""
        # Mock company tickers
        mock_get_tickers.return_value = {
            'AAPL': {'cik': '0000320193', 'title': 'Apple Inc.'}
        }
        
        # Mock filings
        mock_get_filings.return_value = [
            {
                'form': '10-K',
                'filingDate': '2023-12-31',
                'reportDate': '2023-12-31',
                'accessionNumber': '0000320193-23-000077',
                'primaryDocument': 'aapl-20231231.htm',
                'size': 1234567
            }
        ]
        
        # Mock documents
        mock_get_docs.return_value = [
            {
                'filename': 'aapl-20231231.htm',
                'url': 'http://example.com/aapl-20231231.htm',
                'type': '10-K'
            }
        ]
        
        # Mock successful download
        mock_download.return_value = True
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test download
            reports = downloader.download_10k_reports(['AAPL'], temp_dir)
            
            # Verify results
            assert 'AAPL' in reports
            assert len(reports['AAPL']) == 1
            assert reports['AAPL'][0].name == 'AAPL_2023-12-31_10K.txt'
