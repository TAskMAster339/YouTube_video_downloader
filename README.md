# YouTube Video Downloader

<div align="center">

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![yt-dlp](https://img.shields.io/badge/yt--dlp-latest-red.svg)

**A simple, fast, and user-friendly command-line tool for downloading YouTube videos**

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Configuration](#%EF%B8%8F-configuration) • [Contributing](#-contributing)

</div>

---

## 📖 About

YouTube Video Downloader is a lightweight Python script built on top of the powerful [yt-dlp](https://github.com/yt-dlp/yt-dlp) library. It provides an effortless way to batch download videos from YouTube with minimal setup and maximum convenience.

### ✨ Features

- 📥 **Batch downloading** - Download multiple videos at once
- 🚀 **Fast and reliable** - Powered by yt-dlp
- 📝 **Flexible input** - Supports both space and newline-separated URLs
- 🔄 **Auto-cleanup** - Automatically clears the links file after successful downloads
- 💻 **Cross-platform** - Works on Windows, macOS, and Linux
- 🎯 **Simple interface** - No complex configuration required

---

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Steps

1. **Clone the repository**

   ```bash
   git clone https://github.com/TAskMAster339/YouTube_Video_Downloader.git
   cd YouTube_Video_Downloader
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

   Or install yt-dlp directly:

   ```bash
   pip install yt-dlp
   ```

---

## 📚 Usage

### Quick Start

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

### Command-Line Options

```bash
# Basic usage
python main.py

# Custom links file (if implemented)
python main.py --links custom_links.txt

# Custom output directory (if implemented)
python main.py --output downloads/
```

---

## ⚙️ Configuration

### Project Structure

```
YouTube_Video_Downloader/
├── main.py           # Main script
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
