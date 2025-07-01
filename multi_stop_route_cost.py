import processing
from qgis.core import (
    QgsVectorLayer,
    QgsFeature,
    QgsGeometry,
    QgsPointXY,
    QgsProject,
    QgsCoordinateReferenceSystem,
)

# --- CONFIGURATION ---

# 1. Name of your network layer in the QGIS Layers Panel
network_layer_name = "my_road_network"  # <--- CHANGE THIS

# 2. Name of your point layer containing the stops
stops_layer_name = "my_stops_points"  # <--- CHANGE THIS

# 3. Name of the attribute field in the stops layer that defines the route order
#    This field should contain numbers (e.g., 1, 2, 3, ...)
order_field_name = "order_id"  # <--- CHANGE THIS

# --- SCRIPT LOGIC ---

# --- 1. Fetch and Sort Stop Points from the Layer ---

# Find the stops layer in the current project
stops_layer = QgsProject.instance().mapLayersByName(stops_layer_name)
if not stops_layer:
    raise Exception(f"Stops layer not found: '{stops_layer_name}'")
stops_layer = stops_layer[0]

# Find the network layer in the current project
network_layer = QgsProject.instance().mapLayersByName(network_layer_name)
if not network_layer:
    raise Exception(f"Network layer not found: '{network_layer_name}'")
network_layer = network_layer[0]

# Check if the order field exists in the stops layer
if stops_layer.fields().indexFromName(order_field_name) == -1:
    raise Exception(
        f"Order field '{order_field_name}' not found in layer '{stops_layer_name}'"
    )

# Read all features from the stops layer into a list
stops_features = [f for f in stops_layer.getFeatures()]

# Sort the features based on the value in the order field
try:
    stops_features.sort(key=lambda f: f[order_field_name])
except Exception as e:
    print(
        f"Could not sort features. Ensure the '{order_field_name}' field contains sortable values (like numbers)."
    )
    raise e

# Extract the coordinates from the sorted features
sorted_stops_coords = []
for feature in stops_features:
    geom = feature.geometry()
    point = geom.asPoint()
    sorted_stops_coords.append((point.x(), point.y()))

# Check if we have enough points to create a route
if len(sorted_stops_coords) < 2:
    raise Exception(
        "Fewer than two stops found in the layer. Cannot calculate a route."
    )

print(
    f"Found and sorted {len(sorted_stops_coords)} stops from layer '{stops_layer_name}'."
)

# --- 2. Calculate the Route Segments ---

# Get the CRS from the stops layer to use in the algorithm
stops_crs = stops_layer.crs()
route_segments = []

print("Starting multi-stop shortest path calculation...")

# Iterate through the sorted coordinates to calculate the path between each pair
for i in range(len(sorted_stops_coords) - 1):
    start_coords = sorted_stops_coords[i]
    end_coords = sorted_stops_coords[i + 1]

    start_point_str = f"{start_coords[0]},{start_coords[1]} [{stops_crs.authid()}]"
    end_point_str = f"{end_coords[0]},{end_coords[1]} [{stops_crs.authid()}]"

    print(f"  Calculating segment {i+1}: from stop {i+1} to stop {i+2}")

    # Parameters for the shortest path algorithm
    params = {
        "INPUT": network_layer,
        "STRATEGY": 1,  # 0 for Shortest, 1 for Fastest
        "SPEED_FIELD":"cost",
        "START_POINT": start_point_str,
        "END_POINT": end_point_str,
        "OUTPUT": "memory:",
    }

    # Run the shortest path (point to point) algorithm
    result = processing.run("qgis:shortestpathpointtopoint", params)
    route_segments.append(result["OUTPUT"])

print("...calculation finished.")

# --- 3. Merge Segments and Add to Project ---

if route_segments:
    print("Merging route segments...")

    # Parameters for the merge algorithm
    merge_params = {
        "LAYERS": route_segments,
        "CRS": network_layer.crs(),
        "OUTPUT": "memory:",
    }

    # Run the merge algorithm
    merged_result = processing.run("native:mergevectorlayers", merge_params)

    # Add the final merged route to the QGIS project
    final_route_layer = merged_result["OUTPUT"]
    final_route_layer.setName("Multi-Stop Route (from Layer)")
    QgsProject.instance().addMapLayer(final_route_layer)

    print(
        "Multi-stop route created and added to the project as 'Multi-Stop Route (from Layer)'."
    )
else:
    print("No route segments were calculated.")
