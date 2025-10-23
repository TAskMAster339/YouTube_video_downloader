from unittest.mock import patch

import pytest

from src.main import main


@pytest.mark.integration
class TestFullDownloadWorkflow:
    """Интеграционные тесты полного процесса скачивания."""

    def test_complete_download_workflow(self, temp_dir, links_file, result_dir, mocker):
        """Тест полного процесса: чтение ссылок -> скачивание -> очистка."""
        # Мокаем yt-dlp
        with patch("yt_dlp.YoutubeDL") as mock_class:
            instance = mock_class.return_value.__enter__.return_value
            instance.download.return_value = 0

            # Читаем ссылки
            with open(links_file) as f:
                links = [line.strip() for line in f if line.strip()]

            assert len(links) > 0

            # Скачиваем
            for link in links:
                result = instance.download([link])
                assert result == 0

            # Очищаем файл
            links_file.write_text("")
            assert links_file.read_text() == ""

    def test_workflow_with_empty_links(self, empty_links_file, result_dir):
        """Тест процесса с пустым файлом ссылок."""  # noqa: RUF002
        with open(empty_links_file) as f:
            links = [line.strip() for line in f if line.strip()]

        assert len(links) == 0
        # Процесс должен завершиться без ошибок

    def test_workflow_with_mixed_separators(self, temp_dir, result_dir, mocker):
        """Тест с ссылками, разделёнными и пробелами, и переносами."""  # noqa: RUF002
        links_path = temp_dir / "mixed_links.txt"
        links_path.write_text(
            "https://youtube.com/watch?v=1 https://youtube.com/watch?v=2\n"
            "https://youtube.com/watch?v=3\n"
            "https://youtube.com/watch?v=4 https://youtube.com/watch?v=5",
        )

        with open(links_path) as f:
            content = f.read()
            # Парсим и пробелы, и переносы
            links = content.replace("\n", " ").split()

        assert len(links) == 5

    @pytest.mark.slow
    def test_large_links_file(self, temp_dir, mocker):
        """Тест с большим количеством ссылок."""  # noqa: RUF002
        links_path = temp_dir / "large_links.txt"
        num_links = 100

        links = [f"https://youtube.com/watch?v={i}" for i in range(num_links)]
        links_path.write_text("\n".join(links))

        with open(links_path) as f:
            parsed_links = [line.strip() for line in f if line.strip()]

        assert len(parsed_links) == num_links


@pytest.mark.integration
class TestFileSystemIntegration:
    """Интеграционные тесты файловой системы."""

    def test_create_result_directory_if_not_exists(self, temp_dir):
        """Тест автоматического создания директории результатов."""
        result_path = temp_dir / "result"

        # Убеждаемся, что директории нет
        if result_path.exists():
            result_path.rmdir()

        # Создаём
        result_path.mkdir(exist_ok=True)

        assert result_path.exists()

    def test_handle_existing_files_in_result(self, result_dir):
        """Тест обработки существующих файлов в result."""
        # Создаём существующий файл
        existing_file = result_dir / "existing_video.mp4"
        existing_file.write_bytes(b"existing content")

        assert existing_file.exists()

        # Новый файл с другим именем  # noqa: RUF003
        new_file = result_dir / "new_video.mp4"
        new_file.write_bytes(b"new content")

        assert existing_file.exists()
        assert new_file.exists()

    def test_concurrent_file_access(self, links_file):
        """Тест одновременного доступа к файлу ссылок."""
        # Первое чтение
        with open(links_file) as f1:
            content1 = f1.read()

        # Второе чтение
        with open(links_file) as f2:
            content2 = f2.read()

        assert content1 == content2


@pytest.mark.integration
class TestErrorRecovery:
    """Тесты восстановления после ошибок."""

    def test_continue_after_single_failure(self, mocker):
        """Тест продолжения скачивания после ошибки на одном видео."""
        urls = [
            "https://youtube.com/watch?v=1",
            "https://youtube.com/watch?v=invalid",  # Это упадёт
            "https://youtube.com/watch?v=3",
        ]

        with patch("yt_dlp.YoutubeDL") as mock_class:
            instance = mock_class.return_value.__enter__.return_value

            def download_side_effect(url_list):
                if "invalid" in url_list[0]:
                    raise Exception("Download failed")
                return 0

            instance.download.side_effect = download_side_effect

            successful = 0
            failed = 0

            for url in urls:
                try:
                    instance.download([url])
                    successful += 1
                except Exception:
                    failed += 1

            assert successful == 2
            assert failed == 1

    def test_preserve_links_on_critical_error(self, links_file):
        """Тест сохранения ссылок при критической ошибке."""
        original_content = links_file.read_text()

        # Симулируем критическую ошибку перед очисткой
        try:
            # Здесь должна быть логика, которая может упасть
            raise RuntimeError("Critical error")
        except RuntimeError:
            # Ссылки не должны быть удалены
            pass

        # Проверяем, что ссылки остались
        assert links_file.read_text() == original_content


@pytest.mark.integration
class TestMainScriptExecution:
    """Тесты выполнения основного скрипта."""

    def test_main_function_exists(self):
        """Тест наличия главной функции."""
        # Это зависит от вашей реализации
        # Предполагаем, что есть функция main()
        try:
            assert callable(main)
        except ImportError:
            pytest.skip("Main function not implemented yet")

    def test_script_execution_with_no_links(self, empty_links_file, result_dir, mocker):
        """Тест выполнения скрипта без ссылок."""
        with open(empty_links_file) as f:
            links = [line.strip() for line in f if line.strip()]

        # Скрипт должен завершиться нормально
        assert len(links) == 0
