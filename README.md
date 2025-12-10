# Proxicity

### Ingestion - Cleaning - Geospatial Enrichment - Visualization - Regression - Export

This repository contains a fully orchestrated **rental price analytics pipeline** driven by the `main.py` script.
 It automates data ingestion, cleaning, coordinate retrieval, nearest-neighbor enrichment, statistical exports, visualization, and regression modeling using a modular collection of utilities.

The pipeline is designed for **city-level apartment pricing datasets** and includes **robust logging**, **API-based geocoding**, and both **static** and **interactive** visualization outputs.



## Features

- **Automatic environment initialization** using `Settings` and `.env`
- **Data loading & preprocessing**: cleaning invalid entries, enforcing monthly by month rental data, removing outliers
- **Geospatial enrichment** using API clients
  - city center coordinates
  - nearby landmark coordinates
- **Nearest-neighbor computation** using BallTree caching
- **Statistical exports**: summary metrics and correlation tables
- **Visualization suite**
  - scatter plots with regression
  - 3D visualizations
  - correlation heatmap
  - fully interactive geospatial heatmap
- **Regression modeling (OLS)** using the enriched dataset
- **Final cleaned dataset export** to Excel
- **Asynchronous logging** for reliable output during long-running tasks



# Pipeline Overview

### 1. **Environment Initialization**

- Reloads `Settings` to pick up `.env` changes
- Reads configuration paths, cache directories, and export locations

### 2. **Data Loading & Cleaning**

- Uses `load_and_clean_data`
- Drops rows with missing values or unrealistic price values
- Ensures only monthly entries remain

### 3. **Coordinate Retrieval**

- Creates geocoding API clients
- Fetches:
  - city center coordinates for all cities in the dataset
  - landmark coordinates grouped by city
- Ensures API calls succeed before proceeding

### 4. **Nearest-Neighbor Enrichment**

- Computes:
  - distance to nearest city center
  - distance to nearest local landmark
- Uses efficient geospatial utilities with cached BallTree lookups
- Appends results to the DataFrame

### 5. **Statistical Outputs**

- Generates summary tables and correlation matrices
- Exports via custom exporters

### 6. **Visualization**

- Scatter plots using distance metrics vs. price
- Correlation heatmap
- Configurable 3D plots
- Interactive heatmap exported via `InteractiveMapBuilder`

### 7. **Regression Modeling**

- Runs OLS regression on enriched features

### 8. **Final Data Export**

- Saves cleaned and enriched dataset to Excel via `save_xlsx`



# Project Structure

| File/Folder                            | Type              | Description                                                  |
| -------------------------------------- | ----------------- | ------------------------------------------------------------ |
| `main.py`                              | File              | Main entry point for running the pipeline                    |
| `Settings.py`                          | File              | Loads configuration from `.env`                              |
| `README.md`                            | File              | Project documentation                                        |
| `api/`                                 | Folder            | External API clients for geocoding                           |
| `api/clients.py`                       | File              | API client implementations                                   |
| `utils/`                               | Folder            | Utility modules for data processing, logging, and geospatial calculations |
| `utils/dataio/`                        | Folder            | Data input/output utilities                                  |
| `utils/dataio/data_io.py`              | File              | Functions to load and clean datasets, save Excel files       |
| `utils/geo/`                           | Folder            | Geospatial utilities                                         |
| `utils/geo/nearest_utils.py`           | File              | Functions for nearest-neighbor calculations                  |
| `utils/devtools/`                      | Folder            | Developer tools                                              |
| `utils/devtools/multithread_logger.py` | File              | Asynchronous logging utilities                               |
| `visualization/`                       | Folder            | Plotting and visualization modules                           |
| `visualization/plot_generator.py`      | File              | Static scatter plots, heatmaps, and 3D plots                 |
| `visualization/interactive_map.py`     | File              | Build interactive geospatial maps                            |
| `visualization/regression.py`          | File              | OLS regression modeling functions                            |
| `export/`                              | Folder (optional) | Exporters for datasets and reports                           |
| `data/`                                | Folder (optional) | Raw or processed datasets                                    |
| `cache/`                               | Folder (optional) | BallTree or geospatial cache files                           |



# Dependencies

### Core Libraries

- `pandas`
- `geopandas` (implicit in geospatial utilities)
- `openpyxl`

### Custom Modules

- `data_io`
- `api.clients`
- `geo.nearest_utils`
- `visualization.plot_generator`
- `visualization.interactive_map`
- `analysis.regression`
- `export.exporter` (if included)

### Other Components

- Configuration via `Settings` + `.env`
- Asynchronous logging via `AsyncFileLogger`



# Configuration

All variables are read from your `.env` via the `Settings` module.

Example values you may include:

```
INPUT_DATASET=./data/raw/apartments.csv
RELEVANT_COLUMNS=price,cityname,state,date
BALLTREE_CACHE_DIR=./cache/
CLEAN_DATASET_PATH=./exports/cleaned.xlsx
INTERACTIVE_MAP_PATH=./exports/interactive_map.html
MAX_MILE_RANGE=50
ADVANCED_PLOTTING=True
```

------

# Running the Pipeline

To run the full pipeline, run `main`



Optionally, run the following from console:

```
python main.py
```

The script logs progress asynchronously using `AsyncFileLogger`.



# Error Handling

The pipeline includes robust exception handling with descriptive logs:

| Error Type       | Trigger                                                      | Notes                                |
| ---------------- | ------------------------------------------------------------ | ------------------------------------ |
| `AttributeError` | Missing or invalid `.env` via `Settings`                     | Stops pipeline early                 |
| `RuntimeError`   | Failure in any step (API calls, geospatial ops, plots, exports) | Logged and reported cleanly          |
| Logged Failures  | All exceptions recorded by `AsyncFileLogger`                 | Ensures consistent diagnostic output |



# Outputs

Depending on configuration, the pipeline exports:

- Cleaned & enriched dataset (`.xlsx`)
- Scatter plots (static)
- 3D plot (`.png` or similar)
- Correlation heatmap
- Fully interactive geospatial heatmap (`.html`)
- Regression summary tables



# Intended Use

`main.py` serves as the **primary entry point** for conducting full-scale data processing and analytics on the rental price dataset.
 It is ideal for:

- property price analysis
- city-level geospatial research
- regression modeling of urban housing data
- automated batch reporting