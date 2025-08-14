# Indonesia Forest Fire Analysis System

A comprehensive satellite-based system for extracting and analyzing forest fire data and carbon monoxide concentrations across Indonesian districts from 2010-2020.

## Overview

This system extracts and processes:
- **Active fire occurrences** from MODIS (Terra/Aqua) and VIIRS (Suomi NPP) satellites
- **Fire Radiative Power (FRP)** measurements 
- **Carbon Monoxide (CO) concentrations** from MOPITT and AIRS sensors
- **District-level aggregation** for all Indonesian administrative districts

##  Data Sources

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


## Output Products

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

##System Architecture

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

## Acknowledgments

- NASA Fire Information for Resource Management System (FIRMS)
- NASA Goddard Earth Sciences Data and Information Services Center
- NCAR Atmospheric Chemistry Observations and Modeling Lab
- Database of Global Administrative Areas (GADM)

