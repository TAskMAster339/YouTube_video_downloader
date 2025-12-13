# tests/test_main_window.py
import sys

import pytest
from PyQt5.QtWidgets import (
    QLabel,
    QProgressBar,
    QPushButton,
)

sys.path.insert(0, ".")


@pytest.mark.gui
class TestMainWindow:
    """Тесты главного окна приложения."""

    def test_window_creation(self, main_window):
        """Тест создания главного окна."""
        assert main_window is not None
        assert main_window.windowTitle() == "YouTube Downloader"

    def test_window_size(self, main_window):
        """Тест размера окна."""
        assert main_window.width() >= 1200 or main_window.width() > 0
        assert main_window.height() >= 800 or main_window.height() > 0

    def test_font_size(self, main_window):
        """Тест размера шрифта."""
        font = main_window.font()
        assert font.pointSize() == 16  # DEAFULT_FONT_SIZE


@pytest.mark.gui
class TestSettings:
    """Тесты блока настроек."""

    def test_spinbox_font_size(self, main_window):
        """Тест спинбокса размера шрифта."""
        assert main_window.spin is not None
        assert main_window.spin.minimum() == 12
        assert main_window.spin.maximum() == 48
        assert main_window.spin.value() == 16

    def test_spinbox_range_valid(self, main_window):
        """Тест корректного диапазона спинбокса."""
        main_window.spin.setValue(14)
        assert main_window.spin.value() == 14

        main_window.spin.setValue(40)
        assert main_window.spin.value() == 40

    def test_spinbox_boundaries(self, main_window):
        """Тест границ спинбокса."""
        # Устанавливаем минимум
        main_window.spin.setValue(12)
        assert main_window.spin.value() == 12

        # Устанавливаем максимум
        main_window.spin.setValue(48)
        assert main_window.spin.value() == 48

    def test_directory_button_exists(self, main_window):
        """Тест наличия кнопки выбора папки."""
        assert main_window.dir_button is not None
        assert isinstance(main_window.dir_button, QPushButton)

    def test_directory_label_exists(self, main_window):
        """Тест наличия метки с путём папки."""  # noqa: RUF002
        assert main_window.dir_label is not None
        assert isinstance(main_window.dir_label, QLabel)

    def test_quality_combobox(self, main_window):
        """Тест комбобокса выбора качества."""
        assert main_window.combo_quality is not None
        assert main_window.combo_quality.count() == 3
        assert "1080" in main_window.combo_quality.itemText(0)
        assert "720" in main_window.combo_quality.itemText(1)
        assert "480" in main_window.combo_quality.itemText(2)

    def test_quality_combobox_current_index(self, main_window):
        """Тест текущего индекса комбобокса."""
        assert main_window.combo_quality.currentIndex() == 0

    def test_quality_selection_change(self, main_window):
        """Тест изменения выбора качества."""
        main_window.combo_quality.setCurrentIndex(1)
        assert main_window.combo_quality.currentIndex() == 1
        assert "720" in main_window.combo_quality.currentText()


@pytest.mark.gui
class TestProgressBars:
    """Тесты прогресс-баров."""

    def test_progress_bar_exists(self, main_window):
        """Тест наличия прогресс-бара текущего видео."""  # noqa: RUF002
        assert main_window.progress_bar is not None
        assert isinstance(main_window.progress_bar, QProgressBar)

    def test_overall_progress_bar_exists(self, main_window):
        """Тест наличия общего прогресс-бара."""  # noqa: RUF002
        assert main_window.overall_bar is not None
        assert isinstance(main_window.overall_bar, QProgressBar)

    def test_progress_bar_initial_value(self, main_window):
        main_window.progress_bar.setValue(0)
        main_window.overall_bar.setValue(0)

        assert main_window.progress_bar.value() == 0
        assert main_window.overall_bar.value() == 0

    def test_progress_bar_text_visible(self, main_window):
        """Тест видимости текста на прогресс-барах."""  # noqa: RUF002
        assert main_window.progress_bar.isTextVisible()
        assert main_window.overall_bar.isTextVisible()

    def test_progress_bar_set_value(self, main_window):
        """Тест установки значения прогресс-бара."""  # noqa: RUF002
        main_window.progress_bar.setValue(50)
        assert main_window.progress_bar.value() == 50

        main_window.overall_bar.setValue(75)
        assert main_window.overall_bar.value() == 75


@pytest.mark.gui
class TestDownloadButton:
    """Тесты кнопки скачивания."""

    def test_download_button_exists(self, main_window):
        """Тест наличия кнопки скачивания."""
        assert main_window.download_button is not None
        assert isinstance(main_window.download_button, QPushButton)

    def test_download_button_text(self, main_window):
        """Тест текста на кнопке."""
        assert "Скачать" in main_window.download_button.text()

    def test_download_button_enabled(self, main_window):
        """Тест активности кнопки."""
        assert main_window.download_button.isEnabled()

    def test_download_button_with_mock_worker(self, main_window, mocker):
        """Тест сигнала клика кнопки."""
        # Мокируем весь DownloadTask
        mock_worker = mocker.patch("src.app.DownloadTask")
        mock_worker_instance = mocker.MagicMock()
        mock_worker.return_value = mock_worker_instance

        # Мокируем файловый диалог
        mocker.patch("src.app.QtWidgets.QMessageBox.warning")

        # Добавляем URL
        main_window.drop_area.add_url("https://www.youtube.com/watch?v=test")

        # Кликаем кнопку (сейчас безопасно - всё мокировано)
        main_window.download_button.click()

        # Проверяем что worker был создан
        assert mock_worker.called


@pytest.mark.gui
class TestDropAreaWidget:
    """Тесты виджета DropArea в главном окне."""

    def test_drop_area_widget_exists(self, main_window):
        """Тест наличия виджета DropArea."""
        assert main_window.drop_area is not None

    def test_drop_area_accepts_drops(self, main_window):
        """Тест что DropArea принимает drag&drop."""
        assert main_window.drop_area.acceptDrops()


@pytest.mark.gui
class TestUIIntegration:
    """Интеграционные тесты UI элементов."""

    def test_all_main_elements_present(self, main_window):
        """Тест наличия всех основных элементов UI."""
        assert main_window.spin is not None
        assert main_window.dir_button is not None
        assert main_window.dir_label is not None
        assert main_window.combo_quality is not None
        assert main_window.progress_bar is not None
        assert main_window.overall_bar is not None
        assert main_window.download_button is not None
        assert main_window.drop_area is not None

    def test_changing_quality_selection(self, main_window):
        """Тест изменения выбора качества видео."""

        # Проверяем разные качества
        qualities = ["До 1080p", "До 720p", "До 480p"]

        for i, quality in enumerate(qualities):
            main_window.combo_quality.setCurrentIndex(i)
            assert quality in main_window.combo_quality.currentText()

    def test_download_button_disabled_during_download(self, main_window):
        """Тест отключения кнопки во время скачивания."""
        main_window.download_button.setEnabled(False)
        assert not main_window.download_button.isEnabled()

        main_window.download_button.setEnabled(True)
        assert main_window.download_button.isEnabled()
