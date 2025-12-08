"""
Provides the InteractiveMapBuilder class for creating interactive Folium maps of apartment/listing data.
Maps include city center markers, landmark markers, price heatmaps, and listing density heatmaps.
Supports layer control toggling and saving the map to an HTML file.

Classes:
- InteractiveMapBuilder(city_centers, landmarks, df): Builds and saves interactive maps with multiple layers.
"""
import folium
from folium.plugins import HeatMap
from utils.devtools.multithread_logger import AsyncFileLogger
from tqdm import tqdm
log = AsyncFileLogger()


class InteractiveMapBuilder:

    def __init__(self, city_centers: dict, landmarks: dict, df):
        """
        Initializes the InteractiveMapBuilder with city centers, landmarks, and apartment/listing data.
        Sets up an empty map placeholder.
        :param city_centers: DataFrame of city centers.
        :param landmarks: DataFrame of landmarks.
        :param df: DataFrame of apartment/listing data.
        """
        self.city_centers = city_centers
        self.landmarks = landmarks
        self.df = df
        self.map = None
        log.info("InteractiveMapBuilder initialized with data.")

    def build_map(self):
        """
        Builds an interactive Folium map with multiple layers: city center markers, landmark markers, price heatmap,
        and listing density heatmap. Adds a layer control menu and stores the map in self.map
        """

        # Base map centered on the US
        log.info("Building interactive map...")
        self.map = folium.Map(location=[39.5, -98.35], zoom_start=4)
        log.info("Base empty map created.")

        # Feature groups
        log.info("Creating feature groups...")
        city_group = folium.FeatureGroup(name="City Centers")
        landmark_group = folium.FeatureGroup(name="Landmarks")
        price_heatmap = folium.FeatureGroup(name="Price Heatmap")
        density_heatmap = folium.FeatureGroup(name="Listing Density Heatmap")
        log.info("Groups created.")

        # City Center Markers
        log.info("Building city-center markers layer...")
        for city_key, coords in tqdm(self.city_centers.items(), desc="Building city-center markers layer...", colour="green"):
            if coords is None:
                continue
            folium.Marker(
                location=[coords["lat"], coords["lon"]],
                popup=city_key,
                icon=folium.Icon(color="red", icon="glyphicon glyphicon-home")
            ).add_to(city_group)
        log.info("City-center markers layer created.")

        # Landmark Markers
        log.info("Building landmark markers layer...")
        for city_key, items in tqdm(self.landmarks.items(), desc="Building landmark markers layer...", colour="green"):
            if not items:
                continue
            for lm in items:
                if lm["lat"] is None or lm["lon"] is None:
                    continue
                folium.Marker(
                    location=[lm["lat"], lm["lon"]],
                    popup=lm["name"] or "Unknown Landmark",
                    icon=folium.Icon(color="green", icon="glyphicon glyphicon-star")
                ).add_to(landmark_group)
        log.info("Landmark markers layer created.")

        # Price Heatmap
        log.info("Building price heatmap layer...")
        heat_df = self.df[['latitude', 'longitude', 'price']].dropna()
        if not heat_df.empty:
            HeatMap(
                heat_df.values.tolist(),
                radius=5,
                blur=5
            ).add_to(price_heatmap)
        log.info("Price heatmap layer created.")

        # Density Heatmap
        log.info("Building density heatmap layer...")
        density_df = self.df[['latitude', 'longitude']].dropna()
        if not density_df.empty:
            HeatMap(
                density_df.values.tolist(),
                radius=2,
                blur=3
            ).add_to(density_heatmap)
        log.info("Density heatmap layer created.")

        # Attach Layers
        log.info("Attaching layers...")
        city_group.add_to(self.map)
        landmark_group.add_to(self.map)
        price_heatmap.add_to(self.map)
        density_heatmap.add_to(self.map)
        log.info("Layers added.")

        # Add Controls
        log.info("Adding map controls...")
        folium.LayerControl(collapse=False).add_to(self.map)
        log.info("Controls added.")

        log.info("Interactive map built successfully.")

    def save(self, output_path: str):
        """
        Saves the built interactive map to the specified HTML file path.
        Raises a RuntimeError if build_map() has not been called.
        :param output_path: Path to output HTML file.
        """
        if self.map is None:
            log.error("Building interactive map failed.")
            raise RuntimeError("Map has not been built yet. Call build_map() first.")
        log.info(f"Saving interactive map to {output_path}...")
        self.map.save(output_path)
        log.info("Map saved successfully.")
