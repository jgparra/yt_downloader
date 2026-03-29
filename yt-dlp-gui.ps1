<#
================================================================================
yt-dlp GUI Manager
================================================================================
Description: A Windows PowerShell GUI application for downloading videos and 
             audio from YouTube using yt-dlp with an easy-to-use interface.

Author:      gregorio parra
Assistant:   Claude Sonnet 4.5
Date:        March 2026
Version:     1.0

Features:
  - Install/Update yt-dlp automatically
  - Download and install FFmpeg
  - Download videos in MP4 format
  - Download audio in MP3 format
  - Visual log output
  - Automatic file organization

Requirements:
  - Windows PowerShell 5.1 or higher
  - Python 3.x installed and in PATH
  - Internet connection

Usage:
  Run this script with PowerShell: .\yt-dlp-gui.ps1
================================================================================
#>

#Requires -Version 5.1

# ===== ASSEMBLIES =====
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

# ===== CONFIGURATION VARIABLES =====
$script:ProjectFolderName = "mi_yt_dlp"
$script:DownloadsFolderName = "V_A_downloads"
$script:FFmpegUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"

# Form dimensions
$script:FormWidth = 700
$script:FormHeight = 600

# Button positions
$script:Row1Y = 75
$script:Row2Y = 120
$script:ProgressY = 165
$script:LogY = 240
$script:LogHeight = 305

# ===== GLOBAL UI CONTROLS =====
$script:form = $null
$script:txtUrl = $null
$script:logTextBox = $null
$script:progressBar = $null
$script:progressLabel = $null
$script:btnUpdate = $null
$script:btnFFmpeg = $null
$script:btnDownloadVideo = $null
$script:btnDownloadAudio = $null
$script:btnClearLog = $null
$script:btnExit = $null

# ===== UTILITY FUNCTIONS =====

<#
.SYNOPSIS
    Adds a timestamped message to the log output.

.DESCRIPTION
    Appends a message to the log textbox with the current time and scrolls 
    to the bottom to show the latest entry. Automatically detects WARNING, 
    ERROR, and CRITICAL keywords and applies appropriate colors.

.PARAMETER message
    The message string to add to the log.

.PARAMETER color
    Optional color for the message. If not specified, auto-detects based on content:
    - Messages containing "CRITICAL" -> Red
    - Messages containing "ERROR" or "WARNING" -> Yellow
    - Default -> LimeGreen

.EXAMPLE
    Add-Log "Download completed successfully"
    Add-Log "ERROR: Invalid URL"
    Add-Log "WARNING: Connection failed"
#>
function Add-Log {
    param(
        [string]$message,
        [string]$color = ""
    )
    
    # Auto-detect color based on message content if no color specified
    if ([string]::IsNullOrWhiteSpace($color)) {
        if ($message -match "CRITICAL") {
            $color = "Red"
        }
        elseif ($message -match "ERROR|WARNING") {
            $color = "Yellow"
        }
        else {
            $color = "LimeGreen"
        }
    }
    
    $logTextBox.SelectionStart = $logTextBox.TextLength
    $logTextBox.SelectionLength = 0
    $logTextBox.SelectionColor = [System.Drawing.Color]::FromName($color)
    $logTextBox.AppendText("$(Get-Date -Format 'HH:mm:ss') - $message`r`n")
    $logTextBox.SelectionColor = $logTextBox.ForeColor
    $logTextBox.ScrollToCaret()
    [System.Windows.Forms.Application]::DoEvents()
}

<#
.SYNOPSIS
    Updates the progress bar with download progress.

.DESCRIPTION
    Displays or hides the progress bar and updates its value and label.

.PARAMETER percent
    The percentage complete (0-100). Use -1 to hide the progress bar.

.PARAMETER status
    Optional status text to display next to the progress bar.

.EXAMPLE
    Update-Progress 50 "Downloading video..."
    Update-Progress -1  # Hide progress bar
