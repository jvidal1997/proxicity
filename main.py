"""
Main orchestration script for the end-to-end real estate data pipeline.

This module coordinates the complete workflow spanning data ingestion, cleaning,
geospatial enrichment, statistical analysis, visualization, and export. It ties
together multiple subsystems—data loaders, API clients, geospatial utilities,
plot generators, and exporters—while providing structured logging and robust
error handling.

Pipeline Overview:
    1. **Environment Initialization**
       - Reloads the `Settings` module to ensure `.env` changes are captured.
       - Reads configuration variables such as input paths, cache directories,
         and export locations.

    2. **Data Loading & Cleaning**
       - Loads the input dataset using `load_and_clean_data`.
       - Removes missing values, unrealistic prices, and non-monthly entries.

    3. **Coordinate Retrieval**
       - Creates API clients required for geocoding.
       - Fetches coordinates for city centers and nearby landmarks.
       - Validates that all requests complete successfully.

    4. **Nearest-Neighbor Enrichment**
       - Uses geographic utilities to compute nearest city centers and
         nearest landmarks for each apartment record.
       - Appends distance metrics to the dataset.

    5. **Statistical Exports**
       - Generates summary statistics and correlation tables via exporters.

    6. **Visualization**
       - Produces static plots: scatter plots, heatmaps, and 3D visualizations.
       - Builds and exports an interactive heatmap using `InteractiveMapBuilder`.

    7. **Regression Modeling**
       - Runs OLS regression models using the enriched dataset.

    8. **Final Data Export**
       - Writes the cleaned, enriched dataset to an Excel file.

Error Handling:
    - `AttributeError`: Raised if settings or environment configuration
      cannot be initialized (e.g., missing `.env` file).
    - `RuntimeError`: Raised when any pipeline step fails (API calls,
      geospatial calculations, plotting, exporting, etc.).
    - All failures are logged using `AsyncFileLogger` to provide asynchronous
      diagnostic output.

Intended Use:
    Run this script as the main entry point for performing full data processing
    and analytics on apartment pricing datasets. Each operation is logged, and
    exceptions halt the pipeline with clear messages for troubleshooting.

Dependencies:
    - pandas, geopandas (implicit in utilities), openpyxl
    - custom modules: data_io, api.clients, geo.nearest_utils,
      visualization tools, analysis.regression, export.exporter
    - configuration via `Settings` and `.env`
    - asynchronous logging via `AsyncFileLogger`
"""
from utils.dataio.data_io import load_and_clean_data, save_xlsx
from api.clients import create_clients
from utils.geo.nearest_utils import append_apartments_with_nearest
from visualization.plot_generator import scatter, heatmap, plot3d
from visualization.interactive_map import InteractiveMapBuilder
from visualization.regression import run_ols_models
import importlib, Settings
from utils.devtools.multithread_logger import AsyncFileLogger

# Instantiate logger
log = AsyncFileLogger()
log.info("Initializing...")

# Force reload in sys.modules to reread .env
importlib.reload(Settings)

try:
    # Access reloaded env
    try:
        log.info("Configuring settings...")
        PROPERTY = Settings.ENV
        log.info("Settings configured successfully")
    except Exception as _:
        raise AttributeError("Settings module could not be initialized. Missing .env file")

    # Load and clean data
    try:
        log.info("Loading and cleaning data...")
        df = load_and_clean_data(PROPERTY["INPUT_DATASET"], PROPERTY["RELEVANT_COLUMNS"])
        log.info("Data successfully loaded and cleaned.")
    except Exception as e:
        log.error("Could not load and clean data")
        raise e

    # Fetch coordinates
    try:
        try:
            log.info("Creating API clients coordinates...")
            city_client, landmark_client = create_clients()
            log.info("API clients successfully generated.")
        except Exception as e:
            raise RuntimeError("Could not create API clients")
        try:
            log.info("Fetching city center coordinates...")
            city_centers = city_client.generate_all_city_centers(df)
            log.info("City centers successfully generated.")
        except Exception as _:
            raise RuntimeError("Could not fetch city center coordinates")
        try:
            log.info("Fetching landmark coordinates...")
            landmarks_by_city = landmark_client.fetch_landmarks_for_cities(df[['cityname','state']].drop_duplicates().values.tolist())
            log.info("Landmarks successfully fetched.")
        except Exception as _:
            raise RuntimeError("Could not fetch landmark coordinates")
    except Exception as e:
        raise RuntimeError(e)

    # Compute nearest distances
    try:
        log.info("Finding and appending nearest neighbor data...")
        df = append_apartments_with_nearest(
            df,
            city_centers,
            landmarks_by_city,
            cache_dir=PROPERTY["BALLTREE_CACHE_DIR"]
        )
        log.info("Data successfully appended.")
    except Exception as _:
        raise RuntimeError("Could not append nearest neighbor data")

    # Clean data again
    df = df[(df['nearest_city_center_miles'] < PROPERTY['MAX_MILE_RANGE']) & (df['nearest_landmark_miles'] < PROPERTY['MAX_MILE_RANGE'])]

    # Generate plots with linear regression
    try:
        log.info("Generating scatter plots...")
        scatter(df, "Price vs Distance to Nearest City Center", "nearest_city_center_miles", "price")
        scatter(df, "Price vs Distance to Nearest Landmark", "nearest_landmark_miles", "price")
        log.info("Plots successfully exported.")
    except Exception as _:
        raise RuntimeError("Scatter plot generation failed.")

    if PROPERTY["ADVANCED_PLOTTING"]:
        # Generate 3D plot
        try:
            log.info("Plotting 3D Plot...")
            plot3d(df, "3D Plot Prices vs Distances", "nearest_city_center_miles", "price", "nearest_landmark_miles", "(mi)", "(mi)", "($USD)")
            log.info("3D Plot successfully exported...")
        except Exception as _:
            raise RuntimeError("Could not create 3D plot")

        # Generate basic heatmap
        try:
            log.info("Creating \'Correlation Heatmap\'...")
            heatmap(df, "Correlation Heatmap")
            log.info("Scatter plot successfully exported.")
        except Exception as _:
            raise RuntimeError("Could not create \'Correlation Heatmap\'")

        # Generate interactive heatmap
        try:
            log.info("Creating \'Interactive Heatmap\' from data...")
            map_builder = InteractiveMapBuilder(city_centers, landmarks_by_city, df)
            log.info("Building \'Interactive Heatmap\' layers...")
            map_builder.build_map()
            log.info("Exporting \'Interactive Heatmap\'...")
            map_builder.save(PROPERTY["INTERACTIVE_MAP_PATH"])
            log.info("Interactive heatmap successfully exported.")
        except Exception as _:
            raise RuntimeError("Could not create \'Interactive Heatmap\'")

        # Run regression models
        try:
            log.info("Creating \'Interactive Heatmap\' from data...")
            log.info("Attempting to run \'Interactive Heatmap\'...")
            run_ols_models(df)
        except Exception as _:
            raise RuntimeError("Could not run \'Interactive Heatmap\'")

    # Save clean dataset
    try:
        log.info("Exporting final data stream")
        save_xlsx(df, PROPERTY["CLEAN_DATASET_PATH"])
        log.info("Final data stream successfully exported.")
    except Exception as _:
        raise RuntimeError("Could not export final data stream")

# AttributeError: If settings aren't loaded through .env file
except AttributeError as attribute_error:
    log.error(f"{attribute_error}")

# Runtime Error: If any of the application processes fail
except RuntimeError as runtime_error:
    log.error("The program ended unexpectedly")