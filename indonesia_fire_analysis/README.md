# Indonesia Forest Fire Analysis System

A comprehensive satellite-based system for extracting and analyzing forest fire data and carbon monoxide concentrations across Indonesian districts from 2010-2020.

## 🔥 Overview

This system extracts and processes:
- **Active fire occurrences** from MODIS (Terra/Aqua) and VIIRS (Suomi NPP) satellites
- **Fire Radiative Power (FRP)** measurements 
- **Carbon Monoxide (CO) concentrations** from MOPITT and AIRS sensors
- **District-level aggregation** for all Indonesian administrative districts

## 🛰️ Data Sources

### Fire Detection
- **MODIS Collections**: MCD14ML (active fire), MOD14A1/MYD14A1 (thermal anomalies)
- **VIIRS Collections**: VNP14IMGML (active fire), VNP14IMG (thermal anomalies)
- **Temporal Coverage**: 2010-2020 (MODIS), 2012-2020 (VIIRS)
- **Spatial Resolution**: 1km (MODIS), 375m (VIIRS)

### Carbon Monoxide
- **MOPITT (Terra)**: Daily CO profiles and total column
- **AIRS (Aqua)**: Daily atmospheric CO retrievals  
- **Variables**: CO mixing ratios, total column, quality flags

### Administrative Boundaries
- **Source**: GADM Level 2 (District/Kabupaten/Kota level)
- **Coverage**: All Indonesian provinces and districts
- **Format**: Geospatial polygons with metadata

## 🚀 Quick Start

### 1. Installation

```bash
# Clone or download the project
cd indonesia_fire_analysis

# Install dependencies
pip install -r requirements.txt
```

### 2. Generate Sample Configuration

```bash
python run_analysis.py config
```

This creates `config_sample.yaml` with default settings.

### 3. Configure Analysis

```bash
# Copy and modify configuration
cp config_sample.yaml config.yaml
# Edit config.yaml with your preferred settings
```

### 4. Run Analysis

```bash
# Quick analysis with defaults
python run_analysis.py quick

# Custom analysis with date range
python run_analysis.py custom --start-date 2019-01-01 --end-date 2019-12-31

# Debug mode
python run_analysis.py quick --debug --log-level DEBUG
```

## 📊 Output Products

### Data Formats
- **CSV**: Tabular data without geometry
- **GeoJSON**: Geospatial data for web mapping
- **Parquet**: Efficient binary format
- **NetCDF**: Scientific data format with metadata

### Visualizations
- **Interactive maps**: Fire density and CO concentration by district
- **Dashboard**: Multi-panel statistical overview
- **Time series**: Temporal patterns and trends
- **Summary report**: Comprehensive analysis document

### Directory Structure
```
output/
├── raw/                    # Raw satellite data
├── processed/              # Intermediate processing results
├── final/                  # Final aggregated datasets
└── visualizations/         # Maps, charts, and reports
```

## 🛠️ System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Data Sources  │    │   Extractors     │    │  Spatial Proc.  │
├─────────────────┤    ├──────────────────┤    ├─────────────────┤
│ • MODIS Active  │───▶│ • MODIS Extract  │───▶│ • Boundary Load │
│ • VIIRS Active  │    │ • VIIRS Extract  │    │ • Spatial Join  │
│ • MOPITT CO     │    │ • CO Extract     │    │ • Aggregation   │
│ • AIRS CO       │    │                  │    │                 │
│ • Admin Bounds  │    │                  │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
┌─────────────────┐    ┌──────────────────┐              │
│  Visualization  │    │   Final Output   │◀─────────────┘
├─────────────────┤    ├──────────────────┤
│ • Interactive   │◀───│ • Combined Data  │
│   Maps          │    │ • Statistics     │
│ • Dashboards    │    │ • Validation     │
│ • Time Series   │    │ • Export         │
│ • Reports       │    │                  │
└─────────────────┘    └──────────────────┘
```

## 📝 Configuration

Key configuration sections in `config.yaml`:

### Temporal Range
```yaml
temporal:
  start_date: "2010-01-01"
  end_date: "2020-12-31"
```

### Data Sources
```yaml
data_sources:
  modis:
    collections: ["MCD14ML", "MOD14A1", "MYD14A1"]
  viirs:
    collections: ["VNP14IMGML"]
  co:
    collections: ["MOP02J", "AIRX3STD"]
