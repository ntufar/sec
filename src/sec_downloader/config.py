"""
Configuration management for SEC Downloader
"""

import os
from pathlib import Path
from typing import Dict, Any
import yaml


class Config:
    """Configuration manager for SEC Downloader"""
    
    def __init__(self, config_file: str = "config/config.yaml"):
        self.config_file = Path(config_file)
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file or create default"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f)
        else:
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'sec': {
                'base_url': 'https://www.sec.gov',
                'api_url': 'https://data.sec.gov/api/xbrl/companyconcept',
                'edgar_url': 'https://www.sec.gov/Archives/edgar',
                'user_agent': 'ntufar@gmail.com',
                'rate_limit_delay': 0.1  # seconds between requests
            },
            'download': {
                'output_dir': 'data/reports',
                'form_types': ['10-K', '10-Q'],
                'max_reports_per_company': 5,
                'years_back': 5
            },
            'conversion': {
                'output_format': 'pdf',
                'include_attachments': True,
                'quality': 'high'
            },
            'logging': {
                'level': 'INFO',
                'file': 'data/logs/sec_downloader.log',
                'max_size': '10MB',
                'backup_count': 5
            }
        }
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-separated key"""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def save(self):
        """Save current configuration to file"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w') as f:
            yaml.dump(self.config, f, default_flow_style=False)
