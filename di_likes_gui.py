import tkinter as tk
from tkinter import messagebox
import threading
import csv
import os
import sys

from export_di_likes import (
    login,
    fetch_new_votes_until_overlap,
    fetch_votes,
    load_existing_track_ids,
    prepend_new_rows,
    CSV_FILE,
    FIELDNAMES
)

def resource_path(name: str) -> str:
    if getattr(sys, "frozen", False):
        return os.path.join(os.path.dirname(sys.executable), name)
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), name)

def run_update():
    def worker():
        try:
            status.set("Logging in...")
            username = username_entry.get().strip()
            password = password_entry.get().strip()

            session_key, member_id = login(username, password)

            # ----- MODE SWITCH -----
            if mode.get() == "update":
                status.set("Checking for new likes...")
                existing_ids = load_existing_track_ids(CSV_FILE)

                new_rows = fetch_new_votes_until_overlap(
                    session_key,
                    member_id,
                    existing_ids=existing_ids,
                    per_page=200,
                    max_pages=3
                )

                prepend_new_rows(CSV_FILE, new_rows)
                result_count = len(new_rows)

            else:
                status.set("Rebuilding full list...")
                rows = fetch_votes(session_key, member_id, per_page=200)

                with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
                    w = csv.writer(f)
                    w.writerow(FIELDNAMES)
                    w.writerows(rows)

                result_count = len(rows)

            status.set("Done ✓")
            messagebox.showinfo("DI.fm Export", f"Completed.\nRows processed: {result_count}")

        except Exception as e:
            messagebox.showerror("Error", str(e))
            status.set("Error")

    threading.Thread(target=worker, daemon=True).start()

# ----- UI -----
root = tk.Tk()
root.title("DI.fm Likes Updater")
root.geometry("320x300")
root.resizable(False, False)

# Only call iconbitmap if the icon file exists (prevents crash)
ico_path = resource_path("di_icon.ico")
if os.path.exists(ico_path):
    root.iconbitmap(ico_path)

mode = tk.StringVar(value="update")

tk.Label(root, text="Mode").pack(pady=(10, 0))
tk.Radiobutton(root, text="A) Check / update (fast)", variable=mode, value="update").pack(anchor="w", padx=25)
tk.Radiobutton(root, text="B) Rebuild full list", variable=mode, value="rebuild").pack(anchor="w", padx=25)

tk.Label(root, text="Username / Email").pack(pady=(10, 0))
username_entry = tk.Entry(root, width=35)
username_entry.pack()

tk.Label(root, text="Password").pack(pady=(10, 0))
password_entry = tk.Entry(root, show="*", width=35)
password_entry.pack()

tk.Button(root, text="Update Likes", command=run_update).pack(pady=15)

status = tk.StringVar(value="Idle")
tk.Label(root, textvariable=status).pack()

root.mainloop()
