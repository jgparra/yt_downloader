# yt-dlp GUI Manager

---

## English

A user-friendly graphical interface for downloading videos and audio from YouTube using yt-dlp.

### Features

- Easy-to-use GUI: Simple interface for downloading videos and audio.
- Automatic setup: Installs and updates yt-dlp automatically.
- FFmpeg integration: Downloads and configures FFmpeg for media conversion.
- Dual format support:
  - Video: MP4 downloads.
  - Audio: MP3 extraction and conversion.
- Visual feedback: Real-time progress and logs.
- Organized storage: Creates and manages download folders automatically.
- Two versions available:
  - PowerShell (Windows-only): Native Windows GUI.
  - Python (Cross-platform): Works on Windows, macOS, and Linux.

### Getting Started

#### PowerShell Version (Windows)

##### Prerequisites
- Windows 10/11
- PowerShell 5.1 or higher (pre-installed)
- Python 3.x in PATH
- Internet connection

##### Installation
1. Clone this repository:
   ```powershell
   git clone https://github.com/jgparra/yt_downloader.git
   cd yt_downloader
   ```

2. Run the app:
   ```powershell
   .\yt-dlp-gui.ps1
   ```

#### Python Version (Cross-Platform)

##### Prerequisites
- Python 3.7 or higher
- tkinter (usually included)
- Internet connection

##### Installation
1. Clone this repository:
   ```bash
   git clone https://github.com/jgparra/yt_downloader.git
   cd yt_downloader
   ```

2. Run the app:
   ```bash
   python yt-dlp-gui.py
   ```

   On macOS/Linux:
   ```bash
   python3 yt-dlp-gui.py
   ```

### Usage

1. First run setup:
   - Click "Install yt-dlp" to install or update yt-dlp.
   - Click "Install FFmpeg" to download and configure FFmpeg.

2. Download video:
   - Paste a YouTube URL.
   - Click "Download Video (MP4)".
   - Saved to: `V_A_downloads/videos/`

3. Download audio:
   - Paste a YouTube URL.
   - Click "Download Audio (MP3)".
   - Saved to: `V_A_downloads/audios/`

4. Monitor progress:
   - Check real-time logs in the output panel.

### Project Structure

```text
.
├── yt-dlp-gui.ps1          # PowerShell GUI version
├── yt-dlp-gui.py           # Python GUI version
├── run-yt-dl.cmd           # Windows batch runner
├── mi_yt_dlp/              # yt-dlp + FFmpeg install folder
└── V_A_downloads/          # Download output folder
    ├── videos/             # Downloaded videos (MP4)
    └── audios/             # Downloaded audio (MP3)
```

### Dependencies

This project uses the following open-source tools:

