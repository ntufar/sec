"""
Command Line Interface for SEC Downloader
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import List

from .config import Config
from .downloader import SECDownloader
from .converter import PDFConverter


def setup_logging(config: Config):
    """Setup logging configuration"""
    log_level = getattr(logging, config.get('logging.level', 'INFO').upper())
    log_file = config.get('logging.file', 'data/logs/sec_downloader.log')
    
    # Create logs directory if it doesn't exist
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Download and convert SEC 10-K reports to PDF",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Download 10-K reports for Apple and Microsoft
  python -m sec_downloader download AAPL MSFT
  
  # Download and convert to PDF
  python -m sec_downloader download --convert AAPL MSFT
  
  # Download with custom output directory
  python -m sec_downloader download --output-dir ./reports AAPL
  
  # List available tickers
  python -m sec_downloader list-tickers
  
  # Convert existing text files to PDF
  python -m sec_downloader convert ./data/reports/AAPL/
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Download command
    download_parser = subparsers.add_parser('download', help='Download 10-K reports')
    download_parser.add_argument('tickers', nargs='+', help='Stock ticker symbols')
    download_parser.add_argument('--output-dir', '-o', help='Output directory for reports')
    download_parser.add_argument('--convert', '-c', action='store_true', 
                               help='Convert downloaded reports to PDF')
    download_parser.add_argument('--max-reports', type=int, default=5,
                               help='Maximum number of reports per company')
    download_parser.add_argument('--config', help='Path to configuration file')
    
    # List tickers command
    list_parser = subparsers.add_parser('list-tickers', help='List available ticker symbols')
    list_parser.add_argument('--search', '-s', help='Search for specific ticker or company name')
    list_parser.add_argument('--limit', type=int, default=50, help='Maximum number of results')
    list_parser.add_argument('--config', help='Path to configuration file')
    
    # Convert command
    convert_parser = subparsers.add_parser('convert', help='Convert text files to PDF')
    convert_parser.add_argument('input_path', help='Path to input file or directory')
    convert_parser.add_argument('--output-dir', '-o', help='Output directory for PDFs')
    convert_parser.add_argument('--config', help='Path to configuration file')
    
    # Config command
    config_parser = subparsers.add_parser('config', help='Configuration management')
    config_parser.add_argument('--init', action='store_true', help='Initialize default configuration')
    config_parser.add_argument('--show', action='store_true', help='Show current configuration')
    config_parser.add_argument('--config', help='Path to configuration file')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Load configuration
    config_file = getattr(args, 'config', None) or 'config/config.yaml'
    config = Config(config_file)
    
    # Setup logging
    setup_logging(config)
    logger = logging.getLogger(__name__)
    
    try:
        if args.command == 'download':
            return download_command(args, config, logger)
        elif args.command == 'list-tickers':
            return list_tickers_command(args, config, logger)
        elif args.command == 'convert':
            return convert_command(args, config, logger)
        elif args.command == 'config':
            return config_command(args, config, logger)
        else:
            parser.print_help()
            return 1
            
    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return 1


def download_command(args, config: Config, logger: logging.Logger) -> int:
    """Handle download command"""
    # Update config with command line arguments
    if args.output_dir:
        config.config['download']['output_dir'] = args.output_dir
    if args.max_reports:
        config.config['download']['max_reports_per_company'] = args.max_reports
    
    # Initialize downloader
    downloader = SECDownloader(config)
    converter = PDFConverter(config) if args.convert else None
    
    logger.info(f"Starting download for tickers: {', '.join(args.tickers)}")
    
    # Download reports
    downloaded_reports = downloader.download_10k_reports(args.tickers)
    
    total_downloaded = sum(len(reports) for reports in downloaded_reports.values())
    logger.info(f"Downloaded {total_downloaded} reports total")
    
    # Convert to PDF if requested
    if args.convert and converter:
        logger.info("Converting reports to PDF...")
        for ticker, reports in downloaded_reports.items():
            if reports:
                pdf_reports = converter.batch_convert(reports)
                logger.info(f"Converted {len(pdf_reports)} reports to PDF for {ticker}")
    
    return 0


def list_tickers_command(args, config: Config, logger: logging.Logger) -> int:
    """Handle list-tickers command"""
    downloader = SECDownloader(config)
    
    try:
        tickers = downloader.get_company_tickers()
        
        if args.search:
            search_term = args.search.lower()
            filtered_tickers = {
                ticker: data for ticker, data in tickers.items()
                if search_term in ticker.lower() or search_term in data['title'].lower()
            }
            tickers = filtered_tickers
        
        # Sort by ticker symbol
        sorted_tickers = sorted(tickers.items())
        
        # Limit results
        if args.limit:
            sorted_tickers = sorted_tickers[:args.limit]
        
        print(f"\nFound {len(sorted_tickers)} companies:\n")
        print(f"{'Ticker':<8} {'CIK':<12} {'Company Name'}")
        print("-" * 60)
        
        for ticker, data in sorted_tickers:
            print(f"{ticker:<8} {data['cik']:<12} {data['title']}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Failed to list tickers: {e}")
        return 1


def convert_command(args, config: Config, logger: logging.Logger) -> int:
    """Handle convert command"""
    converter = PDFConverter(config)
    input_path = Path(args.input_path)
    
    if not input_path.exists():
        logger.error(f"Input path does not exist: {input_path}")
        return 1
    
    # Determine output directory
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = input_path.parent / 'pdf'
    
    if input_path.is_file():
        # Convert single file
        if converter.convert_to_pdf(input_path, output_dir / f"{input_path.stem}.pdf"):
            logger.info(f"Successfully converted {input_path}")
            return 0
        else:
            logger.error(f"Failed to convert {input_path}")
            return 1
    else:
        # Convert directory
        text_files = list(input_path.rglob("*.txt"))
        if not text_files:
            logger.error(f"No .txt files found in {input_path}")
            return 1
        
        converted_files = converter.batch_convert(text_files, output_dir)
        logger.info(f"Converted {len(converted_files)} files to PDF")
        return 0


def config_command(args, config: Config, logger: logging.Logger) -> int:
    """Handle config command"""
    if args.init:
        config.save()
        logger.info(f"Initialized default configuration at {config.config_file}")
        return 0
    elif args.show:
        import yaml
        print(yaml.dump(config.config, default_flow_style=False))
        return 0
    else:
        logger.error("Use --init to create config or --show to display current config")
        return 1


if __name__ == '__main__':
    sys.exit(main())
