"""Tests for configuration loader utility."""

import pytest
import tempfile
import yaml
from pathlib import Path

import sys
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))

from utils.config_loader import ConfigLoader


class TestConfigLoader:
    """Test configuration loading functionality."""
    
    def test_load_valid_config(self):
        """Test loading a valid configuration file."""
        config_data = {
            'spatial': {'country': 'Indonesia'},
            'temporal': {'start_date': '2010-01-01', 'end_date': '2020-12-31'},
            'data_sources': {'modis': {'collections': ['MCD14ML']}},
            'output': {'formats': ['csv']}
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            config = ConfigLoader.load_config(temp_path)
            assert config['spatial']['country'] == 'Indonesia'
            assert config['temporal']['start_date'] == '2010-01-01'
        finally:
            Path(temp_path).unlink()
    
    def test_missing_config_file(self):
        """Test error handling for missing configuration file."""
        with pytest.raises(FileNotFoundError):
            ConfigLoader.load_config('nonexistent_config.yaml')
    
    def test_invalid_config_structure(self):
        """Test error handling for invalid configuration structure."""
        config_data = {'invalid': 'structure'}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name
        
        try:
            with pytest.raises(ValueError, match="Missing required configuration section"):
                ConfigLoader.load_config(temp_path)
        finally:
            Path(temp_path).unlink()
    
    def test_validate_temporal_config(self):
        """Test temporal configuration validation."""
        valid_config = {
            'temporal': {
                'start_date': '2010-01-01',
                'end_date': '2020-12-31'
            }
        }
        
        assert ConfigLoader.validate_temporal_config(valid_config) is True
        
        # Test invalid date order
        invalid_config = {
            'temporal': {
                'start_date': '2020-01-01',
                'end_date': '2010-12-31'
            }
        }
        
        with pytest.raises(ValueError, match="start_date must be before end_date"):
            ConfigLoader.validate_temporal_config(invalid_config)
    
    def test_invalid_date_format(self):
        """Test error handling for invalid date formats."""
        invalid_config = {
            'temporal': {
                'start_date': 'invalid-date',
                'end_date': '2020-12-31'
            }
        }
        
        with pytest.raises(ValueError, match="Invalid date format"):
            ConfigLoader.validate_temporal_config(invalid_config)