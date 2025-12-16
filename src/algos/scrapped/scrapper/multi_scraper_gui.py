import os
import sys
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox

SCRIPTS = {
    "Century 21": "scrappcentury21.py",
    "La Forêt": "scrappforet.py",
    "Le Figaro": "scrapplefigaro.py",
    "Orpi": "scrapporpi.py",
    "Stéphane Plaza": "scrappstephaneplazaimmobilier.py",
}

def lancer_script(fname: str):
    """Lance le script dans une nouvelle console (Windows) sans capturer la sortie."""
    pyexe = sys.executable or "python"

    creationflags = 0
    if os.name == "nt":
        creationflags = subprocess.CREATE_NEW_CONSOLE

    try:
        subprocess.Popen([pyexe, fname], creationflags=creationflags)
        messagebox.showinfo(
            "Lancement",
            f"Le script '{fname}' a été lancé .\n"
            " le CSV il sera créé ."
        )
    except Exception as e:
        messagebox.showerror("Erreur au lancement", str(e))


root = tk.Tk()
root.title("Lanceur de scrapers ")
root.geometry("420x200")
root.resizable(False, False)

frm = ttk.Frame(root, padding=12)
frm.pack(fill="both", expand=True)

ttk.Label(frm, text="Choisissez un site à scraper :", font=("Segoe UI", 10, "bold")).pack(anchor="w")

site_var = tk.StringVar()
combo = ttk.Combobox(frm, textvariable=site_var, state="readonly", width=30)
combo["values"] = list(SCRIPTS.keys())
combo.current(0)  # sélection par défaut
combo.pack(pady=6, anchor="w")

def on_lancer():
    site = site_var.get().strip()
    fname = SCRIPTS.get(site)
    if not fname:
        messagebox.showwarning("Sélection", "Veuillez choisir un site.")
        return
    lancer_script(fname)

btns = ttk.Frame(frm)
btns.pack(pady=10, fill="x")

ttk.Button(btns, text="Lancer", command=on_lancer).pack(side="left")

root.mainloop()