#>
function Update-Progress {
    param(
        [int]$percent,
        [string]$status = ""
    )
    
    if ($percent -lt 0) {
        # Hide progress bar
        $progressBar.Visible = $false
        $progressLabel.Visible = $false
    }
    else {
        # Show and update progress bar
        $progressBar.Visible = $true
        $progressLabel.Visible = $true
        $progressBar.Value = [Math]::Min(100, [Math]::Max(0, $percent))
        $progressLabel.Text = if ($status) { $status } else { "$percent% complete" }
    }
    
    [System.Windows.Forms.Application]::DoEvents()
}

# ===== INSTALLATION FUNCTIONS ===

<#
.SYNOPSIS
    Installs or updates yt-dlp in a Python virtual environment.

.DESCRIPTION
    Creates a project folder, sets up a Python virtual environment, 
    and installs/updates yt-dlp. All output is logged to the GUI.

.NOTES
    Requires Python to be installed and available in PATH.
    Disables the Update button during execution.
#>
function Install-YtDlp {
    $btnUpdate.Enabled = $false
    Add-Log "=== Starting yt-dlp configuration ==="
    
    try {
        # Get script base path
        $scriptPath = Split-Path -Parent $PSCommandPath
        if (-not $scriptPath) {
            $scriptPath = Get-Location
        }
        
        $projectPath = Join-Path $scriptPath $script:ProjectFolderName
        
        # 1. Create project folder if it doesn't exist
        if (-not (Test-Path $projectPath)) {
            Add-Log "[+] Creating project folder..."
            New-Item -ItemType Directory -Path $projectPath -Force | Out-Null
            Add-Log "Folder created: $projectPath"
        } else {
            Add-Log "[+] Project folder already exists"
        }
        
        # 2. Create virtual environment if it doesn't exist
        $venvPath = Join-Path $projectPath "venv"
        if (-not (Test-Path $venvPath)) {
            Add-Log "[+] Creating virtual environment..."
            $currentDir = Get-Location
            Set-Location $projectPath
            & python -m venv venv 2>&1 | ForEach-Object { Add-Log $_.ToString() }
            Set-Location $currentDir
            Add-Log "Virtual environment created successfully"
        } else {
            Add-Log "[+] Virtual environment already exists"
        }
        
        # 3. Update pip
        Add-Log "[+] Updating pip..."
        $pythonExe = Join-Path $venvPath "Scripts\python.exe"
        & $pythonExe -m pip install --upgrade pip 2>&1 | ForEach-Object { Add-Log $_.ToString() }
        
        # 4. Install/update yt-dlp
        Add-Log "[+] Installing/updating yt-dlp..."
        & $pythonExe -m pip install --upgrade yt-dlp 2>&1 | ForEach-Object { Add-Log $_.ToString() }
        
        Add-Log "=== INSTALLATION COMPLETED SUCCESSFULLY ==="
    }
    catch {
        Add-Log "CRITICAL ERROR: $($_.Exception.Message)" -color "Red"
    }
    finally {
        $btnUpdate.Enabled = $true
    }
}

<#
.SYNOPSIS
    Downloads and installs FFmpeg executables.

.DESCRIPTION
    Downloads the FFmpeg essentials package from gyan.dev, extracts the 
    executables (ffmpeg.exe, ffplay.exe, ffprobe.exe) and copies them 
    to the project folder for use with yt-dlp.

.NOTES
    Downloads approximately 80-100MB.
    Disables the FFmpeg button during execution.
