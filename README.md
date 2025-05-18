# Theta Terminal Manager

A Python application for managing ThetaTerminal.jar with a simple GUI interface.

## Features

- Automatically downloads ThetaTerminal.jar if not present
- Saves and loads username/password credentials
- Start and stop ThetaTerminal with a click
- Log viewing with clear and copy functionality
- Password reveal option for ease of use

## Requirements

- Python 3.6 or newer
- Java Runtime Environment (JRE) for running ThetaTerminal.jar

## Installation

1. Clone this repository
2. Install required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage

Run the application:
```
python main.py
```

1. Enter your ThetaData username and password
2. Click "Start" to launch the terminal
3. The log area will display output from the terminal
4. Click "Stop" to terminate the terminal when done

## Building Executable

To build a standalone executable:

### Using the build script (recommended)

1. Install the requirements:
   ```
   pip install -r requirements.txt
   ```

2. On Windows, run:
   ```
   build.bat
   ```
   
   Or run the Python build script directly:
   ```
   python build.py
   ```

3. The executable will be created in the `dist` directory

### Using PyInstaller directly

You can also build with PyInstaller directly using the spec file:

```
pyinstaller ThetaTerminalManager.spec
```

## Structure

- `main.py` - Entry point for the application
- `app/terminal_manager.py` - Core logic for managing the terminal
- `app/ui/main_window.py` - User interface implementation
- `build.py` - Build script for creating the executable

## License

MIT 