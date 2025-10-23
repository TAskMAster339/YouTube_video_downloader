# YouTube Video Downloader

<div align="center">

![Python](https://img.shields.io/badge/python-3.13+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![yt-dlp](https://img.shields.io/badge/yt--dlp-latest-red.svg)
![PyQt](https://img.shields.io/badge/PyQt-5/6-green.svg)
![Tests](https://img.shields.io/badge/tests-pytest-yellow.svg)

**A powerful desktop application for downloading YouTube videos with an intuitive GUI interface**

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Configuration](#%EF%B8%8F-configuration) • [Contributing](#-contributing)

</div>

---

## 📖 About

YouTube Video Downloader is a versatile Python application that combines the power of [yt-dlp](https://github.com/yt-dlp/yt-dlp) with modern graphical and command-line interfaces. Download individual videos, entire playlists, or use batch mode with both GUI and CLI modes for maximum flexibility.

### ✨ Features

- 🎨 **Modern GUI Interface** - Intuitive PyQt5/PyQt6 desktop application
- 📹 **Multiple Download Modes** - Single video, playlist, or batch downloading
- 🎬 **Format Selection** - Choose video formats (MP4) or audio extraction (MP3)
- 📊 **Quality Options** - Select from best, medium, or lowest quality
- 🔄 **Batch Downloading** - Process multiple URLs from `links.txt`
- 📋 **File Management** - View, refresh, and delete downloaded files directly from the app
- ⚙️ **Dark Mode** - Easy-on-the-eyes dark theme
- 🌍 **Cross-platform** - Works on Windows, macOS, and Linux
- 🚀 **Fast and Reliable** - Powered by yt-dlp with automatic error handling
- 📝 **Progress Tracking** - Real-time download progress and status updates
- 🛠️ **Customizable Settings** - Configure download location and preferences via GUI

---

## 🚀 Installation

### Prerequisites

- **Python 3.13+**
- **pip** (Python package manager)
- **FFmpeg** (required for audio conversion and video processing)

### System-Specific Setup

#### Installing FFmpeg

**Windows:**

Download from [FFmpeg Builds](https://ffmpeg.org/download.html) or use Chocolatey:

```bash
choco install ffmpeg
```

Verify installation: `ffmpeg -version`

**macOS:**

```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**

```bash
sudo apt update
sudo apt install ffmpeg
```

### Python Installation Steps

1. **Clone the repository**

   ```bash
   git clone https://github.com/TAskMAster339/YouTube_video_downloader.git
   cd YouTube_video_downloader
   ```

2. **Create a virtual environment** (recommended)

   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

   **Key Dependencies:**

   - `yt-dlp` - YouTube video downloader
   - `PyQt5` or `PyQt6` - GUI framework
   - `pytest` - Testing framework
   - `pytest-mock` - Mocking library for tests

---

## 📚 Usage

### Quick Start (Command Line)

1. **Prepare your links file**

   Create or edit the `links.txt` file in the project directory and add YouTube URLs. You can separate them with:

   - **Newlines** (one URL per line)
   - **Spaces** (multiple URLs on one line)

   **Example 1** - Newline-separated:

   ```
   https://www.youtube.com/watch?v=dQw4w9WgXcQ
   https://www.youtube.com/watch?v=9bZkp7q19f0
   https://www.youtube.com/watch?v=kJQP7kiw5Fk
   ```

   **Example 2** - Space-separated:

   ```
   https://www.youtube.com/watch?v=dQw4w9WgXcQ https://www.youtube.com/watch?v=9bZkp7q19f0
   ```

2. **Run the script**

   Choose the appropriate command for your operating system:

   **Windows:**

   ```bash
   py main.py
   ```

   **macOS:**

   ```bash
   python main.py
   ```

   **Linux:**

   ```bash
   python3 main.py
   ```

3. **Find your videos**

   Downloaded videos will be saved in the `result/` directory.

### 🎨 GUI Usage

#### Running the GUI Application

```bash
# Windows
py src/app.py

# macOS/Linux
python3 src/app.py
```

#### Interface Overview

The GUI provides an intuitive interface for all downloading needs:

**Main Window Features:**

- **URL Input Field** - Paste YouTube video or playlist URLs
- **Format Selection** - Choose between:
  - MP4 Video (best quality audio + video)
  - MP3 Audio (audio only)
- **Quality Selection** - Select quality tier:
  - **Best** - Highest quality (larger file size)
  - **Semi** - Medium quality (balanced)
  - **Worst** - Lowest quality (smallest file size)
- **Progress Bar** - Real-time download progress
- **Download Button** - Start the download process
- **File List** - View all downloaded files
- **Delete Button** - Remove selected files
- **Settings Button** - Configure app preferences
- **Refresh Button** - Update file list

#### How to Download

1. **Single Video:**

   - Paste a YouTube video URL into the input field
   - Select format (MP4 or MP3) and quality
   - Click "Download Video" or "Download Audio"
   - Monitor progress in the progress bar

2. **Playlist:**

   - Paste a YouTube playlist URL
   - Select format and quality
   - Click "Download Video" or "Download Audio"
   - App downloads all videos sequentially

3. **Batch Processing:**
   - Fill `links.txt` with multiple URLs (one per line or space-separated)
   - Click "Batch Download"
   - App processes all URLs and clears the file upon completion

---

## ⚙️ Configuration

### Project Structure

```
YouTube_Video_Downloader/
├── src/
│   ├── app.py        # gui application
│   ├── local.py      # local yt-dlp usage
│   ├── main.py       # Main script
├── tests/            # Tests dir
├── links.txt         # Input file with video URLs
├── result/           # Downloaded videos directory
├── requirements.txt  # Python dependencies
└── README.md         # This file
```

### Customizing Download Options

You can modify the download settings by editing `main.py`. Common options include:

- **Video quality** - Choose resolution (e.g., 1080p, 720p, best)
- **Audio only** - Extract audio instead of video
- **Subtitles** - Download subtitles automatically
- **Playlist support** - Download entire playlists

Example configuration (in `main.py`):

```python
ydl_opts = {
    'format': 'bestvideo+bestaudio/best',  # Best quality
    'outtmpl': 'result/%(title)s.%(ext)s',  # Output template
    'quiet': False,                          # Show progress
}
```

---

## 🔧 Troubleshooting

### Common Issues

**Problem:** `ModuleNotFoundError: No module named 'yt_dlp'`

**Solution:** Install yt-dlp:

```bash
pip install yt-dlp
```

---

**Problem:** Video download fails with "Video unavailable"

**Solution:**

- Check if the video is public and accessible
- Update yt-dlp to the latest version: `pip install --upgrade yt-dlp`
- Some videos may have regional restrictions

---

**Problem:** Permission error when writing to `result/` directory

**Solution:**

- Ensure you have write permissions in the project directory
- Run the script with appropriate permissions (avoid using `sudo` unless necessary)

---

**Problem:** `links.txt` file not found

**Solution:**

- Create the file in the same directory as `main.py`
- Check the file name (case-sensitive on Linux/macOS)

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/AmazingFeature`)
3. **Commit your changes** (`git commit -m 'Add some AmazingFeature'`)
4. **Push to the branch** (`git push origin feature/AmazingFeature`)
5. **Open a Pull Request**

### Development Setup

```bash
# Clone your fork
git clone https://github.com/YOUR_USERNAME/YouTube_Video_Downloader.git

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements.txt
pip install pytest pytest-mock  # For testing
```

### Running Tests

```bash
pytest tests/
```

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## ⚠️ Disclaimer

This tool is for educational and personal use only. Please respect YouTube's Terms of Service and copyright laws. Do not use this tool to:

- Download copyrighted content without permission
- Violate YouTube's Terms of Service
- Redistribute downloaded content

Always ensure you have the right to download and use any content.

---

## 🙏 Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - The powerful library that makes this possible
- All contributors who have helped improve this project

---

## 📧 Contact

**Project Maintainer:** TAskMAster339

- GitHub: [@TAskMAster339](https://github.com/TAskMAster339)
- Project Link: [https://github.com/TAskMAster339/YouTube_Video_Downloader](https://github.com/TAskMAster339/YouTube_Video_Downloader)

---

## 📊 Project Status

![GitHub last commit](https://img.shields.io/github/last-commit/TAskMAster339/YouTube_Video_Downloader)
![GitHub issues](https://img.shields.io/github/issues/TAskMAster339/YouTube_Video_Downloader)
![GitHub pull requests](https://img.shields.io/github/issues-pr/TAskMAster339/YouTube_Video_Downloader)

**Status:** Done 🚀

---

<div align="center">

**⭐ If you find this project useful, please consider giving it a star!**

Made with ❤️ by TAskMAster339

</div>
