import tkinter as tk
from app.terminal_manager import TerminalManager
from app.ui.main_window import MainWindow


def main():
    root = tk.Tk()
    root.title("Theta Terminal Manager")

    # Create the terminal manager
    terminal_manager = TerminalManager()

    # Create the main window
    main_window = MainWindow(root, terminal_manager)

    # Start the UI loop
    root.mainloop()


if __name__ == "__main__":
    main()
