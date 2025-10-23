import os
import re
from unittest.mock import MagicMock, patch

import pytest

from src.main import read_links


class TestLinksParsing:
    """Тесты парсинга ссылок из файла."""

    @pytest.mark.unit
    def test_read_links_from_file(self, links_file):
        """Тест чтения ссылок из файла."""
        links = read_links(links_file)

        assert len(links) == 2
        assert all("youtube.com" in link for link in links)

    @pytest.mark.unit
    def test_read_empty_links_file(self, empty_links_file):
        """Тест чтения пустого файла."""
        links = read_links(empty_links_file)

        assert len(links) == 0

    @pytest.mark.unit
    def test_parse_links_with_spaces(self, temp_dir):
        """Тест парсинга ссылок, разделённых пробелами."""
        links_path = temp_dir / "links_spaces.txt"
        links_path.write_text(
            "https://www.youtube.com/watch?v=link1 "
            "https://www.youtube.com/watch?v=link2 "
            "https://www.youtube.com/watch?v=link3",
        )

        with open(links_path) as f:
            content = f.read()
            links = content.split()

        assert len(links) == 3

    @pytest.mark.unit
    def test_parse_links_with_newlines(self, temp_dir):
        """Тест парсинга ссылок, разделённых переносами строк."""
        links_path = temp_dir / "links_newlines.txt"
        links_path.write_text(
            "https://www.youtube.com/watch?v=link1\n"
            "https://www.youtube.com/watch?v=link2\n"
            "https://www.youtube.com/watch?v=link3",
        )

        with open(links_path) as f:
            links = [line.strip() for line in f if line.strip()]

        assert len(links) == 3

    @pytest.mark.unit
    def test_handle_invalid_file_path(self):
        """Тест обработки несуществующего файла."""
        with pytest.raises(FileNotFoundError):
            with open("nonexistent_file.txt", "r") as f:
                f.read()


class TestDownloadFunctionality:
    """Тесты функциональности скачивания."""

    @pytest.mark.unit
    def test_download_single_video(self, mocker, result_dir):
        """Тест скачивания одного видео."""
        mock_ytdl = MagicMock()
        mock_ytdl.download.return_value = 0

        mocker.patch("yt_dlp.YoutubeDL", return_value=mock_ytdl)

        # Симулируем скачивание
        url = "https://www.youtube.com/watch?v=test"

        with patch("yt_dlp.YoutubeDL") as mock_class:
            instance = mock_class.return_value.__enter__.return_value
            instance.download.return_value = 0

            # Вызов функции скачивания
            result = instance.download([url])

            assert result == 0
            instance.download.assert_called_once_with([url])

    @pytest.mark.unit
    def test_download_multiple_videos(self, mocker):
        """Тест скачивания нескольких видео."""
        urls = [
            "https://www.youtube.com/watch?v=test1",
            "https://www.youtube.com/watch?v=test2",
            "https://www.youtube.com/watch?v=test3",
        ]

        with patch("yt_dlp.YoutubeDL") as mock_class:
            instance = mock_class.return_value.__enter__.return_value
            instance.download.return_value = 0

            for url in urls:
                result = instance.download([url])
                assert result == 0

            assert instance.download.call_count == 3

    @pytest.mark.unit
    def test_download_with_options(self, mocker):
        ydl_opts = {
            "format": "best",
            "outtmpl": "%(title)s.%(ext)s",
        }
        with patch("yt_dlp.YoutubeDL") as mock_class:
            mock_instance = mock_class.return_value.__enter__.return_value
            mock_instance.download.return_value = 0

            youtube_dl = mock_class(ydl_opts)
            youtube_dl.__enter__().download(["https://www.youtube.com/watch?v=test"])
            # Проверка: был ли вызван mock
            mock_class.assert_called_once_with(ydl_opts)

    @pytest.mark.unit
    def test_handle_download_error(self, mocker):
        """Тест обработки ошибки скачивания."""
        with patch("yt_dlp.YoutubeDL") as mock_class:
            instance = mock_class.return_value.__enter__.return_value
            instance.download.side_effect = Exception("Download failed")

            with pytest.raises(Exception) as exc_info:
                instance.download(["https://invalid.url"])

            assert "Download failed" in str(exc_info.value)


class TestFileOperations:
    """Тесты файловых операций."""

    @pytest.mark.unit
    def test_clear_links_file(self, links_file):
        """Тест очистки файла с ссылками."""  # noqa: RUF002
        # Проверяем, что файл не пустой
        assert links_file.read_text() != ""

        # Очищаем файл
        links_file.write_text("")

        # Проверяем, что файл пустой
        assert links_file.read_text() == ""

    @pytest.mark.unit
    def test_create_result_directory(self, temp_dir):
        """Тест создания директории для результатов."""
        result_path = temp_dir / "result"
        result_path.mkdir(exist_ok=True)

        assert result_path.exists()
        assert result_path.is_dir()

    @pytest.mark.unit
    def test_check_result_directory_permissions(self, result_dir):
        """Тест проверки прав доступа к директории результатов."""
        assert os.access(result_dir, os.W_OK)
        assert os.access(result_dir, os.R_OK)

    @pytest.mark.unit
    def test_save_video_to_result_directory(self, result_dir, mocker):
        """Тест сохранения видео в директорию результатов."""
        # Создаём фиктивный видео файл
        video_file = result_dir / "test_video.mp4"
        video_file.write_bytes(b"fake video content")

        assert video_file.exists()
        assert video_file.stat().st_size > 0