- [yt-dlp](https://github.com/yt-dlp/yt-dlp): Command-line audio/video downloader.
- [FFmpeg](https://ffmpeg.org/): Audio/video conversion and processing suite.

Both are downloaded and configured automatically.

### Important Notes

- Respect copyright laws and YouTube Terms of Service.
- Download only content you are allowed to download.
- Personal-use oriented tool.
- Some videos may be geo/copyright-restricted.

### Contributing

Contributions are welcome. Feel free to open an issue or a Pull Request.

### License

This project is licensed under MIT. See [LICENSE](LICENSE) for details.

#### Third-Party Licenses
- yt-dlp: Unlicense (Public Domain)
- FFmpeg: LGPL 2.1+ / GPL 2+ (depending on build)

### Author

Gregorio Parra
- Assistant: Claude Sonnet 4.5

### Acknowledgments

- Thanks to the yt-dlp development team.
- Thanks to the FFmpeg project.
- Built with assistance from Claude AI.

### Contributor Spotlight

Special thanks to D. for valuable improvements contributed through this fork.

- Repository: https://github.com/likelystudying/yt_downloader
- Notable contribution: queued download processing workflow

If you like this project, please visit more projects by D.:

- https://github.com/likelystudying

### Support

If you have issues or questions, please open a GitHub issue.

---

## Espanol

Una interfaz grafica facil de usar para descargar video y audio de YouTube con yt-dlp.

### Caracteristicas

- GUI facil de usar: Interfaz simple para descargar video y audio.
- Configuracion automatica: Instala y actualiza yt-dlp automaticamente.
- Integracion con FFmpeg: Descarga y configura FFmpeg para conversion multimedia.
- Soporte de doble formato:
  - Video: Descargas en MP4.
  - Audio: Extraccion y conversion a MP3.
- Retroalimentacion visual: Progreso y logs en tiempo real.
- Almacenamiento organizado: Crea y gestiona carpetas de descarga automaticamente.
- Dos versiones disponibles:
  - PowerShell (solo Windows): GUI nativa de Windows.
  - Python (multiplataforma): Funciona en Windows, macOS y Linux.

### Inicio Rapido

#### Version PowerShell (Windows)

##### Requisitos
- Windows 10/11
- PowerShell 5.1 o superior (preinstalado)
- Python 3.x en PATH
- Conexion a internet

##### Instalacion
1. Clona este repositorio:
   ```powershell
   git clone https://github.com/jgparra/yt_downloader.git
   cd yt_downloader
   ```

2. Ejecuta la app:
   ```powershell
   .\yt-dlp-gui.ps1
   ```

#### Version Python (Multiplataforma)

##### Requisitos
- Python 3.7 o superior
- tkinter (normalmente incluido)
- Conexion a internet

##### Instalacion
1. Clona este repositorio:
   ```bash
   git clone https://github.com/jgparra/yt_downloader.git
   cd yt_downloader
   ```

2. Ejecuta la app:
   ```bash
   python yt-dlp-gui.py
   ```

   En macOS/Linux:
   ```bash
   python3 yt-dlp-gui.py
   ```

### Uso

1. Configuracion inicial:
   - Haz clic en "Install yt-dlp" para instalar o actualizar yt-dlp.
   - Haz clic en "Install FFmpeg" para descargar y configurar FFmpeg.

2. Descargar video:
   - Pega una URL de YouTube.
   - Haz clic en "Download Video (MP4)".
   - Guardado en: `V_A_downloads/videos/`

3. Descargar audio:
   - Pega una URL de YouTube.
   - Haz clic en "Download Audio (MP3)".
   - Guardado en: `V_A_downloads/audios/`

4. Ver progreso:
   - Revisa logs en tiempo real en el panel de salida.

### Estructura del Proyecto

```text
.
├── yt-dlp-gui.ps1          # Version GUI PowerShell
├── yt-dlp-gui.py           # Version GUI Python
├── run-yt-dl.cmd           # Lanzador batch para Windows
├── mi_yt_dlp/              # Carpeta de instalacion de yt-dlp + FFmpeg
└── V_A_downloads/          # Carpeta de descargas
    ├── videos/             # Videos descargados (MP4)
    └── audios/             # Audios descargados (MP3)
```

### Dependencias

Este proyecto usa las siguientes herramientas open-source:

- [yt-dlp](https://github.com/yt-dlp/yt-dlp): Descargador de audio/video por linea de comandos.
- [FFmpeg](https://ffmpeg.org/): Suite de conversion y procesamiento de audio/video.

Ambas se descargan y configuran automaticamente.

### Notas Importantes

- Respeta las leyes de copyright y los Terminos de Servicio de YouTube.
- Descarga solo contenido que tengas derecho a descargar.
- Herramienta orientada a uso personal.
- Algunos videos pueden tener restricciones geograficas o de copyright.

### Contribuciones

Las contribuciones son bienvenidas. Puedes abrir un issue o un Pull Request.

### Licencia

Este proyecto esta bajo licencia MIT. Revisa [LICENSE](LICENSE) para mas detalles.

#### Licencias de Terceros
- yt-dlp: Unlicense (Dominio Publico)
- FFmpeg: LGPL 2.1+ / GPL 2+ (segun el build)

### Autor

Gregorio Parra
- Asistente: Claude Sonnet 4.5

### Agradecimientos

- Gracias al equipo de desarrollo de yt-dlp.
- Gracias al proyecto FFmpeg.
- Construido con asistencia de Claude AI.

### Colaborador Destacado

Un agradecimiento especial a D. por sus valiosas mejoras aportadas mediante este fork.

- Repositorio: https://github.com/likelystudying/yt_downloader
- Aporte destacado: flujo de descargas en cola (queued download processing workflow)

Si te gusto este proyecto, visita tambien mas proyectos de D.:

- https://github.com/likelystudying

### Soporte

Si tienes problemas o preguntas, abre un issue en GitHub.

---

Disclaimer: This tool is provided as-is for educational and personal use. The authors are not responsible for misuse.
Descargo de responsabilidad: Esta herramienta se ofrece tal cual para fines educativos y de uso personal. Los autores no se hacen responsables por usos indebidos.
