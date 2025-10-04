# find_coords.py
import math

def tile_to_lat_lon(z, x, y):
    """Converts TMS tile coordinates to latitude and longitude."""
    n = 2.0 ** z
    lon_deg = x / n * 360.0 - 180.0
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
    lat_deg = math.degrees(lat_rad)
    return (lat_deg, lon_deg)

# --- IMPORTANT ---
# Use the tile coordinates that YOU ACTUALLY HAVE from your 'tree' command.
# In your case, these are:
zoom = 10
x_tile = 417
y_tile = 372
# ---------------

# Calculate the coordinates
lat, lon = tile_to_lat_lon(zoom, x_tile, y_tile)

print("-" * 50)
print("Your data is located near:")
print(f"Latitude: {lat:.4f}, Longitude: {lon:.4f}")
print("-" * 50)
print("\nACTION REQUIRED:")
print("1. Open the file: app/index.html")
print("2. Find the line that starts with 'const map = ...'")
print("3. Replace the ENTIRE line with the following line:\n")
# We use a slightly lower zoom level for the initial view to see more context
print(f"const map = L.map('map').setView([{lat:.4f}, {lon:.4f}], {zoom + 1});")
print("-" * 50)