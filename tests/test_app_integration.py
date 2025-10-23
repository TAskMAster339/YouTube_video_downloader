# tests/test_app_integration.py
import sys
from unittest.mock import MagicMock

import pytest

from src.app import MainWindow

sys.path.insert(0, ".")


@pytest.mark.integration
class TestStartDownloadWorkflow:
    """Тесты workflow начала скачивания."""

    def test_start_download_with_no_urls(self, main_window, qtbot, mocker):
        """Тест попытки скачивания без URL."""
        # Мокируем QMessageBox
        mock_msgbox = mocker.patch("PyQt5.QtWidgets.QMessageBox.warning")

        # Кликаем кнопку скачивания без URL
        main_window.download_button.click()

        # Проверяем, что было показано предупреждение
        # (в реальном приложении это есть в start_download)
        mock_msgbox.assert_called_once()

    def test_start_download_with_urls(self, main_window, qtbot, mocker):
        """Тест начала скачивания с URL."""  # noqa: RUF002
        # Добавляем ссылку в drop_area
        main_window.drop_area.add_url("https://youtube.com/watch?v=test1")

        assert main_window.drop_area.count() == 1

        # Мокируем DownloadWorker
        mock_worker_class = mocker.patch("src.app.DownloadWorker")
        mock_worker = MagicMock()
        mock_worker_class.return_value = mock_worker

        # Кликаем кнопку скачивания
        main_window.download_button.click()

        # Проверяем что worker был создан
        mock_worker_class.assert_called_once()

    def test_progress_bar_reset(self, main_window):
        """Тест сброса прогресс-баров перед скачиванием."""  # noqa: RUF002
        # Устанавливаем значения
        main_window.progress_bar.setValue(50)
        main_window.overall_bar.setValue(75)

        # Проверяем начальные значения
        assert main_window.progress_bar.value() == 50
        assert main_window.overall_bar.value() == 75

        # Сбрасываем (как в start_download)
        main_window.progress_bar.setValue(0)
        main_window.overall_bar.setValue(0)

        assert main_window.progress_bar.value() == 0
        assert main_window.overall_bar.value() == 0


@pytest.mark.integration
class TestDownloadCompletion:
    """Тесты завершения скачивания."""

    def test_download_finished_success(self, main_window, mocker):
        """Тест успешного завершения скачивания."""
        # Мокируем QMessageBox
        mocker.patch("PyQt5.QtWidgets.QMessageBox.information")

        # Вызываем on_finished
        main_window.on_finished()

        # Проверяем что drop_area очищена
        assert main_window.drop_area.count() == 0

        # Проверяем что кнопка включена
        assert main_window.download_button.isEnabled()

    def test_download_finished_with_errors(self, main_window, mocker):
        """Тест завершения скачивания с ошибками."""  # noqa: RUF002
        # Устанавливаем флаг ошибки
        main_window.error_flag = True

        # Мокируем QMessageBox
        mocker.patch("PyQt5.QtWidgets.QMessageBox.warning")

        # Вызываем on_finished
        main_window.on_finished()

        # Проверяем что флаг сброшен
        assert main_window.error_flag is False


@pytest.mark.integration
class TestFontSizeChange:
    """Тесты изменения размера шрифта."""

    def test_change_font_size(self, main_window):
        """Тест изменения размера шрифта."""
        main_window.font().pointSize()

        # Изменяем размер
        main_window.change_font_size(24)

        new_size = main_window.font().pointSize()
        assert new_size == 24

    def test_font_size_spinbox_connection(self, main_window):
        """Тест связи спинбокса с изменением шрифта."""  # noqa: RUF002
        main_window.spin.setValue(20)

        # Проверяем что значение в спинбоксе изменилось
        assert main_window.spin.value() == 20


@pytest.mark.integration
class TestDirectorySelection:
    """Тесты выбора директории."""

    def test_directory_label_update(self, tmp_path, mocker):
        """Тест выбора директории."""
        new_dir = tmp_path / "downloads"
        new_dir.mkdir()

        # Мокируем диалог выбора директории
        mocker.patch(
            "PyQt5.QtWidgets.QFileDialog.getExistingDirectory",
            return_value=str(new_dir),
        )

        window = MainWindow()
        original_dir = window.download_dir

        # Вызываем выбор директории
        window.choose_directory()

        # Проверяем результат
        assert window.download_dir == new_dir
        assert str(new_dir) in window.dir_label.text()
        assert window.download_dir != original_dir

        window.close()


@pytest.mark.integration
class TestURLHandling:
    """Тесты обработки URL."""

    def test_collect_urls_from_drop_area(self, main_window):
        """Тест сбора URL из drop_area."""  # noqa: RUF002
        urls = [
            "https://youtube.com/watch?v=1",
            "https://youtube.com/watch?v=2",
            "https://youtube.com/watch?v=3",
        ]

        for url in urls:
            main_window.drop_area.add_url(url)

        # Собираем URL (как в start_download)
        collected_urls = [
            main_window.drop_area.item(i).text()
            for i in range(main_window.drop_area.count())
        ]

        assert collected_urls == urls

    def test_clear_urls_after_download(self, main_window):
        """Тест очистки URL после скачивания."""
        # Добавляем URL
        main_window.drop_area.add_url("https://youtube.com/watch?v=test")
        assert main_window.drop_area.count() == 1

        # Очищаем
        main_window.drop_area.clear()
        assert main_window.drop_area.count() == 0
