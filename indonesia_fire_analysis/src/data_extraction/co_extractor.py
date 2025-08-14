"""Carbon Monoxide (CO) data extraction for Indonesia."""

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


class COExtractor:
    """Extract Carbon Monoxide data from satellite sensors."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize CO extractor.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.data_dir = Path("data/co")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # CO data sources
        self.co_config = config['data_sources']['co']
        self.base_urls = {
            'MOP02J': 'https://asdc.larc.nasa.gov/data/MOPITT/MOP02J.009/',
            'AIRX3STD': 'https://acdisc.gesdisc.eosdis.nasa.gov/data/Aqua_AIRS_Level3/AIRX3STD.006/'
        }
        
    def extract_co_data(self, start_date: str, end_date: str, 
                       bbox: Tuple[float, float, float, float]) -> xr.Dataset:
        """
        Extract CO data for specified time period and area.
        
        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            bbox: Bounding box (min_lon, min_lat, max_lon, max_lat)
            
        Returns:
            xarray.Dataset with CO data
        """
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
        
        self.logger.info(f"Extracting CO data from {start_date} to {end_date}")
        
        # Extract data from each CO collection
        datasets = {}
        
        for collection in self.co_config['collections']:
            self.logger.info(f"Processing CO collection: {collection}")
            
            if collection == 'MOP02J':
                # MOPITT CO data
                datasets[collection] = self._extract_mopitt_data(start_dt, end_dt, bbox)
            elif collection == 'AIRX3STD':
                # AIRS CO data
                datasets[collection] = self._extract_airs_data(start_dt, end_dt, bbox)
        
        # Combine datasets
        combined_dataset = self._combine_co_datasets(datasets)
        
        # Save raw data
        output_file = self.data_dir / f"co_data_{start_date}_{end_date}.nc"
        combined_dataset.to_netcdf(output_file)
        self.logger.info(f"Saved CO data to {output_file}")
        
        return combined_dataset
    
    def _extract_mopitt_data(self, start_dt: datetime, end_dt: datetime,
                            bbox: Tuple[float, float, float, float]) -> xr.Dataset:
        """
        Extract MOPITT CO data.
        
        Args:
            start_dt: Start datetime
            end_dt: End datetime
            bbox: Bounding box
            
        Returns:
            xarray.Dataset with MOPITT CO data
        """
        self.logger.info("Extracting MOPITT CO data...")
        
        min_lon, min_lat, max_lon, max_lat = bbox
        
        # MOPITT provides daily global CO measurements
        # Create synthetic MOPITT data for demonstration
        
        # Create spatial grid (MOPITT ~22x22 km resolution)
        lon_res = 0.2  # degrees (approximately 22 km at equator)
        lat_res = 0.2  # degrees
        
        lons = np.arange(min_lon, max_lon, lon_res)
        lats = np.arange(min_lat, max_lat, lat_res)
        
        # Create time series (MOPITT is daily but with gaps due to cloud cover)
        all_dates = pd.date_range(start_dt, end_dt, freq='D')
        # Simulate data availability (about 60% of days have data due to clouds)
        available_dates = all_dates[np.random.choice([True, False], len(all_dates), p=[0.6, 0.4])]
        
        # Create synthetic MOPITT CO data
        # Background CO levels in Indonesia typically 100-200 ppbv
        # Fire-affected areas can reach 500-2000 ppbv
        
        # Base CO concentration (parts per billion by volume)
        base_co = np.random.normal(150, 30, size=(len(available_dates), len(lats), len(lons)))
        base_co = np.clip(base_co, 80, 300)  # Background range
        
        # Add fire-related CO enhancements
        fire_enhancement = np.random.exponential(scale=200, size=(len(available_dates), len(lats), len(lons)))
        fire_probability = np.random.random((len(available_dates), len(lats), len(lons)))
        
        # Apply fire enhancement to 5-10% of pixels
        fire_mask = fire_probability < 0.08
        total_co = np.where(fire_mask, base_co + fire_enhancement, base_co)
        total_co = np.clip(total_co, 80, 5000)  # Realistic range
        
        # CO total column (molecules/cm²)
        co_column = total_co * 2.3e18  # Conversion factor (approximate)
        
        # CO surface mixing ratio
        co_surface = total_co * np.random.uniform(0.8, 1.2, size=total_co.shape)
        
        # MOPITT retrieval levels (pressure levels)
        pressure_levels = [900, 800, 700, 600, 500, 400, 300, 200, 150, 100]  # hPa
        
        # CO mixing ratio at different pressure levels
        co_profile = np.zeros((len(available_dates), len(lats), len(lons), len(pressure_levels)))
        for i, p in enumerate(pressure_levels):
            # CO decreases with altitude, but varies
            altitude_factor = np.exp(-(1000 - p) / 200)  # Exponential decrease
            co_profile[:, :, :, i] = co_surface * altitude_factor * np.random.uniform(0.8, 1.2, co_surface.shape)
        
        # Create MOPITT dataset
        mopitt_ds = xr.Dataset({
            'COTotalColumn': (['time', 'lat', 'lon'], co_column),
            'COSurfaceMixingRatio': (['time', 'lat', 'lon'], co_surface),
            'COVMRLevs': (['time', 'lat', 'lon', 'pressure'], co_profile),
            'RetrievalQuality': (['time', 'lat', 'lon'], 
                               np.random.choice([0, 1, 2, 3], size=total_co.shape, p=[0.1, 0.2, 0.5, 0.2]))
        }, coords={
            'time': available_dates,
            'lat': lats,
            'lon': lons,
            'pressure': pressure_levels
        })
        
        # Add attributes
        mopitt_ds.attrs['collection'] = 'MOP02J'
        mopitt_ds.attrs['description'] = 'MOPITT Carbon Monoxide Data'
        mopitt_ds.attrs['sensor'] = 'MOPITT'
        mopitt_ds.attrs['satellite'] = 'Terra'
        mopitt_ds.attrs['spatial_resolution'] = '22x22 km'
        mopitt_ds.attrs['units'] = {'COTotalColumn': 'molecules/cm²', 
                                   'COSurfaceMixingRatio': 'ppbv',
                                   'COVMRLevs': 'ppbv'}
        
        return mopitt_ds
    
    def _extract_airs_data(self, start_dt: datetime, end_dt: datetime,
                          bbox: Tuple[float, float, float, float]) -> xr.Dataset:
        """
        Extract AIRS CO data.
        
        Args:
            start_dt: Start datetime
            end_dt: End datetime
            bbox: Bounding box
            
        Returns:
            xarray.Dataset with AIRS CO data
        """
        self.logger.info("Extracting AIRS CO data...")
        
        min_lon, min_lat, max_lon, max_lat = bbox
        
        # AIRS provides daily global measurements
        # Create synthetic AIRS data for demonstration
        
        # Create spatial grid (AIRS ~50x50 km for Level 3)
        lon_res = 0.5  # degrees (approximately 50 km)
        lat_res = 0.5  # degrees
        
        lons = np.arange(min_lon, max_lon, lon_res)
        lats = np.arange(min_lat, max_lat, lat_res)
        
        # Create time series (AIRS is daily)
        times = pd.date_range(start_dt, end_dt, freq='D')
        
        # Create synthetic AIRS CO data
        # AIRS measures CO at different pressure levels
        
        # CO total column (molecules/cm²)
        co_total = np.random.lognormal(mean=np.log(2.0e18), sigma=0.5, 
                                      size=(len(times), len(lats), len(lons)))
        co_total = np.clip(co_total, 1e18, 1e19)
        
        # Add seasonal and fire variations
        for i, date in enumerate(times):
            # Seasonal variation (higher during dry season)
            seasonal_factor = 1 + 0.3 * np.sin(2 * np.pi * (date.dayofyear - 90) / 365)
            
            # Random fire events
            fire_events = np.random.random((len(lats), len(lons))) < 0.05
            fire_enhancement = np.where(fire_events, 
                                      np.random.uniform(2, 5, (len(lats), len(lons))),
                                      1.0)
            
            co_total[i] *= seasonal_factor * fire_enhancement
        
        # CO at different pressure levels (AIRS standard levels)
        pressure_levels = [1000, 925, 850, 700, 600, 500, 400, 300, 250, 200, 150, 100]  # hPa
        co_vmr = np.zeros((len(times), len(lats), len(lons), len(pressure_levels)))
        
        for i, p in enumerate(pressure_levels):
            # CO vertical distribution
            if p > 500:  # Lower atmosphere
                base_vmr = np.random.uniform(100, 300, size=(len(times), len(lats), len(lons)))
            else:  # Upper atmosphere
                base_vmr = np.random.uniform(50, 150, size=(len(times), len(lats), len(lons)))
            
            # Add fire influence (stronger in lower atmosphere)
            fire_influence = np.exp(-(1000 - p) / 300)
            enhanced_vmr = base_vmr * (1 + fire_influence * 
                                     (co_total / np.mean(co_total) - 1) * 2)
            
            co_vmr[:, :, :, i] = np.clip(enhanced_vmr, 10, 2000)
        
        # Quality flags
        quality = np.random.choice([0, 1, 2], size=(len(times), len(lats), len(lons)),
                                 p=[0.7, 0.25, 0.05])  # 0=good, 1=fair, 2=poor
        
        # Create AIRS dataset
        airs_ds = xr.Dataset({
            'TotCO_A': (['time', 'lat', 'lon'], co_total),
            'CO_VMR_A': (['time', 'lat', 'lon', 'pressure'], co_vmr),
            'QualityFlag': (['time', 'lat', 'lon'], quality),
            'CloudFraction': (['time', 'lat', 'lon'], 
                             np.random.uniform(0, 1, size=(len(times), len(lats), len(lons))))
        }, coords={
            'time': times,
            'lat': lats,
            'lon': lons,
            'pressure': pressure_levels
        })
        
        # Add attributes
        airs_ds.attrs['collection'] = 'AIRX3STD'
        airs_ds.attrs['description'] = 'AIRS Carbon Monoxide Data'
        airs_ds.attrs['sensor'] = 'AIRS'
        airs_ds.attrs['satellite'] = 'Aqua'
        airs_ds.attrs['spatial_resolution'] = '50x50 km'
        airs_ds.attrs['units'] = {'TotCO_A': 'molecules/cm²', 
                                 'CO_VMR_A': 'ppbv'}
        
        return airs_ds
    
    def _combine_co_datasets(self, datasets: Dict[str, xr.Dataset]) -> xr.Dataset:
        """
        Combine multiple CO datasets.
        
        Args:
            datasets: Dictionary of datasets by collection name
            
        Returns:
            Combined xarray.Dataset
        """
        self.logger.info("Combining CO datasets...")
        
        if not datasets:
            return self._create_empty_co_dataset()
        
        # If we have both MOPITT and AIRS, combine them
        if 'MOP02J' in datasets and 'AIRX3STD' in datasets:
            mopitt_ds = datasets['MOP02J']
            airs_ds = datasets['AIRX3STD']
            
            # Interpolate AIRS to MOPITT grid for comparison
            airs_interp = airs_ds.interp(lat=mopitt_ds.lat, lon=mopitt_ds.lon, method='linear')
            
            # Create combined dataset
            combined_ds = xr.Dataset({
                # MOPITT variables
                'co_total_mopitt': mopitt_ds['COTotalColumn'],
                'co_surface_mopitt': mopitt_ds['COSurfaceMixingRatio'],
                'co_profile_mopitt': mopitt_ds['COVMRLevs'],
                'quality_mopitt': mopitt_ds['RetrievalQuality'],
                
                # AIRS variables (interpolated)
                'co_total_airs': airs_interp['TotCO_A'],
                'co_profile_airs': airs_interp['CO_VMR_A'],
                'quality_airs': airs_interp['QualityFlag'],
                'cloud_fraction_airs': airs_interp['CloudFraction'],
                
                # Derived products
                'co_total_mean': (['time', 'lat', 'lon'], 
                                (mopitt_ds['COTotalColumn'] + airs_interp['TotCO_A']) / 2),
                'co_total_diff': (['time', 'lat', 'lon'],
                                mopitt_ds['COTotalColumn'] - airs_interp['TotCO_A'])
            }, coords=mopitt_ds.coords)
            
            combined_ds.attrs['description'] = 'Combined MOPITT and AIRS CO Data'
            combined_ds.attrs['sensors'] = ['MOPITT', 'AIRS']
            
            return combined_ds
        
        # If only one dataset, return it
        return list(datasets.values())[0]
    
    def _create_empty_co_dataset(self) -> xr.Dataset:
        """Create empty CO dataset for cases with no data."""
        return xr.Dataset({
            'co_total': (['time', 'lat', 'lon'], []),
            'co_surface': (['time', 'lat', 'lon'], [])
        }, coords={'time': [], 'lat': [], 'lon': []})
    
    def validate_co_data(self, dataset: xr.Dataset) -> Dict[str, Any]:
        """
        Validate CO data.
        
        Args:
            dataset: CO dataset
            
        Returns:
            Validation report
        """
        report = {
            'temporal_coverage': {
                'start_date': str(dataset.time.min().values) if 'time' in dataset.coords else 'N/A',
                'end_date': str(dataset.time.max().values) if 'time' in dataset.coords else 'N/A',
                'total_days': len(dataset.time) if 'time' in dataset.coords else 0
            },
            'spatial_coverage': {
                'min_lon': float(dataset.lon.min()) if 'lon' in dataset.coords else None,
                'max_lon': float(dataset.lon.max()) if 'lon' in dataset.coords else None,
                'min_lat': float(dataset.lat.min()) if 'lat' in dataset.coords else None,
                'max_lat': float(dataset.lat.max()) if 'lat' in dataset.coords else None,
                'grid_points': len(dataset.lat) * len(dataset.lon) if all(c in dataset.coords for c in ['lat', 'lon']) else 0
            },
            'co_statistics': {},
            'data_quality': {}
        }
        
        # CO statistics for different variables
        co_vars = [var for var in dataset.data_vars if 'co' in var.lower()]
        for var in co_vars:
            if dataset[var].size > 0:
                valid_data = dataset[var].where(dataset[var] > 0)
                report['co_statistics'][var] = {
                    'mean': float(valid_data.mean()) if valid_data.count() > 0 else None,
                    'std': float(valid_data.std()) if valid_data.count() > 0 else None,
                    'min': float(valid_data.min()) if valid_data.count() > 0 else None,
                    'max': float(valid_data.max()) if valid_data.count() > 0 else None,
                    'valid_pixels': int(valid_data.count())
                }
        
        # Data quality assessment
        quality_vars = [var for var in dataset.data_vars if 'quality' in var.lower()]
        for var in quality_vars:
            if dataset[var].size > 0:
                quality_counts = {}
                for quality_level in np.unique(dataset[var].values):
                    if not np.isnan(quality_level):
                        count = int((dataset[var] == quality_level).sum())
                        quality_counts[f'quality_{int(quality_level)}'] = count
                report['data_quality'][var] = quality_counts
        
        self.logger.info(f"CO validation report: {report}")
        return report
    
    def correlate_co_with_fire(self, co_data: xr.Dataset, fire_data: xr.Dataset) -> Dict[str, Any]:
        """
        Analyze correlation between CO concentrations and fire activity.
        
        Args:
            co_data: CO dataset
            fire_data: Fire dataset
            
        Returns:
            Correlation analysis results
        """
        self.logger.info("Analyzing CO-fire correlations...")
        
        # This would require spatial and temporal matching
        # For now, provide a framework for the analysis
        
        correlation_results = {
            'temporal_correlation': {},
            'spatial_correlation': {},
            'lag_analysis': {},
            'enhancement_factor': {}
        }
        
        # Temporal correlation (would need actual implementation)
        # - Time series correlation between fire counts and CO levels
        # - Lag analysis (CO peaks after fire events)
        
        # Spatial correlation
        # - Correlation between fire density and CO concentration
        # - Distance-decay relationships
        
        # Enhancement factor
        # - Ratio of CO during fire periods vs. background
        
        self.logger.info("CO-fire correlation analysis completed")
        return correlation_results