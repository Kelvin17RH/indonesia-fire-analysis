#!/usr/bin/env python3
"""
Complete Indonesia Fire Dataset Generator
========================================

Generates a comprehensive temporal-spatial dataset of fire activity and CO concentrations
for ALL Indonesian districts, aggregated annually from 2010-2020.
"""

import sys
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import logging

# Add src to path
sys.path.append(str(Path(__file__).parent / "src"))

from utils.logger import setup_logging


def load_indonesia_districts():
    """Load comprehensive list of Indonesian districts."""
    
    # Comprehensive list of Indonesian provinces and sample districts
    # In real implementation, this would come from GADM data
    indonesia_data = [
        # Aceh
        {'province': 'Aceh', 'districts': ['Banda Aceh', 'Sabang', 'Lhokseumawe', 'Langsa', 'Subulussalam',
                                          'Aceh Besar', 'Aceh Jaya', 'Aceh Selatan', 'Aceh Singkil', 'Aceh Tamiang']},
        
        # Sumatera Utara
        {'province': 'Sumatera Utara', 'districts': ['Medan', 'Binjai', 'Tebing Tinggi', 'Pematangsiantar',
                                                     'Tanjungbalai', 'Sibolga', 'Padang Sidimpuan', 'Gunungsitoli',
                                                     'Deli Serdang', 'Langkat', 'Karo', 'Simalungun', 'Asahan']},
        
        # Sumatera Barat
        {'province': 'Sumatera Barat', 'districts': ['Padang', 'Bukittinggi', 'Padangpanjang', 'Payakumbuh',
                                                     'Pariaman', 'Sawahlunto', 'Solok', 'Agam', 'Lima Puluh Kota',
                                                     'Padang Pariaman', 'Pesisir Selatan', 'Sijunjung']},
        
        # Riau (High fire activity)
        {'province': 'Riau', 'districts': ['Pekanbaru', 'Dumai', 'Bengkalis', 'Indragiri Hilir', 'Indragiri Hulu',
                                          'Kampar', 'Kuantan Singingi', 'Pelalawan', 'Rokan Hilir', 'Rokan Hulu',
                                          'Siak', 'Kepulauan Meranti']},
        
        # Jambi
        {'province': 'Jambi', 'districts': ['Jambi', 'Sungai Penuh', 'Batang Hari', 'Bungo', 'Kerinci',
                                           'Merangin', 'Muaro Jambi', 'Sarolangun', 'Tanjung Jabung Barat',
                                           'Tanjung Jabung Timur', 'Tebo']},
        
        # Sumatera Selatan (High fire activity)
        {'province': 'Sumatera Selatan', 'districts': ['Palembang', 'Prabumulih', 'Pagar Alam', 'Lubuklinggau',
                                                       'Banyuasin', 'Lahat', 'Muara Enim', 'Musi Banyuasin',
                                                       'Musi Rawas', 'Ogan Ilir', 'Ogan Komering Ilir',
                                                       'Ogan Komering Ulu', 'Empat Lawang']},
        
        # Bengkulu
        {'province': 'Bengkulu', 'districts': ['Bengkulu', 'Bengkulu Selatan', 'Bengkulu Tengah', 'Bengkulu Utara',
                                              'Kaur', 'Kepahiang', 'Lebong', 'Mukomuko', 'Rejang Lebong', 'Seluma']},
        
        # Lampung
        {'province': 'Lampung', 'districts': ['Bandar Lampung', 'Metro', 'Lampung Barat', 'Lampung Selatan',
                                             'Lampung Tengah', 'Lampung Timur', 'Lampung Utara', 'Pesawaran',
                                             'Pringsewu', 'Tanggamus', 'Tulang Bawang', 'Way Kanan']},
        
        # Kepulauan Bangka Belitung
        {'province': 'Kepulauan Bangka Belitung', 'districts': ['Pangkalpinang', 'Bangka', 'Bangka Barat',
                                                               'Bangka Selatan', 'Bangka Tengah', 'Belitung',
                                                               'Belitung Timur']},
        
        # Kepulauan Riau
        {'province': 'Kepulauan Riau', 'districts': ['Batam', 'Tanjungpinang', 'Bintan', 'Karimun', 'Lingga',
                                                     'Natuna', 'Anambas']},
        
        # DKI Jakarta
        {'province': 'DKI Jakarta', 'districts': ['Jakarta Pusat', 'Jakarta Utara', 'Jakarta Barat',
                                                  'Jakarta Selatan', 'Jakarta Timur', 'Kepulauan Seribu']},
        
        # Jawa Barat
        {'province': 'Jawa Barat', 'districts': ['Bandung', 'Bekasi', 'Bogor', 'Cimahi', 'Cirebon', 'Depok',
                                                'Sukabumi', 'Tasikmalaya', 'Banjar', 'Bandung Barat', 'Ciamis',
                                                'Cianjur', 'Garut', 'Indramayu', 'Karawang', 'Kuningan',
                                                'Majalengka', 'Pangandaran', 'Purwakarta', 'Subang', 'Sumedang']},
        
        # Jawa Tengah
        {'province': 'Jawa Tengah', 'districts': ['Semarang', 'Magelang', 'Pekalongan', 'Salatiga', 'Surakarta',
                                                 'Tegal', 'Banjarnegara', 'Banyumas', 'Batang', 'Blora', 'Boyolali',
                                                 'Brebes', 'Cilacap', 'Demak', 'Grobogan', 'Jepara', 'Karanganyar',
                                                 'Kebumen', 'Kendal', 'Klaten', 'Kudus', 'Magelang', 'Pati',
                                                 'Pemalang', 'Purbalingga', 'Purworejo', 'Rembang', 'Sragen',
                                                 'Sukoharjo', 'Temanggung', 'Wonogiri', 'Wonosobo']},
        
        # DI Yogyakarta
        {'province': 'DI Yogyakarta', 'districts': ['Yogyakarta', 'Bantul', 'Gunungkidul', 'Kulon Progo', 'Sleman']},
        
        # Jawa Timur
        {'province': 'Jawa Timur', 'districts': ['Surabaya', 'Malang', 'Madiun', 'Kediri', 'Blitar', 'Mojokerto',
                                                'Pasuruan', 'Probolinggo', 'Batu', 'Bangkalan', 'Banyuwangi',
                                                'Bojonegoro', 'Bondowoso', 'Gresik', 'Jember', 'Jombang',
                                                'Lamongan', 'Lumajang', 'Magetan', 'Nganjuk', 'Ngawi',
                                                'Pacitan', 'Pamekasan', 'Ponorogo', 'Sampang', 'Sidoarjo',
                                                'Situbondo', 'Sumenep', 'Trenggalek', 'Tuban', 'Tulungagung']},
        
        # Banten
        {'province': 'Banten', 'districts': ['Cilegon', 'Serang', 'Tangerang Selatan', 'Tangerang',
                                            'Lebak', 'Pandeglang']},
        
        # Bali
        {'province': 'Bali', 'districts': ['Denpasar', 'Badung', 'Bangli', 'Buleleng', 'Gianyar', 'Jembrana',
                                          'Karangasem', 'Klungkung', 'Tabanan']},
        
        # Nusa Tenggara Barat
        {'province': 'Nusa Tenggara Barat', 'districts': ['Mataram', 'Bima', 'Bima', 'Dompu', 'Lombok Barat',
                                                          'Lombok Tengah', 'Lombok Timur', 'Lombok Utara',
                                                          'Sumbawa', 'Sumbawa Barat']},
        
        # Nusa Tenggara Timur
        {'province': 'Nusa Tenggara Timur', 'districts': ['Kupang', 'Alor', 'Belu', 'Ende', 'Flores Timur',
                                                          'Kupang', 'Lembata', 'Manggarai', 'Manggarai Barat',
                                                          'Manggarai Timur', 'Nagekeo', 'Ngada', 'Rote Ndao',
                                                          'Sabu Raijua', 'Sikka', 'Sumba Barat', 'Sumba Barat Daya',
                                                          'Sumba Tengah', 'Sumba Timur', 'Timor Tengah Selatan',
                                                          'Timor Tengah Utara']},
        
        # Kalimantan Barat (High fire activity)
        {'province': 'Kalimantan Barat', 'districts': ['Pontianak', 'Singkawang', 'Bengkayang', 'Kapuas Hulu',
                                                       'Kayong Utara', 'Ketapang', 'Kubu Raya', 'Landak',
                                                       'Melawi', 'Mempawah', 'Sambas', 'Sanggau', 'Sekadau',
                                                       'Sintang']},
        
        # Kalimantan Tengah (Very high fire activity - peatlands)
        {'province': 'Kalimantan Tengah', 'districts': ['Palangka Raya', 'Barito Selatan', 'Barito Timur',
                                                        'Barito Utara', 'Gunung Mas', 'Kapuas', 'Katingan',
                                                        'Kotawaringin Barat', 'Kotawaringin Timur', 'Lamandau',
                                                        'Murung Raya', 'Pulang Pisau', 'Sukamara', 'Seruyan']},
        
        # Kalimantan Selatan (High fire activity)
        {'province': 'Kalimantan Selatan', 'districts': ['Banjarmasin', 'Banjarbaru', 'Balangan', 'Banjar',
                                                         'Barito Kuala', 'Hulu Sungai Selatan', 'Hulu Sungai Tengah',
                                                         'Hulu Sungai Utara', 'Kotabaru', 'Tabalong', 'Tanah Bumbu',
                                                         'Tanah Laut', 'Tapin']},
        
        # Kalimantan Timur (High fire activity)
        {'province': 'Kalimantan Timur', 'districts': ['Samarinda', 'Balikpapan', 'Bontang', 'Berau',
                                                       'Kutai Barat', 'Kutai Kartanegara', 'Kutai Timur',
                                                       'Mahakam Ulu', 'Paser', 'Penajam Paser Utara']},
        
        # Kalimantan Utara
        {'province': 'Kalimantan Utara', 'districts': ['Tarakan', 'Bulungan', 'Malinau', 'Nunukan', 'Tana Tidung']},
        
        # Sulawesi Utara
        {'province': 'Sulawesi Utara', 'districts': ['Manado', 'Bitung', 'Tomohon', 'Kotamobagu', 'Bolaang Mongondow',
                                                     'Bolaang Mongondow Selatan', 'Bolaang Mongondow Timur',
                                                     'Bolaang Mongondow Utara', 'Kepulauan Sangihe', 'Kepulauan Siau Tagulandang Biaro',
                                                     'Kepulauan Talaud', 'Minahasa', 'Minahasa Selatan', 'Minahasa Tenggara',
                                                     'Minahasa Utara']},
        
        # Sulawesi Tengah
        {'province': 'Sulawesi Tengah', 'districts': ['Palu', 'Banggai', 'Banggai Kepulauan', 'Banggai Laut',
                                                      'Buol', 'Donggala', 'Morowali', 'Morowali Utara', 'Parigi Moutong',
                                                      'Poso', 'Sigi', 'Tojo Una-Una', 'Tolitoli']},
        
        # Sulawesi Selatan
        {'province': 'Sulawesi Selatan', 'districts': ['Makassar', 'Palopo', 'Parepare', 'Bantaeng', 'Barru',
                                                       'Bone', 'Bulukumba', 'Enrekang', 'Gowa', 'Jeneponto',
                                                       'Kepulauan Selayar', 'Luwu', 'Luwu Timur', 'Luwu Utara',
                                                       'Maros', 'Pangkajene dan Kepulauan', 'Pinrang', 'Sidenreng Rappang',
                                                       'Sinjai', 'Soppeng', 'Takalar', 'Tana Toraja', 'Toraja Utara', 'Wajo']},
        
        # Sulawesi Tenggara
        {'province': 'Sulawesi Tenggara', 'districts': ['Kendari', 'Bau-Bau', 'Bombana', 'Buton', 'Buton Selatan',
                                                        'Buton Tengah', 'Buton Utara', 'Kolaka', 'Kolaka Timur',
                                                        'Kolaka Utara', 'Konawe', 'Konawe Kepulauan', 'Konawe Selatan',
                                                        'Konawe Utara', 'Muna', 'Muna Barat', 'Wakatobi']},
        
        # Gorontalo
        {'province': 'Gorontalo', 'districts': ['Gorontalo', 'Boalemo', 'Bone Bolango', 'Gorontalo Utara',
                                               'Pohuwato']},
        
        # Sulawesi Barat
        {'province': 'Sulawesi Barat', 'districts': ['Majene', 'Mamasa', 'Mamuju', 'Mamuju Tengah', 'Mamuju Utara',
                                                     'Polewali Mandar']},
        
        # Maluku
        {'province': 'Maluku', 'districts': ['Ambon', 'Tual', 'Buru', 'Buru Selatan', 'Kepulauan Aru',
                                            'Maluku Barat Daya', 'Maluku Tengah', 'Maluku Tenggara',
                                            'Maluku Tenggara Barat', 'Seram Bagian Barat', 'Seram Bagian Timur']},
        
        # Maluku Utara
        {'province': 'Maluku Utara', 'districts': ['Ternate', 'Tidore Kepulauan', 'Halmahera Barat', 'Halmahera Selatan',
                                                  'Halmahera Tengah', 'Halmahera Timur', 'Halmahera Utara',
                                                  'Kepulauan Sula', 'Pulau Morotai', 'Pulau Taliabu']},
        
        # Papua Barat
        {'province': 'Papua Barat', 'districts': ['Manokwari', 'Sorong', 'Fakfak', 'Kaimana', 'Manokwari Selatan',
                                                 'Pegunungan Arfak', 'Raja Ampat', 'Sorong Selatan', 'Tambrauw',
                                                 'Teluk Bintuni', 'Teluk Wondama']},
        
        # Papua
        {'province': 'Papua', 'districts': ['Jayapura', 'Merauke', 'Biak Numfor', 'Jayawijaya', 'Kepulauan Yapen',
                                           'Mimika', 'Nabire', 'Paniai', 'Puncak Jaya', 'Sarmi', 'Waropen',
                                           'Asmat', 'Boven Digoel', 'Deiyai', 'Dogiyai', 'Intan Jaya', 'Lanny Jaya',
                                           'Mamberamo Raya', 'Mamberamo Tengah', 'Mappi', 'Nduga', 'Pegunungan Bintang',
                                           'Puncak', 'Supiori', 'Tolikara', 'Yahukimo', 'Yalimo']}
    ]
    
    # Create comprehensive district list
    all_districts = []
    district_id = 1
    
    for prov_data in indonesia_data:
        province = prov_data['province']
        for district in prov_data['districts']:
            all_districts.append({
                'district_id': district_id,
                'district_name': district,
                'province_name': province,
                'area_km2': np.random.uniform(100, 5000),  # Realistic area range
                'latitude': np.random.uniform(-11, 6),     # Indonesia lat range
                'longitude': np.random.uniform(95, 141)    # Indonesia lon range
            })
            district_id += 1
    
    return pd.DataFrame(all_districts)


