"""
Tests for configuration management
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from sec_downloader.config import Config


class TestConfig:
    """Test cases for Config class"""
    
    def test_default_config(self):
        """Test default configuration creation"""
        config = Config()
        
        # Test basic structure
        assert 'sec' in config.config
        assert 'download' in config.config
        assert 'conversion' in config.config
        assert 'logging' in config.config
        
        # Test specific values
        assert config.get('sec.user_agent') == 'ntufar@gmail.com'
        assert config.get('download.output_dir') == 'data/reports'
        assert config.get('conversion.output_format') == 'pdf'
    
    def test_config_file_loading(self):
        """Test loading configuration from file"""
        # Create temporary config file
        config_data = {
            'sec': {
                'user_agent': 'test@example.com',
                'rate_limit_delay': 0.5
            },
            'download': {
                'output_dir': 'test_reports',
                'max_reports_per_company': 10
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            config_file = f.name
        
        try:
            config = Config(config_file)
            
            # Test loaded values
            assert config.get('sec.user_agent') == 'test@example.com'
            assert config.get('sec.rate_limit_delay') == 0.5
            assert config.get('download.output_dir') == 'test_reports'
            assert config.get('download.max_reports_per_company') == 10
            
        finally:
            Path(config_file).unlink()
    
    def test_config_file_not_found(self):
        """Test behavior when config file doesn't exist"""
        config = Config('nonexistent_config.yaml')
        
        # Should fall back to default config
        assert config.get('sec.user_agent') == 'ntufar@gmail.com'
    
    def test_get_with_default(self):
        """Test get method with default values"""
        config = Config()
        
        # Test existing key
        assert config.get('sec.user_agent') == 'ntufar@gmail.com'
        
        # Test non-existing key with default
        assert config.get('nonexistent.key', 'default_value') == 'default_value'
        
        # Test non-existing key without default
        assert config.get('nonexistent.key') is None
    
    def test_save_config(self):
        """Test saving configuration to file"""
        config = Config()
        
        # Modify a value
        config.config['sec']['user_agent'] = 'modified@example.com'
        
        with tempfile.TemporaryDirectory() as temp_dir:
            config_file = Path(temp_dir) / 'test_config.yaml'
            config.config_file = config_file
            
            # Save configuration
            config.save()
            
            # Verify file was created
            assert config_file.exists()
            
            # Load and verify content
            with open(config_file, 'r') as f:
                saved_data = yaml.safe_load(f)
            
            assert saved_data['sec']['user_agent'] == 'modified@example.com'
    
    def test_nested_key_access(self):
        """Test accessing nested configuration keys"""
        config = Config()
        
        # Test valid nested keys
        assert config.get('sec.base_url') == 'https://www.sec.gov'
        assert config.get('download.max_reports_per_company') == 5
        assert config.get('logging.level') == 'INFO'
        
        # Test invalid nested keys
        assert config.get('sec.nonexistent') is None
        assert config.get('nonexistent.key') is None
