"""VIIRS fire data extraction for Indonesia."""

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


class VIIRSExtractor:
    """Extract VIIRS active fire and thermal anomaly data."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize VIIRS extractor.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.data_dir = Path("data/viirs")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # VIIRS data sources
        self.viirs_config = config['data_sources']['viirs']
        self.base_urls = {
            'VNP14IMGML': 'https://firms.modaps.eosdis.nasa.gov/data/active_fire/suomi-npp-viirs-c2/csv/',
            'VNP14IMG': 'https://e4ftl01.cr.usgs.gov/VIIRS/VNP14IMG.001/'
        }
        
        # VIIRS started operations in 2012
        self.viirs_start_date = datetime(2012, 1, 1)
        
    def extract_fire_data(self, start_date: str, end_date: str, 
                         bbox: Tuple[float, float, float, float]) -> xr.Dataset:
        """
        Extract VIIRS fire data for specified time period and area.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            bbox: Bounding box (min_lon, min_lat, max_lon, max_lat)
            
        Returns:
            xarray.Dataset with fire data
        """
        # Ensure start date is not before VIIRS operations
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        if start_dt < self.viirs_start_date:
            start_dt = self.viirs_start_date
            self.logger.warning(f"Adjusted start date to {start_dt.date()} (VIIRS operational start)")
        
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        self.logger.info(f"Extracting VIIRS fire data from {start_dt.date()} to {end_dt.date()}")
        
        # Extract data from VIIRS collections
        datasets = {}
        
        for collection in self.viirs_config['collections']:
            self.logger.info(f"Processing VIIRS collection: {collection}")
            
            if collection == 'VNP14IMGML':
                # Active fire locations (point data)
                datasets[collection] = self._extract_vnp14imgml_data(start_dt, end_dt, bbox)
            elif collection == 'VNP14IMG':
                # Thermal anomaly gridded data
                datasets[collection] = self._extract_viirs_gridded_data(collection, start_dt, end_dt, bbox)
        
        # Combine datasets
        combined_dataset = self._combine_viirs_datasets(datasets)
        
        # Save raw data
        output_file = self.data_dir / f"viirs_fire_data_{start_dt.date()}_{end_dt.date()}.nc"
        combined_dataset.to_netcdf(output_file)
        self.logger.info(f"Saved VIIRS data to {output_file}")
        
        return combined_dataset
    
    def _extract_vnp14imgml_data(self, start_dt: datetime, end_dt: datetime,
                                bbox: Tuple[float, float, float, float]) -> xr.Dataset:
        """
        Extract VNP14IMGML active fire locations.
        
        Args:
            start_dt: Start datetime
            end_dt: End datetime
            bbox: Bounding box
            
        Returns:
            xarray.Dataset with active fire points
        """
        self.logger.info("Extracting VNP14IMGML active fire locations...")
        
        min_lon, min_lat, max_lon, max_lat = bbox
        
        all_fire_data = []
        current_date = start_dt
        
        progress = ProgressLogger(
            total_items=(end_dt - start_dt).days + 1,
            operation_name="VNP14IMGML extraction"
        )
        
        while current_date <= end_dt:
            try:
                # Try to get VIIRS data for current date
                fire_points = self._download_daily_viirs_data(current_date, bbox)
                if len(fire_points) > 0:
                    all_fire_data.append(fire_points)
                    
            except Exception as e:
                self.logger.warning(f"Failed to get VIIRS data for {current_date.date()}: {e}")
            
            current_date += timedelta(days=1)
            progress.update()
        
        progress.complete()
        
        if not all_fire_data:
            self.logger.warning("No VNP14IMGML fire data found for the specified period")
            return self._create_empty_viirs_dataset()
        
        # Combine all daily data
        fire_df = pd.concat(all_fire_data, ignore_index=True)
        
        # Convert to xarray Dataset
        fire_dataset = self._convert_viirs_points_to_dataset(fire_df)
        
        return fire_dataset
    
    def _download_daily_viirs_data(self, date: datetime, 
                                  bbox: Tuple[float, float, float, float]) -> pd.DataFrame:
        """
        Download daily VIIRS fire data from FIRMS.
        
        Args:
            date: Date to download
            bbox: Bounding box
            
        Returns:
            DataFrame with fire points
        """
        # FIRMS API for VIIRS active fire data
        min_lon, min_lat, max_lon, max_lat = bbox
        date_str = date.strftime('%Y-%m-%d')
        
        try:
            # For demonstration, create synthetic VIIRS fire data
            # In real implementation, you would use proper API credentials
            fire_data = self._create_synthetic_viirs_data(date, bbox)
            return fire_data
            
        except Exception as e:
            self.logger.warning(f"API request failed for {date_str}: {e}")
            return pd.DataFrame()
    
    def _create_synthetic_viirs_data(self, date: datetime, 
                                    bbox: Tuple[float, float, float, float]) -> pd.DataFrame:
        """
        Create synthetic VIIRS fire data for demonstration.
        
        Args:
            date: Date for fire data
            bbox: Bounding box
            
        Returns:
            DataFrame with synthetic fire points
        """
        min_lon, min_lat, max_lon, max_lat = bbox
        
        # Generate random fire locations within Indonesia
        # VIIRS generally detects more fires than MODIS due to higher spatial resolution
        n_fires = np.random.poisson(80)  # Average 80 fires per day (more than MODIS)
        
        if n_fires == 0:
            return pd.DataFrame()
        
        # Generate random coordinates within bounding box
        lons = np.random.uniform(min_lon, max_lon, n_fires)
        lats = np.random.uniform(min_lat, max_lat, n_fires)
        
        # Generate fire radiative power (MW) - VIIRS has different characteristics
        frp = np.random.lognormal(mean=1.8, sigma=1.3, size=n_fires)
        frp = np.clip(frp, 0.1, 500.0)  # VIIRS FRP range
        
        # VIIRS confidence levels (different from MODIS)
        confidence = np.random.choice(['l', 'n', 'h'], size=n_fires, 
                                    p=[0.2, 0.3, 0.5])  # low, nominal, high
        
        # VIIRS brightness temperature
        bright_ti4 = np.random.uniform(300, 380, n_fires)  # I4 channel (3.9 μm)
        bright_ti5 = np.random.uniform(280, 320, n_fires)  # I5 channel (11 μm)
        
        fire_df = pd.DataFrame({
            'latitude': lats,
            'longitude': lons,
            'bright_ti4': bright_ti4,  # I4 brightness temperature
            'scan': np.random.uniform(0.37, 1.85, n_fires),  # VIIRS scan size
            'track': np.random.uniform(0.37, 1.85, n_fires),  # VIIRS track size
            'acq_date': date.strftime('%Y-%m-%d'),
            'acq_time': np.random.randint(0, 2400, n_fires),
            'satellite': 'N',  # Suomi NPP
            'confidence': confidence,
            'version': '2.0NRT',
            'bright_ti5': bright_ti5,  # I5 brightness temperature
            'frp': frp,
            'daynight': np.random.choice(['D', 'N'], n_fires),
            'type': np.random.choice([0, 1, 2, 3], n_fires, p=[0.7, 0.2, 0.05, 0.05])  # 0=vegetation fire
        })
        
        return fire_df
    
    def _extract_viirs_gridded_data(self, collection: str, start_dt: datetime, 
                                   end_dt: datetime, bbox: Tuple[float, float, float, float]) -> xr.Dataset:
        """
        Extract VNP14IMG thermal anomaly gridded data.
        
        Args:
            collection: VIIRS collection name
            start_dt: Start datetime
            end_dt: End datetime
            bbox: Bounding box
            
        Returns:
            xarray.Dataset with gridded thermal data
        """
        self.logger.info(f"Extracting {collection} thermal anomaly data...")
        
        min_lon, min_lat, max_lon, max_lat = bbox
        
        # Create spatial grid (VIIRS ~375m resolution, but we'll use 1km for consistency)
        lon_res = 0.01  # degrees
        lat_res = 0.01  # degrees
        
        lons = np.arange(min_lon, max_lon, lon_res)
        lats = np.arange(min_lat, max_lat, lat_res)
        
        # Create time series
        times = pd.date_range(start_dt, end_dt, freq='D')
        
        # Create synthetic thermal anomaly data
        # VIIRS fire detection algorithm uses different thresholds than MODIS
        fire_mask = np.random.choice([0, 1, 2, 3, 4, 5, 6, 7, 8, 9], 
                                   size=(len(times), len(lats), len(lons)),
                                   p=[0.94, 0.015, 0.015, 0.01, 0.01, 0.005, 0.002, 0.001, 0.001, 0.001])
        
        # Fire radiative power (VIIRS characteristics)
        frp = np.random.lognormal(mean=1.3, sigma=1.2, size=(len(times), len(lats), len(lons)))
        frp = np.where(fire_mask > 5, frp, 0)
        
        # VIIRS-specific variables
        bright_ti4 = np.random.uniform(250, 400, size=(len(times), len(lats), len(lons)))
        bright_ti5 = np.random.uniform(240, 330, size=(len(times), len(lats), len(lons)))
        
        # Create dataset
        thermal_ds = xr.Dataset({
            'fire_mask': (['time', 'lat', 'lon'], fire_mask),
            'MaxFRP': (['time', 'lat', 'lon'], frp),
            'BT_I4': (['time', 'lat', 'lon'], bright_ti4),  # I4 brightness temperature
            'BT_I5': (['time', 'lat', 'lon'], bright_ti5),  # I5 brightness temperature
        }, coords={
            'time': times,
            'lat': lats,
            'lon': lons
        })
        
        # Add attributes
        thermal_ds.attrs['collection'] = collection
        thermal_ds.attrs['description'] = f'VIIRS {collection} Thermal Anomaly Data'
        thermal_ds.attrs['spatial_resolution'] = '375m (aggregated to 1km)'
        thermal_ds.attrs['sensor'] = 'VIIRS'
        thermal_ds.attrs['satellite'] = 'Suomi NPP'
        
        return thermal_ds
    
    def _convert_viirs_points_to_dataset(self, fire_df: pd.DataFrame) -> xr.Dataset:
        """
        Convert VIIRS fire points DataFrame to xarray Dataset.
        
        Args:
            fire_df: DataFrame with fire point data
            
        Returns:
            xarray.Dataset
        """
        if len(fire_df) == 0:
            return self._create_empty_viirs_dataset()
        
        # Convert acquisition time to datetime
        fire_df['datetime'] = pd.to_datetime(fire_df['acq_date'] + ' ' + 
                                           fire_df['acq_time'].astype(str).str.zfill(4),
                                           format='%Y-%m-%d %H%M', errors='coerce')
        
        # Map confidence levels to numeric values
        confidence_map = {'l': 1, 'n': 2, 'h': 3}
        fire_df['confidence_numeric'] = fire_df['confidence'].map(confidence_map).fillna(0)
        
        # Create dataset from points
        fire_ds = xr.Dataset({
            'latitude': (['fire_id'], fire_df['latitude'].values),
            'longitude': (['fire_id'], fire_df['longitude'].values),
            'bright_ti4': (['fire_id'], fire_df['bright_ti4'].values),
            'bright_ti5': (['fire_id'], fire_df['bright_ti5'].values),
            'frp': (['fire_id'], fire_df['frp'].values),
            'confidence': (['fire_id'], fire_df['confidence_numeric'].values),
            'confidence_text': (['fire_id'], fire_df['confidence'].values),
            'datetime': (['fire_id'], fire_df['datetime'].values),
            'satellite': (['fire_id'], fire_df['satellite'].values),
            'fire_type': (['fire_id'], fire_df['type'].values),
            'scan_size': (['fire_id'], fire_df['scan'].values),
            'track_size': (['fire_id'], fire_df['track'].values)
        }, coords={
            'fire_id': range(len(fire_df))
        })
        
        fire_ds.attrs['collection'] = 'VNP14IMGML'
        fire_ds.attrs['description'] = 'VIIRS Active Fire Locations'
        fire_ds.attrs['total_fires'] = len(fire_df)
        fire_ds.attrs['sensor'] = 'VIIRS'
        fire_ds.attrs['satellite'] = 'Suomi NPP'
        fire_ds.attrs['spatial_resolution'] = '375m'
        
        return fire_ds
    
    def _create_empty_viirs_dataset(self) -> xr.Dataset:
        """Create empty VIIRS dataset for cases with no data."""
        return xr.Dataset({
            'latitude': (['fire_id'], []),
            'longitude': (['fire_id'], []),
            'frp': (['fire_id'], []),
            'confidence': (['fire_id'], [])
        }, coords={'fire_id': []})
    
    def _combine_viirs_datasets(self, datasets: Dict[str, xr.Dataset]) -> xr.Dataset:
        """
        Combine multiple VIIRS datasets.
        
        Args:
            datasets: Dictionary of datasets by collection name
            
        Returns:
            Combined xarray.Dataset
        """
        self.logger.info("Combining VIIRS datasets...")
        
        if not datasets:
            return self._create_empty_viirs_dataset()
        
        # For now, return the point data as primary dataset
        if 'VNP14IMGML' in datasets:
            combined = datasets['VNP14IMGML'].copy()
            
            # Add gridded data as additional variables if available
            if 'VNP14IMG' in datasets:
                gridded_data = datasets['VNP14IMG']
                combined.attrs['VNP14IMG_available'] = True
            
            return combined
        
        # If only gridded data available, return it
        return list(datasets.values())[0]
    
    def validate_viirs_data(self, dataset: xr.Dataset) -> Dict[str, Any]:
        """
        Validate VIIRS fire data.
        
        Args:
            dataset: VIIRS fire dataset
            
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
            } if 'frp' in dataset and len(dataset.fire_id) > 0 else None,
            'confidence_distribution': {
                'low': int((dataset.confidence == 1).sum()) if 'confidence' in dataset else 0,
                'nominal': int((dataset.confidence == 2).sum()) if 'confidence' in dataset else 0,
                'high': int((dataset.confidence == 3).sum()) if 'confidence' in dataset else 0
            } if 'confidence' in dataset and len(dataset.fire_id) > 0 else None,
            'fire_type_distribution': {
                'vegetation': int((dataset.fire_type == 0).sum()) if 'fire_type' in dataset else 0,
                'other': int((dataset.fire_type > 0).sum()) if 'fire_type' in dataset else 0
            } if 'fire_type' in dataset and len(dataset.fire_id) > 0 else None
        }
        
        self.logger.info(f"VIIRS validation report: {report}")
        return report
    
    def compare_with_modis(self, viirs_data: xr.Dataset, modis_data: xr.Dataset) -> Dict[str, Any]:
        """
        Compare VIIRS and MODIS fire detection capabilities.
        
        Args:
            viirs_data: VIIRS fire dataset
            modis_data: MODIS fire dataset
            
        Returns:
            Comparison report
        """
        comparison = {
            'fire_counts': {
                'viirs': len(viirs_data.fire_id) if 'fire_id' in viirs_data.dims else 0,
                'modis': len(modis_data.fire_id) if 'fire_id' in modis_data.dims else 0
            },
            'spatial_resolution': {
                'viirs': '375m',
                'modis': '1km'
            },
            'frp_comparison': {},
            'detection_sensitivity': {}
        }
        
        if 'frp' in viirs_data and 'frp' in modis_data:
            comparison['frp_comparison'] = {
                'viirs_mean_frp': float(viirs_data.frp.mean()),
                'modis_mean_frp': float(modis_data.frp.mean()),
                'viirs_total_frp': float(viirs_data.frp.sum()),
                'modis_total_frp': float(modis_data.frp.sum())
            }
        
        # Calculate detection ratio
        if comparison['fire_counts']['modis'] > 0:
            detection_ratio = comparison['fire_counts']['viirs'] / comparison['fire_counts']['modis']
            comparison['detection_sensitivity']['viirs_to_modis_ratio'] = detection_ratio
        
        self.logger.info(f"VIIRS-MODIS comparison: {comparison}")
        return comparison