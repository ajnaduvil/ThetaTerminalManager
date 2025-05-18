import os
import json
import subprocess
import urllib.request
import threading
import sys
import atexit


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

        # Load configuration if it exists
        self.load_config()

        # Register cleanup function to ensure processes are terminated on exit
        atexit.register(self.cleanup)

    def cleanup(self):
        """Clean up resources when the application exits"""
        if self.running:
            self.stop_terminal()

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

    def download_jar_file(self):
        """Download the JAR file from the URL with progress"""
        try:
            if self.log_callback:
                self.log_callback("Downloading ThetaTerminal.jar...")

            progress_tracker = DownloadProgressTracker(self._download_progress)
            urllib.request.urlretrieve(
                self.download_url, self.jar_file, reporthook=progress_tracker
            )

            if self.log_callback:
                self.log_callback("Download completed successfully.")

            self.is_downloading = False
            return True
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"Error downloading JAR file: {e}")
            self.is_downloading = False
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

            # Start process with piped stdout and stderr
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
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
            # Terminate the process
            if self.process:
                self.process.terminate()
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.process.kill()

            self.running = False
            if self.log_callback:
                self.log_callback("Terminal stopped.")
            return True
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"Error stopping terminal: {e}")
            return False

    def is_running(self):
        """Check if the terminal is currently running"""
        return self.running

    def set_log_callback(self, callback):
        """Set callback function to receive log output"""
        self.log_callback = callback

    def set_download_progress_callback(self, callback):
        """Set callback function to receive download progress updates"""
        self.download_progress_callback = callback

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
