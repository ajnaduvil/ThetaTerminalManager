import os
import subprocess
import shutil
import sys
import platform


def build_executable():
    """Build the executable using PyInstaller"""
    print("Building Theta Terminal Manager executable...")

    # Clean up previous build artifacts if they exist
    if os.path.exists("dist"):
        print("Cleaning up previous build files...")
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")
    for file in os.listdir("."):
        if file.endswith(".spec"):
            os.remove(file)

    # Create directory for icon if it doesn't exist
    icon_dir = os.path.join("app", "resources")
    if not os.path.exists(icon_dir):
        os.makedirs(icon_dir)

    # Determine if we're on Windows
    is_windows = sys.platform.startswith("win")

    # Check for icon file
    icon_path = os.path.join(icon_dir, "icon.ico")
    if not os.path.exists(icon_path):
        print(f"Icon file not found at {icon_path}")
        print(
            "The executable will use the default Python icon. To add a custom icon, place icon.ico in app/resources/"
        )
        icon_param = ""
    else:
        icon_param = f"--icon={icon_path}"

    # Data separator for PyInstaller is different on Windows vs. other platforms
    separator = ";" if is_windows else ":"

    # Build the PyInstaller command
    cmd = [
        "pyinstaller",
        "--name=ThetaTerminalManager",
        "--onefile",
        "--windowed",
        f"--add-data=README.md{separator}.",
    ]

    # Add icon if available
    if icon_param:
        cmd.append(icon_param)

    # Add main script
    cmd.append("main.py")

    # Execute the command
    print(f"Running command: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print("Error building executable:")
        print(result.stderr)

        # Try with spec file if direct command fails
        print("Attempting to build with spec file...")
        if os.path.exists("ThetaTerminalManager.spec"):
            spec_result = subprocess.run(
                ["pyinstaller", "ThetaTerminalManager.spec"],
                capture_output=True,
                text=True,
            )
            if spec_result.returncode != 0:
                print("Error building with spec file:")
                print(spec_result.stderr)
                return False
            else:
                print("Build with spec file completed successfully!")
        else:
            return False

    # Check if executable was created
    exe_path = os.path.join(
        "dist", "ThetaTerminalManager.exe" if is_windows else "ThetaTerminalManager"
    )
    if os.path.exists(exe_path):
        print("Build completed successfully!")
        print(f"Executable created at: {os.path.abspath(exe_path)}")

        # Copy README to dist folder
        shutil.copy("README.md", os.path.join("dist", "README.md"))

        return True
    else:
        print(f"Build process completed, but executable not found at {exe_path}")
        return False


if __name__ == "__main__":
    build_executable()
