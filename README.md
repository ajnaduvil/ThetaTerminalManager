# ThetaData Terminal Manager

A Python application for managing ThetaTerminal.jar with a simple GUI interface.

## Features

- Automatically downloads ThetaTerminal.jar if not present
- Saves and loads username/password credentials
- Start and stop ThetaTerminal with a click
- Log viewing with clear and copy functionality
- Password reveal option for ease of use

## Requirements

- Python 3.12 or newer
- Java Runtime Environment (JRE) for running ThetaTerminal.jar
- uv package manager

## Installation

1. Clone this repository
2. Install uv if you haven't already:
   ```
   # On Windows
   powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
   
   # On macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Or with pip
   pip install uv
   ```

3. Install dependencies and create virtual environment:
   ```
   uv sync
   ```

## Usage

Run the application:
```
uv run main.py
```

Or activate the virtual environment and run directly:
```
# Activate the environment
source .venv/bin/activate  # On Unix/macOS
# or
.venv\Scripts\activate     # On Windows

# Run the application
python main.py
```

1. Enter your ThetaData username and password
2. Click "Start" to launch the terminal
3. The log area will display output from the terminal
4. Click "Stop" to terminate the terminal when done

## Development

To work on the project:

1. Install development dependencies:
   ```
   uv sync --dev
   ```

2. Add new dependencies:
   ```
   uv add package-name
   ```

3. Add development dependencies:
   ```
   uv add --dev package-name
   ```

## Building Executable

To build a standalone executable:

### Using the build script (recommended)

1. Ensure dependencies are installed:
   ```
   uv sync
   ```

2. On Windows, run:
   ```
   build.bat
   ```
   
   Or run the Python build script directly:
   ```
   uv run build.py
   ```

3. The executable will be created in the `dist` directory

### Using PyInstaller directly

You can also build with PyInstaller directly:

```
uv run pyinstaller --name=ThetaDataTerminalManager --onefile --windowed main.py
```

## Structure

- `main.py` - Entry point for the application
- `app/terminal_manager.py` - Core logic for managing the terminal
- `app/ui/main_window.py` - User interface implementation
- `build.py` - Build script for creating the executable
- `pyproject.toml` - Project configuration and dependencies

## License

MIT

## Troubleshooting

### Virtual Environment Conflicts

If you see warnings about `VIRTUAL_ENV` not matching or if you have an old pipenv environment active, you can:

1. Run `deactivate.bat` to clear old virtual environment variables
2. Or manually deactivate pipenv: `exit` from the pipenv shell
3. The `build.bat` script automatically handles this by clearing environment variables

### Build Issues

If the build fails:
1. Ensure all dependencies are installed: `uv sync`
2. Check that Python 3.12+ is available
3. Verify Java Runtime Environment is installed for ThetaTerminal.jar

### Icon Issues

If the executable doesn't show the custom icon:

1. **Verify icon is included**: The build script will show "Using icon: --icon=app\resources\icon.ico" if found
2. **Refresh Windows icon cache**: Run `refresh_icon.bat` to clear and refresh the icon cache
3. **Check icon format**: Ensure the icon.ico file is a valid Windows icon format
4. **Alternative icons**: The build script will try these files in order:
   - `app/resources/icon.ico`
   - `app/resources/icon_32x32.ico` 
   - `app/resources/icon_128x128.ico`
5. **Manual verification**: Right-click the executable → Properties to see if the icon appears there 