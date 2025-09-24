#!/usr/bin/env python3
import os
import subprocess
import sys
import tkinter as tk
import threading
from tkinter import messagebox, filedialog
import webbrowser

def run_command_term(cmd_args, done_callback=None):
    """Run command with terminal window, even when python is running without one."""

    proc = subprocess.Popen(
        cmd_args,
        creationflags=subprocess.CREATE_NEW_CONSOLE if os.name == "nt" else 0,
    )

    def wait_thread():
        proc.wait()
        if done_callback:
            done_callback()

    threading.Thread(target=wait_thread).start()

# GUI
root = tk.Tk()
root.title("yt-dlp")
root.geometry("500x380")

url_var = tk.StringVar()
yt_dlp_flags_var = tk.StringVar()
playlist_items_var = tk.StringVar(value="1:-1")

yt_dlp_flags_var.set("--no-playlist")

# **************************************
# Paths and directories (Edit as needed)
# **************************************

HOME = os.path.expanduser("~")
TEMP_AUDIO_DIR = os.path.join(HOME, "Downloads", "Music") # Temporary download directory (default: ~/Downloads/Music)
VIDEO_OUTDIR = os.path.join(HOME, "Videos") # Video download directory (default: ~/Videos)
AUDIO_OUTDIR = os.path.join(HOME, "Music") # Beets music library directory (default: ~/Music)

# ************************************
# Beets configuration (Edit as needed)
# ************************************

CONFIG_DIR = os.path.join(HOME, ".config", "beets") # Beets config directory (default: ~/.config/beets)
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.yaml") # Beets config file (default: ~/.config/beets/config.yaml)
VENVDIR = os.path.join(CONFIG_DIR, ".venv") # Virtual environment directory (default: ~/.config/beets/.venv)
LIBRARY_DB = os.path.join(HOME, ".local", "share", "beets", "library.db") # Beets library database file (default: ~/.local/share/beets/library.db)

# ****************************
# End of paths and directories
# ****************************

# Ensure output directories exist
os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)
os.makedirs(VIDEO_OUTDIR, exist_ok=True)

def run_command(cmd, cwd=None, show_terminal=False, use_shell=False):
    """Run command with or without showing a terminal window."""
    startupinfo = None
    if os.name == "nt" and not show_terminal:
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    try:
        subprocess.run(cmd, cwd=cwd, check=True, startupinfo=startupinfo, shell=use_shell)
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Error", f"Command failed: {cmd}\n{e}")

def setup_venv():
    """Create virtual environment and install dependencies if needed."""
    if not os.path.isdir(VENVDIR):
        os.makedirs(VENVDIR, exist_ok=True)
        os.rmdir(VENVDIR)  # Remove if exists to avoid venv creation issues
        run_command([sys.executable, "-m", "venv", VENVDIR], show_terminal=True)
        exe_dir = "Scripts" if os.name == "nt" else "bin"
        pip = os.path.join(VENVDIR, exe_dir, "pip.exe" if os.name == "nt" else "pip")
        python = os.path.join(VENVDIR, exe_dir, "python.exe" if os.name == "nt" else "python")
        run_command([python, "-m", "pip", "install", "--upgrade", "pip"], show_terminal=True)
        run_command_term([pip, "install", "beets[fetchart,lyrics,mbsubmit,embedart,chroma]", "mutagen", "yt-dlp"])

def do_update():
    """Update yt-dlp and beets in the virtual environment."""
    setup_venv()
    exe_dir = "Scripts" if os.name == "nt" else "bin"
    pip = os.path.join(VENVDIR, exe_dir, "pip.exe" if os.name == "nt" else "pip")
    run_command_term([pip, "install", "--upgrade", "yt-dlp", "beets"], 
                     done_callback=lambda: messagebox.showinfo("Update", "yt-dlp and beets have been updated."))

def ensure_config():
    """Ensure beets config file exists."""
    if not os.path.isfile(CONFIG_FILE):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(f"""directory: {AUDIO_OUTDIR}
library: {LIBRARY_DB}

import:
    move: yes
    write: yes
    copy: no
    autotag: yes
    quiet_fallback: asis

plugins: fetchart lyrics mbsync embedart chroma

fetchart:
    auto: yes
    maxwidth: 1200
    quality: 90
    sources: spotify itunes coverart albumart

embedart:
    auto: yes
    remove_art_file: yes
    ifempty: no
    compare_threshold: 0
    maxwidth: 1200
    quality: 80

lyrics:
    auto: yes
    sources: [lrclib, genius, tekstowo]
    synced: yes
    force: yes
""")
    if not os.path.isdir(AUDIO_OUTDIR):
        os.makedirs(AUDIO_OUTDIR, exist_ok=True)
    if not os.path.isdir(VIDEO_OUTDIR):
        os.makedirs(VIDEO_OUTDIR, exist_ok=True)

