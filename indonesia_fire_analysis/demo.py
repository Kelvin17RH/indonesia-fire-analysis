#!/usr/bin/env python3
"""
Indonesia Fire Analysis - Demo Script
====================================

This script demonstrates the key capabilities of the Indonesia Fire Analysis system
with sample data and simplified configurations.
"""

import sys
import os
from pathlib import Path
import pandas as pd
import geopandas as gpd
import numpy as np
import matplotlib.pyplot as plt
import logging

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from utils.logger import setup_logging
from utils.config_loader import ConfigLoader
from spatial_processing.boundary_processor import BoundaryProcessor
from visualization.fire_maps import FireVisualizer


def create_demo_config():
    """Create a demo configuration for testing."""
    return {
        'spatial': {
            'country': 'Indonesia',
            'admin_level': 'district',
            'crs': 'EPSG:4326'
        },
        'temporal': {
            'start_date': '2019-01-01',
            'end_date': '2019-12-31'
        },
        'data_sources': {
            'modis': {
                'collections': ['MCD14ML'],
                'variables': ['fire_mask', 'FirePix', 'MaxFRP']
            },
            'viirs': {
                'collections': ['VNP14IMGML'],
                'variables': ['fire_mask', 'MaxFRP']
            },
            'co': {
                'collections': ['MOP02J', 'AIRX3STD'],
                'variables': ['COVMRLevs', 'TotCO_A']
            }
        },
        'output': {
            'formats': ['csv', 'geojson'],
            'directory': 'demo_output'
        }
    }


def create_sample_data():
    """Create sample fire and CO data for demonstration."""
    
    # Create sample district data for a few Indonesian provinces
    districts_data = [
        {'district_id': 1, 'district_name': 'Jakarta Pusat', 'province_name': 'DKI Jakarta', 
         'district_type': 'Kota', 'area_km2': 48.13, 'lat': -6.2088, 'lon': 106.8456},
        {'district_id': 2, 'district_name': 'Palangka Raya', 'province_name': 'Kalimantan Tengah',
         'district_type': 'Kota', 'area_km2': 2678.51, 'lat': -2.2058, 'lon': 113.9213},
        {'district_id': 3, 'district_name': 'Pekanbaru', 'province_name': 'Riau',
         'district_type': 'Kota', 'area_km2': 632.26, 'lat': 0.5071, 'lon': 101.4478},
        {'district_id': 4, 'district_name': 'Pontianak', 'province_name': 'Kalimantan Barat',
         'district_type': 'Kota', 'area_km2': 107.82, 'lat': -0.0263, 'lon': 109.3425},
        {'district_id': 5, 'district_name': 'Palembang', 'province_name': 'Sumatera Selatan',
         'district_type': 'Kota', 'area_km2': 400.61, 'lat': -2.9920, 'lon': 104.7458}
    ]
    
    # Create GeoDataFrame with simplified geometries
    from shapely.geometry import Point
    
    districts = []
    for district in districts_data:
        # Create a simple buffer around the center point as district geometry
        center = Point(district['lon'], district['lat'])
        # Buffer size based on area (very approximate)
        buffer_deg = np.sqrt(district['area_km2']) / 100  # Rough conversion
        geometry = center.buffer(buffer_deg)
        
        district['geometry'] = geometry
        districts.append(district)
    
    districts_gdf = gpd.GeoDataFrame(districts, crs='EPSG:4326')
    
    # Add Wikipedia URLs using the memory about Indonesian districts
    def construct_wikipedia_url(row):
        district_name = row['district_name'].replace(' ', '_')
        if 'kota' in row['district_type'].lower() or 'city' in row['district_type'].lower():
            # For cities, use 'Wali Kota' format
            return f"https://id.wikipedia.org/wiki/Wali_Kota_{district_name}"
        else:
            # For regencies, use 'Bupati' format
            return f"https://id.wikipedia.org/wiki/Bupati_{district_name}"
    
    districts_gdf['wikipedia_url'] = districts_gdf.apply(construct_wikipedia_url, axis=1)
    
    # Generate sample fire data
    np.random.seed(42)  # For reproducible results
    
    fire_data = []
    for _, district in districts_gdf.iterrows():
        # Simulate different fire intensities by province
        if 'Kalimantan' in district['province_name']:
            # High fire activity in Kalimantan (peat fires)
            fire_count_modis = np.random.poisson(500)
            fire_count_viirs = np.random.poisson(800)
            co_level = np.random.normal(300, 100)
        elif 'Riau' in district['province_name']:
            # Very high fire activity in Riau
            fire_count_modis = np.random.poisson(800)
            fire_count_viirs = np.random.poisson(1200)
            co_level = np.random.normal(450, 150)
        elif 'Sumatera' in district['province_name']:
            # Moderate fire activity in Sumatra
            fire_count_modis = np.random.poisson(300)
            fire_count_viirs = np.random.poisson(450)
            co_level = np.random.normal(250, 80)
        else:
            # Low fire activity in other areas
            fire_count_modis = np.random.poisson(50)
            fire_count_viirs = np.random.poisson(75)
            co_level = np.random.normal(150, 50)
        
        # Ensure positive values
        fire_count_modis = max(0, fire_count_modis)
        fire_count_viirs = max(0, fire_count_viirs)
        co_level = max(50, co_level)
        
        # Calculate derived metrics
        total_fires = fire_count_modis + fire_count_viirs
        fire_density = total_fires / district['area_km2']
        
        # Simulate FRP values
        total_frp_modis = fire_count_modis * np.random.lognormal(1.5, 1.0) if fire_count_modis > 0 else 0
        total_frp_viirs = fire_count_viirs * np.random.lognormal(1.3, 0.8) if fire_count_viirs > 0 else 0
        
        fire_stats = {
            'district_id': district['district_id'],
            'fire_count_modis': fire_count_modis,
            'fire_count_viirs': fire_count_viirs,
            'total_fires_all_sensors': total_fires,
            'fire_density': fire_density,
            'total_frp_modis': total_frp_modis,
            'total_frp_viirs': total_frp_viirs,
            'total_frp_all_sensors': total_frp_modis + total_frp_viirs,
            'mean_frp_modis': total_frp_modis / fire_count_modis if fire_count_modis > 0 else 0,
            'mean_frp_viirs': total_frp_viirs / fire_count_viirs if fire_count_viirs > 0 else 0,
            'co_total_mean': co_level,
            'co_total_std': co_level * 0.2,
            'high_conf_fires_modis': int(fire_count_modis * 0.7),
            'high_conf_fires_viirs': int(fire_count_viirs * 0.8)
        }
        
        fire_data.append(fire_stats)
    
    # Merge fire data with districts
    fire_df = pd.DataFrame(fire_data)
    combined_gdf = districts_gdf.merge(fire_df, on='district_id', how='left')
    
    return combined_gdf


