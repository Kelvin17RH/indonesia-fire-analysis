"""Spatial aggregation of satellite data to district level."""

import geopandas as gpd
import pandas as pd
import numpy as np
import xarray as xr
from pathlib import Path
from datetime import datetime
import logging
from typing import Dict, Any, List, Tuple, Optional, Union
from shapely.geometry import Point
import yaml
from tqdm import tqdm

from ..utils.logger import ProgressLogger


class SpatialAggregator:
    """Aggregate satellite data to administrative district level."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize spatial aggregator.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.processing_config = config.get('processing', {})
        
    def aggregate_fire_data(self, fire_data: Dict[str, xr.Dataset], 
                           districts_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Aggregate fire data to district level.
        
        Args:
            fire_data: Dictionary containing MODIS and VIIRS fire datasets
            districts_gdf: District boundaries GeoDataFrame
            
        Returns:
            GeoDataFrame with aggregated fire statistics by district
        """
        self.logger.info("Aggregating fire data to district level...")
        
        # Initialize result dataframes
        district_stats = districts_gdf.copy()
        
        # Process each fire dataset
        for sensor, dataset in fire_data.items():
            self.logger.info(f"Processing {sensor} fire data...")
            
            if 'fire_id' in dataset.dims and len(dataset.fire_id) > 0:
                # Point data (active fire locations)
                sensor_stats = self._aggregate_point_fire_data(dataset, districts_gdf, sensor)
            else:
                # Gridded data
                sensor_stats = self._aggregate_gridded_fire_data(dataset, districts_gdf, sensor)
            
            # Merge with district stats
            district_stats = district_stats.merge(
                sensor_stats, on='district_id', how='left', suffixes=('', f'_{sensor}')
            )
        
        # Calculate combined statistics
        district_stats = self._calculate_combined_fire_stats(district_stats, list(fire_data.keys()))
        
        return district_stats
    
    def _aggregate_point_fire_data(self, fire_dataset: xr.Dataset, 
                                  districts_gdf: gpd.GeoDataFrame, 
                                  sensor: str) -> pd.DataFrame:
        """
        Aggregate point fire data to districts.
        
        Args:
            fire_dataset: Fire point dataset
            districts_gdf: District boundaries
            sensor: Sensor name (modis/viirs)
            
        Returns:
            DataFrame with aggregated statistics
        """
        if len(fire_dataset.fire_id) == 0:
            # Return empty stats for all districts
            return self._create_empty_fire_stats(districts_gdf, sensor)
        
        # Convert fire points to GeoDataFrame
        fire_points = []
        for i in range(len(fire_dataset.fire_id)):
            point_data = {
                'geometry': Point(float(fire_dataset.longitude[i]), float(fire_dataset.latitude[i])),
                'frp': float(fire_dataset.frp[i]) if 'frp' in fire_dataset else 0.0,
                'confidence': float(fire_dataset.confidence[i]) if 'confidence' in fire_dataset else 0,
                'datetime': pd.to_datetime(fire_dataset.datetime[i].values) if 'datetime' in fire_dataset else None
            }
            
            # Add sensor-specific attributes
            if sensor.lower() == 'viirs':
                point_data.update({
                    'bright_ti4': float(fire_dataset.bright_ti4[i]) if 'bright_ti4' in fire_dataset else 0,
                    'bright_ti5': float(fire_dataset.bright_ti5[i]) if 'bright_ti5' in fire_dataset else 0,
                    'fire_type': int(fire_dataset.fire_type[i]) if 'fire_type' in fire_dataset else 0
                })
            elif sensor.lower() == 'modis':
                point_data.update({
                    'brightness': float(fire_dataset.brightness[i]) if 'brightness' in fire_dataset else 0
                })
            
            fire_points.append(point_data)
        
        fire_gdf = gpd.GeoDataFrame(fire_points, crs='EPSG:4326')
        
        # Ensure same CRS
        if fire_gdf.crs != districts_gdf.crs:
            fire_gdf = fire_gdf.to_crs(districts_gdf.crs)
        
        # Spatial join with districts
        fire_with_districts = gpd.sjoin(fire_gdf, districts_gdf[['district_id', 'geometry']], 
                                       how='left', predicate='within')
        
        # Aggregate statistics by district
        progress = ProgressLogger(
            total_items=len(districts_gdf),
            operation_name=f"{sensor} fire aggregation"
        )
        
        district_fire_stats = []
        
        for _, district in districts_gdf.iterrows():
            district_id = district['district_id']
            district_fires = fire_with_districts[fire_with_districts['district_id'] == district_id]
            
            # Basic fire statistics
            fire_count = len(district_fires)
            total_frp = district_fires['frp'].sum() if fire_count > 0 else 0.0
            mean_frp = district_fires['frp'].mean() if fire_count > 0 else 0.0
            max_frp = district_fires['frp'].max() if fire_count > 0 else 0.0
            
            # Confidence statistics
            high_conf_fires = len(district_fires[district_fires['confidence'] >= 7]) if sensor.lower() == 'modis' else \
                             len(district_fires[district_fires['confidence'] >= 3]) if sensor.lower() == 'viirs' else 0
            
            # Temporal statistics
            if fire_count > 0 and 'datetime' in district_fires.columns:
                first_fire = district_fires['datetime'].min()
                last_fire = district_fires['datetime'].max()
                fire_days = district_fires['datetime'].dt.date.nunique()
            else:
                first_fire = None
                last_fire = None
                fire_days = 0
            
            # Fire density (fires per km²)
            fire_density = fire_count / district['area_km2'] if district['area_km2'] > 0 else 0
            
            # Sensor-specific statistics
            sensor_stats = {}
            if sensor.lower() == 'viirs' and fire_count > 0:
                sensor_stats.update({
                    f'vegetation_fires_{sensor}': len(district_fires[district_fires['fire_type'] == 0]),
                    f'mean_bright_ti4_{sensor}': district_fires['bright_ti4'].mean(),
                    f'mean_bright_ti5_{sensor}': district_fires['bright_ti5'].mean()
                })
            elif sensor.lower() == 'modis' and fire_count > 0:
                sensor_stats.update({
                    f'mean_brightness_{sensor}': district_fires['brightness'].mean()
                })
            
            stats = {
                'district_id': district_id,
                f'fire_count_{sensor}': fire_count,
                f'total_frp_{sensor}': total_frp,
                f'mean_frp_{sensor}': mean_frp,
                f'max_frp_{sensor}': max_frp,
                f'high_conf_fires_{sensor}': high_conf_fires,
                f'fire_density_{sensor}': fire_density,
                f'fire_days_{sensor}': fire_days,
                f'first_fire_{sensor}': first_fire,
                f'last_fire_{sensor}': last_fire,
                **sensor_stats
            }
            
            district_fire_stats.append(stats)
            progress.update()
        
        progress.complete()
        
        return pd.DataFrame(district_fire_stats)
    
    def _aggregate_gridded_fire_data(self, fire_dataset: xr.Dataset, 
                                    districts_gdf: gpd.GeoDataFrame, 
                                    sensor: str) -> pd.DataFrame:
        """
        Aggregate gridded fire data to districts.
        
        Args:
            fire_dataset: Gridded fire dataset
            districts_gdf: District boundaries
            sensor: Sensor name
            
        Returns:
            DataFrame with aggregated statistics
        """
        self.logger.info(f"Aggregating gridded {sensor} data...")
        
        # For gridded data, we need to mask by district boundaries
        # This is a simplified approach - in practice, you'd use more sophisticated methods
        
        district_stats = []
        
        for _, district in districts_gdf.iterrows():
            district_id = district['district_id']
            
            # Create mask for district area
            # This is simplified - you'd typically use rasterio.mask or similar
            bounds = district.geometry.bounds
            min_lon, min_lat, max_lon, max_lat = bounds
            
            # Subset dataset to district bounds
            district_data = fire_dataset.sel(
                lat=slice(min_lat, max_lat),
                lon=slice(min_lon, max_lon)
            )
            
            # Calculate statistics
            if 'fire_mask' in district_data:
                fire_pixels = (district_data['fire_mask'] > 6).sum().values
                total_fire_pixels = int(fire_pixels) if not np.isnan(fire_pixels) else 0
            else:
                total_fire_pixels = 0
            
            if 'MaxFRP' in district_data:
                total_frp = float(district_data['MaxFRP'].sum().values)
                mean_frp = float(district_data['MaxFRP'].mean().values)
            else:
                total_frp = 0.0
                mean_frp = 0.0
            
            stats = {
                'district_id': district_id,
                f'fire_pixels_{sensor}': total_fire_pixels,
                f'total_frp_gridded_{sensor}': total_frp,
                f'mean_frp_gridded_{sensor}': mean_frp
            }
            
            district_stats.append(stats)
        
        return pd.DataFrame(district_stats)
    
    def aggregate_co_data(self, co_data: xr.Dataset, 
                         districts_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Aggregate CO data to district level.
        
        Args:
            co_data: CO dataset
            districts_gdf: District boundaries
            
        Returns:
            GeoDataFrame with aggregated CO statistics by district
        """
        self.logger.info("Aggregating CO data to district level...")
        
        district_co_stats = []
        
        progress = ProgressLogger(
            total_items=len(districts_gdf),
            operation_name="CO data aggregation"
        )
        
        for _, district in districts_gdf.iterrows():
            district_id = district['district_id']
            
            # Get district bounds
            bounds = district.geometry.bounds
            min_lon, min_lat, max_lon, max_lat = bounds
            
            # Subset CO data to district bounds
            try:
                district_co = co_data.sel(
                    lat=slice(min_lat, max_lat),
                    lon=slice(min_lon, max_lon)
                )
                
                # Calculate CO statistics
                co_stats = self._calculate_co_statistics(district_co, district_id)
                
            except Exception as e:
                self.logger.warning(f"Failed to process CO data for district {district_id}: {e}")
                co_stats = self._create_empty_co_stats(district_id)
            
            district_co_stats.append(co_stats)
            progress.update()
        
        progress.complete()
        
        # Merge with districts
        co_stats_df = pd.DataFrame(district_co_stats)
        result_gdf = districts_gdf.merge(co_stats_df, on='district_id', how='left')
        
        return result_gdf
    
    def _calculate_co_statistics(self, co_data: xr.Dataset, district_id: int) -> Dict[str, Any]:
        """
        Calculate CO statistics for a district.
        
        Args:
            co_data: CO data subset for district
            district_id: District ID
            
        Returns:
            Dictionary with CO statistics
        """
        stats = {'district_id': district_id}
        
        # Find CO variables
        co_vars = [var for var in co_data.data_vars if 'co' in var.lower()]
        
        for var in co_vars:
            if co_data[var].size > 0:
                # Remove invalid values
                valid_data = co_data[var].where(co_data[var] > 0)
                
                if valid_data.count() > 0:
                    stats.update({
                        f'{var}_mean': float(valid_data.mean()),
                        f'{var}_std': float(valid_data.std()),
                        f'{var}_min': float(valid_data.min()),
                        f'{var}_max': float(valid_data.max()),
                        f'{var}_median': float(valid_data.median()),
                        f'{var}_p95': float(valid_data.quantile(0.95)),
                        f'{var}_valid_pixels': int(valid_data.count())
                    })
                    
                    # Temporal statistics
                    if 'time' in co_data.dims:
                        time_series = valid_data.mean(dim=['lat', 'lon'])
                        if time_series.count() > 0:
                            stats.update({
                                f'{var}_temporal_mean': float(time_series.mean()),
                                f'{var}_temporal_std': float(time_series.std()),
                                f'{var}_temporal_trend': self._calculate_trend(time_series)
                            })
                else:
                    # No valid data
                    for stat in ['mean', 'std', 'min', 'max', 'median', 'p95']:
                        stats[f'{var}_{stat}'] = 0.0
                    stats[f'{var}_valid_pixels'] = 0
        
        return stats
    
    def _calculate_trend(self, time_series: xr.DataArray) -> float:
        """
        Calculate temporal trend in time series.
        
        Args:
            time_series: Time series data
            
        Returns:
            Trend slope (units per day)
        """
        try:
            if len(time_series) < 3:
                return 0.0
            
            # Simple linear trend
            x = np.arange(len(time_series))
            y = time_series.values
            
            # Remove NaN values
            valid_mask = ~np.isnan(y)
            if np.sum(valid_mask) < 3:
                return 0.0
            
            x_valid = x[valid_mask]
            y_valid = y[valid_mask]
            
            # Calculate trend
            trend = np.polyfit(x_valid, y_valid, 1)[0]
            return float(trend)
            
        except Exception:
            return 0.0
    
    def combine_datasets(self, fire_stats: gpd.GeoDataFrame, 
                        co_stats: gpd.GeoDataFrame,
                        districts_gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Combine fire and CO datasets with district information.
        
        Args:
            fire_stats: Aggregated fire statistics
            co_stats: Aggregated CO statistics  
            districts_gdf: Original district boundaries
            
        Returns:
            Combined GeoDataFrame
        """
        self.logger.info("Combining fire and CO datasets...")
        
        # Start with district boundaries
        combined_gdf = districts_gdf.copy()
        
        # Merge fire statistics
        fire_cols = [col for col in fire_stats.columns if col != 'geometry']
        combined_gdf = combined_gdf.merge(
            fire_stats[fire_cols], on='district_id', how='left', suffixes=('', '_fire')
        )
        
        # Merge CO statistics
        co_cols = [col for col in co_stats.columns if col not in ['geometry', 'district_id']]
        co_data = co_stats[['district_id'] + co_cols]
        combined_gdf = combined_gdf.merge(
            co_data, on='district_id', how='left', suffixes=('', '_co')
        )
        
        # Calculate derived metrics
        combined_gdf = self._calculate_derived_metrics(combined_gdf)
        
        return combined_gdf
    
    def _calculate_derived_metrics(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Calculate derived metrics from fire and CO data.
        
        Args:
            gdf: Combined GeoDataFrame
            
        Returns:
            GeoDataFrame with derived metrics
        """
        # Fire intensity metrics
        fire_cols = [col for col in gdf.columns if 'fire_count' in col]
        if fire_cols:
            gdf['total_fires'] = gdf[fire_cols].sum(axis=1)
        
        frp_cols = [col for col in gdf.columns if 'total_frp' in col and 'gridded' not in col]
        if frp_cols:
            gdf['total_frp_all'] = gdf[frp_cols].sum(axis=1)
        
        # CO enhancement during fire periods
        # This would require temporal analysis in a full implementation
        
        # Fire-CO correlation metrics
        # This would be calculated from time series data
        
        return gdf
    
    def export_data(self, data: gpd.GeoDataFrame, output_path: Path, 
                   format_type: str) -> None:
        """
        Export data in specified format.
        
        Args:
            data: Data to export
            output_path: Output file path
            format_type: Export format (csv, geojson, netcdf, parquet)
        """
        self.logger.info(f"Exporting data to {output_path} in {format_type} format...")
        
        try:
            if format_type.lower() == 'csv':
                # Export without geometry for CSV
                df = pd.DataFrame(data.drop(columns='geometry'))
                df.to_csv(output_path, index=False)
                
            elif format_type.lower() == 'geojson':
                data.to_file(output_path, driver='GeoJSON')
                
            elif format_type.lower() == 'parquet':
                # Convert to parquet (preserving geometry)
                data.to_parquet(output_path)
                
            elif format_type.lower() == 'netcdf':
                # Convert to xarray and save as NetCDF
                # This requires careful handling of geometries
                df = pd.DataFrame(data.drop(columns='geometry'))
                ds = df.to_xarray()
                ds.to_netcdf(output_path)
            
            self.logger.info(f"Successfully exported to {output_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to export to {format_type}: {e}")
            raise
    
    def generate_summary_statistics(self, data: gpd.GeoDataFrame) -> Dict[str, Any]:
        """
        Generate summary statistics for the combined dataset.
        
        Args:
            data: Combined dataset
            
        Returns:
            Summary statistics dictionary
        """
        summary = {
            'dataset_info': {
                'total_districts': len(data),
                'provinces': data['province_name'].nunique(),
                'temporal_coverage': self._get_temporal_coverage(data),
                'spatial_coverage': {
                    'bbox': data.total_bounds.tolist(),
                    'total_area_km2': data['area_km2'].sum()
                }
            },
            'fire_statistics': self._summarize_fire_data(data),
            'co_statistics': self._summarize_co_data(data),
            'correlations': self._calculate_correlations(data)
        }
        
        return summary
    
    def _get_temporal_coverage(self, data: gpd.GeoDataFrame) -> Dict[str, str]:
        """Get temporal coverage from first/last fire dates."""
        date_cols = [col for col in data.columns if 'first_fire' in col or 'last_fire' in col]
        
        if not date_cols:
            return {'start': 'N/A', 'end': 'N/A'}
        
        all_dates = []
        for col in date_cols:
            valid_dates = data[col].dropna()
            all_dates.extend(valid_dates.tolist())
        
        if all_dates:
            return {
                'start': str(min(all_dates).date()),
                'end': str(max(all_dates).date())
            }
        return {'start': 'N/A', 'end': 'N/A'}
    
    def _summarize_fire_data(self, data: gpd.GeoDataFrame) -> Dict[str, Any]:
        """Summarize fire statistics."""
        fire_summary = {}
        
        # Total fires by sensor
        fire_count_cols = [col for col in data.columns if 'fire_count' in col]
        for col in fire_count_cols:
            sensor = col.split('_')[-1]
            fire_summary[f'total_fires_{sensor}'] = int(data[col].sum())
            fire_summary[f'districts_with_fires_{sensor}'] = int((data[col] > 0).sum())
        
        # FRP statistics
        frp_cols = [col for col in data.columns if 'total_frp' in col]
        for col in frp_cols:
            fire_summary[f'{col}_total'] = float(data[col].sum())
            fire_summary[f'{col}_mean'] = float(data[col].mean())
        
        return fire_summary
    
    def _summarize_co_data(self, data: gpd.GeoDataFrame) -> Dict[str, Any]:
        """Summarize CO statistics."""
        co_summary = {}
        
        co_cols = [col for col in data.columns if 'co_' in col.lower() and '_mean' in col]
        for col in co_cols:
            co_summary[f'{col}_overall_mean'] = float(data[col].mean())
            co_summary[f'{col}_overall_std'] = float(data[col].std())
        
        return co_summary
    
    def _calculate_correlations(self, data: gpd.GeoDataFrame) -> Dict[str, float]:
        """Calculate correlations between fire and CO variables."""
        correlations = {}
        
        fire_cols = [col for col in data.columns if 'fire_count' in col]
        co_cols = [col for col in data.columns if 'co_' in col.lower() and '_mean' in col]
        
        for fire_col in fire_cols:
            for co_col in co_cols:
                if data[fire_col].std() > 0 and data[co_col].std() > 0:
                    corr = data[fire_col].corr(data[co_col])
                    if not np.isnan(corr):
                        correlations[f'{fire_col}_vs_{co_col}'] = float(corr)
        
        return correlations
    
    def _create_empty_fire_stats(self, districts_gdf: gpd.GeoDataFrame, 
                                sensor: str) -> pd.DataFrame:
        """Create empty fire statistics for districts."""
        stats = []
        for _, district in districts_gdf.iterrows():
            stats.append({
                'district_id': district['district_id'],
                f'fire_count_{sensor}': 0,
                f'total_frp_{sensor}': 0.0,
                f'mean_frp_{sensor}': 0.0,
                f'max_frp_{sensor}': 0.0,
                f'high_conf_fires_{sensor}': 0,
                f'fire_density_{sensor}': 0.0,
                f'fire_days_{sensor}': 0,
                f'first_fire_{sensor}': None,
                f'last_fire_{sensor}': None
            })
        return pd.DataFrame(stats)
    
    def _create_empty_co_stats(self, district_id: int) -> Dict[str, Any]:
        """Create empty CO statistics for a district."""
        return {
            'district_id': district_id,
            'co_total_mean': 0.0,
            'co_total_std': 0.0,
            'co_total_min': 0.0,
            'co_total_max': 0.0,
            'co_total_valid_pixels': 0
        }
    
    def _calculate_combined_fire_stats(self, data: gpd.GeoDataFrame, 
                                     sensors: List[str]) -> gpd.GeoDataFrame:
        """Calculate combined statistics across sensors."""
        # Total fires across all sensors
        fire_count_cols = [f'fire_count_{sensor}' for sensor in sensors if f'fire_count_{sensor}' in data.columns]
        if fire_count_cols:
            data['total_fires_all_sensors'] = data[fire_count_cols].sum(axis=1)
        
        # Total FRP across all sensors
        frp_cols = [f'total_frp_{sensor}' for sensor in sensors if f'total_frp_{sensor}' in data.columns]
        if frp_cols:
            data['total_frp_all_sensors'] = data[frp_cols].sum(axis=1)
        
        return data