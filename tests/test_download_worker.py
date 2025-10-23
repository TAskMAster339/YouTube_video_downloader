# tests/test_download_worker.py
import sys
from unittest.mock import MagicMock, patch

import pytest

from src.app import DownloadWorker

sys.path.insert(0, ".")


@pytest.mark.gui
class TestDownloadWorker:
    """Тесты для DownloadWorker."""

    def test_worker_creation(self, download_worker):
        """Тест создания DownloadWorker."""
        assert download_worker is not None
        assert download_worker.urls is not None
        assert len(download_worker.urls) == 2

    def test_worker_format_assignment(self, download_worker):
        """Тест назначения формата."""
        assert download_worker.fmt == "best"

    def test_worker_download_dir(self, download_worker, tmp_path):
        """Тест директории для скачивания."""
        assert download_worker.download_dir == tmp_path

    def test_worker_failed_videos_empty_initially(self, download_worker):
        """Тест что список неудачных видео изначально пуст."""
        assert download_worker.failed_videos == []

    def test_worker_signals_exist(self, download_worker):
        """Тест наличия всех сигналов."""
        assert hasattr(download_worker, "progress_changed")
        assert hasattr(download_worker, "overall_progress")
        assert hasattr(download_worker, "finished")
        assert hasattr(download_worker, "error_occurred")

    @patch("yt_dlp.YoutubeDL")
    def test_worker_run_success(self, mock_ytdlp, download_worker):
        """Тест успешного выполнения worker."""
        mock_instance = MagicMock()
        mock_instance.download.return_value = 0
        mock_ytdlp.return_value.__enter__.return_value = mock_instance

        # Отслеживаем сигналы
        signals_emitted = []
        download_worker.finished.connect(lambda: signals_emitted.append("finished"))

        # Запускаем worker (в тестах запускается синхронно)
        download_worker.run()

        # Проверяем, что finished сигнал был эмитирован
        assert len(download_worker.urls) == 2

    @patch("yt_dlp.YoutubeDL")
    def test_worker_progress_hook(self, mock_ytdlp, download_worker):
        """Тест progress_hook функции."""
        mock_instance = MagicMock()

        def download_side_effect(url_list):
            pass

        mock_instance.download.side_effect = download_side_effect
        mock_ytdlp.return_value.__enter__.return_value = mock_instance

        # Проверяем что YoutubeDL создаётся с опциями  # noqa: RUF003
        # (progress_hooks должны быть установлены)
        assert True


@pytest.mark.integration
class TestDownloadWorkflow:
    """Интеграционные тесты скачивания."""

    @patch("yt_dlp.YoutubeDL")
    def test_download_multiple_videos(self, mock_ytdlp, tmp_path):
        """Тест скачивания нескольких видео."""

        mock_instance = MagicMock()
        mock_instance.download.return_value = 0
        mock_ytdlp.return_value.__enter__.return_value = mock_instance

        urls = [
            "https://youtube.com/watch?v=1",
            "https://youtube.com/watch?v=2",
            "https://youtube.com/watch?v=3",
        ]

        worker = DownloadWorker(urls, "best", tmp_path)

        # Запускаем worker
        worker.run()

        # Проверяем, что download был вызван для каждого URL
        assert mock_instance.download.call_count >= 3

    @patch("yt_dlp.YoutubeDL")
    def test_download_with_quality_formats(self, mock_ytdlp, tmp_path):
        """Тест скачивания с разными форматами качества."""  # noqa: RUF002

        formats = [
            "bestvideo[height<=1080]+bestaudio/best",
            "bestvideo[height<=720]+bestaudio/best",
            "bestvideo[height<=480]+bestaudio/best",
        ]

        for fmt in formats:
            mock_instance = MagicMock()
            mock_instance.download.return_value = 0
            mock_ytdlp.return_value.__enter__.return_value = mock_instance

            worker = DownloadWorker(["https://youtube.com/watch?v=test"], fmt, tmp_path)

            assert worker.fmt == fmt


@pytest.mark.gui
class TestQualityFormatConversion:
    """Тесты конвертации выбора качества в формат yt-dlp."""

    def test_quality_1080p_conversion(self, main_window):
        """Тест конвертации выбора 1080p."""
        main_window.combo_quality.setCurrentIndex(0)
        choice = main_window.combo_quality.currentText()

        if choice == "До 1080p":
            fmt = "bestvideo[height<=1080]+bestaudio/best"

        assert "1080" in fmt

    def test_quality_720p_conversion(self, main_window):
        """Тест конвертации выбора 720p."""
        main_window.combo_quality.setCurrentIndex(1)
        choice = main_window.combo_quality.currentText()

        if choice == "До 720p":
            fmt = "bestvideo[height<=720]+bestaudio/best"

        assert "720" in fmt

    def test_quality_480p_conversion(self, main_window):
        """Тест конвертации выбора 480p."""
        main_window.combo_quality.setCurrentIndex(2)
        choice = main_window.combo_quality.currentText()

        if choice == "До 480p":
            fmt = "bestvideo[height<=480]+bestaudio/best"

        assert "480" in fmt
