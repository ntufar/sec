#!/usr/bin/env python3
"""
Advanced usage example for SEC Downloader
"""

from sec_downloader import SECDownloader, PDFConverter, Config
import logging
from pathlib import Path
import time

def main():
    # Setup detailed logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Load configuration
    config = Config('config/config.yaml')
    
    # Modify configuration for this example
    config.config['download']['max_reports_per_company'] = 3
    config.config['sec']['rate_limit_delay'] = 0.2  # Slower requests
    
    # Initialize downloader and converter
    downloader = SECDownloader(config)
    converter = PDFConverter(config)
    
    # Get available companies
    logger.info("Fetching company tickers...")
    try:
        tickers = downloader.get_company_tickers()
        logger.info(f"Found {len(tickers)} companies in SEC database")
    except Exception as e:
        logger.error(f"Failed to get company tickers: {e}")
        return
    
    # Search for technology companies
    tech_companies = []
    search_terms = ['apple', 'microsoft', 'google', 'amazon', 'tesla', 'meta', 'nvidia']
    
    for term in search_terms:
        for ticker, data in tickers.items():
            if term in data['title'].lower() and ticker not in tech_companies:
                tech_companies.append(ticker)
                break
    
    logger.info(f"Selected technology companies: {', '.join(tech_companies)}")
    
    # Download reports
    logger.info("Starting download process...")
    start_time = time.time()
    
    try:
        reports = downloader.download_10k_reports(tech_companies)
        
        # Print detailed results
        total_downloaded = 0
        for ticker, files in reports.items():
            if files:
                total_downloaded += len(files)
                logger.info(f"{ticker}: {len(files)} reports downloaded")
                for file_path in files:
                    logger.info(f"  - {file_path}")
            else:
                logger.warning(f"{ticker}: No reports downloaded")
        
        logger.info(f"Total reports downloaded: {total_downloaded}")
        
    except Exception as e:
        logger.error(f"Download failed: {e}")
        return
    
    # Convert to PDF
    logger.info("Starting PDF conversion...")
    conversion_start = time.time()
    
    try:
        total_converted = 0
        for ticker, files in reports.items():
            if files:
                logger.info(f"Converting {ticker} reports to PDF...")
                pdf_files = converter.batch_convert(files)
                total_converted += len(pdf_files)
                logger.info(f"Converted {len(pdf_files)} files for {ticker}")
        
        logger.info(f"Total files converted to PDF: {total_converted}")
        
    except Exception as e:
        logger.error(f"PDF conversion failed: {e}")
        return
    
    # Print timing information
    total_time = time.time() - start_time
    conversion_time = time.time() - conversion_start
    
    logger.info(f"Total execution time: {total_time:.2f} seconds")
    logger.info(f"PDF conversion time: {conversion_time:.2f} seconds")
    
    # Create summary report
    create_summary_report(reports, total_time, conversion_time)

def create_summary_report(reports, total_time, conversion_time):
    """Create a summary report of the download process"""
    summary_path = Path('data/reports/download_summary.txt')
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(summary_path, 'w') as f:
        f.write("SEC Downloader - Summary Report\n")
        f.write("=" * 40 + "\n\n")
        f.write(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Total execution time: {total_time:.2f} seconds\n")
        f.write(f"PDF conversion time: {conversion_time:.2f} seconds\n\n")
        
        f.write("Downloaded Reports:\n")
        f.write("-" * 20 + "\n")
        
        total_files = 0
        for ticker, files in reports.items():
            f.write(f"\n{ticker}:\n")
            if files:
                for file_path in files:
                    f.write(f"  - {file_path.name}\n")
                    total_files += 1
            else:
                f.write("  - No reports downloaded\n")
        
        f.write(f"\nTotal files downloaded: {total_files}\n")
    
    print(f"Summary report saved to: {summary_path}")

if __name__ == "__main__":
    main()
