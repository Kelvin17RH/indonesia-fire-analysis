"""Spatial boundary processing for Indonesia districts."""

import geopandas as gpd
import pandas as pd
import requests
from pathlib import Path
from typing import Tuple, Dict, Any
import logging
from shapely.geometry import box


class BoundaryProcessor:
    """Process Indonesia administrative boundaries at district level."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize boundary processor.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.data_dir = Path("data/boundaries")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
    def load_indonesia_districts(self) -> gpd.GeoDataFrame:
        """
        Load Indonesia district-level administrative boundaries.
        
        Returns:
            GeoDataFrame with district boundaries
        """
        boundaries_file = self.data_dir / "indonesia_districts.geojson"
        
        if boundaries_file.exists():
            self.logger.info("Loading existing district boundaries...")
            districts_gdf = gpd.read_file(boundaries_file)
        else:
            self.logger.info("Downloading district boundaries...")
            districts_gdf = self._download_indonesia_boundaries()
            
            # Save for future use
            districts_gdf.to_file(boundaries_file, driver="GeoJSON")
            self.logger.info(f"Saved boundaries to {boundaries_file}")
        
        # Ensure proper CRS
        target_crs = self.config['spatial']['crs']
        if districts_gdf.crs != target_crs:
            districts_gdf = districts_gdf.to_crs(target_crs)
        
        # Add area calculation
        districts_gdf['area_km2'] = districts_gdf.geometry.to_crs('EPSG:3857').area / 1e6
        
        # Standardize column names
        districts_gdf = self._standardize_columns(districts_gdf)
        
        return districts_gdf
    
    def _download_indonesia_boundaries(self) -> gpd.GeoDataFrame:
        """
        Download Indonesia district boundaries from online sources.
        
        Returns:
            GeoDataFrame with district boundaries
        """
        # Try multiple sources for Indonesia boundaries
        sources = [
            {
                'name': 'GADM',
                'url': 'https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_IDN_2.json',
                'level': 2  # District level
            },
            {
                'name': 'Natural Earth',
                'url': 'https://raw.githubusercontent.com/holtzy/The-Python-Graph-Gallery/master/static/data/Indonesia.geojson',
                'level': 1  # Province level (fallback)
            }
        ]
        
        for source in sources:
            try:
                self.logger.info(f"Trying to download from {source['name']}...")
                
                if source['name'] == 'GADM':
                    # GADM provides detailed administrative boundaries
                    gdf = gpd.read_file(source['url'])
                    
                    # GADM level 2 = Districts (Kabupaten/Kota)
                    if 'NAME_2' in gdf.columns:
                        gdf['district_name'] = gdf['NAME_2']
                        gdf['province_name'] = gdf['NAME_1']
                        gdf['country_name'] = gdf['NAME_0']
                        
                        # Add district type (Kabupaten vs Kota)
                        gdf['district_type'] = gdf['TYPE_2']
                        
                        return gdf[['district_name', 'province_name', 'country_name', 
                                  'district_type', 'geometry']]
                
                elif source['name'] == 'Natural Earth':
                    # Fallback to province level if district not available
                    gdf = gpd.read_file(source['url'])
                    return gdf
                    
            except Exception as e:
                self.logger.warning(f"Failed to download from {source['name']}: {e}")
                continue
        
        # If all sources fail, create a fallback using country boundary
        self.logger.warning("Creating fallback Indonesia boundary...")
        return self._create_fallback_boundary()
    
    def _create_fallback_boundary(self) -> gpd.GeoDataFrame:
        """
        Create a fallback Indonesia boundary if detailed data unavailable.
        
        Returns:
            GeoDataFrame with country-level boundary
        """
        try:
            # Use Natural Earth country data as fallback
            url = "https://raw.githubusercontent.com/holtzy/natural-earth-vector/master/110m_cultural/ne_110m_admin_0_countries.geojson"
            world = gpd.read_file(url)
            indonesia = world[world['NAME'] == 'Indonesia'].copy()
            
            if len(indonesia) > 0:
                indonesia['district_name'] = 'Indonesia'
                indonesia['province_name'] = 'Indonesia'
                indonesia['country_name'] = 'Indonesia'
                indonesia['district_type'] = 'Country'
                
                return indonesia[['district_name', 'province_name', 'country_name', 
                                'district_type', 'geometry']]
        except Exception as e:
            self.logger.error(f"Failed to create fallback boundary: {e}")
        
        # Ultimate fallback: create a bounding box for Indonesia
        self.logger.warning("Using bounding box as ultimate fallback...")
        bbox = self.get_indonesia_bbox()
        geometry = box(*bbox)
        
        fallback_gdf = gpd.GeoDataFrame({
            'district_name': ['Indonesia'],
            'province_name': ['Indonesia'],
            'country_name': ['Indonesia'],
            'district_type': ['Country'],
            'geometry': [geometry]
        }, crs='EPSG:4326')
        
        return fallback_gdf
    
    def _standardize_columns(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Standardize column names and add required fields.
        
        Args:
            gdf: Input GeoDataFrame
            
        Returns:
            Standardized GeoDataFrame
        """
        # Ensure required columns exist
        required_cols = ['district_name', 'province_name', 'country_name']
        
        for col in required_cols:
            if col not in gdf.columns:
                gdf[col] = 'Unknown'
        
        # Add unique district ID
        gdf['district_id'] = range(len(gdf))
        
        # Clean district names for URL construction (Wikipedia links)
        gdf['district_name_clean'] = gdf['district_name'].str.replace(' ', '_')
        
        # Add Wikipedia URL construction for Indonesian districts
        def construct_wikipedia_url(row):
            """Construct Wikipedia URL for Indonesian districts."""
            district_type = row.get('district_type', '')
            district_name = row['district_name_clean']
            
            if 'kota' in district_type.lower() or 'city' in district_type.lower():
                # For cities, use 'Wali Kota' format
                return f"https://id.wikipedia.org/wiki/Wali_Kota_{district_name}"
            else:
                # For regencies, use 'Bupati' format  
                return f"https://id.wikipedia.org/wiki/Bupati_{district_name}"
        
        gdf['wikipedia_url'] = gdf.apply(construct_wikipedia_url, axis=1)
        
        return gdf
    
    def get_indonesia_bbox(self) -> Tuple[float, float, float, float]:
        """
        Get bounding box for Indonesia.
        
        Returns:
            Tuple of (min_lon, min_lat, max_lon, max_lat)
        """
        # Indonesia bounding box (approximate)
        return (94.7717, -11.0081, 141.0194, 6.0765)
    
    def validate_boundaries(self, gdf: gpd.GeoDataFrame) -> Dict[str, Any]:
        """
        Validate district boundaries data.
        
        Args:
            gdf: District boundaries GeoDataFrame
            
        Returns:
            Validation report
        """
        report = {
            'total_districts': len(gdf),
            'has_geometry': gdf.geometry.notna().sum(),
            'valid_geometry': gdf.geometry.is_valid.sum(),
            'crs': str(gdf.crs),
            'bounds': gdf.total_bounds.tolist(),
            'provinces': gdf['province_name'].nunique(),
            'province_list': sorted(gdf['province_name'].unique().tolist())
        }
        
        self.logger.info(f"Validation report: {report}")
        return report