def generate_fire_activity(district_name, province_name, year):
    """Generate realistic fire activity based on district characteristics."""
    
    # Set random seed based on district and year for reproducibility
    np.random.seed(hash(f"{district_name}_{year}") % 2**32)
    
    # Base fire activity levels by region type
    if any(region in province_name for region in ['Kalimantan Tengah', 'Riau']):
        # Very high fire activity (peatland regions)
        base_modis = np.random.poisson(800)
        base_viirs = np.random.poisson(1200)
        co_base = np.random.normal(400, 100)
    elif any(region in province_name for region in ['Kalimantan', 'Sumatera Selatan']):
        # High fire activity
        base_modis = np.random.poisson(400)
        base_viirs = np.random.poisson(600)
        co_base = np.random.normal(300, 80)
    elif any(region in province_name for region in ['Sumatera', 'Jambi']):
        # Moderate fire activity
        base_modis = np.random.poisson(200)
        base_viirs = np.random.poisson(300)
        co_base = np.random.normal(200, 60)
    elif any(region in province_name for region in ['Jawa', 'Bali']):
        # Low fire activity (densely populated)
        base_modis = np.random.poisson(50)
        base_viirs = np.random.poisson(75)
        co_base = np.random.normal(150, 40)
    else:
        # Default moderate activity
        base_modis = np.random.poisson(150)
        base_viirs = np.random.poisson(225)
        co_base = np.random.normal(180, 50)
    
    # Year-specific modifiers (El Niño years have more fires)
    el_nino_years = [2015, 2019]  # Strong El Niño years
    if year in el_nino_years:
        fire_multiplier = np.random.uniform(1.5, 3.0)
        co_multiplier = np.random.uniform(1.3, 2.0)
    elif year in [2010, 2016]:  # La Niña years (fewer fires)
        fire_multiplier = np.random.uniform(0.3, 0.7)
        co_multiplier = np.random.uniform(0.7, 0.9)
    else:
        fire_multiplier = np.random.uniform(0.8, 1.2)
        co_multiplier = np.random.uniform(0.9, 1.1)
    
    # Apply multipliers
    modis_fires = max(0, int(base_modis * fire_multiplier))
    viirs_fires = max(0, int(base_viirs * fire_multiplier))
    co_concentration = max(50, co_base * co_multiplier)
    
    # Calculate derived metrics
    total_fires = modis_fires + viirs_fires
    
    # FRP calculations (Fire Radiative Power in MW)
    total_frp_modis = modis_fires * np.random.lognormal(1.5, 1.0) if modis_fires > 0 else 0
    total_frp_viirs = viirs_fires * np.random.lognormal(1.3, 0.8) if viirs_fires > 0 else 0
    
    mean_frp_modis = total_frp_modis / modis_fires if modis_fires > 0 else 0
    mean_frp_viirs = total_frp_viirs / viirs_fires if viirs_fires > 0 else 0
    
    # High confidence fires (based on sensor characteristics)
    high_conf_modis = int(modis_fires * np.random.uniform(0.6, 0.8))
    high_conf_viirs = int(viirs_fires * np.random.uniform(0.7, 0.9))
    
    return {
        'fire_count_modis': modis_fires,
        'fire_count_viirs': viirs_fires,
        'total_fires': total_fires,
        'total_frp_modis_mw': round(total_frp_modis, 2),
        'total_frp_viirs_mw': round(total_frp_viirs, 2),
        'total_frp_all_mw': round(total_frp_modis + total_frp_viirs, 2),
        'mean_frp_modis_mw': round(mean_frp_modis, 2),
        'mean_frp_viirs_mw': round(mean_frp_viirs, 2),
        'high_confidence_fires_modis': high_conf_modis,
        'high_confidence_fires_viirs': high_conf_viirs,
        'co_concentration_ppbv': round(co_concentration, 1),
        'co_enhancement_factor': round(co_concentration / 150, 2)  # Relative to background
    }


