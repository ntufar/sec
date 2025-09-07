#!/usr/bin/env python3
"""
Basic usage example for SEC Downloader
"""

from sec_downloader import SECDownloader, PDFConverter, Config
import logging

def main():
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Load configuration
    config = Config('config/config.yaml')
    
    # Initialize downloader and converter
    downloader = SECDownloader(config)
    converter = PDFConverter(config)
    
    # List of companies to download
    companies = ['AAPL', 'MSFT', 'GOOGL']
    
    logger.info(f"Starting download for companies: {', '.join(companies)}")
    
    # Download 10-K reports
    reports = downloader.download_10k_reports(companies)
    
    # Print summary
    total_downloaded = sum(len(files) for files in reports.values())
    logger.info(f"Downloaded {total_downloaded} reports total")
    
    # Convert to PDF
    logger.info("Converting reports to PDF...")
    for ticker, files in reports.items():
        if files:
            pdf_files = converter.batch_convert(files)
            logger.info(f"Converted {len(pdf_files)} reports to PDF for {ticker}")
    
    logger.info("Download and conversion completed!")

if __name__ == "__main__":
    main()
