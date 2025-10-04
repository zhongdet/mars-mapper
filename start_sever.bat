@echo off
echo Starting Python HTTP server on port 8000...
echo Open your browser and go to http://localhost:8000/app/
echo.

:: This script is smart. It checks for the local Conda environment's Python.
:: Your Conda environment seems to be in a hidden ".conda" folder.
set "CONDA_PYTHON=.\.conda\python.exe"

if exist %CONDA_PYTHON% (
    echo --- Found and using local Conda Python ---
    %CONDA_PYTHON% -m http.server 8000
) else (
    echo --- Could not find local Conda Python. Using system 'python'. ---
    echo --- This might not work if your packages are only in Conda. ---
    python -m http.server 8000
)

echo Server stopped.
pause