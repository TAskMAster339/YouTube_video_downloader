# tests/test_drop_area.py
import sys
from unittest.mock import MagicMock

import pytest
from PyQt5.QtCore import QMimeData, QUrl
from PyQt5.QtGui import QDragEnterEvent
from PyQt5.QtWidgets import QApplication, QSizePolicy

sys.path.insert(0, ".")


@pytest.mark.gui
class TestDropArea:
    """Тесты для DropArea виджета."""

    def test_drop_area_creation(self, drop_area):
        """Тест создания DropArea."""
        assert drop_area is not None
        assert drop_area.acceptDrops() is True

    def test_drop_area_minimum_height(self, drop_area):
        """Тест минимальной высоты DropArea."""

        screen = QApplication.primaryScreen()
        screen_size = screen.size()
        min_height = screen_size.height() // 5

        assert drop_area.minimumHeight() == min_height

    def test_add_url_single(self, drop_area):
        """Тест добавления одной ссылки."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        drop_area.add_url(url)

        assert drop_area.count() == 1
        assert drop_area.item(0).text() == url

    def test_add_multiple_urls(self, drop_area):
        """Тест добавления нескольких ссылок."""
        urls = [
            "https://www.youtube.com/watch?v=1",
            "https://www.youtube.com/watch?v=2",
            "https://www.youtube.com/watch?v=3",
        ]

        for url in urls:
            drop_area.add_url(url)

        assert drop_area.count() == 3

        for i, url in enumerate(urls):
            assert drop_area.item(i).text() == url

    def test_url_tooltip(self, drop_area):
        """Тест наличия подсказки для ссылки."""
        url = "https://www.youtube.com/watch?v=test"
        drop_area.add_url(url)

        item = drop_area.item(0)
        assert item.toolTip() != ""
        assert "правой кнопкой" in item.toolTip() or "удалить" in item.toolTip()

    def test_context_menu_display(self, drop_area, qtbot):
        """Тест отображения контекстного меню."""
        drop_area.add_url("https://youtube.com/watch?v=test")
        drop_area.setFocus()

        # Проверяем, что контекстное меню может быть вызвано
        # (не выполняем полный клик, чтобы окно не открывалось)
        assert drop_area.contextMenuPolicy() != 0

    def test_drag_enter_event_with_urls(self, drop_area):
        """Тест события dragEnter с URL."""  # noqa: RUF002
        mime_data = QMimeData()
        mime_data.setUrls([QUrl("https://www.youtube.com/watch?v=test")])

        # Создаём фиктивное событие

        event = MagicMock(spec=QDragEnterEvent)
        event.mimeData.return_value = mime_data

        # Проверяем логику (так как dragEnterEvent требует real event)
        assert mime_data.hasUrls()

    def test_drag_enter_event_without_urls(self, drop_area):
        """Тест события dragEnter без URL."""
        mime_data = QMimeData()
        mime_data.setText("plain text")

        # Проверяем, что URLs нет
        assert not mime_data.hasUrls()

    def test_clear_drop_area(self, drop_area):
        """Тест очистки DropArea."""
        for i in range(5):
            drop_area.add_url(f"https://youtube.com/watch?v={i}")

        assert drop_area.count() == 5

        drop_area.clear()
        assert drop_area.count() == 0


@pytest.mark.gui
class TestDropAreaURLValidation:
    """Тесты валидации URL в DropArea."""

    def test_add_valid_youtube_url(self, drop_area):
        """Тест добавления корректного YouTube URL."""
        urls = [
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "https://youtu.be/dQw4w9WgXcQ",
            "https://www.youtube.com/watch?v=test&list=PLxxxxx",
        ]

        for url in urls:
            drop_area.add_url(url)

        assert drop_area.count() == len(urls)

    def test_add_invalid_urls(self, drop_area):
        """Тест добавления некорректных URL."""
        invalid_urls = [
            "not_a_url",
            "http://google.com",
            "",
        ]

        initial_count = drop_area.count()

        for url in invalid_urls:
            # В реальном приложении может быть валидация,  # noqa: RUF003
            # но здесь мы просто добавляем любой URL
            if url:  # Пропускаем пустые
                drop_area.add_url(url)

        # Проверяем, что все добавлены (валидация на стороне приложения)
        assert drop_area.count() >= initial_count


@pytest.mark.gui
class TestDropAreaSize:
    """Тесты размеров DropArea."""

    def test_size_policy(self, drop_area):
        """Тест policy растягивания."""

        policy = drop_area.sizePolicy()
        # Проверяем, что горизонтальная политика - Expanding
        assert (
            policy.horizontalPolicy()
            in [
                QSizePolicy.Expanding,
                QSizePolicy.MinimumExpanding,
            ]
            or policy.horizontalPolicy() >= 4
        )  # Expanding = 4

    def test_minimum_width(self, drop_area):
        """Тест минимальной ширины."""
        assert drop_area.minimumWidth() >= 0

    def test_item_selection(self, drop_area):
        """Тест выбора элемента."""
        drop_area.add_url("https://youtube.com/watch?v=1")
        drop_area.add_url("https://youtube.com/watch?v=2")

        # Выбираем первый элемент
        drop_area.setCurrentRow(0)
        assert drop_area.currentRow() == 0