#>
function Install-FFmpeg {
    $btnFFmpeg.Enabled = $false
    Add-Log "=== Starting ffmpeg download ==="
    
    try {
        # Get script base path
        $scriptPath = Split-Path -Parent $PSCommandPath
        if (-not $scriptPath) {
            $scriptPath = Get-Location
        }
        
        $projectPath = Join-Path $scriptPath $script:ProjectFolderName
        
        # Create project folder if it doesn't exist
        if (-not (Test-Path $projectPath)) {
            Add-Log "[+] Creating project folder..."
            New-Item -ItemType Directory -Path $projectPath -Force | Out-Null
        }
        
        $zipPath = Join-Path $projectPath "ffmpeg-temp.zip"
        $extractPath = Join-Path $projectPath "ffmpeg-temp"
        
        # Download ZIP file
        Add-Log "[+] Downloading ffmpeg from $($script:FFmpegUrl)"
        Add-Log "    This may take several minutes..."
        
        $webClient = New-Object System.Net.WebClient
        $webClient.DownloadFile($script:FFmpegUrl, $zipPath)
        
        Add-Log "[+] Download completed: $(([System.IO.FileInfo]$zipPath).Length / 1MB) MB"
        
        # Extract ZIP temporarily
        Add-Log "[+] Extracting files..."
        if (Test-Path $extractPath) {
            Remove-Item $extractPath -Recurse -Force
        }
        
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        [System.IO.Compression.ZipFile]::ExtractToDirectory($zipPath, $extractPath)
        
        # Find bin folder inside extracted ZIP
        $binFolder = Get-ChildItem -Path $extractPath -Recurse -Directory | Where-Object { $_.Name -eq 'bin' } | Select-Object -First 1
        
        if ($binFolder) {
            Add-Log "[+] Bin folder found: $($binFolder.FullName)"
            
            # Copy .exe files from bin folder
            $exeFiles = Get-ChildItem -Path $binFolder.FullName -Filter *.exe
            
            foreach ($exeFile in $exeFiles) {
                $destPath = Join-Path $projectPath $exeFile.Name
                Copy-Item -Path $exeFile.FullName -Destination $destPath -Force
                Add-Log "    [OK] $($exeFile.Name) copied successfully"
            }
            
            Add-Log "[+] Copied $($exeFiles.Count) executable files"
        } else {
            Add-Log "ERROR: Bin folder not found in ZIP file" -color "Yellow"
        }
        
        # Clean up temporary files
        Add-Log "[+] Cleaning temporary files..."
        Remove-Item $zipPath -Force
        Remove-Item $extractPath -Recurse -Force
        
        Add-Log "=== FFMPEG INSTALLATION COMPLETED ==="
    }
    catch {
        Add-Log "CRITICAL ERROR: $($_.Exception.Message)" -color "Red"
    }
    finally {
        $btnFFmpeg.Enabled = $true
    }
}

# ===== DOWNLOAD FUNCTIONS =====

<#
.SYNOPSIS
    Downloads audio from a YouTube URL and converts it to MP3.

.DESCRIPTION
    Validates the YouTube URL, downloads the audio using yt-dlp, converts 
    it to MP3 format using FFmpeg, moves the file to the downloads folder, 
    and opens the folder in Windows Explorer.

.NOTES
    Requires yt-dlp and FFmpeg to be installed first.
    Uses the URL from the txtUrl textbox.
    Disables the Download Audio button during execution.
