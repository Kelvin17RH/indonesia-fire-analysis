"""Tests for demo functionality."""

import pytest
import pandas as pd
import geopandas as gpd
from pathlib import Path
import tempfile
import shutil

import sys
sys.path.append(str(Path(__file__).parent.parent))

from demo import create_sample_data, create_demo_config


class TestDemo:
    """Test demo functionality."""
    
    def test_create_demo_config(self):
        """Test demo configuration creation."""
        config = create_demo_config()
        
        # Check required sections exist
        assert 'spatial' in config
        assert 'temporal' in config
        assert 'data_sources' in config
        assert 'output' in config
        
        # Check specific values
        assert config['spatial']['country'] == 'Indonesia'
        assert config['temporal']['start_date'] == '2019-01-01'
        assert config['temporal']['end_date'] == '2019-12-31'
    
    def test_create_sample_data(self):
        """Test sample data generation."""
        sample_data = create_sample_data()
        
        # Check data structure
        assert isinstance(sample_data, gpd.GeoDataFrame)
        assert len(sample_data) > 0
        
        # Check required columns
        required_cols = [
            'district_id', 'district_name', 'province_name',
            'fire_count_modis', 'fire_count_viirs', 'total_fires_all_sensors',
            'co_total_mean', 'geometry'
        ]
        
        for col in required_cols:
            assert col in sample_data.columns
        
        # Check data types
        assert sample_data['fire_count_modis'].dtype in ['int64', 'int32']
        assert sample_data['fire_count_viirs'].dtype in ['int64', 'int32']
        assert sample_data['co_total_mean'].dtype in ['float64', 'float32']
        
        # Check data ranges
        assert (sample_data['fire_count_modis'] >= 0).all()
        assert (sample_data['fire_count_viirs'] >= 0).all()
        assert (sample_data['co_total_mean'] > 0).all()
        
        # Check geometry
        assert sample_data.crs == 'EPSG:4326'
        assert sample_data.geometry.notna().all()
    
    def test_fire_data_consistency(self):
        """Test consistency of fire data in sample."""
        sample_data = create_sample_data()
        
        # Total fires should equal sum of sensor fires
        total_calculated = sample_data['fire_count_modis'] + sample_data['fire_count_viirs']
        assert (sample_data['total_fires_all_sensors'] == total_calculated).all()
        
        # Fire density should be positive where there are fires
        fires_mask = sample_data['total_fires_all_sensors'] > 0
        if fires_mask.any():
            assert (sample_data.loc[fires_mask, 'fire_density'] > 0).all()
    
    def test_wikipedia_url_construction(self):
        """Test Wikipedia URL construction for Indonesian districts."""
        sample_data = create_sample_data()
        
        # Check URLs are constructed
        assert 'wikipedia_url' in sample_data.columns
        assert sample_data['wikipedia_url'].notna().all()
        
        # Check URL format
        for _, row in sample_data.iterrows():
            url = row['wikipedia_url']
            assert url.startswith('https://id.wikipedia.org/wiki/')
            
            if 'kota' in row['district_type'].lower():
                assert 'Wali_Kota_' in url
            else:
                assert 'Bupati_' in url
    
    @pytest.fixture
    def temp_output_dir(self):
        """Create temporary directory for test outputs."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    def test_data_export_formats(self, temp_output_dir):
        """Test data export in different formats."""
        sample_data = create_sample_data()
        
        # Test CSV export
        csv_file = Path(temp_output_dir) / "test_data.csv"
        csv_data = sample_data.drop(columns=['geometry'])
        csv_data.to_csv(csv_file, index=False)
        
        assert csv_file.exists()
        
        # Test reading back
        loaded_csv = pd.read_csv(csv_file)
        assert len(loaded_csv) == len(sample_data)
        
        # Test GeoJSON export
        geojson_file = Path(temp_output_dir) / "test_data.geojson"
        sample_data.to_file(geojson_file, driver='GeoJSON')
        
        assert geojson_file.exists()
        
        # Test reading back
        loaded_geojson = gpd.read_file(geojson_file)
        assert len(loaded_geojson) == len(sample_data)
        assert loaded_geojson.crs == sample_data.crs