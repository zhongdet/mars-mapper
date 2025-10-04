# tile_calculator.py
import math

def tile_to_lat_lon(z, x, y):
    """將 TMS 瓦片坐標轉換為緯度和經度。"""
    n = 2.0 ** z
    # 經度計算
    lon_deg = x / n * 360.0 - 180.0
    # 緯度計算 (使用 TMS 的 Y 坐標)
    lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * y / n)))
    lat_deg = math.degrees(lat_rad)
    return (lat_deg, lon_deg)

# --- 在這裡輸入您已知的、確實存在的瓦片坐標 ---
# 根據您之前的觀察，我們使用：
zoom = 11
x_tile = 834  # 您的 X 坐標
y_tile = 261  # 您的 Y 坐標 (新的 geodetic 模式下的)
# ----------------------------------------------------

# 為了讓地圖居中，我們計算瓦片中心點的坐標 (x+0.5, y+0.5)
lat, lon = tile_to_lat_lon(zoom, x_tile + 0.5, y_tile + 0.5)

print("-" * 60)
print(f"計算瓦片 (Z={zoom}, X={x_tile}, Y={y_tile}) 中心的坐標...")
print(f"緯度 (Latitude): {lat:.6f}")
print(f"經度 (Longitude): {lon:.6f}")
print("-" * 60)
print("\n請執行以下操作：")
print("1. 打開 app/index.html 文件。")
print("2. 找到 'const map = L.map(...)' 這一行。")
print("3. 用下面這行代碼完全替換它：\n")
# 我們使用比瓦片稍高的縮放級別來看得更清楚
print(f"const map = L.map('map').setView([{lat:.6f}, {lon:.6f}], {zoom + 2});")
print("-" * 60)