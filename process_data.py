# =============================================================================
# Mars Mapper Data Processing Pipeline
#
# Description:
# This script automates the full pipeline for processing raw HiRISE JP2 images
# from the NASA PDS into a web-mappable format (TMS tiles).
#
# Pipeline Steps:
# 1. (Parallel) Converts raw JP2 images into Cloud-Optimized GeoTIFFs.
# 2. Merges all GeoTIFFs into a single large mosaic using a VRT for efficiency.
# 3. (Parallel) Slices the final mosaic into map tiles suitable for Leaflet.
#
# Author: Your Name
# Date: 2024-10-04
# =============================================================================

import os
import glob
import shutil
import time
import multiprocessing
from concurrent.futures import ProcessPoolExecutor, as_completed

# IMPORTANT: Set the environment variable BEFORE importing GDAL.
# This tells the underlying PROJ library to allow coordinate transformations
# between different celestial bodies (e.g., Mars to an Earth-based web map projection).
# This is the solution to the "Source and target ellipsoid do not belong to the
# same celestial body" error.
os.environ['PROJ_IGNORE_CELESTIAL_BODY'] = 'YES'

# Now, import the GDAL libraries.
from osgeo import gdal
from osgeo_utils import gdal2tiles

# --- Configuration ---

# Enable GDAL/OGR exceptions for cleaner error handling
gdal.UseExceptions()

# Directory paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DATA_DIR = os.path.join(BASE_DIR, "downloaded_data/raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "processed_data")
TILES_DIR = os.path.join(BASE_DIR, "map_tiles")
MERGED_TIF = os.path.join(PROCESSED_DIR, "mosaic.tif")

# Processing settings
# Use slightly fewer workers than total CPUs to keep the system responsive.
NUM_WORKERS = max(1, multiprocessing.cpu_count() - 2)
# Set the desired zoom levels for your map tiles.
ZOOM_LEVELS = "10-18"


def process_single_jp2(jp2_path):
    """
    Worker function to convert a single JP2 file to a tiled, compressed GeoTIFF.
    Designed to be run in a separate process by the ProcessPoolExecutor.
    """
    try:
        basename = os.path.basename(jp2_path)
        output_tif = os.path.join(PROCESSED_DIR, basename.replace('.JP2', '.tif'))
        
        print(f"  -> Starting conversion for: {basename}")
        
        # Define gdal.Translate options for creating a high-performance GeoTIFF.
        translate_options = gdal.TranslateOptions(
            format='GTiff',
            creationOptions=[
                'TILED=YES',          # Important for efficient access
                'COMPRESS=LZW',       # Good lossless compression
                'NUM_THREADS=ALL_CPUS',# Use all threads for compression
                'BIGTIFF=YES'         # Allows files larger than 4GB
            ]
        )
        
        # Execute the conversion
        gdal.Translate(output_tif, jp2_path, options=translate_options)
        
        print(f"  <- Finished conversion for: {basename}")
        return output_tif
    except Exception as e:
        print(f"!!!!!! ERROR processing {os.path.basename(jp2_path)}: {e}")
        return None


def main():
    """Main function to orchestrate the entire processing pipeline."""
    script_start_time = time.time()
    print("========== Mars Data Processing Pipeline (Python API) ==========\n")
    print(f"Using {NUM_WORKERS} parallel workers for processing.")

    # --- Step 0: Clean up previous runs ---
    print("\n--- Step 0: Cleaning up previous run... ---")
    for directory in [PROCESSED_DIR, TILES_DIR]:
        if os.path.exists(directory):
            shutil.rmtree(directory)
        os.makedirs(directory)
    print("--- Cleanup complete ---")

    # --- Step 1: Convert JP2 to GeoTIFF in parallel ---
    print("\n========== Step 1: Converting JP2 files to GeoTIFF (in parallel) ==========")
    step1_start_time = time.time()
    jp2_files = glob.glob(os.path.join(RAW_DATA_DIR, '*.JP2'))
    if not jp2_files:
        print(f"!!!!!! ERROR: No .JP2 files found in '{RAW_DATA_DIR}'. Aborting.")
        return
    
    tif_files = []
    with ProcessPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = {executor.submit(process_single_jp2, jp2_path): jp2_path for jp2_path in jp2_files}
        for future in as_completed(futures):
            result = future.result()
            if result:
                tif_files.append(result)

    if not tif_files or len(tif_files) != len(jp2_files):
        print("!!!!!! ERROR: Some files failed to convert. Aborting pipeline.")
        return
        
    print(f"--- Step 1 finished. Converted {len(tif_files)} files. Took {time.time() - step1_start_time:.2f}s ---")

    # --- Step 2: Merge GeoTIFFs into a single mosaic ---
    print("\n========== Step 2: Merging all GeoTIFFs into a single mosaic ==========")
    step2_start_time = time.time()
    
    # First, build a Virtual Raster (VRT). This is an XML file that points to the
    # other files, acting as a virtual mosaic. It's extremely fast to create.
    vrt_file = os.path.join(PROCESSED_DIR, "mosaic.vrt")
    print("  -> Building VRT...")
    gdal.BuildVRT(vrt_file, tif_files)
    print("  <- VRT built successfully.")
    
    # Second, "materialize" the VRT into a single, large GeoTIFF file.
    # This step does the actual merging and can take time.
    print("  -> Materializing VRT to final TIFF (this may take a while)...")
    merge_options = gdal.TranslateOptions(
        format='GTiff',
        creationOptions=['TILED=YES', 'COMPRESS=LZW', 'NUM_THREADS=ALL_CPUS', 'BIGTIFF=YES']
    )
    gdal.Translate(MERGED_TIF, vrt_file, options=merge_options)
    print(f"--- Step 2 finished. Merged into {os.path.basename(MERGED_TIF)}. Took {time.time() - step2_start_time:.2f}s ---")
    
    # --- Step 3: Generate map tiles from the final mosaic ---
    print("\n========== Step 3: Generating map tiles from the mosaic ==========")
    step3_start_time = time.time()

    # The gdal2tiles Python API can be inconsistent between versions.
    # The most reliable method is to call its main() function, simulating a
    # command-line execution. This is far more stable across different GDAL installs.
    print("  -> Calling gdal2tiles.main() to generate tiles...")
    
    # Construct the argument list for gdal2tiles.main()
    argv = [
        "gdal2tiles.py",                 # A placeholder for the script name
        "--processes=" + str(NUM_WORKERS), # Use parallel processing
        "--zoom=" + ZOOM_LEVELS,           # Set the zoom range
        "--profile=geodetic",            # Use the web mercator profile
        "-w", "leaflet",                 # Generate a Leaflet preview page (old/compatible syntax)
        "-v",                            # Enable verbose output
        MERGED_TIF,                      # Input file
        TILES_DIR                        # Output directory
    ]
    
    print(f"  -> Arguments for gdal2tiles: {' '.join(argv[1:])}")
    gdal2tiles.main(argv)
    
    print(f"--- Step 3 finished. Tiles generated. Took {time.time() - step3_start_time:.2f}s ---")

    total_time = time.time() - script_start_time
    print(f"\n========== All steps completed successfully! ==========")
    print(f"Total processing time: {total_time // 60:.0f} minutes and {total_time % 60:.2f} seconds.")
    print(f"Your map tiles are ready in the '{TILES_DIR}' directory.")
    print("You can now start the web server to view your map.")


if __name__ == '__main__':
    # This check is crucial for multiprocessing to work correctly, especially on Windows.
    # It prevents child processes from re-importing and re-executing the main script's code.
    multiprocessing.freeze_support()
    main()