#>
function Download-Audio {
    $btnDownloadAudio.Enabled = $false
    
    try {
        # Validate URL is provided
        if ([string]::IsNullOrWhiteSpace($txtUrl.Text)) {
            Add-Log "ERROR: Please enter a URL" -color "Yellow"
            return
        }
        
        # Validate URL is from YouTube
        $url = $txtUrl.Text.Trim()
        if ($url -notmatch 'youtube\.com|youtu\.be') {
            Add-Log "ERROR: URL must be from youtube.com or youtu.be" -color "Yellow"
            return
        }
        
        Add-Log "=== Starting audio download ==="
        Add-Log "URL: $url"
        
        # Get script base path
        $scriptPath = Split-Path -Parent $PSCommandPath
        if (-not $scriptPath) {
            $scriptPath = Get-Location
        }
        
        # Verify/create downloads folder
        $downloadsPath = Join-Path $scriptPath $script:DownloadsFolderName
        if (-not (Test-Path $downloadsPath)) {
            Add-Log "[+] Creating $($script:DownloadsFolderName) folder..."
            New-Item -ItemType Directory -Path $downloadsPath -Force | Out-Null
        } else {
            Add-Log "[+] $($script:DownloadsFolderName) folder found"
        }
        
        # Verify virtual environment exists
        $projectPath = Join-Path $scriptPath $script:ProjectFolderName
        $venvPath = Join-Path $projectPath "venv"
        $pythonExe = Join-Path $venvPath "Scripts\python.exe"
        $ytDlpExe = Join-Path $venvPath "Scripts\yt-dlp.exe"
        
        if (-not (Test-Path $pythonExe)) {
            Add-Log "ERROR: Python virtual environment not found" -color "Yellow"
            Add-Log "       Please run the 'Update' button first" -color "Yellow"
            return
        }
        
        if (-not (Test-Path $ytDlpExe)) {
            Add-Log "ERROR: yt-dlp not found in virtual environment" -color "Yellow"
            Add-Log "       Please run the 'Update' button first" -color "Yellow"
            return
        }
        
        Add-Log "[+] Downloading audio in MP3 format..."
        Add-Log "    This may take several minutes depending on the video..."
        
        # Execute yt-dlp directly in project folder (where ffmpeg is)
        $currentDir = Get-Location
        Set-Location $projectPath
        
        Update-Progress 0 "Starting download..."
        
        & $ytDlpExe -x --audio-format mp3 $url 2>&1 | ForEach-Object {
            $line = $_.ToString()
            
            # Check if this is a download progress line
            if ($line -match '\[download\]\s+([0-9.]+)%') {
                $percent = [int][Math]::Floor([double]$matches[1])
                
                # Extract additional info if available
                if ($line -match 'of\s+([0-9.]+\w+)') {
                    $size = $matches[1]
                    Update-Progress $percent "Downloading: $percent% of $size"
                }
                else {
                    Update-Progress $percent "Downloading: $percent%"
                }
                
                # Log when download completes
                if ($percent -ge 100) {
                    Add-Log "[+] Download completed: $line"
                }
            }
            # Log non-progress lines (but skip repetitive "100%" lines)
            elseif ($line -notmatch '\[download\]\s+100%') {
                Add-Log $line
            }
        }
        
        Update-Progress -1  # Hide progress bar
        
        Set-Location $currentDir
        
        # Move MP3 files to downloads folder
        Add-Log "[+] Waiting 3 seconds before moving MP3 files..."
        Start-Sleep -Seconds 3
        Add-Log "[+] Moving MP3 files to $($script:DownloadsFolderName)..."
        $mp3Files = Get-ChildItem -LiteralPath $projectPath -Filter *.mp3
        
        if ($mp3Files.Count -eq 0) {
            Add-Log "WARNING: No MP3 files downloaded" -color "Yellow"
        } else {
            $movedCount = 0
            foreach ($mp3File in $mp3Files) {
                try {
                    $destPath = Join-Path $downloadsPath $mp3File.Name
                    Move-Item -LiteralPath $mp3File.FullName -Destination $destPath -Force -ErrorAction Stop
                    Add-Log "    [OK] $($mp3File.Name) moved successfully"
                    $movedCount++
                }
                catch {
                    Add-Log "    [ERROR] Could not move $($mp3File.Name): $($_.Exception.Message)" -color "Yellow"
                }
            }
            
            Add-Log "[+] Moved $movedCount of $($mp3Files.Count) MP3 file(s)"
        }
        
        # Open explorer in downloads folder
        Add-Log "[+] Opening file explorer..."
        Start-Process explorer.exe -ArgumentList $downloadsPath
        
        Add-Log "=== AUDIO DOWNLOAD COMPLETED ==="
    }
    catch {
        Add-Log "CRITICAL ERROR: $($_.Exception.Message)" -color "Red"
    }
    finally {
        Update-Progress -1  # Hide progress bar
        $btnDownloadAudio.Enabled = $true
    }
}

<#
.SYNOPSIS
    Downloads video from a YouTube URL in MP4 format.

.DESCRIPTION
    Validates the YouTube URL, downloads the video using yt-dlp in the 
    best available MP4 quality, moves the file to the downloads folder, 
    and opens the folder in Windows Explorer.

