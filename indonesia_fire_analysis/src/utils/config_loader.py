"""Configuration loader utility for Indonesia fire analysis."""

import yaml
from pathlib import Path
from typing import Dict, Any


class ConfigLoader:
    """Load and validate configuration files."""
    
    @staticmethod
    def load_config(config_path: str) -> Dict[str, Any]:
        """
        Load configuration from YAML file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        # Validate required sections
        required_sections = ['spatial', 'temporal', 'data_sources', 'output']
        for section in required_sections:
            if section not in config:
                raise ValueError(f"Missing required configuration section: {section}")
        
        return config
    
    @staticmethod
    def validate_temporal_config(config: Dict[str, Any]) -> bool:
        """
        Validate temporal configuration.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            True if valid
        """
        temporal = config.get('temporal', {})
        
        # Check required fields
        required_fields = ['start_date', 'end_date']
        for field in required_fields:
            if field not in temporal:
                raise ValueError(f"Missing temporal field: {field}")
        
        # Validate date format (YYYY-MM-DD)
        import datetime
        try:
            start = datetime.datetime.strptime(temporal['start_date'], '%Y-%m-%d')
            end = datetime.datetime.strptime(temporal['end_date'], '%Y-%m-%d')
            
            if start >= end:
                raise ValueError("start_date must be before end_date")
                
        except ValueError as e:
            raise ValueError(f"Invalid date format: {e}")
        
        return True