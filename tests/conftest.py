# tests/conftest.py

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.app import DownloadTask, DropArea, MainWindow

# Добавляем src в sys.path
sys.path.insert(0, str((Path(__file__).parent.parent / "src").resolve()))
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PyQt5.QtWidgets import QApplication

# Мокируем get_ffmpeg_path перед импортом app
with patch("src.app.get_ffmpeg_path", return_value="ffmpeg"):
    import src.app as app_module

# Глобальный QApplication для всех тестов
_qapp = None


def pytest_configure(config):
    """Создаём QApplication перед началом тестов."""
    global _qapp  # noqa: PLW0603
    if QApplication.instance() is None:
        _qapp = QApplication(sys.argv)


# ==================== ОБЩИЕ ФИКСТУРЫ ====================


@pytest.fixture
def qapp():
    """QApplication fixture для PyQt тестов."""
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    return app


@pytest.fixture
def temp_dir(tmp_path):
    """Временная директория для тестов."""
    return tmp_path


# ==================== CLI ФИКСТУРЫ ====================


@pytest.fixture
def links_file(tmp_path):
    """Файл с тестовыми ссылками для CLI."""  # noqa: RUF002
    links_path = tmp_path / "links.txt"
    test_links = [
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://www.youtube.com/watch?v=9bZkp7q19f0",
    ]
    links_path.write_text("\n".join(test_links))
    return links_path


@pytest.fixture
def empty_links_file(tmp_path):
    """Пустой файл ссылок для CLI."""
    links_path = tmp_path / "links.txt"
    links_path.write_text("")
    return links_path


@pytest.fixture
def result_dir(tmp_path):
    """Директория для результатов CLI."""
    result_path = tmp_path / "result"
    result_path.mkdir(exist_ok=True)
    return result_path


@pytest.fixture
def sample_video_info():
    """Возвращает образец информации о видео."""  # noqa: RUF002
    return {
        "id": "dQw4w9WgXcQ",
        "title": "Test Video",
        "duration": 212,
        "uploader": "Test Channel",
        "view_count": 1000000,
    }


@pytest.fixture
def mock_yt_dlp(mocker):
    """Мокирует yt_dlp для избежания реальных скачиваний."""
    mock_ytdl = MagicMock()
    mock_ytdl.download.return_value = 0

    mocker.patch("yt_dlp.YoutubeDL", return_value=mock_ytdl)
    return mock_ytdl


# ==================== GUI ФИКСТУРЫ ====================


@pytest.fixture
def main_window(qapp, tmp_path, monkeypatch):
    """Фикстура главного окна приложения."""
    result_dir = tmp_path / "result"
    result_dir.mkdir(exist_ok=True)
    monkeypatch.setattr(app_module, "DOWNLOAD_DIR", result_dir)

    window = MainWindow()
    yield window
    window.close()


@pytest.fixture
def download_worker(tmp_path):
    """Фикстура для DownloadTask."""
    urls = [
        "https://www.youtube.com/watch?v=test1",
        "https://www.youtube.com/watch?v=test2",
    ]
    fmt = "best"

    return DownloadTask(urls, fmt, tmp_path)


@pytest.fixture
def drop_area(qapp):
    """Фикстура для DropArea."""
    return DropArea()
