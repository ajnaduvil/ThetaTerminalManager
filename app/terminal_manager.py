import os
import json
import subprocess
import urllib.request
import threading
import sys
import atexit
import time


class DownloadProgressTracker:
    def __init__(self, callback=None):
        self.callback = callback
        self.total_size = 0
        self.downloaded = 0

    def __call__(self, count, block_size, total_size):
        self.total_size = total_size
        self.downloaded += block_size
        percentage = 0
        if self.total_size > 0:
            percentage = int(self.downloaded * 100 / self.total_size)
        if self.callback:
            self.callback(percentage, self.downloaded, self.total_size)


class TerminalManager:
    def __init__(self):
        self.config_file = "config.json"
        self.jar_file = "ThetaTerminal.jar"
        self.download_url = "https://download-stable.thetadata.us/ThetaTerminal.jar"
        self.username = ""
        self.password = ""
        self.process = None
        self.running = False
        self.log_callback = None
        self.download_progress_callback = None
        self.download_thread = None
        self.is_downloading = False
        self.download_complete_callback = None

        # Paths for logs and config folders
        self.logs_folder = os.path.join(
            os.path.expanduser("~"), "ThetaData", "ThetaTerminal", "logs"
        )
        self.config_folder = os.path.dirname(
            os.path.join(
                os.path.expanduser("~"),
                "ThetaData",
                "ThetaTerminal",
                "config_0.properties",
            )
        )

        # Server region options
        self.mdds_regions = ["MDDS_NJ_HOSTS", "MDDS_STAGE_HOSTS", "MDDS_DEV_HOSTS"]
        self.fpss_regions = ["FPSS_NJ_HOSTS", "FPSS_STAGE_HOSTS", "FPSS_DEV_HOSTS"]
        self.current_mdds_region = "MDDS_NJ_HOSTS"
        self.current_fpss_region = "FPSS_NJ_HOSTS"

        # Read current settings from properties file if it exists
        self._read_properties_file()

        # Load configuration if it exists
        self.load_config()

        # Register cleanup function to ensure processes are terminated on exit
        atexit.register(self.cleanup)

    def cleanup(self):
        """Clean up resources when the application exits"""
        try:
            # Temporarily save and clear the log_callback to prevent errors during cleanup
            temp_callback = self.log_callback
            self.log_callback = None

            if self.running:
                # Perform the actual cleanup with a simple direct approach to avoid hanging
                if self.process:
                    try:
                        # Quick force kill rather than graceful termination
                        self.process.kill()
                    except Exception:
                        pass

                    # Close pipes regardless of termination success
                    try:
                        if hasattr(self.process, "stdout") and self.process.stdout:
                            self.process.stdout.close()
                    except Exception:
                        pass

                    try:
                        if hasattr(self.process, "stderr") and self.process.stderr:
                            self.process.stderr.close()
                    except Exception:
                        pass

                self.running = False

            # Run cleanup in a separate thread with timeout to prevent hanging the application exit
            cleanup_thread = threading.Thread(target=self._final_cleanup)
            cleanup_thread.daemon = True
            cleanup_thread.start()

            # Only wait a very short time for cleanup to avoid blocking application exit
            cleanup_thread.join(timeout=0.1)  # Reduced from 0.2 to 0.1 seconds

            # Restore the callback
            self.log_callback = temp_callback

        except Exception:
            # Ensure we don't propagate exceptions during cleanup
            pass

    def _final_cleanup(self):
        """Final cleanup operations run in a separate thread"""
        try:
            # Check for any lingering Java processes
            self._cleanup_java_processes()

            # Force terminate any JVM instances
            if sys.platform.startswith("win"):
                try:
                    # Force terminate any Java processes that might be running with our JAR file
                    jar_name = os.path.basename(self.jar_file)
                    subprocess.run(
                        f'taskkill /F /IM java.exe /FI "WINDOWTITLE eq *{jar_name}*"',
                        shell=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=1,
                    )
                except Exception:
                    pass
        except Exception:
            # Ignore any errors in final cleanup
            pass

    def load_config(self):
        """Load username and password from config file if it exists"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                    self.username = config.get("username", "")
                    self.password = config.get("password", "")
            except Exception as e:
                print(f"Error loading config: {e}")

    def save_config(self):
        """Save username and password to config file"""
        try:
            with open(self.config_file, "w") as f:
                json.dump({"username": self.username, "password": self.password}, f)
        except Exception as e:
            print(f"Error saving config: {e}")

    def check_jar_file(self):
        """Check if JAR file exists, download if not"""
        if not os.path.exists(self.jar_file):
            # Start async download
            self._download_jar_file_async()
            return False
        return True

    def _download_progress(self, percentage, downloaded, total_size):
        """Handle download progress updates"""
        if self.download_progress_callback:
            self.download_progress_callback(percentage, downloaded, total_size)

    def _download_jar_file_async(self):
        """Start asynchronous download of the JAR file"""
        if self.is_downloading:
            return

        self.is_downloading = True

        if self.log_callback:
            self.log_callback("Starting ThetaTerminal.jar download...")

        self.download_thread = threading.Thread(target=self.download_jar_file)
        self.download_thread.daemon = True
        self.download_thread.start()

    def _notify_download_complete(self):
        """Safely notify that download is complete"""
        self.is_downloading = False
        if self.download_complete_callback:
            try:
                self.download_complete_callback()
            except Exception as e:
                if self.log_callback:
                    self.log_callback(f"Error in download complete notification: {e}")

    def download_jar_file(self):
        """Download the JAR file from the URL with progress"""
        try:
            if self.log_callback:
                self.log_callback("Downloading ThetaTerminal.jar...")

            progress_tracker = DownloadProgressTracker(self._download_progress)
            urllib.request.urlretrieve(
                self.download_url, self.jar_file, reporthook=progress_tracker
            )

            # Ensure we send a final 100% progress update to hide the progress bar
            if self.download_progress_callback and progress_tracker.total_size > 0:
                self.download_progress_callback(
                    100, progress_tracker.total_size, progress_tracker.total_size
                )

            if self.log_callback:
                self.log_callback("Download completed successfully.")

            # Small delay to ensure UI updates happen in the correct order
            time.sleep(0.5)

            # Notify that download is complete using a safer method
            self._notify_download_complete()

            return True
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"Error downloading JAR file: {e}")

            # Notify that download process is finished, even if with error
            self._notify_download_complete()

            return False

    def start_terminal(self, username, password):
        """Start the terminal process with the given credentials"""
        if self.running:
            return False

        # Save credentials
        self.username = username
        self.password = password
        self.save_config()

        # Check if JAR file exists, download if not
        if not os.path.exists(self.jar_file):
            if self.log_callback:
                self.log_callback("ThetaTerminal.jar not found. Starting download...")
            self._download_jar_file_async()
            return False

        # Don't start if download is in progress
        if self.is_downloading:
            if self.log_callback:
                self.log_callback(
                    "Download in progress. Please wait until download completes."
                )
            return False

        # Start the process
        try:
            # Create the command
            cmd = ["java", "-jar", self.jar_file, username, password]

            # Configure startup info to hide the console window on Windows
            startup_info = None
            if sys.platform.startswith("win"):
                startup_info = subprocess.STARTUPINFO()
                startup_info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startup_info.wShowWindow = 0  # SW_HIDE

            # Start process with piped stdout and stderr
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                startupinfo=startup_info,
            )

            self.running = True

            # Start thread to read output
            self.output_thread = threading.Thread(target=self._read_output)
            self.output_thread.daemon = True
            self.output_thread.start()

            if self.log_callback:
                self.log_callback("Terminal started.")

            return True
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"Error starting terminal: {e}")
            return False

    def stop_terminal(self):
        """Stop the terminal process if it's running"""
        if not self.running:
            return False

        try:
            # Set a flag to track successful termination
            termination_successful = False

            # Terminate the process
            if self.process:
                # Store the process ID before termination
                pid = self.process.pid

                # First attempt a graceful termination
                try:
                    self.process.terminate()

                    # Wait for process to terminate with a shorter timeout for better responsiveness
                    self.process.wait(timeout=2)  # Reduced from 3 to 2 seconds
                    termination_successful = True
                except (subprocess.TimeoutExpired, Exception) as e:
                    # If process doesn't terminate in time or there's an error, force kill it
                    if self.log_callback is not None:
                        self.log_callback(
                            "Process not responding - forcing termination..."
                        )

                    try:
                        self.process.kill()
                        # Wait again to ensure it's terminated with a shorter timeout
                        self.process.wait(timeout=0.5)  # Reduced from 1 to 0.5 seconds
                        termination_successful = True
                    except Exception:
                        # If kill also fails, use platform-specific force kill (last resort)
                        if sys.platform.startswith("win"):
                            try:
                                subprocess.run(
                                    f"taskkill /F /PID {pid}",
                                    shell=True,
                                    stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL,
                                    timeout=1,  # Add timeout to prevent hanging
                                )
                                termination_successful = True
                            except Exception:
                                pass

                # Close pipes regardless of termination success
                try:
                    if hasattr(self.process, "stdout") and self.process.stdout:
                        self.process.stdout.close()
                except Exception:
                    pass

                try:
                    if hasattr(self.process, "stderr") and self.process.stderr:
                        self.process.stderr.close()
                except Exception:
                    pass

                # Use a timeout for process cleanup to prevent hanging - reduce timeout
                cleanup_thread = threading.Thread(
                    target=self._cleanup_java_processes_with_timeout,
                    args=(pid, 3),  # Reduced from 5 to 3 seconds
                )
                cleanup_thread.daemon = True
                cleanup_thread.start()

                # Give a shorter time for cleanup to run, but don't wait for completion
                cleanup_thread.join(timeout=0.2)  # Reduced from 0.5 to 0.2 seconds

            # Mark as not running regardless of termination success
            self.running = False

            # Quick release of resources - don't wait for long operations
            try:
                # Force JVM garbage collection (quick operation)
                if sys.platform.startswith("win"):
                    subprocess.run(
                        "jcmd %* GC.run",
                        shell=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        timeout=0.5,  # Reduced from 1 to 0.5 seconds
                    )
            except Exception:
                pass

            if self.log_callback is not None:
                self.log_callback("Terminal stopped.")

            return True
        except Exception as e:
            # Mark as not running even if there was an error
            self.running = False

            if self.log_callback is not None:
                self.log_callback(f"Error stopping terminal: {e}")
            return False

    def _cleanup_java_processes_with_timeout(self, parent_pid, timeout):
        """Run process cleanup with a timeout to prevent hanging"""
        try:
            self._cleanup_java_processes(parent_pid)
        except Exception:
            pass

    def _cleanup_java_processes(self, parent_pid=None):
        """Clean up any Java processes that might be holding onto our JAR file"""
        # Windows-specific cleanup
        if sys.platform.startswith("win"):
            try:
                # Find Java processes related to our application
                if parent_pid:
                    # Try to find child processes by parent PID first (more targeted)
                    cmd = f'wmic process where (ParentProcessId={parent_pid} and Name like "%java%") get ProcessId'
                    result = subprocess.run(
                        cmd,
                        shell=True,
                        capture_output=True,
                        text=True,
                        timeout=1,  # Reduced from 2 to 1 second
                    )

                    if result.stdout and "ProcessId" in result.stdout:
                        # Parse process IDs
                        lines = result.stdout.strip().split("\n")
                        # Skip header line
                        for line in lines[1:]:
                            if line.strip():
                                try:
                                    pid = int(line.strip())
                                    # Force terminate the process
                                    subprocess.run(
                                        f"taskkill /F /PID {pid}",
                                        shell=True,
                                        stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL,
                                        timeout=0.5,  # Reduced from 1 to 0.5 seconds
                                    )
                                    if self.log_callback is not None:
                                        self.log_callback(
                                            f"Terminated Java child process with PID: {pid}"
                                        )
                                except (ValueError, subprocess.TimeoutExpired):
                                    continue

                # Fallback: Look for Java processes using our JAR file
                jar_name = os.path.basename(self.jar_file)
                cmd = f'wmic process where Name like "%java%" get CommandLine,ProcessId'
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=1,  # Reduced from 2 to 1 second
                )

                if result.stdout:
                    lines = result.stdout.strip().split("\n")
                    # Skip header line
                    for line in lines[1:]:
                        if jar_name in line:
                            # Extract process ID
                            parts = line.strip().split()
                            for i, part in enumerate(parts):
                                if (
                                    part.isdigit() and i > 0
                                ):  # Avoid first column which might be numeric command
                                    try:
                                        pid = int(part)
                                        # Force terminate the process
                                        subprocess.run(
                                            f"taskkill /F /PID {pid}",
                                            shell=True,
                                            stdout=subprocess.DEVNULL,
                                            stderr=subprocess.DEVNULL,
                                            timeout=0.5,  # Reduced from 1 to 0.5 seconds
                                        )
                                        if self.log_callback is not None:
                                            self.log_callback(
                                                f"Terminated Java process with PID: {pid}"
                                            )
                                    except (ValueError, subprocess.TimeoutExpired):
                                        continue
            except Exception as e:
                # Log but don't fail - this is a best-effort cleanup
                if self.log_callback is not None:
                    self.log_callback(f"Error in Java process cleanup: {e}")

        # Unix-like systems (Linux, macOS)
        elif sys.platform.startswith(("linux", "darwin")):
            try:
                # Find Java processes that might be using our JAR file
                jar_name = os.path.basename(self.jar_file)
                cmd = f"ps -ef | grep java | grep {jar_name} | grep -v grep | awk '{{print $2}}'"
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=1,  # Reduced from 2 to 1 second
                )

                if result.stdout:
                    pids = result.stdout.strip().split("\n")
                    for pid in pids:
                        if pid.strip():
                            try:
                                # Force terminate the process
                                subprocess.run(
                                    f"kill -9 {pid}",
                                    shell=True,
                                    stdout=subprocess.DEVNULL,
                                    stderr=subprocess.DEVNULL,
                                    timeout=0.5,  # Reduced from 1 to 0.5 seconds
                                )
                                if self.log_callback is not None:
                                    self.log_callback(
                                        f"Terminated Java process with PID: {pid}"
                                    )
                            except (Exception, subprocess.TimeoutExpired):
                                continue
            except Exception as e:
                # Log but don't fail - this is a best-effort cleanup
                if self.log_callback is not None:
                    self.log_callback(f"Error in Java process cleanup: {e}")

    def is_running(self):
        """Check if the terminal is currently running"""
        return self.running

    def get_downloading_status(self):
        """Check if a download is in progress"""
        return self.is_downloading

    def set_log_callback(self, callback):
        """Set callback function to receive log output"""
        self.log_callback = callback

    def set_download_progress_callback(self, callback):
        """Set callback function to receive download progress updates"""
        self.download_progress_callback = callback

    def set_download_complete_callback(self, callback):
        """Set callback function to be called when download completes"""
        self.download_complete_callback = callback

    def _read_output(self):
        """Read output from the process and send to callback"""
        try:
            for line in self.process.stdout:
                if self.log_callback:
                    self.log_callback(line.strip())
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"Error reading output: {e}")
        finally:
            if self.process.poll() is not None:
                self.running = False

    def open_logs_folder(self):
        """Open the logs folder in file explorer"""
        if os.path.exists(self.logs_folder):
            self._open_folder(self.logs_folder)
            if self.log_callback:
                self.log_callback(f"Opening logs folder: {self.logs_folder}")
            return True
        else:
            if self.log_callback:
                self.log_callback(f"Logs folder not found: {self.logs_folder}")
            return False

    def open_config_folder(self):
        """Open the config folder in file explorer"""
        if os.path.exists(self.config_folder):
            self._open_folder(self.config_folder)
            if self.log_callback:
                self.log_callback(f"Opening config folder: {self.config_folder}")
            return True
        else:
            if self.log_callback:
                self.log_callback(f"Config folder not found: {self.config_folder}")
            return False

    def _open_folder(self, folder_path):
        """Open a folder in the default file explorer"""
        try:
            if sys.platform.startswith("win"):
                os.startfile(folder_path)
            elif sys.platform.startswith("darwin"):  # macOS
                subprocess.call(["open", folder_path])
            else:  # Linux
                subprocess.call(["xdg-open", folder_path])
            return True
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"Error opening folder: {e}")
            return False

    def _read_properties_file(self):
        """Read the server region settings from config_0.properties file"""
        if os.path.exists(os.path.join(self.config_folder, "config_0.properties")):
            properties_path = os.path.join(self.config_folder, "config_0.properties")
            try:
                with open(properties_path, "r") as f:
                    lines = f.readlines()
                    for line in lines:
                        line = line.strip()
                        if line.startswith("MDDS_REGION="):
                            self.current_mdds_region = line.split("=")[1]
                        elif line.startswith("FPSS_REGION="):
                            self.current_fpss_region = line.split("=")[1]
                if self.log_callback:
                    self.log_callback(
                        f"Current server settings loaded: MDDS={self.current_mdds_region}, FPSS={self.current_fpss_region}"
                    )
            except Exception as e:
                if self.log_callback:
                    self.log_callback(f"Error reading properties file: {e}")

    def update_server_regions(self, mdds_region, fpss_region):
        """Update the server region settings in config_0.properties file"""
        properties_path = os.path.join(self.config_folder, "config_0.properties")

        # Check if properties file exists
        if not os.path.exists(properties_path):
            if self.log_callback:
                self.log_callback(
                    "Properties file not found. It will be created when ThetaTerminal runs for the first time."
                )
            # Save the values for when the file is created
            self.current_mdds_region = mdds_region
            self.current_fpss_region = fpss_region
            return False

        try:
            # Read existing properties file
            with open(properties_path, "r") as f:
                lines = f.readlines()

            # Update region settings
            updated_lines = []
            for line in lines:
                if line.strip().startswith("MDDS_REGION="):
                    updated_lines.append(f"MDDS_REGION={mdds_region}\n")
                elif line.strip().startswith("FPSS_REGION="):
                    updated_lines.append(f"FPSS_REGION={fpss_region}\n")
                else:
                    updated_lines.append(line)

            # Write updated content back to file
            with open(properties_path, "w") as f:
                f.writelines(updated_lines)

            # Update current values
            self.current_mdds_region = mdds_region
            self.current_fpss_region = fpss_region

            if self.log_callback:
                self.log_callback(
                    f"Server settings updated: MDDS={mdds_region}, FPSS={fpss_region}"
                )
            return True
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"Error updating properties file: {e}")
            return False

    def get_server_regions(self):
        """Get the current server region settings"""
        return {
            "mdds_region": self.current_mdds_region,
            "fpss_region": self.current_fpss_region,
            "mdds_options": self.mdds_regions,
            "fpss_options": self.fpss_regions,
        }
