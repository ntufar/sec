"""
SEC 10-K Report Downloader

A Python package for downloading and converting SEC 10-K reports to PDF format.
"""

__version__ = "1.0.0"
__author__ = "ntufar"
__email__ = "ntufar@gmail.com"

from .downloader import SECDownloader
from .converter import PDFConverter
from .config import Config

__all__ = ["SECDownloader", "PDFConverter", "Config"]