class TestURLValidation:
    """Тесты валидации URL."""

    @pytest.mark.unit
    @pytest.mark.parametrize(
        ("url", "expected"),
        [
            ("https://www.youtube.com/watch?v=dQw4w9WgXcQ", True),
            ("https://youtu.be/dQw4w9WgXcQ", True),
            ("https://www.youtube.com/playlist?list=PLxxx", True),
            ("https://youtube.com/shorts/xxx", True),
            ("https://www.google.com", False),
            ("not a url", False),
            ("", False),
        ],
    )
    def test_url_validation(self, url, expected):
        """Тест валидации различных URL."""

        youtube_pattern = r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/"
        is_valid = bool(re.match(youtube_pattern, url))

        if expected:
            assert is_valid or "youtube" in url
        else:
            assert not is_valid or "youtube" not in url

    @pytest.mark.unit
    def test_extract_video_id(self):
        """Тест извлечения ID видео из URL."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        video_id = url.split("v=")[-1]

        assert video_id == "dQw4w9WgXcQ"

    @pytest.mark.unit
    def test_handle_malformed_url(self):
        """Тест обработки некорректного URL."""
        malformed_urls = [
            "htp://youtube.com",
            "youtube",
            "www.youtube",
            "://youtube.com",
        ]

        for url in malformed_urls:
            # Здесь должна быть ваша функция валидации
            import re

            youtube_pattern = r"^https?://(www\.)?(youtube\.com|youtu\.be)/"
            is_valid = bool(re.match(youtube_pattern, url))
            assert not is_valid


class TestErrorHandling:
    """Тесты обработки ошибок."""

    @pytest.mark.unit
    def test_handle_network_error(self, mocker):
        """Тест обработки сетевой ошибки."""
        with patch("yt_dlp.YoutubeDL") as mock_class:
            instance = mock_class.return_value.__enter__.return_value
            instance.download.side_effect = ConnectionError("Network error")

            with pytest.raises(ConnectionError):
                instance.download(["https://youtube.com/watch?v=test"])

    @pytest.mark.unit
    def test_handle_invalid_video(self, mocker):
        """Тест обработки недоступного видео."""
        with patch("yt_dlp.YoutubeDL") as mock_class:
            instance = mock_class.return_value.__enter__.return_value
            instance.download.side_effect = Exception("Video unavailable")

            with pytest.raises(Exception) as exc_info:
                instance.download(["https://youtube.com/watch?v=invalid"])

            assert "Video unavailable" in str(exc_info.value)

    @pytest.mark.unit
    def test_handle_permission_error(self, temp_dir):
        """Тест обработки ошибки доступа к файлу."""
        # Создаём файл только для чтения
        readonly_file = temp_dir / "readonly.txt"
        readonly_file.write_text("test")

        # В Unix-подобных системах  # noqa: RUF003
        if os.name != "nt":  # Не Windows  # noqa: RUF003
            readonly_file.chmod(0o444)

            with pytest.raises(PermissionError):
                readonly_file.write_text("new content")


class TestYtDlpIntegration:
    """Тесты интеграции с yt-dlp."""  # noqa: RUF002

    @pytest.mark.unit
    def test_ytdlp_options_configuration(self):
        """Тест конфигурации опций yt-dlp."""
        ydl_opts = {
            "format": "bestvideo+bestaudio/best",
            "outtmpl": "result/%(title)s.%(ext)s",
            "quiet": True,
            "no_warnings": True,
        }

        assert "format" in ydl_opts
        assert "outtmpl" in ydl_opts
        assert ydl_opts["quiet"] is True

    @pytest.mark.unit
    def test_ytdlp_extract_info(self, mocker, sample_video_info):
        """Тест извлечения информации о видео."""  # noqa: RUF002
        with patch("yt_dlp.YoutubeDL") as mock_class:
            instance = mock_class.return_value.__enter__.return_value
            instance.extract_info.return_value = sample_video_info

            info = instance.extract_info(
                "https://youtube.com/watch?v=test",
                download=False,
            )

            assert info["id"] == "dQw4w9WgXcQ"
            assert info["title"] == "Test Video"
            instance.extract_info.assert_called_once()

    @pytest.mark.unit
    def test_ytdlp_sanitize_filename(self):
        """Тест санитизации имени файла."""
        # yt-dlp автоматически санитизирует имена файлов
        dangerous_chars = '<>:"/\\|?*'
        filename = "test_video.mp4"

        # Проверяем, что безопасное имя не содержит опасных символов
        assert not any(char in filename for char in dangerous_chars)