.NOTES
    Requires yt-dlp and FFmpeg to be installed first.
    Uses the URL from the txtUrl textbox.
    Disables the Download Video button during execution.
    Forces MP4 format for maximum compatibility.
#>
function Download-Video {
    $btnDownloadVideo.Enabled = $false
    
    try {
        # Validate URL is provided
        if ([string]::IsNullOrWhiteSpace($txtUrl.Text)) {
            Add-Log "ERROR: Please enter a URL" -color "Yellow"
            return
        }
        
        # Validate URL is from YouTube
        $url = $txtUrl.Text.Trim()
        if ($url -notmatch 'youtube\.com|youtu\.be') {
            Add-Log "ERROR: URL must be from youtube.com or youtu.be" -color "Yellow"
            return
        }
        
        Add-Log "=== Starting video download ==="
        Add-Log "URL: $url"
        
        # Get script base path
        $scriptPath = Split-Path -Parent $PSCommandPath
        if (-not $scriptPath) {
            $scriptPath = Get-Location
        }
        
        # Verify/create downloads folder
        $downloadsPath = Join-Path $scriptPath $script:DownloadsFolderName
        if (-not (Test-Path $downloadsPath)) {
            Add-Log "[+] Creating $($script:DownloadsFolderName) folder..."
            New-Item -ItemType Directory -Path $downloadsPath -Force | Out-Null
        } else {
            Add-Log "[+] $($script:DownloadsFolderName) folder found"
        }
        
        # Verify virtual environment exists
        $projectPath = Join-Path $scriptPath $script:ProjectFolderName
        $venvPath = Join-Path $projectPath "venv"
        $pythonExe = Join-Path $venvPath "Scripts\python.exe"
        $ytDlpExe = Join-Path $venvPath "Scripts\yt-dlp.exe"
        
        if (-not (Test-Path $pythonExe)) {
            Add-Log "ERROR: Python virtual environment not found" -color "Yellow"
            Add-Log "       Please run the 'Update' button first" -color "Yellow"
            return
        }
        
        if (-not (Test-Path $ytDlpExe)) {
            Add-Log "ERROR: yt-dlp not found in virtual environment" -color "Yellow"
            Add-Log "       Please run the 'Update' button first" -color "Yellow"
            return
        }
        
        Add-Log "[+] Downloading video in MP4 format..."
        Add-Log "    This may take several minutes depending on the video..."
        
        # Execute yt-dlp directly in project folder (where ffmpeg is)
        $currentDir = Get-Location
        Set-Location $projectPath
        
        Update-Progress 0 "Starting download..."
        
        & $ytDlpExe -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best" --merge-output-format mp4 $url 2>&1 | ForEach-Object {
            $line = $_.ToString()
            
            # Check if this is a download progress line
            if ($line -match '\[download\]\s+([0-9.]+)%') {
                $percent = [int][Math]::Floor([double]$matches[1])
                
                # Extract additional info if available
                if ($line -match 'of\s+([0-9.]+\w+)') {
                    $size = $matches[1]
                    Update-Progress $percent "Downloading: $percent% of $size"
                }
                else {
                    Update-Progress $percent "Downloading: $percent%"
                }
                
                # Log when download completes
                if ($percent -ge 100) {
                    Add-Log "[+] Download completed: $line"
                }
            }
            # Log non-progress lines (but skip repetitive "100%" lines)
            elseif ($line -notmatch '\[download\]\s+100%') {
                Add-Log $line
            }
        }
        
        Update-Progress -1  # Hide progress bar
        
        Set-Location $currentDir
        
        # Move video files to downloads folder
        Add-Log "[+] Waiting 3 seconds before moving files..."
        Start-Sleep -Seconds 3
        Add-Log "[+] Moving MP4 files to $($script:DownloadsFolderName)..."
        
        # Find MP4 files
        $videoFiles = Get-ChildItem -LiteralPath $projectPath -Filter *.mp4 -ErrorAction SilentlyContinue
        
        if ($videoFiles.Count -eq 0) {
            Add-Log "WARNING: No MP4 files downloaded" -color "Yellow"
        } else {
            $movedCount = 0
            foreach ($videoFile in $videoFiles) {
                try {
                    $destPath = Join-Path $downloadsPath $videoFile.Name
                    Move-Item -LiteralPath $videoFile.FullName -Destination $destPath -Force -ErrorAction Stop
                    Add-Log "    [OK] $($videoFile.Name) moved successfully"
                    $movedCount++
                }
                catch {
                    Add-Log "    [ERROR] Could not move $($videoFile.Name): $($_.Exception.Message)" -color "Yellow"
                }
            }
            
            Add-Log "[+] Moved $movedCount of $($videoFiles.Count) MP4 file(s)"
        }
        
        # Open explorer in downloads folder
        Add-Log "[+] Opening file explorer..."
        Start-Process explorer.exe -ArgumentList $downloadsPath
        
        Add-Log "=== VIDEO DOWNLOAD COMPLETED ==="
    }
    catch {
        Add-Log "CRITICAL ERROR: $($_.Exception.Message)" -color "Red"
    }
    finally {
        Update-Progress -1  # Hide progress bar
        $btnDownloadVideo.Enabled = $true
    }
}

