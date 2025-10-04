# =============================================================================
# Mars Mapper Data Processing Pipeline (Windows-safe)
# =============================================================================

import os
import shutil
import time
import subprocess
from pathlib import Path
from osgeo import gdal
from osgeo_utils import gdal2tiles

# ----------------- GDAL Environment -----------------
os.environ['PROJ_IGNORE_CELESTIAL_BODY'] = 'YES'

# Replace this path with your conda environment's gdal_translate.exe location
GDAL_TRANSLATE_EXE = r"C:\Users\User\miniconda3\envs\mars-mapper\Library\bin\gdal_translate.exe"

# Enable GDAL exceptions
gdal.UseExceptions()

# ----------------- Configuration -----------------
BASE_DIR = Path(__file__).parent.resolve()
RAW_DATA_DIR = BASE_DIR / "downloaded_data" / "raw"
PROCESSED_DIR = BASE_DIR / "processed_data"
TILES_DIR = BASE_DIR / "map_tiles"
MERGED_TIF = PROCESSED_DIR / "mosaic.tif"
ZOOM_LEVELS = "10-18"

# ----------------- JP2 Conversion Worker (CLI) -----------------
def process_single_jp2_cli(jp2_path: Path):
    """
    Convert JP2 → GeoTIFF using the gdal_translate CLI.
    Fully avoids Python UTF-8 decode errors.
    """
    try:
        output_tif = PROCESSED_DIR / jp2_path.name.replace(".JP2", ".tif")
        print(f"  -> Converting {jp2_path.name} to GeoTIFF using gdal_translate...")

        cmd = [
            GDAL_TRANSLATE_EXE,
            "-of", "GTiff",
            "-co", "TILED=YES",
            "-co", "COMPRESS=LZW",
            "-co", "BIGTIFF=YES",
            str(jp2_path),
            str(output_tif)
        ]

        subprocess.run(cmd, check=True)
        print(f"  <- Finished {jp2_path.name}")
        return str(output_tif)

    except subprocess.CalledProcessError as e:
        print(f"!!!!!! ERROR converting {jp2_path.name}: {e}")
        return None

# ----------------- Main Pipeline -----------------
def main():
    script_start_time = time.time()
    print("========== Mars Data Processing Pipeline (gdal_translate CLI) ==========\n")

    # Step 0: Clean previous runs
    print("\n--- Step 0: Cleaning up previous run... ---")
    for directory in [PROCESSED_DIR, TILES_DIR]:
        if directory.exists():
            shutil.rmtree(directory)
        directory.mkdir(parents=True, exist_ok=True)
    print("--- Cleanup complete ---")

    # Step 1: Convert JP2 to GeoTIFF (CLI, Serial)
    print("\n========== Step 1: Converting JP2 files to GeoTIFF (Serial via CLI) ==========")
    step1_start_time = time.time()
    jp2_files = list(RAW_DATA_DIR.glob("*.JP2"))
    if not jp2_files:
        print(f"!!!!!! ERROR: No .JP2 files found in '{RAW_DATA_DIR}'. Aborting.")
        return

    tif_files = []
    for jp2_path in jp2_files:
        result = process_single_jp2_cli(jp2_path)
        if result:
            tif_files.append(result)

    if not tif_files or len(tif_files) != len(jp2_files):
        print("!!!!!! ERROR: Some files failed to convert. Aborting pipeline.")
        return

    print(f"--- Step 1 finished. Converted {len(tif_files)} files. Took {time.time() - step1_start_time:.2f}s ---")

    # Step 2: Merge GeoTIFFs into a mosaic
    print("\n========== Step 2: Merging all GeoTIFFs into a single mosaic ==========")
    step2_start_time = time.time()
    vrt_file = PROCESSED_DIR / "mosaic.vrt"
    print("  -> Building VRT...")
    gdal.BuildVRT(str(vrt_file), tif_files)
    print("  <- VRT built successfully.")

    print("  -> Materializing VRT to final TIFF...")
    merge_options = gdal.TranslateOptions(
        format='GTiff',
        creationOptions=['TILED=YES','COMPRESS=LZW','NUM_THREADS=ALL_CPUS','BIGTIFF=YES']
    )
    gdal.Translate(str(MERGED_TIF), str(vrt_file), options=merge_options)
    print(f"--- Step 2 finished. Merged into {MERGED_TIF.name}. Took {time.time() - step2_start_time:.2f}s ---")

    # Step 3: Generate map tiles (Parallel via gdal2tiles)
    print("\n========== Step 3: Generating map tiles from the mosaic ==========")
    step3_start_time = time.time()
    argv = [
        "gdal2tiles.py",
        "--processes=4",
        "--zoom=" + ZOOM_LEVELS,
        "--profile=geodetic",
        "-w", "leaflet",
        "-v",
        str(MERGED_TIF),
        str(TILES_DIR)
    ]
    print(f"  -> Arguments for gdal2tiles: {' '.join(argv[1:])}")
    gdal2tiles.main(argv)
    print(f"--- Step 3 finished. Tiles generated. Took {time.time() - step3_start_time:.2f}s ---")

    total_time = time.time() - script_start_time
    print(f"\n========== All steps completed successfully! ==========")
    print(f"Total processing time: {total_time // 60:.0f} minutes and {total_time % 60:.2f} seconds.")
    print(f"Your map tiles are ready in the '{TILES_DIR}' directory.")

# ----------------- Entry Point -----------------
if __name__ == '__main__':
    main()
