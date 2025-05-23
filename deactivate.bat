@echo off
echo Deactivating pipenv virtual environment...
set VIRTUAL_ENV=
set PIPENV_ACTIVE=
echo Virtual environment deactivated. You can now use uv commands directly.
echo.
echo To use this project:
echo   uv sync          - Install dependencies
echo   uv run main.py   - Run the application
echo   build.bat        - Build executable 