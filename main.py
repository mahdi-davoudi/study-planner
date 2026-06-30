import sys
import tkinter as tk
from tkinter import messagebox
from database import DatabaseManager
from gui.main_window import MainWindow


def main():
    try:
        db = DatabaseManager()
    except ConnectionError as e:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("error for connect to database", str(e))
        sys.exit(1)

    app = MainWindow(db)
    app.protocol("WM_DELETE_WINDOW", lambda: (db.close(), app.destroy()))
    app.mainloop()


if __name__ == "__main__":
    main()