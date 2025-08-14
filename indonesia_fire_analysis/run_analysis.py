#!/usr/bin/env python3
"""
Quick start script for Indonesia Fire Analysis
=============================================

This script provides a simplified interface to run the fire analysis
with common configurations and options.
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
import logging

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from main import main
from utils.config_loader import ConfigLoader
from utils.logger import setup_logging


def create_sample_config(config_path: str) -> None:
    """Create a sample configuration file."""
    sample_config = """# Indonesia Fire Analysis Configuration - Sample

# Spatial boundaries
spatial:
  country: "Indonesia"
  admin_level: "district"
  crs: "EPSG:4326"

# Temporal range (adjust dates as needed)
temporal:
  start_date: "2019-01-01"  # Reduced range for testing
  end_date: "2019-12-31"

# Data sources
data_sources:
  modis:
    collections: ["MCD14ML"]  # Active fire points only for testing
    variables: ["fire_mask", "FirePix", "MaxFRP"]
    
  viirs:
    collections: ["VNP14IMGML"]
    variables: ["fire_mask", "MaxFRP"]
    start_year: 2012
    
  co:
    collections: ["MOP02J", "AIRX3STD"]
    variables: ["COVMRLevs", "TotCO_A"]

# Processing parameters
processing:
  chunk_size: "1GB"
  parallel_workers: 2  # Reduced for testing
  quality_flags:
    confidence_threshold: 7
    frp_threshold: 0

# Output settings
output:
  formats: ["csv", "geojson"]  # Reduced formats for testing
  directory: "output"
  temporal_aggregation: ["yearly"]  # Simplified aggregation

# API endpoints
apis:
  nasa_earthdata: "https://ladsweb.modaps.eosdis.nasa.gov"
  google_earth_engine: true
  earthdata_username: null
  earthdata_password: null
"""
    
    with open(config_path, 'w') as f:
        f.write(sample_config)
    
    print(f"Created sample configuration at: {config_path}")
    print("Please review and modify the configuration as needed before running the analysis.")


def run_quick_analysis(args):
    """Run a quick analysis with predefined settings."""
    
    # Setup logging
    setup_logging(log_level=args.log_level)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Indonesia Fire Analysis - Quick Mode")
    
    try:
        # Use sample config if main config doesn't exist
        config_file = Path("config.yaml")
        if not config_file.exists():
            logger.warning("config.yaml not found. Creating sample configuration...")
            create_sample_config("config_sample.yaml")
            logger.info("Please copy config_sample.yaml to config.yaml and modify as needed")
            return
        
        # Run main analysis
        result = main()
        
        logger.info("Analysis completed successfully!")
        logger.info(f"Results saved to: {Path('output').absolute()}")
        
        # Print summary
        if hasattr(result, '__len__'):
            logger.info(f"Processed {len(result)} districts")
        
        return result
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        if args.debug:
            raise
        return None


def run_custom_analysis(args):
    """Run analysis with custom parameters."""
    
    # Setup logging
    setup_logging(log_level=args.log_level)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Indonesia Fire Analysis - Custom Mode")
    
    # Load and modify configuration
    config = ConfigLoader.load_config(args.config)
    
    # Override temporal range if provided
    if args.start_date:
        config['temporal']['start_date'] = args.start_date
    if args.end_date:
        config['temporal']['end_date'] = args.end_date
    
    # Override output formats if provided
    if args.formats:
        config['output']['formats'] = args.formats.split(',')
    
    logger.info(f"Configuration loaded from: {args.config}")
    logger.info(f"Temporal range: {config['temporal']['start_date']} to {config['temporal']['end_date']}")
    
    try:
        # Run main analysis
        result = main()
        
        logger.info("Custom analysis completed successfully!")
        return result
        
    except Exception as e:
        logger.error(f"Custom analysis failed: {str(e)}")
        if args.debug:
            raise
        return None


def main_cli():
    """Command line interface for the analysis."""
    
    parser = argparse.ArgumentParser(
        description="Indonesia Forest Fire Analysis Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Quick analysis with default settings
  python run_analysis.py quick
  
  # Custom analysis with date range
  python run_analysis.py custom --start-date 2018-01-01 --end-date 2018-12-31
  
  # Generate sample configuration
  python run_analysis.py config
  
  # Run with debug output
  python run_analysis.py quick --debug --log-level DEBUG
        """
    )
    
    parser.add_argument(
        'mode',
        choices=['quick', 'custom', 'config'],
        help='Analysis mode: quick (predefined), custom (configurable), or config (generate sample)'
    )
    
    parser.add_argument(
        '--config', '-c',
        default='config.yaml',
        help='Configuration file path (default: config.yaml)'
    )
    
    parser.add_argument(
        '--start-date',
        help='Start date for analysis (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--end-date',
        help='End date for analysis (YYYY-MM-DD)'
    )
    
    parser.add_argument(
        '--formats',
        help='Output formats (comma-separated): csv,geojson,netcdf,parquet'
    )
    
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='Logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode (show full tracebacks)'
    )
    
    args = parser.parse_args()
    
    if args.mode == 'config':
        create_sample_config('config_sample.yaml')
        return
    
    elif args.mode == 'quick':
        result = run_quick_analysis(args)
        
    elif args.mode == 'custom':
        result = run_custom_analysis(args)
    
    # Print final status
    if result is not None:
        print(f"\n✅ Analysis completed successfully!")
        print(f"📁 Output directory: {Path('output').absolute()}")
        print(f"📊 Visualizations: {Path('output/visualizations').absolute()}")
        print(f"📈 Check output/final/ for processed datasets")
    else:
        print(f"\n❌ Analysis failed. Check logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    main_cli()