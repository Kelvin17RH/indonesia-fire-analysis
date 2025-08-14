#!/usr/bin/env python3
"""
Indonesia Forest Fire Data Extraction System
============================================

This system extracts and processes satellite-based forest fire data for Indonesia
at the district level for 2010-2020, including:
- Active fire occurrences (MODIS, VIIRS)
- Fire Radiative Power (FRP)
- Carbon Monoxide (CO) concentrations

Author: Generated for Indonesia Fire Analysis
Date: 2024
"""

import os
import sys
import logging
import yaml
from pathlib import Path
from datetime import datetime

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

from data_extraction.modis_extractor import MODISExtractor
from data_extraction.viirs_extractor import VIIRSExtractor
from data_extraction.co_extractor import COExtractor
from spatial_processing.boundary_processor import BoundaryProcessor
from spatial_processing.aggregator import SpatialAggregator
from utils.config_loader import ConfigLoader
from utils.logger import setup_logging


def main():
    """Main execution function for Indonesia fire data extraction."""
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Load configuration
    config = ConfigLoader.load_config("config.yaml")
    logger.info("Configuration loaded successfully")
    
    # Create output directories
    output_dir = Path(config['output']['directory'])
    output_dir.mkdir(exist_ok=True)
    (output_dir / "raw").mkdir(exist_ok=True)
    (output_dir / "processed").mkdir(exist_ok=True)
    (output_dir / "final").mkdir(exist_ok=True)
    
    try:
        # Step 1: Load Indonesia district boundaries
        logger.info("Loading Indonesia district boundaries...")
        boundary_processor = BoundaryProcessor(config)
        districts_gdf = boundary_processor.load_indonesia_districts()
        logger.info(f"Loaded {len(districts_gdf)} districts")
        
        # Step 2: Extract MODIS fire data (2010-2020)
        logger.info("Extracting MODIS fire data...")
        modis_extractor = MODISExtractor(config)
        modis_data = modis_extractor.extract_fire_data(
            start_date=config['temporal']['start_date'],
            end_date=config['temporal']['end_date'],
            bbox=boundary_processor.get_indonesia_bbox()
        )
        
        # Step 3: Extract VIIRS fire data (2012-2020)
        logger.info("Extracting VIIRS fire data...")
        viirs_extractor = VIIRSExtractor(config)
        viirs_data = viirs_extractor.extract_fire_data(
            start_date="2012-01-01",  # VIIRS starts from 2012
            end_date=config['temporal']['end_date'],
            bbox=boundary_processor.get_indonesia_bbox()
        )
        
        # Step 4: Extract CO data
        logger.info("Extracting CO data...")
        co_extractor = COExtractor(config)
        co_data = co_extractor.extract_co_data(
            start_date=config['temporal']['start_date'],
            end_date=config['temporal']['end_date'],
            bbox=boundary_processor.get_indonesia_bbox()
        )
        
        # Step 5: Spatial aggregation to district level
        logger.info("Performing spatial aggregation...")
        aggregator = SpatialAggregator(config)
        
        # Aggregate fire data
        district_fire_stats = aggregator.aggregate_fire_data(
            fire_data={'modis': modis_data, 'viirs': viirs_data},
            districts_gdf=districts_gdf
        )
        
        # Aggregate CO data
        district_co_stats = aggregator.aggregate_co_data(
            co_data=co_data,
            districts_gdf=districts_gdf
        )
        
        # Step 6: Combine and export results
        logger.info("Combining results and exporting...")
        final_data = aggregator.combine_datasets(
            fire_stats=district_fire_stats,
            co_stats=district_co_stats,
            districts_gdf=districts_gdf
        )
        
        # Export in multiple formats
        for fmt in config['output']['formats']:
            output_file = output_dir / "final" / f"indonesia_fire_data_2010_2020.{fmt}"
            aggregator.export_data(final_data, output_file, fmt)
            logger.info(f"Exported data to {output_file}")
        
        # Generate summary statistics
        summary_stats = aggregator.generate_summary_statistics(final_data)
        summary_file = output_dir / "final" / "summary_statistics.yaml"
        with open(summary_file, 'w') as f:
            yaml.dump(summary_stats, f, default_flow_style=False)
        
        logger.info("Fire data extraction completed successfully!")
        logger.info(f"Results saved to: {output_dir.absolute()}")
        
        return final_data
        
    except Exception as e:
        logger.error(f"Error during execution: {str(e)}")
        raise


if __name__ == "__main__":
    main()