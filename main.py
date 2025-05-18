import tkinter as tk
from tkinter import messagebox
from app.terminal_manager import TerminalManager
from app.ui.main_window import MainWindow


def main():
    root = tk.Tk()
    root.title("Theta Terminal Manager")

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
                terminal_manager.stop_terminal()
                root.destroy()
        else:
            root.destroy()

    # Bind closing event
    root.protocol("WM_DELETE_WINDOW", on_closing)

    # Start the UI loop
    root.mainloop()


if __name__ == "__main__":
    main()