def demo_analysis():
    """Run a demonstration of the fire analysis system."""
    
    print("🔥 Indonesia Fire Analysis - Demo Mode")
    print("=" * 50)
    
    # Setup logging
    setup_logging(log_level="INFO")
    logger = logging.getLogger(__name__)
    
    # Create demo output directory
    demo_dir = Path("demo_output")
    demo_dir.mkdir(exist_ok=True)
    
    try:
        # 1. Create demo configuration
        print("\n📋 Setting up demo configuration...")
        config = create_demo_config()
        logger.info("Demo configuration created")
        
        # 2. Create sample data
        print("📊 Generating sample fire and CO data...")
        sample_data = create_sample_data()
        logger.info(f"Generated data for {len(sample_data)} districts")
        
        # 3. Display summary statistics
        print("\n📈 Sample Data Summary:")
        print(f"  • Districts: {len(sample_data)}")
        print(f"  • Provinces: {sample_data['province_name'].nunique()}")
        print(f"  • Total MODIS fires: {sample_data['fire_count_modis'].sum():,}")
        print(f"  • Total VIIRS fires: {sample_data['fire_count_viirs'].sum():,}")
        print(f"  • Mean CO concentration: {sample_data['co_total_mean'].mean():.1f} ppbv")
        
        # 4. Show top fire districts
        print(f"\n🔥 Top Fire Districts:")
        top_districts = sample_data.nlargest(3, 'total_fires_all_sensors')
        for _, district in top_districts.iterrows():
            print(f"  • {district['district_name']}, {district['province_name']}: "
                  f"{district['total_fires_all_sensors']:,} fires")
        
        # 5. Export sample data
        print(f"\n💾 Exporting sample data...")
        
        # CSV export (no geometry)
        csv_data = sample_data.drop(columns=['geometry'])
        csv_file = demo_dir / "sample_fire_data.csv"
        csv_data.to_csv(csv_file, index=False)
        print(f"  • CSV: {csv_file}")
        
        # GeoJSON export
        geojson_file = demo_dir / "sample_fire_data.geojson"
        sample_data.to_file(geojson_file, driver='GeoJSON')
        print(f"  • GeoJSON: {geojson_file}")
        
        # 6. Create visualizations
        print(f"\n🗺️ Creating visualizations...")
        
        # Initialize visualizer
        visualizer = FireVisualizer(config)
        
        # Create fire density map
        fire_map = visualizer.create_fire_density_map(
            sample_data, 
            fire_column='total_fires_all_sensors',
            title="Sample Fire Density Map - Indonesia Districts"
        )
        
        # Create CO map
        co_map = visualizer.create_co_concentration_map(
            sample_data,
            co_column='co_total_mean',
            title="Sample CO Concentration Map - Indonesia Districts"  
        )
        
        # Create simple dashboard plot
        plt.figure(figsize=(15, 10))
        
        # Fire count by province
        plt.subplot(2, 2, 1)
        province_fires = sample_data.groupby('province_name')['total_fires_all_sensors'].sum()
        province_fires.plot(kind='bar', color='orangered')
        plt.title('Fire Count by Province', fontweight='bold')
        plt.xticks(rotation=45)
        plt.ylabel('Total Fires')
        
        # Fire vs CO scatter plot
        plt.subplot(2, 2, 2)
        plt.scatter(sample_data['total_fires_all_sensors'], sample_data['co_total_mean'], 
                   c='darkred', alpha=0.7, s=100)
        plt.xlabel('Total Fires')
        plt.ylabel('CO Concentration (ppbv)')
        plt.title('Fire vs CO Concentration', fontweight='bold')
        
        # Fire density histogram
        plt.subplot(2, 2, 3)
        sample_data['fire_density'].hist(bins=10, alpha=0.7, color='orange', edgecolor='black')
        plt.xlabel('Fire Density (fires/km²)')
        plt.ylabel('Number of Districts')
        plt.title('Fire Density Distribution', fontweight='bold')
        
        # Sensor comparison
        plt.subplot(2, 2, 4)
        sensor_data = [
            sample_data['fire_count_modis'].sum(),
            sample_data['fire_count_viirs'].sum()
        ]
        plt.pie(sensor_data, labels=['MODIS', 'VIIRS'], autopct='%1.1f%%', 
               colors=['#ff9999', '#66b3ff'], startangle=90)
        plt.title('Fire Detection by Sensor', fontweight='bold')
        
        plt.tight_layout()
        
        dashboard_file = demo_dir / "demo_dashboard.png"
        plt.savefig(dashboard_file, dpi=300, bbox_inches='tight', facecolor='white')
        plt.close()
        
        print(f"  • Dashboard: {dashboard_file}")
        print(f"  • Fire Map: {demo_dir / 'fire_density_map.html'}")
        print(f"  • CO Map: {demo_dir / 'co_concentration_map.html'}")
        
        # 7. Summary report
        summary_file = demo_dir / "demo_summary.txt"
        with open(summary_file, 'w') as f:
            f.write("Indonesia Fire Analysis - Demo Results\n")
            f.write("=" * 40 + "\n\n")
            f.write(f"Analysis Date: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Demo Mode: Sample data generation\n\n")
            
            f.write("Dataset Summary:\n")
            f.write(f"- Districts analyzed: {len(sample_data)}\n")
            f.write(f"- Provinces covered: {sample_data['province_name'].nunique()}\n")
            f.write(f"- Total area: {sample_data['area_km2'].sum():,.1f} km²\n\n")
            
            f.write("Fire Activity:\n")
            f.write(f"- MODIS fires: {sample_data['fire_count_modis'].sum():,}\n")
            f.write(f"- VIIRS fires: {sample_data['fire_count_viirs'].sum():,}\n")
            f.write(f"- Total fires: {sample_data['total_fires_all_sensors'].sum():,}\n")
            f.write(f"- Mean fire density: {sample_data['fire_density'].mean():.3f} fires/km²\n\n")
            
            f.write("CO Analysis:\n")
            f.write(f"- Mean concentration: {sample_data['co_total_mean'].mean():.1f} ppbv\n")
            f.write(f"- Max concentration: {sample_data['co_total_mean'].max():.1f} ppbv\n")
            f.write(f"- Standard deviation: {sample_data['co_total_mean'].std():.1f} ppbv\n\n")
            
            f.write("Top Fire Districts:\n")
            for _, district in top_districts.iterrows():
                f.write(f"- {district['district_name']}: {district['total_fires_all_sensors']:,} fires\n")
        
        print(f"  • Summary: {summary_file}")
        
        print(f"\n✅ Demo completed successfully!")
        print(f"📁 All outputs saved to: {demo_dir.absolute()}")
        
        print(f"\n🎯 Next Steps:")
        print(f"  1. Review the generated sample data and visualizations")
        print(f"  2. Modify config.yaml for your specific analysis needs")
        print(f"  3. Run: python run_analysis.py quick")
        print(f"  4. For real data, ensure NASA API credentials are configured")
        
        return sample_data
        
    except Exception as e:
        logger.error(f"Demo failed: {str(e)}")
        print(f"\n❌ Demo failed: {str(e)}")
        raise


if __name__ == "__main__":
    result = demo_analysis()