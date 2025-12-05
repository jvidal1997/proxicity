from dataio.data_io import load_and_clean_data, save_xlsx
from api.clients import create_clients
from geo.nearest_utils import append_apartments_with_nearest
from visualization.plot_generator import scatter, heatmap, plot3d
from visualization.interactive_map import InteractiveMapBuilder
from analysis.regression import run_ols_models
from export.exporter import export_summary, export_correlation
import importlib, Settings

# Force reload in sys.modules to reread .env
importlib.reload(Settings)

# Access reloaded env
PROPERTY = Settings.ENV
# print(PROPERTY)
# print()



# Load and clean data
df = load_and_clean_data(PROPERTY["INPUT_DATASET"], PROPERTY["RELEVANT_COLUMNS"])

# Fetch coordinates
city_client, landmark_client = create_clients()
city_centers = city_client.generate_all_city_centers(df)
landmarks_by_city = landmark_client.fetch_landmarks_for_cities(df[['cityname','state']].drop_duplicates().values.tolist())

# Compute nearest distances
df = append_apartments_with_nearest(
    df,
    city_centers,
    landmarks_by_city,
    cache_dir=PROPERTY["BALLTREE_CACHE_DIR"]
)

# Export stats & correlation
export_summary(df, PROPERTY["STAT_SUMMARY_PATH)"])
export_correlation(df, PROPERTY["CORRELATION_SUMMARY_PATH)"])

# Generate plots
scatter(df, "Price vs Distance to Nearest City Center", "nearest_city_center_miles", "price")
scatter(df, "Price vs Distance to Nearest Landmark", "nearest_landmark_miles", "price")
plot3d(df, "3D Plot Prices vs Distances", "nearest_city_center_miles", "nearest_landmark_miles", "price", "(mi)", "(mi)", "($USD)")
heatmap(df, "Correlation Heatmap")

# Generate interactive heatmap
map_builder = InteractiveMapBuilder(city_centers, landmarks_by_city, df)
map_builder.build_map()
map_builder.save(PROPERTY["INTERACTIVE_MAP_PATH"])

# Run regression models
run_ols_models(df)

# Save clean dataset
save_xlsx(df, PROPERTY["CLEAN_DATASET_PATH"])