# ===== UI INITIALIZATION =====

<#
.SYNOPSIS
    Initializes and displays the main GUI form.

.DESCRIPTION
    Creates all UI controls (form, buttons, textboxes, labels) and 
    displays the application window.
#>
function Initialize-GUI {
    # Create main form
    $script:form = New-Object System.Windows.Forms.Form
    $form.Text = 'yt-dlp GUI Manager'
    $form.Size = New-Object System.Drawing.Size($script:FormWidth, $script:FormHeight)
    $form.StartPosition = 'CenterScreen'
    $form.FormBorderStyle = 'FixedDialog'
    $form.MaximizeBox = $false

    # URL input section
    $labelUrl = New-Object System.Windows.Forms.Label
    $labelUrl.Location = New-Object System.Drawing.Point(10, 15)
    $labelUrl.Size = New-Object System.Drawing.Size(100, 20)
    $labelUrl.Text = 'Video URL:'
    $form.Controls.Add($labelUrl)

    $script:txtUrl = New-Object System.Windows.Forms.TextBox
    $txtUrl.Location = New-Object System.Drawing.Point(10, 40)
    $txtUrl.Size = New-Object System.Drawing.Size(660, 25)
    $txtUrl.Font = New-Object System.Drawing.Font("Consolas", 10)
    $form.Controls.Add($txtUrl)

    # Buttons - Row 1 (Setup buttons)
    $script:btnUpdate = New-Object System.Windows.Forms.Button
    $btnUpdate.Location = New-Object System.Drawing.Point(10, $script:Row1Y)
    $btnUpdate.Size = New-Object System.Drawing.Size(100, 35)
    $btnUpdate.Text = 'Update'
    $btnUpdate.BackColor = [System.Drawing.Color]::LightGreen
    $btnUpdate.Add_Click({ Install-YtDlp })
    $form.Controls.Add($btnUpdate)

    $script:btnFFmpeg = New-Object System.Windows.Forms.Button
    $btnFFmpeg.Location = New-Object System.Drawing.Point(120, $script:Row1Y)
    $btnFFmpeg.Size = New-Object System.Drawing.Size(100, 35)
    $btnFFmpeg.Text = 'FFmpeg'
    $btnFFmpeg.BackColor = [System.Drawing.Color]::LightSalmon
    $btnFFmpeg.Add_Click({ Install-FFmpeg })
    $form.Controls.Add($btnFFmpeg)

    # Buttons - Row 2 (Action buttons)
    $script:btnDownloadVideo = New-Object System.Windows.Forms.Button
    $btnDownloadVideo.Location = New-Object System.Drawing.Point(10, $script:Row2Y)
    $btnDownloadVideo.Size = New-Object System.Drawing.Size(135, 35)
    $btnDownloadVideo.Text = 'Download Video'
    $btnDownloadVideo.BackColor = [System.Drawing.Color]::LightBlue
    $btnDownloadVideo.Add_Click({ Download-Video })
    $form.Controls.Add($btnDownloadVideo)

    $script:btnDownloadAudio = New-Object System.Windows.Forms.Button
    $btnDownloadAudio.Location = New-Object System.Drawing.Point(155, $script:Row2Y)
    $btnDownloadAudio.Size = New-Object System.Drawing.Size(135, 35)
    $btnDownloadAudio.Text = 'Download Audio'
    $btnDownloadAudio.BackColor = [System.Drawing.Color]::LightCoral
    $btnDownloadAudio.Add_Click({ Download-Audio })
    $form.Controls.Add($btnDownloadAudio)

    $script:btnClearLog = New-Object System.Windows.Forms.Button
    $btnClearLog.Location = New-Object System.Drawing.Point(300, $script:Row2Y)
    $btnClearLog.Size = New-Object System.Drawing.Size(135, 35)
    $btnClearLog.Text = 'Clear Log'
    $btnClearLog.BackColor = [System.Drawing.Color]::LightYellow
    $btnClearLog.Add_Click({
        $logTextBox.Clear()
        Add-Log "Log cleared"
    })
    $form.Controls.Add($btnClearLog)

    $script:btnExit = New-Object System.Windows.Forms.Button
    $btnExit.Location = New-Object System.Drawing.Point(445, $script:Row2Y)
    $btnExit.Size = New-Object System.Drawing.Size(225, 35)
    $btnExit.Text = 'Exit'
    $btnExit.BackColor = [System.Drawing.Color]::LightGray
    $btnExit.Add_Click({ $form.Close() })
    $form.Controls.Add($btnExit)

    # Progress bar section
    $script:progressLabel = New-Object System.Windows.Forms.Label
    $progressLabel.Location = New-Object System.Drawing.Point(10, $script:ProgressY)
    $progressLabel.Size = New-Object System.Drawing.Size(660, 20)
    $progressLabel.Text = 'Ready'
    $progressLabel.Visible = $false
    $form.Controls.Add($progressLabel)

    $script:progressBar = New-Object System.Windows.Forms.ProgressBar
    $progressBar.Location = New-Object System.Drawing.Point(10, ($script:ProgressY + 20))
    $progressBar.Size = New-Object System.Drawing.Size(660, 25)
    $progressBar.Minimum = 0
    $progressBar.Maximum = 100
    $progressBar.Value = 0
    $progressBar.Visible = $false
    $form.Controls.Add($progressBar)

    # Log display section
    $labelLog = New-Object System.Windows.Forms.Label
    $labelLog.Location = New-Object System.Drawing.Point(10, ($script:ProgressY + 50))
    $labelLog.Size = New-Object System.Drawing.Size(100, 20)
    $labelLog.Text = 'Log:'
    $form.Controls.Add($labelLog)

    $script:logTextBox = New-Object System.Windows.Forms.RichTextBox
    $logTextBox.Location = New-Object System.Drawing.Point(10, $script:LogY)
    $logTextBox.Size = New-Object System.Drawing.Size(660, $script:LogHeight)
    $logTextBox.ScrollBars = 'Vertical'
    $logTextBox.Font = New-Object System.Drawing.Font("Consolas", 9)
    $logTextBox.ReadOnly = $true
    $logTextBox.BackColor = [System.Drawing.Color]::Black
    $logTextBox.ForeColor = [System.Drawing.Color]::LimeGreen
    $form.Controls.Add($logTextBox)

    # Welcome message
    Add-Log "=== yt-dlp GUI Manager started ==="
    Add-Log "Press [Update] to install/update yt-dlp"
    Add-Log ""

    # Show the form
    $form.ShowDialog() | Out-Null
}

# ===== MAIN EXECUTION =====
Initialize-GUI
