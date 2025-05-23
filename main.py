import tkinter as tk
from tkinter import messagebox
import time
import sys
import os
from app.terminal_manager import TerminalManager
from app.ui.main_window import MainWindow
from app.ui import set_window_icon


def main():
    root = tk.Tk()
    root.title("Theta Terminal Manager")

    # Set the window icon
    if set_window_icon(root):
        print("Window icon set successfully")
    else:
        print("Could not set window icon")

    # Create the terminal manager
    terminal_manager = TerminalManager()

    # Create the main window
    main_window = MainWindow(root, terminal_manager)

    # Set up proper exit handling
    def on_closing():
        if terminal_manager.is_running():
            if messagebox.askyesno(
                "Confirm Exit",
                "Terminal is still running. Do you want to stop it and exit?",
                parent=root,
            ):
                # Disable window interactions and show status
                root.config(cursor="wait")
                root.title("Theta Terminal Manager - Stopping...")

                # Update UI immediately
                root.update_idletasks()

                # Stop terminal in background with timeout
                def stop_and_exit():
                    try:
                        # Set a shorter timeout for exit scenarios
                        import threading
                        import time

                        stop_success = False

                        def stop_terminal():
                            nonlocal stop_success
                            stop_success = terminal_manager.stop_terminal()

                        stop_thread = threading.Thread(
                            target=stop_terminal, daemon=True
                        )
                        stop_thread.start()

                        # Wait for stop to complete with timeout
                        stop_thread.join(timeout=5.0)  # 5 second timeout for exit

                        if not stop_success:
                            print("Warning: Terminal may not have stopped cleanly")

                        # Force cleanup and exit
                        terminal_manager.cleanup()

                    except Exception as e:
                        print(f"Error during shutdown: {e}")

                    finally:
                        # Schedule window destruction on main thread
                        root.after(0, force_exit)

                def force_exit():
                    # Additional cleanup for Windows to help release file handles
                    if sys.platform.startswith("win"):
                        # Explicitly call garbage collection
                        import gc

                        gc.collect()

                    root.destroy()

                # Start background stop operation
                exit_thread = threading.Thread(target=stop_and_exit, daemon=True)
                exit_thread.start()

                # Don't return here - let the background thread handle exit
                return
        else:
            # Additional cleanup for Windows to help release file handles
            if sys.platform.startswith("win"):
                # Explicitly call garbage collection
                import gc

                gc.collect()

            root.destroy()

    # Bind closing event
    root.protocol("WM_DELETE_WINDOW", on_closing)

    # Start the UI loop
    root.mainloop()


if __name__ == "__main__":
    main()