def download(url, mode="audio"):
    """Download audio or video."""
    setup_venv()
    exe_dir = "Scripts" if os.name == "nt" else "bin"
    yt_dlp = os.path.join(VENVDIR, exe_dir, "yt-dlp.exe" if os.name == "nt" else "yt-dlp")

    args = [
        yt_dlp,
        # "--cookies-from-browser", "chrome:Default",
        "-N", "10"
    ]
    args += yt_dlp_flags_var.get().split()
    if mode == "video":
        args += ["-o", os.path.join(VIDEO_OUTDIR, "%(title)s [%(id)s].%(ext)s")]
    else:
        args += [
            "--extract-audio", "--audio-format", "mp3",
            "--embed-thumbnail", "--add-metadata",
            "--metadata-from-title", "%(artist)s - %(title)s",
            # "--download-archive", os.path.join(TEMP_AUDIO_DIR, "yt-dlp-archive.txt"),
            "-o", os.path.join(TEMP_AUDIO_DIR, "%(title)s [%(id)s].%(ext)s")
        ]
    args.append(url)
    if mode == "audio":
        run_command_term(args, done_callback=lambda: import_to_beets(TEMP_AUDIO_DIR))
    else:
        run_command_term(args)

def import_to_beets(dir):
    """Import downloads into beets library."""
    setup_venv()
    ensure_config()
    exe_dir = "Scripts" if os.name == "nt" else "bin"
    beet = os.path.join(VENVDIR, exe_dir, "beet.exe" if os.name == "nt" else "beet")
    run_command_term([beet, "import", dir], done_callback=lambda: run_command(("del /Q /F " + os.path.join(dir, "*.*")) if os.name == "nt" else ("rm -f " + os.path.join(dir, "*.*")), use_shell=True))

def import_to_beets_gui():
    """GUI to select directory and import to beets."""
    dir = filedialog.askdirectory(initialdir=TEMP_AUDIO_DIR, title="Select Directory to Import")
    if dir:
        import_to_beets(dir)

def open_playlist_options():
    """Open playlist options window."""
    def save_options():
        options = []
        if var_all.get():
            options.append("--yes-playlist")
        if var_single.get():
            options.append("--no-playlist")
        if playlist_items_var.get().strip():
            options.append(f"-I {playlist_items_var.get().strip()}")
        yt_dlp_flags_var.set(" ".join(options))
        top.destroy()

    top = tk.Toplevel(root)
    top.title("Playlist Options")
    var_all = tk.BooleanVar(value="--yes-playlist" in yt_dlp_flags_var.get())
    var_single = tk.BooleanVar(value="--no-playlist" in yt_dlp_flags_var.get())

    if "-I" in yt_dlp_flags_var.get().split():
        list_index = yt_dlp_flags_var.get().split().index("-I")
        playlist_items_var.set(yt_dlp_flags_var.get().split()[list_index + 1])
    elif "--playlist-items" in yt_dlp_flags_var.get().split():
        list_index = yt_dlp_flags_var.get().split().index("--playlist-items")
        playlist_items_var.set(yt_dlp_flags_var.get().split()[list_index + 1])

    tk.Checkbutton(top, text="Download entire playlist", variable=var_all).pack(anchor="w", padx=10, pady=5)
    tk.Checkbutton(top, text="Download single video only", variable=var_single).pack(anchor="w", padx=10, pady=5)
    tk.Label(top, text="playlist items to download").pack(anchor="w", padx=10, pady=5)
    link = tk.Label(top, text="https://github.com/yt-dlp/yt-dlp?tab=readme-ov-file#video-selection", fg="blue", cursor="hand2")
    link.pack()
    link.bind("<Button-1>", lambda event: webbrowser.open(link.cget("text")))
    tk.Entry(top, textvariable=playlist_items_var).pack(padx=10, pady=5)
    tk.Button(top, text="Save", command=save_options).pack(pady=10)

tk.Label(root, text="Enter URL:").pack(pady=5)
tk.Entry(root, textvariable=url_var, width=60).pack(pady=5)

tk.Button(root, text="Playlist options", command=open_playlist_options).pack(pady=5)

tk.Label(root, text="yt-dlp flags:").pack(pady=5)
link = tk.Label(root, text="https://github.com/yt-dlp/yt-dlp?tab=readme-ov-file#general-options", fg="blue", cursor="hand2")
link.pack()
link.bind("<Button-1>", lambda event: webbrowser.open(link.cget("text")))
tk.Entry(root, textvariable=yt_dlp_flags_var, width=60).pack(pady=5)

tk.Button(root, text="Download Audio", command=lambda: download(url_var.get(), "audio")).pack(pady=5)
tk.Button(root, text="Download Video", command=lambda: download(url_var.get(), "video")).pack(pady=5)
tk.Button(root, text="Import to Beets", command=import_to_beets_gui).pack(pady=5)
tk.Button(root, text="Open Music Library", command=lambda: os.startfile(AUDIO_OUTDIR) if os.name == "nt" else subprocess.run(["xdg-open", AUDIO_OUTDIR])).pack(pady=5)
tk.Button(root, text="Open Video Library", command=lambda: os.startfile(VIDEO_OUTDIR) if os.name == "nt" else subprocess.run(["xdg-open", VIDEO_OUTDIR])).pack(pady=5)
tk.Button(root, text="Update", command=do_update).pack(pady=5)

setup_venv()
ensure_config()

root.mainloop()
