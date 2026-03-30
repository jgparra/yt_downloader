#!/usr/bin/env python3
"""
================================================================================
yt-dlp GUI Manager (Cross-Platform)
================================================================================
Description: A cross-platform Python GUI application for downloading videos and 
             audio from YouTube using yt-dlp with an easy-to-use interface.
             Works on Windows, macOS, and Linux.

Author:      gregorio parra
Assistant:   Claude Sonnet 4.5
Date:        March 2026
Version:     2.0

Features:
  - Cross-platform: Windows, macOS, Linux
  - Install/Update yt-dlp automatically
  - Smart FFmpeg detection and installation
  - Download videos in MP4 format
  - Download audio in MP3 format
  - Visual log output
  - Automatic file organization

Requirements:
  - Python 3.7 or higher
  - tkinter (usually comes with Python)
  - Internet connection

Usage:
  python yt-dlp-gui.py
  or
  python3 yt-dlp-gui.py (on macOS/Linux)
================================================================================
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import subprocess
import sys
import os
import platform
import shutil
import urllib.request
import zipfile
import threading
import re
from collections import deque
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, parse_qs

# ===== CONFIGURATION =====
PROJECT_FOLDER_NAME = "mi_yt_dlp"
DOWNLOADS_FOLDER_NAME = "V_A_downloads"
FFMPEG_WINDOWS_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"

# Detect operating system
CURRENT_OS = platform.system()  # 'Windows', 'Darwin' (macOS), 'Linux'

# GUI Configuration
WINDOW_WIDTH = 700
WINDOW_HEIGHT = 550

# Colors
APP_BG_COLOR = "#d4d0c8"
CARD_BG_COLOR = "#efefef"
TEXT_COLOR = "#1a1a1a"
MUTED_TEXT_COLOR = "#4a4a4a"
ACCENT_COLOR = "#2f6db2"
LOG_BG_COLOR = "#ffffff"
LOG_FG_COLOR = "#1a1a1a"
BORDER_COLOR = "#9b9b9b"
BUTTON_TEXT_COLOR = "#1a1a1a"


class YtDlpGUI:
    """Main GUI application class"""
    PROGRESS_PATTERN = re.compile(r"\[download\]\s+(\d{1,3}(?:\.\d+)?)%")

    def set_progress(self, percent):
        """Set progress bar and percentage label (0-100)."""
        if hasattr(self, "progress_var"):
            clamped = max(0.0, min(100.0, float(percent)))
            self.progress_var.set(clamped)
            self.progress_value_label.config(text=f"{clamped:5.1f}%")
            self.progress_bar.update()

    def reset_progress(self):
        """Reset progress widgets."""
        if hasattr(self, "progress_var"):
            self.progress_var.set(0)
            self.progress_value_label.config(text="  0.0%")
            self.progress_bar.update()

    def update_download_progress_from_line(self, line):
        """Parse yt-dlp output line and update progress when percentage appears."""
        match = self.PROGRESS_PATTERN.search(line)
        if match:
            self.set_progress(float(match.group(1)))

    def validate_url(self, url):
        """Validate that URL is a YouTube video URL."""
        if not url:
            self.add_log("ERROR: Please enter a URL")
            messagebox.showerror("Error", "Please enter a URL")
            return False

        try:
            parsed = urlparse(url)
        except Exception:
            self.add_log("ERROR: Invalid URL format")
            messagebox.showerror("Error", "Invalid URL format")
            return False

        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            self.add_log("ERROR: URL must include http/https and a valid domain")
            messagebox.showerror("Error", "Please enter a valid URL (http/https)")
            return False

        host = parsed.netloc.lower()
        if host.startswith("www."):
            host = host[4:]

        allowed_hosts = {"youtube.com", "m.youtube.com", "music.youtube.com", "youtu.be"}
        if host not in allowed_hosts:
            self.add_log("ERROR: URL must be from YouTube")
            messagebox.showerror("Error", "URL must be from YouTube")
            return False

        # Validate this is a video endpoint (watch/shorts/embed/live/youtu.be ID)
        path = parsed.path.strip("/")
        path_parts = [p for p in path.split("/") if p]
        query = parse_qs(parsed.query)
        video_id = None

        if host == "youtu.be":
            if path_parts:
                video_id = path_parts[0]
        elif path_parts and path_parts[0] == "watch":
            video_id = query.get("v", [""])[0]
        elif path_parts and path_parts[0] in {"shorts", "embed", "live"} and len(path_parts) >= 2:
            video_id = path_parts[1]

        if not video_id or len(video_id.strip()) < 6:
            self.add_log("ERROR: URL must point to a specific YouTube video")
            messagebox.showerror(
                "Error",
                "Please paste a valid YouTube video URL.\n"
                "Examples:\n"
                "- https://www.youtube.com/watch?v=...\n"
                "- https://youtu.be/..."
            )
            return False

        return True

    def make_button(self, text, bg, active_bg, command):
        """Create a consistently styled action button."""
        button = tk.Button(
            self.root,
            text=text,
            bg=bg,
            fg=BUTTON_TEXT_COLOR,
            activebackground=active_bg,
            activeforeground=BUTTON_TEXT_COLOR,
            relief="raised",
            bd=2,
            cursor="hand2",
            highlightthickness=1,
            highlightbackground=APP_BG_COLOR,
            font=("Helvetica", 10, "normal"),
            command=command
        )
        button.bind("<Enter>", lambda _e, b=button, c=active_bg: b.config(bg=c))
        button.bind("<Leave>", lambda _e, b=button, c=bg: b.config(bg=c))
        return button

    def make_label(self, text, x, y, width=None, height=None, bold=False, font_size=10):
        """Create a modern-styled label."""
        label = tk.Label(
            self.root,
            text=text,
            bg=APP_BG_COLOR,
            fg=TEXT_COLOR,
            font=("Helvetica", font_size, "bold" if bold else "normal"),
            anchor="w"
        )
        if width is None and height is None:
            label.place(x=x, y=y)
        else:
            place_kwargs = {"x": x, "y": y}
            if width is not None:
                place_kwargs["width"] = width
            if height is not None:
                place_kwargs["height"] = height
            label.place(**place_kwargs)
        return label

    def configure_styles(self):
        """Configure ttk widgets with a cleaner modern look."""
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure(
            "Modern.Horizontal.TProgressbar",
            troughcolor="#d8d8d8",
            background=ACCENT_COLOR,
            bordercolor=BORDER_COLOR,
            lightcolor=ACCENT_COLOR,
            darkcolor=ACCENT_COLOR
        )
        style.configure(
            "Modern.TCombobox",
            fieldbackground=CARD_BG_COLOR,
            background=CARD_BG_COLOR,
            foreground=TEXT_COLOR,
            bordercolor=BORDER_COLOR,
            arrowsize=14
        )

    def refresh_queue_display(self):
        """Refresh current download and pending queue display."""
        if self.current_download:
            mode = self.current_download["mode"].upper()
            url = self.current_download["url"]
            self.current_label.config(text=f"Now downloading [{mode}]: {url[:85]}")
        else:
            self.current_label.config(text="Now downloading: (idle)")

        self.queue_list.delete(0, 'end')
        for index, item in enumerate(self.download_queue, start=1):
            self.queue_list.insert('end', f"{index:02d}. [{item['mode'].upper()}] {item['url']}")
        self.update_action_button_states()

    def update_action_button_states(self):
        """Enable/disable buttons based on current UI state."""
        has_url = bool(self.url_entry.get().strip())
        has_selection = bool(self.queue_list.curselection())
        has_pending = len(self.download_queue) > 0
        self.btn_start.config(state="normal" if has_url else "disabled")
        self.btn_remove_selected.config(state="normal" if has_selection else "disabled")
        self.btn_clear_queue.config(state="normal" if has_pending else "disabled")

    def on_url_change(self, _event=None):
        """Refresh button states when URL field changes."""
        self.update_action_button_states()

    def remove_selected_queue_item(self):
        """Remove selected item from pending queue."""
        selection = self.queue_list.curselection()
        if not selection:
            return
        index = selection[0]
        with self.queue_lock:
            if 0 <= index < len(self.download_queue):
                removed = self.download_queue[index]
                del self.download_queue[index]
            else:
                return
        self.add_log(f"[-] Removed from queue [{removed['mode'].upper()}]: {removed['url']}")
        self.refresh_queue_display()

    def clear_queue_items(self):
        """Clear all pending queue items (keeps active download)."""
        with self.queue_lock:
            count = len(self.download_queue)
            self.download_queue.clear()
        if count:
            self.add_log(f"[-] Cleared queue: {count} pending item(s) removed")
        self.refresh_queue_display()

    def open_downloads_folder(self):
        """Open the downloads folder, creating it if needed."""
        if not self.downloads_path.exists():
            self.downloads_path.mkdir(parents=True, exist_ok=True)
            self.add_log(f"[+] Created downloads folder: {self.downloads_path}")
        self.open_folder(self.downloads_path)

    def enqueue_current_url(self):
        """Add current URL to queue and start worker if idle."""
        url = self.url_entry.get().strip()
        if not self.validate_url(url):
            return

        mode = self.download_type_var.get().strip().lower() or "video"
        item = {"url": url, "mode": mode}

        with self.queue_lock:
            self.download_queue.append(item)
            pending_count = len(self.download_queue)
            worker_busy = self.worker_running

        self.add_log(f"[+] Added to queue [{mode.upper()}]: {url}")
        self.add_log(f"    Pending items: {pending_count}")
        self.url_entry.delete(0, 'end')
        self.refresh_queue_display()

        if not worker_busy:
            thread = threading.Thread(target=self.process_queue, daemon=True)
            thread.start()

    def get_ytdlp_paths(self):
        """Return yt-dlp and Python executables from venv."""
        venv_path = self.project_path / "venv"
        if CURRENT_OS == "Windows":
            ytdlp_exe = venv_path / "Scripts" / "yt-dlp.exe"
            python_exe = venv_path / "Scripts" / "python.exe"
        else:
            ytdlp_exe = venv_path / "bin" / "yt-dlp"
            python_exe = venv_path / "bin" / "python"

        if not python_exe.exists():
            self.add_log("ERROR: Python virtual environment not found")
            self.add_log("       Please run the 'Update' button first")
            messagebox.showerror("Error", "Please install yt-dlp first (Update button)")
            return None

        if not ytdlp_exe.exists():
            self.add_log("ERROR: yt-dlp not found in virtual environment")
            self.add_log("       Please run the 'Update' button first")
            messagebox.showerror("Error", "Please install yt-dlp first (Update button)")
            return None

        return ytdlp_exe

    def process_queue(self):
        """Process queue one by one."""
        with self.queue_lock:
            if self.worker_running:
                return
            self.worker_running = True

        try:
            while True:
                with self.queue_lock:
                    if not self.download_queue:
                        self.current_download = None
                        self.refresh_queue_display()
                        break
                    item = self.download_queue.popleft()
                    self.current_download = item
                    self.refresh_queue_display()
                self.download_item(item)
        finally:
            with self.queue_lock:
                self.worker_running = False
                self.current_download = None
            self.refresh_queue_display()
            self.reset_progress()

    def download_item(self, item):
        """Download one queued item."""
        mode = item["mode"]
        url = item["url"]
        self.reset_progress()
        self.add_log(f"=== Starting {mode} download ===")
        self.add_log(f"URL: {url}")

        try:
            if not self.downloads_path.exists():
                self.add_log(f"[+] Creating {DOWNLOADS_FOLDER_NAME} folder...")
                self.downloads_path.mkdir(parents=True)
            else:
                self.add_log(f"[+] {DOWNLOADS_FOLDER_NAME} folder found")

            ytdlp_exe = self.get_ytdlp_paths()
            if not ytdlp_exe:
                return

            self.add_log(f"[+] Downloading {mode}...")
            self.add_log("    This may take several minutes...")
            ssl_env = self.get_ssl_env()

            if mode == "audio":
                command = [str(ytdlp_exe), "-x", "--audio-format", "mp3", url]
                ext_glob = "*.mp3"
                media_tag = "MP3"
            else:
                command = [
                    str(ytdlp_exe),
                    "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                    "--merge-output-format", "mp4",
                    url
                ]
                ext_glob = "*.mp4"
                media_tag = "MP4"

            success = self.run_command(
                command,
                cwd=self.project_path,
                env=ssl_env,
                line_callback=self.update_download_progress_from_line
            )
            if not success:
                self.add_log(f"ERROR: {mode.capitalize()} download failed")
                return

            self.add_log(f"[+] Moving {media_tag} files to downloads folder...")
            files = list(self.project_path.glob(ext_glob))
            if not files:
                self.add_log(f"WARNING: No {media_tag} files downloaded")
            else:
                moved_count = 0
                for media_file in files:
                    try:
                        dest_path = self.downloads_path / media_file.name
                        shutil.move(str(media_file), str(dest_path))
                        self.add_log(f"    [OK] {media_file.name} moved successfully")
                        moved_count += 1
                    except Exception as e:
                        self.add_log(f"    [ERROR] Could not move {media_file.name}: {str(e)}")
                self.add_log(f"[+] Moved {moved_count} of {len(files)} {media_tag} file(s)")

            self.open_folder(self.downloads_path)
            self.set_progress(100)
            self.add_log(f"=== {mode.upper()} DOWNLOAD COMPLETED ===")
        except Exception as e:
            self.add_log(f"CRITICAL ERROR ({mode}): {str(e)}")

    def __init__(self, root):
        self.root = root
        self.root.title("yt-dlp GUI Manager (Cross-Platform)")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.resizable(False, False)
        self.root.configure(bg=APP_BG_COLOR)
        self.download_queue = deque()
        self.current_download = None
        self.queue_lock = threading.Lock()
        self.worker_running = False
        self.configure_styles()
        
        # Get script directory
        if getattr(sys, 'frozen', False):
            # Running as compiled executable
            self.script_dir = Path(sys.executable).parent
        else:
            # Running as script
            self.script_dir = Path(__file__).parent.absolute()
        
        self.project_path = self.script_dir / PROJECT_FOLDER_NAME
        self.downloads_path = self.script_dir / DOWNLOADS_FOLDER_NAME
        
        # Create GUI elements
        self.create_widgets()
        
        # Welcome message
        self.add_log("=== yt-dlp GUI Manager started ===")
        self.add_log(f"Detected OS: {CURRENT_OS}")
        self.add_log("Press [Update] to install/update yt-dlp")
        self.add_log("Use [Start] to add URL to the queue")
        
        # macOS specific SSL certificate notice
        if CURRENT_OS == "Darwin":
            self.add_log("")
            self.add_log("NOTE: macOS requires SSL certificate setup.")
            self.add_log("      The [Update] button will install certifi automatically.")
        
        self.add_log("")
    
    def create_widgets(self):
        """Create all GUI widgets"""
        
        # URL input section
        self.make_label("YouTube URL:", 10, 15, bold=True)
        
        self.url_entry = tk.Entry(
            self.root,
            font=("Helvetica", 10, "normal"),
            width=75,
            bg=CARD_BG_COLOR,
            fg=TEXT_COLOR,
            insertbackground=TEXT_COLOR,
            relief="solid",
            bd=1,
            disabledbackground="#dddddd",
            disabledforeground="#777777",
            highlightthickness=1,
            highlightbackground=BORDER_COLOR
        )
        self.url_entry.place(x=10, y=40, width=660, height=25)
        self.url_entry.bind("<KeyRelease>", self.on_url_change)
        
        # Buttons - Row 1 (Setup buttons)
        self.btn_update = self.make_button(
            text="Update yt-dlp",
            bg="#e6e6e6",
            active_bg="#d9d9d9",
            command=self.install_ytdlp_thread
        )
        self.btn_update.place(x=10, y=75, width=150, height=35)
        
        self.btn_ffmpeg = self.make_button(
            text="Setup FFmpeg",
            bg="#e6e6e6",
            active_bg="#d9d9d9",
            command=self.install_ffmpeg_thread
        )
        self.btn_ffmpeg.place(x=170, y=75, width=130, height=35)
        
        # Download options
        self.make_label("Type:", 315, 82, bold=True)
        self.download_type_var = tk.StringVar(value="audio")
        self.download_type_combo = ttk.Combobox(
            self.root,
            textvariable=self.download_type_var,
            values=["video", "audio"],
            state="readonly",
            style="Modern.TCombobox"
        )
        self.download_type_combo.place(x=355, y=80, width=105, height=28)

        # Buttons - Row 2 (Queue actions)
        self.btn_start = self.make_button(
            text="Add to Queue",
            bg="#e6e6e6",
            active_bg="#d9d9d9",
            command=self.enqueue_current_url
        )
        self.btn_start.place(x=10, y=120, width=120, height=35)
        
        self.btn_remove_selected = self.make_button(
            text="Remove Selected",
            bg="#e6e6e6",
            active_bg="#d9d9d9",
            command=self.remove_selected_queue_item
        )
        self.btn_remove_selected.place(x=140, y=120, width=120, height=35)
        
        self.btn_clear_queue = self.make_button(
            text="Clear Queue",
            bg="#e6e6e6",
            active_bg="#d9d9d9",
            command=self.clear_queue_items
        )
        self.btn_clear_queue.place(x=270, y=120, width=120, height=35)

        self.btn_clear_log = self.make_button(
            text="Clear Log",
            bg="#e6e6e6",
            active_bg="#d9d9d9",
            command=self.clear_log
        )
        self.btn_clear_log.place(x=400, y=120, width=85, height=35)

        self.btn_open_downloads = self.make_button(
            text="Open Downloads",
            bg="#e6e6e6",
            active_bg="#d9d9d9",
            command=self.open_downloads_folder
        )
        self.btn_open_downloads.place(x=490, y=120, width=105, height=35)
        
        self.btn_exit = self.make_button(
            text="Exit",
            bg="#e6e6e6",
            active_bg="#d9d9d9",
            command=self.root.quit
        )
        self.btn_exit.place(x=600, y=120, width=70, height=35)
        
        # Queue section
        self.make_label("Queue:", 10, 165, bold=True)
        self.current_label = tk.Label(
            self.root,
            text="Now downloading: (idle)",
            font=("Helvetica", 9, "normal"),
            anchor="w",
            bg=APP_BG_COLOR,
            fg=MUTED_TEXT_COLOR
        )
        self.current_label.place(x=10, y=188, width=660, height=22)
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            self.root,
            variable=self.progress_var,
            maximum=100,
            mode="determinate",
            style="Modern.Horizontal.TProgressbar"
        )
        self.progress_bar.place(x=10, y=212, width=610, height=20)
        self.progress_value_label = tk.Label(
            self.root,
            text="  0.0%",
            font=("Helvetica", 9, "bold"),
            anchor="e",
            bg=APP_BG_COLOR,
            fg=ACCENT_COLOR
        )
        self.progress_value_label.place(x=625, y=212, width=45, height=20)
        self.queue_list = tk.Listbox(
            self.root,
            font=("Helvetica", 9),
            bg=CARD_BG_COLOR,
            fg=TEXT_COLOR,
            relief="solid",
            bd=1,
            highlightthickness=1,
            highlightbackground=BORDER_COLOR,
            selectbackground="#316ac5",
            selectforeground="#ffffff"
        )
        self.queue_list.place(x=10, y=238, width=660, height=46)
        self.queue_list.bind("<<ListboxSelect>>", lambda _e: self.update_action_button_states())
        
        # Log section
        self.make_label("Log:", 10, 290, bold=True)
        
        self.log_text = scrolledtext.ScrolledText(
            self.root,
            font=("Helvetica", 9),
            bg=LOG_BG_COLOR,
            fg=LOG_FG_COLOR,
            insertbackground=TEXT_COLOR,
            state='disabled',
            wrap='word',
            relief="solid",
            bd=1,
            highlightthickness=1,
            highlightbackground=BORDER_COLOR
        )
        self.log_text.place(x=10, y=315, width=660, height=180)
        self.update_action_button_states()
    
    def add_log(self, message):
        """Add timestamped message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_message = f"{timestamp} - {message}\n"
        
        self.log_text.config(state='normal')
        self.log_text.insert('end', log_message)
        self.log_text.see('end')
        self.log_text.config(state='disabled')
        self.root.update_idletasks()
    
    def clear_log(self):
        """Clear log content"""
        self.log_text.config(state='normal')
        self.log_text.delete('1.0', 'end')
        self.log_text.config(state='disabled')
        self.add_log("Log cleared")
    
    def run_command(self, command, cwd=None, shell=False, env=None, line_callback=None):
        """Run a command and return output line by line"""
        try:
            # Use system environment and add custom env if provided
            cmd_env = os.environ.copy()
            if env:
                cmd_env.update(env)
            
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=cwd,
                shell=shell,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env=cmd_env
            )
            
            if process.stdout is not None:
                for line in process.stdout:
                    line = line.strip()
                    if line:
                        self.add_log(line)
                        if line_callback:
                            line_callback(line)
            
            process.wait()
            return process.returncode == 0
        except Exception as e:
            self.add_log(f"ERROR: {str(e)}")
            return False
    
    def check_ffmpeg_installed(self):
        """Check if FFmpeg is installed in system PATH"""
        return shutil.which("ffmpeg") is not None
    
    def get_ssl_env(self):
        """Get SSL environment variables for macOS certificate handling"""
        env = {}
        
        if CURRENT_OS == "Darwin":
            # Try to find certifi certificates
            venv_path = self.project_path / "venv"
            if CURRENT_OS == "Windows":
                python_exe = venv_path / "Scripts" / "python.exe"
            else:
                python_exe = venv_path / "bin" / "python"
            
            if python_exe.exists():
                try:
                    # Get certifi certificate path
                    result = subprocess.run(
                        [str(python_exe), "-c", "import certifi; print(certifi.where())"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )
                    if result.returncode == 0:
                        cert_path = result.stdout.strip()
                        if cert_path and os.path.exists(cert_path):
                            env['SSL_CERT_FILE'] = cert_path
                            env['REQUESTS_CA_BUNDLE'] = cert_path
                            self.add_log(f"[+] Using SSL certificates from: {cert_path}")
                except Exception as e:
                    self.add_log(f"[DEBUG] Could not get certifi path: {str(e)}")
        
        return env
    
    # ===== INSTALLATION FUNCTIONS =====
    
    def install_ytdlp_thread(self):
        """Thread wrapper for install_ytdlp"""
        thread = threading.Thread(target=self.install_ytdlp, daemon=True)
        thread.start()
    
    def install_ytdlp(self):
        """Install or update yt-dlp in a virtual environment"""
        self.btn_update.config(state='disabled')
        self.add_log("=== Starting yt-dlp configuration ===")
        
        try:
            # Create project folder
            if not self.project_path.exists():
                self.add_log("[+] Creating project folder...")
                self.project_path.mkdir(parents=True)
                self.add_log(f"Folder created: {self.project_path}")
            else:
                self.add_log("[+] Project folder already exists")
            
            # Create virtual environment
            venv_path = self.project_path / "venv"
            if not venv_path.exists():
                self.add_log("[+] Creating virtual environment...")
                result = self.run_command(
                    [sys.executable, "-m", "venv", "venv"],
                    cwd=self.project_path
                )
                if result:
                    self.add_log("Virtual environment created successfully")
            else:
                self.add_log("[+] Virtual environment already exists")
            
            # Get Python executable in venv
            if CURRENT_OS == "Windows":
                python_exe = venv_path / "Scripts" / "python.exe"
            else:
                python_exe = venv_path / "bin" / "python"
            
            if not python_exe.exists():
                self.add_log(f"ERROR: Python not found in venv: {python_exe}")
                return
            
            # Update pip
            self.add_log("[+] Updating pip...")
            self.run_command([str(python_exe), "-m", "pip", "install", "--upgrade", "pip"])
            
            # Install/update yt-dlp
            self.add_log("[+] Installing/updating yt-dlp...")
            self.run_command([str(python_exe), "-m", "pip", "install", "--upgrade", "yt-dlp"])
            
            # Install certifi for macOS SSL certificate handling
            if CURRENT_OS == "Darwin":
                self.add_log("[+] Installing certifi for SSL certificate support (macOS)...")
                self.run_command([str(python_exe), "-m", "pip", "install", "--upgrade", "certifi"])
                self.add_log("[+] macOS SSL certificates configured")
            
            self.add_log("=== INSTALLATION COMPLETED SUCCESSFULLY ===")
        
        except Exception as e:
            self.add_log(f"CRITICAL ERROR: {str(e)}")
        
        finally:
            self.btn_update.config(state='normal')
    
    def install_ffmpeg_thread(self):
        """Thread wrapper for install_ffmpeg"""
        thread = threading.Thread(target=self.install_ffmpeg, daemon=True)
        thread.start()
    
    def install_ffmpeg(self):
        """Install FFmpeg based on operating system"""
        self.btn_ffmpeg.config(state='disabled')
        
        try:
            # First check if FFmpeg is already in system PATH
            if self.check_ffmpeg_installed():
                self.add_log("=== FFmpeg already installed in system PATH ===")
                self.add_log("FFmpeg is available and ready to use!")
                messagebox.showinfo(
                    "FFmpeg Found",
                    "FFmpeg is already installed in your system PATH.\n"
                    "No additional installation needed!"
                )
                return
            
            # FFmpeg not found, proceed with OS-specific installation
            self.add_log("=== Starting FFmpeg configuration ===")
            self.add_log("[+] FFmpeg not found in system PATH")
            
            if CURRENT_OS == "Windows":
                self.install_ffmpeg_windows()
            
            elif CURRENT_OS == "Darwin":  # macOS
                self.install_ffmpeg_macos()
            
            elif CURRENT_OS == "Linux":
                self.install_ffmpeg_linux()
            
            else:
                self.add_log(f"ERROR: Unsupported operating system: {CURRENT_OS}")
        
        except Exception as e:
            self.add_log(f"CRITICAL ERROR: {str(e)}")
        
        finally:
            self.btn_ffmpeg.config(state='normal')
    
    def install_ffmpeg_windows(self):
        """Download and install FFmpeg on Windows"""
        self.add_log("[+] Detected Windows - Downloading FFmpeg...")
        
        try:
            # Create project folder if needed
            if not self.project_path.exists():
                self.project_path.mkdir(parents=True)
            
            zip_path = self.project_path / "ffmpeg-temp.zip"
            extract_path = self.project_path / "ffmpeg-temp"
            
            # Download FFmpeg
            self.add_log(f"[+] Downloading from {FFMPEG_WINDOWS_URL}")
            self.add_log("    This may take several minutes...")
            
            urllib.request.urlretrieve(FFMPEG_WINDOWS_URL, zip_path)
            
            file_size_mb = zip_path.stat().st_size / (1024 * 1024)
            self.add_log(f"[+] Download completed: {file_size_mb:.1f} MB")
            
            # Extract ZIP
            self.add_log("[+] Extracting files...")
            if extract_path.exists():
                shutil.rmtree(extract_path)
            
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_path)
            
            # Find bin folder
            bin_folder = None
            for root, dirs, files in os.walk(extract_path):
                if 'bin' in dirs:
                    bin_folder = Path(root) / 'bin'
                    break
            
            if bin_folder:
                self.add_log(f"[+] Bin folder found: {bin_folder}")
                
                # Copy exe files
                exe_files = list(bin_folder.glob("*.exe"))
                for exe_file in exe_files:
                    dest_path = self.project_path / exe_file.name
                    shutil.copy2(exe_file, dest_path)
                    self.add_log(f"    [OK] {exe_file.name} copied successfully")
                
                self.add_log(f"[+] Copied {len(exe_files)} executable files")
            else:
                self.add_log("ERROR: Bin folder not found in ZIP file")
            
            # Cleanup
            self.add_log("[+] Cleaning temporary files...")
            zip_path.unlink()
            shutil.rmtree(extract_path)
            
            self.add_log("=== FFMPEG INSTALLATION COMPLETED ===")
        
        except Exception as e:
            self.add_log(f"ERROR during FFmpeg installation: {str(e)}")
    
    def install_ffmpeg_macos(self):
        """Show instructions for installing FFmpeg on macOS"""
        instructions = """
╔════════════════════════════════════════════════════════════════════╗
║            INSTALLING FFMPEG ON macOS - INSTRUCTIONS              ║
╚════════════════════════════════════════════════════════════════════╝

FFmpeg is required for audio conversion and video merging.

OPTION 1 - Using Homebrew (Recommended):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
If you have Homebrew installed, open Terminal and run:

    brew install ffmpeg

This is the easiest method and keeps FFmpeg updated.

If you don't have Homebrew, install it first:
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"


OPTION 2 - Download Static Binary:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. Visit: https://evermeet.cx/ffmpeg/
2. Download the latest "ffmpeg" DMG or zip
3. Extract and copy ffmpeg to /usr/local/bin/
4. Open Terminal and run:
   
   sudo mkdir -p /usr/local/bin
   sudo cp /path/to/downloaded/ffmpeg /usr/local/bin/
   sudo chmod +x /usr/local/bin/ffmpeg


OPTION 3 - Using MacPorts:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
If you use MacPorts instead of Homebrew:

    sudo port install ffmpeg


After installation, restart this application to use FFmpeg.

╚════════════════════════════════════════════════════════════════════╝
        """
        
        self.add_log("[+] macOS detected - Manual installation required")
        self.add_log("")
        self.add_log(instructions)
        
        # Show dialog with instructions
        messagebox.showinfo(
            "FFmpeg Installation - macOS",
            "FFmpeg installation requires manual setup on macOS.\n\n"
            "Please check the LOG window for detailed instructions.\n\n"
            "RECOMMENDED: Use Homebrew\n"
            "  brew install ffmpeg\n\n"
            "After installation, restart this application."
        )
    
    def install_ffmpeg_linux(self):
        """Show instructions for installing FFmpeg on Linux"""
        instructions = """
╔════════════════════════════════════════════════════════════════════╗
║            INSTALLING FFMPEG ON LINUX - INSTRUCTIONS              ║
╚════════════════════════════════════════════════════════════════════╝

FFmpeg is required for audio conversion and video merging.

Choose the command for your Linux distribution:

Debian/Ubuntu/Mint:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    sudo apt update
    sudo apt install ffmpeg

Fedora:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    sudo dnf install ffmpeg

RHEL/CentOS (with EPEL):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    sudo yum install epel-release
    sudo yum install ffmpeg

Arch Linux:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    sudo pacman -S ffmpeg

openSUSE:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    sudo zypper install ffmpeg


After installation, restart this application to use FFmpeg.

╚════════════════════════════════════════════════════════════════════╝
        """
        
        self.add_log("[+] Linux detected - Package manager installation required")
        self.add_log("")
        self.add_log(instructions)
        
        # Show dialog with instructions
        messagebox.showinfo(
            "FFmpeg Installation - Linux",
            "FFmpeg installation requires package manager.\n\n"
            "Please check the LOG window for commands specific\n"
            "to your Linux distribution.\n\n"
            "Example for Ubuntu/Debian:\n"
            "  sudo apt install ffmpeg\n\n"
            "After installation, restart this application."
        )
    
    # ===== DOWNLOAD FUNCTIONS =====
    
    def open_folder(self, folder_path):
        """Open folder in system file explorer"""
        try:
            if CURRENT_OS == "Windows":
                os.startfile(folder_path)
            elif CURRENT_OS == "Darwin":  # macOS
                subprocess.run(["open", str(folder_path)])
            else:  # Linux
                subprocess.run(["xdg-open", str(folder_path)])
        except Exception as e:
            self.add_log(f"Could not open folder: {str(e)}")


# ===== MAIN EXECUTION =====
def main():
    """Main entry point"""
    root = tk.Tk()
    app = YtDlpGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()