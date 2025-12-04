import folium
from folium.plugins import HeatMap


class InteractiveMapBuilder:
    def __init__(self, city_centers: dict, landmarks: dict, df):
        """
        city_centers: dict of "City, State" → {"lat": ..., "lon": ...}
        landmarks: dict of "City, State" → [ {name, lat, lon}, ... ]
        df: cleaned dataframe with latitude, longitude, price, etc.
        """
        self.city_centers = city_centers
        self.landmarks = landmarks
        self.df = df
        self.map = None

    def build_map(self):
        print("Building interactive heatmap...")

        # Base map centered on the US
        self.map = folium.Map(location=[39.5, -98.35], zoom_start=4)
        print("Base empty map created.")

        # Feature groups
        city_group = folium.FeatureGroup(name="City Centers")
        landmark_group = folium.FeatureGroup(name="Landmarks")
        price_heatmap = folium.FeatureGroup(name="Price Heatmap")
        density_heatmap = folium.FeatureGroup(name="Listing Density Heatmap")

        print("Building city center markers...")
        for city_key, coords in self.city_centers.items():
            if coords is None:
                continue
            folium.Marker(
                location=[coords["lat"], coords["lon"]],
                popup=city_key,
                icon=folium.Icon(color="red", icon="glyphicon glyphicon-home")
            ).add_to(city_group)
        print("City center markers created.")

        print("Building landmark markers...")
        for city_key, items in self.landmarks.items():
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
        print("Landmark markers created.")

        print("Building price heatmap...")
        heat_df = self.df[['latitude', 'longitude', 'price']].dropna()
        if not heat_df.empty:
            HeatMap(
                heat_df.values.tolist(),
                radius=5,
                blur=5
            ).add_to(price_heatmap)
        print("Price heatmap created.")

        print("Building density heatmap...")
        density_df = self.df[['latitude', 'longitude']].dropna()
        if not density_df.empty:
            HeatMap(
                density_df.values.tolist(),
                radius=2,
                blur=3
            ).add_to(density_heatmap)
        print("Density heatmap created.")

        print("Attaching layers...")
        city_group.add_to(self.map)
        landmark_group.add_to(self.map)
        price_heatmap.add_to(self.map)
        density_heatmap.add_to(self.map)
        print("Layers added.")

        # Layer control toggle menu
        folium.LayerControl(collapse=False).add_to(self.map)
        print("Controls added.")

        print("Interactive map built successfully.")

    def save(self, output_path: str):
        if self.map is None:
            raise RuntimeError("Map has not been built yet. Call build_map() first.")
        print(f"Saving interactive map to {output_path}...")
        self.map.save(output_path)
        print("Map saved successfully.")