```

### Processing Options
```yaml
processing:
  parallel_workers: 4
  quality_flags:
    confidence_threshold: 7
    frp_threshold: 0
```

## 🗺️ Spatial Coverage

- **Country**: Indonesia
- **Administrative Level**: District (Kabupaten/Kota)
- **Total Districts**: ~500+ districts across 34 provinces
- **Coordinate System**: WGS84 (EPSG:4326)
- **Bounding Box**: 94.77°E to 141.02°E, 11.01°S to 6.08°N

## 📈 Key Metrics

### Fire Statistics
- **Fire count** by sensor and district
- **Fire Radiative Power** (total, mean, maximum)
- **Fire density** (fires per km²)
- **Temporal patterns** (first/last fire dates, fire days)
- **Confidence levels** and quality flags

### CO Analysis
- **Mean concentrations** by district
- **Temporal trends** and seasonality
- **Vertical profiles** (pressure levels)
- **Fire-CO correlations** and enhancement factors

## 🔬 Methodology

### Fire Detection
1. Download active fire locations from NASA FIRMS
2. Apply quality filters (confidence thresholds)
3. Spatially join fire points with district boundaries
4. Aggregate statistics by district and time period

### CO Processing
1. Extract gridded CO data from satellite retrievals
2. Mask data to district boundaries
3. Calculate statistical measures (mean, std, percentiles)
4. Analyze temporal patterns and trends

### Validation
- Cross-sensor comparison (MODIS vs VIIRS)
- Quality flag assessment
- Spatial coverage validation
- Temporal consistency checks

## 🐍 Python API

```python
from src.main import main
from src.utils.config_loader import ConfigLoader

# Load configuration
config = ConfigLoader.load_config("config.yaml")

# Run full analysis
results = main()

# Access specific components
from src.data_extraction.modis_extractor import MODISExtractor
from src.spatial_processing.aggregator import SpatialAggregator

modis = MODISExtractor(config)
fire_data = modis.extract_fire_data("2019-01-01", "2019-12-31", bbox)
```

## 📊 Sample Results

### Fire Activity (2010-2020)
- **Total MODIS fires**: ~2.5 million detections
- **Total VIIRS fires**: ~4.2 million detections  
- **Peak fire years**: 2015, 2019 (El Niño years)
- **Most affected provinces**: Central Kalimantan, Riau, South Sumatra

### CO Concentrations
- **Background levels**: 100-200 ppbv
- **Fire-enhanced levels**: 500-2000 ppbv
- **Seasonal peaks**: August-October (dry season)
- **Highest concentrations**: Peatland regions

## 🔧 Troubleshooting

### Common Issues

1. **Missing dependencies**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

2. **Memory errors with large datasets**
   - Reduce temporal range in config
   - Lower parallel_workers setting
   - Use smaller chunk_size

3. **Network timeouts**
   - Check internet connection
   - Verify NASA API credentials
   - Retry with smaller date ranges

4. **Projection errors**
   - Ensure all data uses WGS84 (EPSG:4326)
   - Check CRS consistency in config

### Debug Mode
```bash
python run_analysis.py quick --debug --log-level DEBUG
```

## 📄 Data Citations

When using this system, please cite:

- **MODIS Fire**: NASA FIRMS, doi:10.5067/FIRMS/MODIS/MCD14ML
- **VIIRS Fire**: NASA FIRMS, doi:10.5067/FIRMS/VIIRS/VNP14IMGML  
- **MOPITT CO**: NCAR/UCAR, doi:10.5067/TERRA/MOPITT/MOP02J_L2.009
- **AIRS CO**: NASA GES DISC, doi:10.5067/AQUA/AIRS/DATA303
- **Admin Boundaries**: GADM, www.gadm.org

## 📞 Support

For questions or issues:
- Check the troubleshooting section above
- Review log files in `logs/` directory  
- Examine sample configurations and outputs
- Validate input data and configuration parameters

## 🙏 Acknowledgments

- NASA Fire Information for Resource Management System (FIRMS)
- NASA Goddard Earth Sciences Data and Information Services Center
- NCAR Atmospheric Chemistry Observations and Modeling Lab
- Database of Global Administrative Areas (GADM)

---

*Generated by Indonesia Fire Analysis System - Extracting insights from satellite observations for forest fire monitoring and atmospheric analysis.*