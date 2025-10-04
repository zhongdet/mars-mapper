# Mars Mapper - 火星地圖製作入門專案

歡迎使用！本專案將引導您將 NASA PDS 的原始 HiRISE 影像資料，轉換成一個可以在網頁瀏覽器中互動的地圖。

## 系統需求

在開始之前，請確保您的電腦已安裝以下軟體：

1.  **Python 3**: [官方下載頁面](https://www.python.org/downloads/)。安裝時請務必勾選 "Add Python to PATH"。
2.  **GDAL**: 這是最強大的地理空間數據處理函式庫。
    - **推薦方式 (使用 Conda)**: 如果您不熟悉 GDAL 的安裝，建議先安裝 [Miniconda](https://docs.conda.io/en/latest/miniconda.html)，然後在終端機執行 `conda install -c conda-forge gdal`。
    - **其他方式**: 您也可以參考 [GDAL 官方安裝說明](https://gdal.org/download.html)，但過程可能較為複雜。

安裝完成後，在您的終端機 (命令提示字元或 PowerShell) 輸入 `gdalinfo --version`，如果能看到版本號，代表安裝成功。

## 操作步驟

### 步驟一：下載火星原始資料

1.  前往 HiRISE DTM 數據庫，例如這個目錄：[https://hirise-pds.lpl.arizona.edu/PDS/DTM/ESP/](https://hirise-pds.lpl.arizona.edu/PDS/DTM/ESP/)
2.  選擇一個您感興趣的 `ORB_...` 資料夾，再進入一個 `ESP_...` 資料夾。
3.  **下載所有後綴為 `_RED...ORTHO.JP2` 的檔案**。這些是正射校正後的影像。通常一個資料夾會有 2 到 4 個這樣的檔案。
4.  將下載好的所有 `.JP2` 檔案，**全部放入 `1_downloaded_data/raw/` 這個資料夾內**。

> **範例**: 假設您進入 `ORB_011200_011299/ESP_011265_1560_ESP_011331_1560/`，您應該下載以下四個檔案：
>
> - `ESP_011265_1560_RED_A_01_ORTHO.JP2`
> - `ESP_011265_1560_RED_C_01_ORTHO.JP2`
> - `ESP_011331_1560_RED_A_01_ORTHO.JP2`
> - `ESP_011331_1560_RED_C_01_ORTHO.JP2`
>
> 然後把它們都放進 `1_downloaded_data/raw/`。

### 步驟二：執行數據處理腳本

1.  打開您的終端機 (命令提示字元、PowerShell、Terminal)。
2.  使用 `cd` 命令，切換到 `mars-mapper` 這個專案的根目錄。
3.  執行 Python 腳本：
    ```bash
    python process_data.py
    ```
4.  腳本會開始自動執行以下任務，請耐心等待：

    - 將 `raw` 資料夾中的 JP2 影像轉換為 GeoTIFF 格式。
    - 將所有 GeoTIFF 影像合併成一張大的馬賽克影像。
    - 將合併後的大影像切割成網頁地圖用的圖磚 (Tiles)。

    當您看到 "All steps completed successfully!" 的訊息時，代表處理完成。

### 步驟三：啟動網頁伺服器並查看地圖

1.  **Windows 使用者**: 直接雙擊 `start_server.bat` 檔案。
2.  **macOS / Linux 使用者**: 在終端機中執行 `./start_server.sh` (可能需要先執行 `chmod +x start_server.sh` 給予執行權限)。
3.  您的終端機將會顯示類似 `Serving HTTP on 0.0.0.0 port 8000 (http://0.0.0.0:8000/) ...` 的訊息。
4.  打開您的網頁瀏覽器 (推薦 Chrome 或 Firefox)，訪問以下網址：
    [http://localhost:8000/app/](http://localhost:8000/app/)

現在，您應該能看到並操作您親手製作的火星地圖了！

### 疑難排解與進階

- **地圖是空白的？**
  - 按 `F12` 打開瀏覽器開發者工具，查看 "Console" 和 "Network" 標籤頁是否有錯誤訊息。最常見的是圖磚路徑錯誤或檔案找不到 (404)。
  - 請確保 `3_map_tiles` 資料夾內已經生成了許多數字命名的資料夾。
- **如何調整地圖初始位置？**
  - 編輯 `app/index.html` 檔案，找到 `L.map('map').setView(...)` 這一行。第一個參數是緯度和經度的陣列 `[lat, lng]`，第二個是縮放層級。您需要手動調整這些值，讓地圖一打開就對準您感興趣的區域。
- **下一步：3D 地圖**
  - 這個專案使用的是 Leaflet.js 製作 2D 地圖。如果您想挑戰 3D，可以研究 **CesiumJS**。您需要用類似的流程處理 `DTEEC...IMG` 地形檔，生成地形圖磚，然後在 CesiumJS 中同時載入影像圖磚和地形圖磚。
