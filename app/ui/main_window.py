import tkinter as tk
from tkinter import ttk
import pyperclip
import os
from tkinter import messagebox


class MainWindow:
    def __init__(self, root, terminal_manager):
        self.root = root
        self.terminal_manager = terminal_manager

        # Set a minimum size for the window
        self.root.minsize(600, 400)

        # Configure the main frame with padding
        self.main_frame = ttk.Frame(root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Create the credential frame at the top
        self._create_credential_frame()

        # Create the control frame with start/stop buttons
        self._create_control_frame()

        # Create the log area
        self._create_log_area()

        # Create download progress bar (hidden by default)
        self._create_progress_bar()

        # Set the callbacks
        self.terminal_manager.set_log_callback(self._append_log)
        self.terminal_manager.set_download_progress_callback(self._update_progress)

        # Initialize UI state
        self._update_ui_state()

        # Check if JAR file exists on startup
        self._check_jar_file()

    def _create_credential_frame(self):
        """Create the frame for username and password inputs"""
        cred_frame = ttk.Frame(self.main_frame)
        cred_frame.pack(fill=tk.X, pady=(0, 10))

        # Username
        ttk.Label(cred_frame, text="Username:").grid(
            row=0, column=0, sticky=tk.W, padx=(0, 5)
        )
        self.username_var = tk.StringVar(value=self.terminal_manager.username)
        ttk.Entry(cred_frame, textvariable=self.username_var, width=20).grid(
            row=0, column=1, sticky=tk.W, padx=(0, 10)
        )

        # Password
        ttk.Label(cred_frame, text="Password:").grid(
            row=0, column=2, sticky=tk.W, padx=(10, 5)
        )
        self.password_var = tk.StringVar(value=self.terminal_manager.password)
        self.password_entry = ttk.Entry(
            cred_frame, textvariable=self.password_var, show="*", width=20
        )
        self.password_entry.grid(row=0, column=3, sticky=tk.W)

        # Show/Hide password button
        self.show_password = tk.BooleanVar(value=False)
        self.show_password_btn = ttk.Checkbutton(
            cred_frame,
            text="Show",
            variable=self.show_password,
            command=self._toggle_password_visibility,
        )
        self.show_password_btn.grid(row=0, column=4, sticky=tk.W, padx=(5, 0))

    def _toggle_password_visibility(self):
        """Toggle password visibility"""
        if self.show_password.get():
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="*")

    def _create_control_frame(self):
        """Create the frame with control buttons"""
        self.control_frame = ttk.Frame(self.main_frame)
        self.control_frame.pack(fill=tk.X, pady=(0, 10))

        # Start button with icon color
        self.start_btn = ttk.Button(
            self.control_frame,
            text="▶ Start",
            command=self._start_terminal,
            style="Green.TButton",
        )
        self.start_btn.pack(side=tk.LEFT, padx=(0, 5))

        # Stop button with icon color
        self.stop_btn = ttk.Button(
            self.control_frame,
            text="■ Stop",
            command=self._stop_terminal,
            style="Red.TButton",
        )
        self.stop_btn.pack(side=tk.LEFT)

        # Define styles for colored buttons
        self.root.tk_setPalette(background="#f0f0f0")

        style = ttk.Style()
        style.configure("Green.TButton", foreground="green")
        style.configure("Red.TButton", foreground="red")

    def _create_progress_bar(self):
        """Create the download progress frame (initially hidden)"""
        self.progress_frame = ttk.Frame(self.main_frame)
        self.progress_frame.pack(fill=tk.X, pady=(0, 10))
        self.progress_frame.pack_forget()  # Hide initially

        # Progress label
        self.progress_label = ttk.Label(
            self.progress_frame, text="Downloading ThetaTerminal.jar: 0%"
        )
        self.progress_label.pack(anchor=tk.W, pady=(0, 5))

        # Progress bar
        self.progress_bar = ttk.Progressbar(
            self.progress_frame, orient=tk.HORIZONTAL, length=100, mode="determinate"
        )
        self.progress_bar.pack(fill=tk.X)

    def _create_log_area(self):
        """Create the log text area with controls"""
        log_frame = ttk.Frame(self.main_frame)
        log_frame.pack(fill=tk.BOTH, expand=True)

        # Log area label
        ttk.Label(log_frame, text="Log Output:").pack(anchor=tk.W)

        # Create a frame for the text widget and scrollbar
        text_frame = ttk.Frame(log_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        # Log text area with scrollbar
        self.log_text = tk.Text(text_frame, wrap=tk.WORD, height=15)
        self.log_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Add scrollbar
        scrollbar = ttk.Scrollbar(text_frame, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)

        # Create log control buttons
        log_controls = ttk.Frame(log_frame)
        log_controls.pack(fill=tk.X, pady=(5, 0))

        ttk.Button(log_controls, text="Clear Log", command=self._clear_log).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Button(log_controls, text="Copy to Clipboard", command=self._copy_log).pack(
            side=tk.LEFT
        )

    def _check_jar_file(self):
        """Check if JAR file exists on startup"""
        if not os.path.exists(self.terminal_manager.jar_file):
            self._append_log(f"{self.terminal_manager.jar_file} not found.")
            reply = messagebox.askyesno(
                "File Missing",
                f"{self.terminal_manager.jar_file} is not found. Do you want to download it now?",
                parent=self.root,
            )
            if reply:
                self._append_log("Starting download...")
                self.terminal_manager._download_jar_file_async()
                self.progress_frame.pack(
                    fill=tk.X, pady=(0, 10), after=self.control_frame
                )
            else:
                self._append_log(
                    "Download cancelled. You'll need the JAR file to start the terminal."
                )

    def _update_progress(self, percentage, downloaded, total_size):
        """Update the progress bar and label"""
        if percentage == 100 and self.progress_frame.winfo_ismapped():
            self.progress_frame.pack_forget()
            self._append_log("Download complete.")
            return

        if not self.progress_frame.winfo_ismapped():
            self.progress_frame.pack(fill=tk.X, pady=(0, 10), after=self.control_frame)

        # Format the label with progress information
        if total_size > 0:
            downloaded_mb = downloaded / (1024 * 1024)
            total_mb = total_size / (1024 * 1024)
            self.progress_label.config(
                text=f"Downloading ThetaTerminal.jar: {percentage}% ({downloaded_mb:.1f} MB / {total_mb:.1f} MB)"
            )
        else:
            self.progress_label.config(
                text=f"Downloading ThetaTerminal.jar: {percentage}%"
            )

        # Update the progress bar
        self.progress_bar["value"] = percentage

    def _start_terminal(self):
        """Start the terminal with the given credentials"""
        username = self.username_var.get()
        password = self.password_var.get()

        if not username or not password:
            self._append_log("Error: Username and password are required")
            return

        success = self.terminal_manager.start_terminal(username, password)
        if success:
            self._update_ui_state()

    def _stop_terminal(self):
        """Stop the terminal if it's running"""
        success = self.terminal_manager.stop_terminal()
        if success:
            self._update_ui_state()

    def _update_ui_state(self):
        """Update UI elements based on the terminal state"""
        running = self.terminal_manager.is_running()

        # Update button states
        if running:
            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
        else:
            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)

    def _append_log(self, message):
        """Append a message to the log text area"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)  # Scroll to the end
        self.log_text.config(state=tk.DISABLED)

    def _clear_log(self):
        """Clear the log text area"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _copy_log(self):
        """Copy log contents to clipboard"""
        log_content = self.log_text.get(1.0, tk.END)
        pyperclip.copy(log_content)
        self._append_log("Log copied to clipboard")