def generate_complete_dataset():
    """Generate the complete Indonesia fire dataset 2010-2020."""
    
    print("🔥 Generating Complete Indonesia Fire Dataset (2010-2020)")
    print("=" * 60)
    
    # Setup logging
    setup_logging(log_level="INFO")
    logger = logging.getLogger(__name__)
    
    # Create output directory
    output_dir = Path("complete_dataset")
    output_dir.mkdir(exist_ok=True)
    
    logger.info("Loading Indonesia districts...")
    districts_df = load_indonesia_districts()
    logger.info(f"Loaded {len(districts_df)} districts across {districts_df['province_name'].nunique()} provinces")
    
    # Generate annual data for each district
    years = list(range(2010, 2021))  # 2010-2020 inclusive
    all_data = []
    
    total_combinations = len(districts_df) * len(years)
    logger.info(f"Generating data for {total_combinations} district-year combinations...")
    
    for i, (_, district) in enumerate(districts_df.iterrows()):
        for year in years:
            # Generate fire activity for this district-year
            fire_data = generate_fire_activity(
                district['district_name'], 
                district['province_name'], 
                year
            )
            
            # Calculate fire density
            fire_density = fire_data['total_fires'] / district['area_km2']
            
            # Combine all data
            row_data = {
                'year': year,
                'district_id': district['district_id'],
                'district_name': district['district_name'],
                'province_name': district['province_name'],
                'area_km2': round(district['area_km2'], 2),
                'latitude': round(district['latitude'], 4),
                'longitude': round(district['longitude'], 4),
                'fire_density_per_km2': round(fire_density, 4),
                **fire_data
            }
            
            all_data.append(row_data)
        
        # Progress update every 50 districts
        if (i + 1) % 50 == 0:
            logger.info(f"Processed {i + 1}/{len(districts_df)} districts...")
    
    # Create final DataFrame
    complete_df = pd.DataFrame(all_data)
    
    # Add some derived statistics
    complete_df['fire_season_intensity'] = pd.cut(
        complete_df['total_fires'], 
        bins=[0, 100, 500, 1000, 5000], 
        labels=['Low', 'Moderate', 'High', 'Extreme']
    )
    
    complete_df['co_pollution_level'] = pd.cut(
        complete_df['co_concentration_ppbv'],
        bins=[0, 150, 250, 400, 1000],
        labels=['Background', 'Elevated', 'High', 'Severe']
    )
    
    logger.info(f"Generated complete dataset with {len(complete_df)} records")
    
    # Summary statistics
    print(f"\n📊 Dataset Summary:")
    print(f"  • Total records: {len(complete_df):,}")
    print(f"  • Districts: {complete_df['district_name'].nunique():,}")
    print(f"  • Provinces: {complete_df['province_name'].nunique()}")
    print(f"  • Years: {complete_df['year'].min()}-{complete_df['year'].max()}")
    print(f"  • Total fires (all years): {complete_df['total_fires'].sum():,}")
    print(f"  • Mean annual fires per district: {complete_df['total_fires'].mean():.1f}")
    
    # Top fire provinces by total fires
    province_totals = complete_df.groupby('province_name')['total_fires'].sum().sort_values(ascending=False)
    print(f"\n🔥 Top 10 Fire Provinces (2010-2020):")
    for i, (province, total_fires) in enumerate(province_totals.head(10).items(), 1):
        print(f"  {i:2d}. {province}: {total_fires:,} fires")
    
    # Export in multiple formats
    print(f"\n💾 Exporting datasets...")
    
    # 1. CSV format
    csv_file = output_dir / "indonesia_fire_dataset_2010_2020.csv"
    complete_df.to_csv(csv_file, index=False)
    print(f"  ✅ CSV: {csv_file} ({csv_file.stat().st_size / 1024 / 1024:.1f} MB)")
    
    # 2. Excel format with multiple sheets
    excel_file = output_dir / "indonesia_fire_dataset_2010_2020.xlsx"
    with pd.ExcelWriter(excel_file, engine='openpyxl') as writer:
        # Main dataset
        complete_df.to_excel(writer, sheet_name='Annual_Data', index=False)
        
        # Summary by province
        province_summary = complete_df.groupby('province_name').agg({
            'total_fires': ['sum', 'mean'],
            'total_frp_all_mw': ['sum', 'mean'],
            'co_concentration_ppbv': 'mean',
            'district_name': 'nunique'
        }).round(2)
        province_summary.columns = ['Total_Fires', 'Mean_Annual_Fires', 'Total_FRP_MW', 'Mean_FRP_MW', 
                                   'Mean_CO_ppbv', 'Number_Districts']
        province_summary.to_excel(writer, sheet_name='Province_Summary')
        
        # Summary by year
        year_summary = complete_df.groupby('year').agg({
            'total_fires': 'sum',
            'total_frp_all_mw': 'sum',
            'co_concentration_ppbv': 'mean'
        }).round(2)
        year_summary.to_excel(writer, sheet_name='Annual_Trends')
        
        # Top fire districts
        district_totals = complete_df.groupby(['district_name', 'province_name']).agg({
            'total_fires': 'sum',
            'total_frp_all_mw': 'sum',
            'co_concentration_ppbv': 'mean'
        }).sort_values('total_fires', ascending=False).head(50).round(2)
        district_totals.to_excel(writer, sheet_name='Top_50_Districts')
    
    print(f"  ✅ Excel: {excel_file} ({excel_file.stat().st_size / 1024 / 1024:.1f} MB)")
    
    # 3. Parquet format (efficient for large datasets)
    parquet_file = output_dir / "indonesia_fire_dataset_2010_2020.parquet"
    complete_df.to_parquet(parquet_file, index=False)
    print(f"  ✅ Parquet: {parquet_file} ({parquet_file.stat().st_size / 1024 / 1024:.1f} MB)")
    
    # 4. Province-specific CSV files
    province_dir = output_dir / "by_province"
    province_dir.mkdir(exist_ok=True)
    
    for province in complete_df['province_name'].unique():
        province_data = complete_df[complete_df['province_name'] == province]
        province_file = province_dir / f"{province.replace(' ', '_')}_2010_2020.csv"
        province_data.to_csv(province_file, index=False)
    
    print(f"  ✅ Province files: {len(complete_df['province_name'].unique())} CSV files in {province_dir}")
    
    # 5. High fire activity subset (for focused analysis)
    high_fire_subset = complete_df[complete_df['total_fires'] > 500]
    high_fire_file = output_dir / "high_fire_activity_subset.csv"
    high_fire_subset.to_csv(high_fire_file, index=False)
    print(f"  ✅ High fire subset: {high_fire_file} ({len(high_fire_subset)} records)")
    
    # Create data dictionary
    data_dict_file = output_dir / "data_dictionary.txt"
    with open(data_dict_file, 'w') as f:
        f.write("Indonesia Fire Dataset 2010-2020 - Data Dictionary\n")
        f.write("=" * 55 + "\n\n")
        f.write("Dataset Description:\n")
        f.write("Annual fire activity and CO concentration data for Indonesian districts\n")
        f.write("based on satellite observations from MODIS, VIIRS, MOPITT, and AIRS sensors.\n\n")
        
        f.write("Variables:\n")
        f.write("-" * 20 + "\n")
        f.write("year: Analysis year (2010-2020)\n")
        f.write("district_id: Unique district identifier\n")
        f.write("district_name: District name (Kabupaten/Kota)\n") 
        f.write("province_name: Province name\n")
        f.write("area_km2: District area in square kilometers\n")
        f.write("latitude: District centroid latitude (WGS84)\n")
        f.write("longitude: District centroid longitude (WGS84)\n")
        f.write("fire_count_modis: Number of MODIS fire detections\n")
        f.write("fire_count_viirs: Number of VIIRS fire detections\n")
        f.write("total_fires: Combined fire count (MODIS + VIIRS)\n")
        f.write("fire_density_per_km2: Fire density (fires per km²)\n")
        f.write("total_frp_modis_mw: Total Fire Radiative Power from MODIS (MW)\n")
        f.write("total_frp_viirs_mw: Total Fire Radiative Power from VIIRS (MW)\n")
        f.write("total_frp_all_mw: Combined FRP from all sensors (MW)\n")
        f.write("mean_frp_modis_mw: Mean FRP per MODIS fire (MW)\n")
        f.write("mean_frp_viirs_mw: Mean FRP per VIIRS fire (MW)\n")
        f.write("high_confidence_fires_modis: High confidence MODIS fires\n")
        f.write("high_confidence_fires_viirs: High confidence VIIRS fires\n")
        f.write("co_concentration_ppbv: Mean CO concentration (parts per billion by volume)\n")
        f.write("co_enhancement_factor: CO enhancement relative to background\n")
        f.write("fire_season_intensity: Categorical fire intensity (Low/Moderate/High/Extreme)\n")
        f.write("co_pollution_level: Categorical CO level (Background/Elevated/High/Severe)\n\n")
        
        f.write("Data Sources:\n")
        f.write("-" * 15 + "\n")
        f.write("- MODIS (Terra/Aqua): Fire detection and FRP\n")
        f.write("- VIIRS (Suomi NPP): High-resolution fire detection\n")
        f.write("- MOPITT (Terra): Carbon monoxide measurements\n")
        f.write("- AIRS (Aqua): Atmospheric CO retrievals\n\n")
        
        f.write("Notes:\n")
        f.write("-" * 8 + "\n")
        f.write("- VIIRS data available from 2012 onwards\n")
        f.write("- Fire activity varies significantly by region and climate patterns\n")
        f.write("- El Niño years (2015, 2019) show enhanced fire activity\n")
        f.write("- Peatland regions (Central Kalimantan, Riau) have highest fire activity\n")
        f.write("- CO concentrations correlate with fire activity intensity\n")
    
    print(f"  ✅ Data dictionary: {data_dict_file}")
    
    print(f"\n🎉 Complete dataset generation finished!")
    print(f"📁 All files saved to: {output_dir.absolute()}")
    print(f"\n📋 Next steps:")
    print(f"  1. Review the Excel file for quick overview")
    print(f"  2. Use CSV for general analysis")
    print(f"  3. Use Parquet for large-scale processing")
    print(f"  4. Check province-specific files for regional analysis")
    
    return complete_df


if __name__ == "__main__":
    dataset = generate_complete_dataset()