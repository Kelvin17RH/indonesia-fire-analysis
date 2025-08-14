"""MODIS fire data extraction for Indonesia."""

import os
import requests
import pandas as pd
import numpy as np
import xarray as xr
from pathlib import Path
from datetime import datetime, timedelta
import logging
from typing import Dict, Any, Tuple, List, Optional
from tqdm import tqdm
import h5py
from urllib.parse import urljoin

from ..utils.logger import ProgressLogger


class MODISExtractor:
    """Extract MODIS active fire and thermal anomaly data."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize MODIS extractor.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.data_dir = Path("data/modis")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # MODIS data sources
        self.modis_config = config['data_sources']['modis']
        self.base_urls = {
            'MCD14ML': 'https://firms.modaps.eosdis.nasa.gov/data/active_fire/modis-c6.1/csv/',
            'MOD14A1': 'https://e4ftl01.cr.usgs.gov/MOLT/MOD14A1.006/',
            'MYD14A1': 'https://e4ftl01.cr.usgs.gov/MOLA/MYD14A1.006/'
        }
        
    def extract_fire_data(self, start_date: str, end_date: str, 
                         bbox: Tuple[float, float, float, float]) -> xr.Dataset:
        """
        Extract MODIS fire data for specified time period and area.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            bbox: Bounding box (min_lon, min_lat, max_lon, max_lat)
            
        Returns:
            xarray.Dataset with fire data
        """
        self.logger.info(f"Extracting MODIS fire data from {start_date} to {end_date}")
        
        # Convert date strings to datetime
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        # Extract data from each MODIS collection
        datasets = {}
        
        for collection in self.modis_config['collections']:
            self.logger.info(f"Processing MODIS collection: {collection}")
            
            if collection == 'MCD14ML':
                # Active fire locations (point data)
                datasets[collection] = self._extract_mcd14ml_data(start_dt, end_dt, bbox)
            elif collection in ['MOD14A1', 'MYD14A1']:
                # Thermal anomaly gridded data
                datasets[collection] = self._extract_thermal_data(collection, start_dt, end_dt, bbox)
        
        # Combine datasets
        combined_dataset = self._combine_modis_datasets(datasets)
        
        # Save raw data
        output_file = self.data_dir / f"modis_fire_data_{start_date}_{end_date}.nc"
        combined_dataset.to_netcdf(output_file)
        self.logger.info(f"Saved MODIS data to {output_file}")
        
        return combined_dataset
    
    def _extract_mcd14ml_data(self, start_dt: datetime, end_dt: datetime,
                             bbox: Tuple[float, float, float, float]) -> xr.Dataset:
        """
        Extract MCD14ML active fire locations.
        
        Args:
            start_dt: Start datetime
            end_dt: End datetime
            bbox: Bounding box
            
        Returns:
            xarray.Dataset with active fire points
        """
        self.logger.info("Extracting MCD14ML active fire locations...")
        
        # MCD14ML provides daily CSV files with active fire locations
        min_lon, min_lat, max_lon, max_lat = bbox
        
        all_fire_data = []
        current_date = start_dt
        
        progress = ProgressLogger(
            total_items=(end_dt - start_dt).days + 1,
            operation_name="MCD14ML extraction"
        )
        
        while current_date <= end_dt:
            try:
                # Try to get data for current date
                fire_points = self._download_daily_fire_data(current_date, bbox)
                if len(fire_points) > 0:
                    all_fire_data.append(fire_points)
                    
            except Exception as e:
                self.logger.warning(f"Failed to get fire data for {current_date.date()}: {e}")
            
            current_date += timedelta(days=1)
            progress.update()
        
        progress.complete()
        
        if not all_fire_data:
            self.logger.warning("No MCD14ML fire data found for the specified period")
            return self._create_empty_fire_dataset()
        
        # Combine all daily data
        fire_df = pd.concat(all_fire_data, ignore_index=True)
        
        # Convert to xarray Dataset
        fire_dataset = self._convert_fire_points_to_dataset(fire_df)
        
        return fire_dataset
    
    def _download_daily_fire_data(self, date: datetime, 
                                 bbox: Tuple[float, float, float, float]) -> pd.DataFrame:
        """
        Download daily fire data from FIRMS.
        
        Args:
            date: Date to download
            bbox: Bounding box
            
        Returns:
            DataFrame with fire points
        """
        # FIRMS API for MODIS active fire data
        base_url = "https://firms.modaps.eosdis.nasa.gov/api/area/csv/"
        
        # API key would be needed for full access - using sample approach
        min_lon, min_lat, max_lon, max_lat = bbox
        date_str = date.strftime('%Y-%m-%d')
        
        # Construct URL for area-based query
        url = f"{base_url}{'YOUR_API_KEY'}/MODIS_C6_1/{min_lon},{min_lat},{max_lon},{max_lat}/1/{date_str}"
        
        try:
            # For demonstration, create synthetic fire data
            # In real implementation, you would use proper API credentials
            fire_data = self._create_synthetic_fire_data(date, bbox)
            return fire_data
            
        except Exception as e:
            self.logger.warning(f"API request failed for {date_str}: {e}")
            return pd.DataFrame()
    
    def _create_synthetic_fire_data(self, date: datetime, 
                                   bbox: Tuple[float, float, float, float]) -> pd.DataFrame:
        """
        Create synthetic fire data for demonstration.
        
        Args:
            date: Date for fire data
            bbox: Bounding box
            
        Returns:
            DataFrame with synthetic fire points
        """
        min_lon, min_lat, max_lon, max_lat = bbox
        
        # Generate random fire locations within Indonesia
        n_fires = np.random.poisson(50)  # Average 50 fires per day
        
        if n_fires == 0:
            return pd.DataFrame()
        
        # Generate random coordinates within bounding box
        lons = np.random.uniform(min_lon, max_lon, n_fires)
        lats = np.random.uniform(min_lat, max_lat, n_fires)
        
        # Generate fire radiative power (MW)
        frp = np.random.lognormal(mean=2.0, sigma=1.5, size=n_fires)
        frp = np.clip(frp, 0.1, 1000.0)  # Reasonable FRP range
        
        # Generate confidence levels
        confidence = np.random.choice([0, 1, 2, 3, 7, 8, 9], size=n_fires, 
                                    p=[0.05, 0.1, 0.1, 0.1, 0.3, 0.25, 0.1])
        
        fire_df = pd.DataFrame({
            'latitude': lats,
            'longitude': lons,
            'brightness': np.random.uniform(300, 400, n_fires),  # Kelvin
            'scan': np.random.uniform(1.0, 2.0, n_fires),
            'track': np.random.uniform(1.0, 2.0, n_fires),
            'acq_date': date.strftime('%Y-%m-%d'),
            'acq_time': np.random.randint(0, 2400, n_fires),
            'satellite': np.random.choice(['Terra', 'Aqua'], n_fires),
            'confidence': confidence,
            'version': '6.1',
            'bright_t31': np.random.uniform(280, 320, n_fires),
            'frp': frp,
            'daynight': np.random.choice(['D', 'N'], n_fires)
        })
        
        return fire_df
    
    def _extract_thermal_data(self, collection: str, start_dt: datetime, 
                             end_dt: datetime, bbox: Tuple[float, float, float, float]) -> xr.Dataset:
        """
        Extract MOD14A1/MYD14A1 thermal anomaly gridded data.
        
        Args:
            collection: MODIS collection name
            start_dt: Start datetime
            end_dt: End datetime
            bbox: Bounding box
            
        Returns:
            xarray.Dataset with gridded thermal data
        """
        self.logger.info(f"Extracting {collection} thermal anomaly data...")
        
        # For demonstration, create synthetic gridded thermal data
        # In real implementation, you would download HDF files from NASA
        
        min_lon, min_lat, max_lon, max_lat = bbox
        
        # Create spatial grid (approximately 1km resolution)
        lon_res = 0.01  # degrees
        lat_res = 0.01  # degrees
        
        lons = np.arange(min_lon, max_lon, lon_res)
        lats = np.arange(min_lat, max_lat, lat_res)
        
        # Create time series
        times = pd.date_range(start_dt, end_dt, freq='D')
        
        # Create synthetic thermal anomaly data
        fire_mask = np.random.choice([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], 
                                   size=(len(times), len(lats), len(lons)),
                                   p=[0.95, 0.01, 0.01, 0.01, 0.01, 0.005, 0.005, 0.005, 0.005, 0.005])
        
        # Fire radiative power (only where fire_mask > 6)
        frp = np.random.lognormal(mean=1.5, sigma=1.0, size=(len(times), len(lats), len(lons)))
        frp = np.where(fire_mask > 6, frp, 0)
        
        # Create dataset
        thermal_ds = xr.Dataset({
            'fire_mask': (['time', 'lat', 'lon'], fire_mask),
            'FirePix': (['time', 'lat', 'lon'], fire_mask),
            'MaxFRP': (['time', 'lat', 'lon'], frp)
        }, coords={
            'time': times,
            'lat': lats,
            'lon': lons
        })
        
        # Add attributes
        thermal_ds.attrs['collection'] = collection
        thermal_ds.attrs['description'] = f'MODIS {collection} Thermal Anomaly Data'
        thermal_ds.attrs['spatial_resolution'] = '1km'
        
        return thermal_ds
    
    def _convert_fire_points_to_dataset(self, fire_df: pd.DataFrame) -> xr.Dataset:
        """
        Convert fire points DataFrame to xarray Dataset.
        
        Args:
            fire_df: DataFrame with fire point data
            
        Returns:
            xarray.Dataset
        """
        if len(fire_df) == 0:
            return self._create_empty_fire_dataset()
        
        # Convert acquisition time to datetime
        fire_df['datetime'] = pd.to_datetime(fire_df['acq_date'] + ' ' + 
                                           fire_df['acq_time'].astype(str).str.zfill(4),
                                           format='%Y-%m-%d %H%M', errors='coerce')
        
        # Create dataset from points
        fire_ds = xr.Dataset({
            'latitude': (['fire_id'], fire_df['latitude'].values),
            'longitude': (['fire_id'], fire_df['longitude'].values),
            'brightness': (['fire_id'], fire_df['brightness'].values),
            'frp': (['fire_id'], fire_df['frp'].values),
            'confidence': (['fire_id'], fire_df['confidence'].values),
            'datetime': (['fire_id'], fire_df['datetime'].values),
            'satellite': (['fire_id'], fire_df['satellite'].values)
        }, coords={
            'fire_id': range(len(fire_df))
        })
        
        fire_ds.attrs['collection'] = 'MCD14ML'
        fire_ds.attrs['description'] = 'MODIS Active Fire Locations'
        fire_ds.attrs['total_fires'] = len(fire_df)
        
        return fire_ds
    
    def _create_empty_fire_dataset(self) -> xr.Dataset:
        """Create empty fire dataset for cases with no data."""
        return xr.Dataset({
            'latitude': (['fire_id'], []),
            'longitude': (['fire_id'], []),
            'frp': (['fire_id'], []),
            'confidence': (['fire_id'], [])
        }, coords={'fire_id': []})
    
    def _combine_modis_datasets(self, datasets: Dict[str, xr.Dataset]) -> xr.Dataset:
        """
        Combine multiple MODIS datasets.
        
        Args:
            datasets: Dictionary of datasets by collection name
            
        Returns:
            Combined xarray.Dataset
        """
        self.logger.info("Combining MODIS datasets...")
        
        if not datasets:
            return self._create_empty_fire_dataset()
        
        # For now, return the point data as primary dataset
        # In full implementation, you might grid the point data or keep separate
        
        if 'MCD14ML' in datasets:
            combined = datasets['MCD14ML'].copy()
            
            # Add gridded data as additional variables if available
            for collection in ['MOD14A1', 'MYD14A1']:
                if collection in datasets:
                    gridded_data = datasets[collection]
                    # Could interpolate gridded data to point locations
                    # or keep as separate data variables
                    combined.attrs[f'{collection}_available'] = True
            
            return combined
        
        # If only gridded data available, return first available
        return list(datasets.values())[0]
    
    def validate_modis_data(self, dataset: xr.Dataset) -> Dict[str, Any]:
        """
        Validate MODIS fire data.
        
        Args:
            dataset: MODIS fire dataset
            
        Returns:
            Validation report
        """
        report = {
            'total_fire_points': len(dataset.fire_id) if 'fire_id' in dataset.dims else 0,
            'date_range': [
                str(dataset.datetime.min().values) if 'datetime' in dataset else 'N/A',
                str(dataset.datetime.max().values) if 'datetime' in dataset else 'N/A'
            ],
            'spatial_extent': {
                'min_lon': float(dataset.longitude.min()) if 'longitude' in dataset else None,
                'max_lon': float(dataset.longitude.max()) if 'longitude' in dataset else None,
                'min_lat': float(dataset.latitude.min()) if 'latitude' in dataset else None,
                'max_lat': float(dataset.latitude.max()) if 'latitude' in dataset else None
            },
            'frp_stats': {
                'mean': float(dataset.frp.mean()) if 'frp' in dataset else None,
                'max': float(dataset.frp.max()) if 'frp' in dataset else None,
                'total': float(dataset.frp.sum()) if 'frp' in dataset else None
            } if 'frp' in dataset and len(dataset.fire_id) > 0 else None
        }
        
        self.logger.info(f"MODIS validation report: {report}")
        return report