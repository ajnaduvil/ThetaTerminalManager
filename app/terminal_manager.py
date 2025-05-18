import os
import json
import subprocess
import urllib.request
import threading
import sys


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

        # Load configuration if it exists
        self.load_config()

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
            return self.download_jar_file()
        return True

    def download_jar_file(self):
        """Download the JAR file from the URL"""
        try:
            if self.log_callback:
                self.log_callback("Downloading ThetaTerminal.jar...")

            urllib.request.urlretrieve(self.download_url, self.jar_file)

            if self.log_callback:
                self.log_callback("Download completed successfully.")
            return True
        except Exception as e:
            if self.log_callback:
                self.log_callback(f"Error downloading JAR file: {e}")
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
        if not self.check_jar_file():
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
