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
import tarfile
import threading
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
        """Configure ttk widgets with a cleaner look."""
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure(
            "Modern.TCombobox",
            fieldbackground=CARD_BG_COLOR,
            background=CARD_BG_COLOR,
            foreground=TEXT_COLOR,
            bordercolor=BORDER_COLOR,
            arrowsize=14
        )

    def __init__(self, root):
        self.root = root
        self.root.title("yt-dlp GUI Manager (Cross-Platform)")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.resizable(False, False)
        self.root.configure(bg=APP_BG_COLOR)
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
        
        # macOS specific SSL certificate notice
        if CURRENT_OS == "Darwin":
            self.add_log("")
            self.add_log("NOTE: macOS requires SSL certificate setup.")
            self.add_log("      The [Update] button will install certifi automatically.")
        
        self.add_log("")
    

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

    def create_widgets(self):
        """Create all GUI widgets"""
        
        # URL input section
        url_label = tk.Label(self.root, text="Video URL:", font=("Arial", 10))
        url_label.place(x=10, y=15)
        
        self.url_entry = tk.Entry(self.root, font=("Consolas", 10), width=75)
        self.url_entry.place(x=10, y=40, width=660, height=25)
        
        # Buttons - Row 1 (Setup buttons)
        self.btn_update = tk.Button(
            self.root, text="Update", bg="#90EE90", 
            font=("Arial", 10, "bold"), command=self.install_ytdlp_thread
        )
        self.btn_update.place(x=10, y=75, width=100, height=35)
        
        self.btn_ffmpeg = tk.Button(
            self.root, text="FFmpeg", bg="#FFA07A",
            font=("Arial", 10, "bold"), command=self.install_ffmpeg_thread
        )
        self.btn_ffmpeg.place(x=120, y=75, width=100, height=35)
        
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

        # Buttons - Row 2 (Action buttons)
        self.btn_start = tk.Button(
            self.root, text="Start", bg="#ADD8E6",
            font=("Arial", 10, "bold"), command=self.start_download_thread
        )
        self.btn_start.place(x=10, y=120, width=160, height=35)

        self.btn_clear_log = tk.Button(
            self.root, text="Clear Log", bg="#FFFFE0",
            font=("Arial", 10, "bold"), command=self.clear_log
        )
        self.btn_clear_log.place(x=180, y=120, width=160, height=35)

        self.btn_exit = tk.Button(
            self.root, text="Exit", bg="#D3D3D3",
            font=("Arial", 10, "bold"), command=self.root.quit
        )
        self.btn_exit.place(x=350, y=120, width=320, height=35)
        
        # Log section
        log_label = tk.Label(self.root, text="Log:", font=("Arial", 10))
        log_label.place(x=10, y=165)
        
        self.log_text = scrolledtext.ScrolledText(
            self.root, font=("Consolas", 9), bg=LOG_BG_COLOR,
            fg=LOG_FG_COLOR, state='disabled', wrap='word'
        )
        self.log_text.place(x=10, y=190, width=660, height=305)
    
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
    
    def run_command(self, command, cwd=None, shell=False, env=None):
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
            
            for line in process.stdout:
                line = line.strip()
                if line:
                    self.add_log(line)
            
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
    

    def start_download_thread(self):
        """Start download based on selected type."""
        mode = self.download_type_var.get().strip().lower()
        if mode == "video":
            self.download_video_thread()
        else:
            self.download_audio_thread()

    def download_video_thread(self):
        """Thread wrapper for download_video"""
        thread = threading.Thread(target=self.download_video, daemon=True)
        thread.start()
    
    def download_video(self):
        """Download video in MP4 format"""
        self.btn_download_video.config(state='disabled')
        
        try:
            # Validate URL
            url = self.url_entry.get().strip()
            if not self.validate_url(url):
                return
            
            self.add_log("=== Starting video download ===")
            self.add_log(f"URL: {url}")
            
            # Create downloads folder
            if not self.downloads_path.exists():
                self.add_log(f"[+] Creating {DOWNLOADS_FOLDER_NAME} folder...")
                self.downloads_path.mkdir(parents=True)
            else:
                self.add_log(f"[+] {DOWNLOADS_FOLDER_NAME} folder found")
            
            # Get yt-dlp executable
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
                return
            
            if not ytdlp_exe.exists():
                self.add_log("ERROR: yt-dlp not found in virtual environment")
                self.add_log("       Please run the 'Update' button first")
                messagebox.showerror("Error", "Please install yt-dlp first (Update button)")
                return
            
            self.add_log("[+] Downloading video in MP4 format...")
            self.add_log("    This may take several minutes...")
            
            # Get SSL environment for macOS
            ssl_env = self.get_ssl_env()
            
            # Run yt-dlp
            self.run_command(
                [str(ytdlp_exe), "-f", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                 "--merge-output-format", "mp4", url],
                cwd=self.project_path,
                env=ssl_env
            )
            
            # Move MP4 files to downloads folder
            self.add_log("[+] Moving MP4 files to downloads folder...")
            mp4_files = list(self.project_path.glob("*.mp4"))
            
            if not mp4_files:
                self.add_log("WARNING: No MP4 files downloaded")
            else:
                moved_count = 0
                for mp4_file in mp4_files:
                    try:
                        dest_path = self.downloads_path / mp4_file.name
                        shutil.move(str(mp4_file), str(dest_path))
                        self.add_log(f"    [OK] {mp4_file.name} moved successfully")
                        moved_count += 1
                    except Exception as e:
                        self.add_log(f"    [ERROR] Could not move {mp4_file.name}: {str(e)}")
                
                self.add_log(f"[+] Moved {moved_count} of {len(mp4_files)} MP4 file(s)")
            
            # Open downloads folder
            self.add_log("[+] Opening downloads folder...")
            self.open_folder(self.downloads_path)
            
            self.add_log("=== VIDEO DOWNLOAD COMPLETED ===")
            messagebox.showinfo("Success", "Video download completed!")
        
        except Exception as e:
            self.add_log(f"CRITICAL ERROR: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        
        finally:
            self.btn_download_video.config(state='normal')
    
    def download_audio_thread(self):
        """Thread wrapper for download_audio"""
        thread = threading.Thread(target=self.download_audio, daemon=True)
        thread.start()
    
    def download_audio(self):
        """Download audio in MP3 format"""
        self.btn_download_audio.config(state='disabled')
        
        try:
            # Validate URL
            url = self.url_entry.get().strip()
            if not self.validate_url(url):
                return
            
            self.add_log("=== Starting audio download ===")
            self.add_log(f"URL: {url}")
            
            # Create downloads folder
            if not self.downloads_path.exists():
                self.add_log(f"[+] Creating {DOWNLOADS_FOLDER_NAME} folder...")
                self.downloads_path.mkdir(parents=True)
            else:
                self.add_log(f"[+] {DOWNLOADS_FOLDER_NAME} folder found")
            
            # Get yt-dlp executable
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
                return
            
            if not ytdlp_exe.exists():
                self.add_log("ERROR: yt-dlp not found in virtual environment")
                self.add_log("       Please run the 'Update' button first")
                messagebox.showerror("Error", "Please install yt-dlp first (Update button)")
                return
            
            self.add_log("[+] Downloading audio in MP3 format...")
            self.add_log("    This may take several minutes...")
            
            # Get SSL environment for macOS
            ssl_env = self.get_ssl_env()
            
            # Run yt-dlp
            self.run_command(
                [str(ytdlp_exe), "-x", "--audio-format", "mp3", url],
                cwd=self.project_path,
                env=ssl_env
            )
            
            # Move MP3 files to downloads folder
            self.add_log("[+] Moving MP3 files to downloads folder...")
            mp3_files = list(self.project_path.glob("*.mp3"))
            
            if not mp3_files:
                self.add_log("WARNING: No MP3 files downloaded")
            else:
                moved_count = 0
                for mp3_file in mp3_files:
                    try:
                        dest_path = self.downloads_path / mp3_file.name
                        shutil.move(str(mp3_file), str(dest_path))
                        self.add_log(f"    [OK] {mp3_file.name} moved successfully")
                        moved_count += 1
                    except Exception as e:
                        self.add_log(f"    [ERROR] Could not move {mp3_file.name}: {str(e)}")
                
                self.add_log(f"[+] Moved {moved_count} of {len(mp3_files)} MP3 file(s)")
            
            # Open downloads folder
            self.add_log("[+] Opening downloads folder...")
            self.open_folder(self.downloads_path)
            
            self.add_log("=== AUDIO DOWNLOAD COMPLETED ===")
            messagebox.showinfo("Success", "Audio download completed!")
        
        except Exception as e:
            self.add_log(f"CRITICAL ERROR: {str(e)}")
            messagebox.showerror("Error", f"An error occurred: {str(e)}")
        
        finally:
            self.btn_download_audio.config(state='normal')
    
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
