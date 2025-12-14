__all__ = []

import logging
import os
import pathlib
import platform
import re
import shutil
import subprocess
import sys
import traceback
from logging.handlers import RotatingFileHandler
from urllib.parse import urlparse

import yt_dlp
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import QThreadPool

ROOT_PATH = pathlib.Path(__file__).parent.parent

DEAFULT_FONT_SIZE = 16


def resource_path(relative_path: str) -> pathlib.Path:
    """Получает абсолютный путь к ресурсу, работает для dev и PyInstaller"""  # noqa: RUF002
    try:
        # PyInstaller создает временную папку и сохраняет путь в _MEIPASS
        base_path = pathlib.Path(sys._MEIPASS)  # noqa: SLF001
    except AttributeError:
        base_path = pathlib.Path(__file__).resolve().parent.parent
    return base_path / pathlib.Path(relative_path)


def get_app_directory() -> pathlib.Path:
    """Получает директорию приложения (для exe и для исходников)"""
    if getattr(sys, "frozen", False):
        # Запущено из PyInstaller (.exe)
        app_dir = pathlib.Path(sys.executable).parent
    else:
        # Запущено из исходников (.py)
        app_dir = pathlib.Path(__file__).parent.parent
    return app_dir


def setup_logging():
    """
    Настраивает логирование в файл с ротацией.
    Работает как в dev-режиме, так и в exe.
    """
    log_file = APP_DIR / "app.log"

    # Создаём logger
    logger = logging.getLogger("YouTubeDownloader")
    logger.setLevel(logging.DEBUG)

    # Создаём обработчик с ротацией
    handler = RotatingFileHandler(
        log_file,
        maxBytes=5 * 1024 * 1024,  # 5 МБ
        backupCount=5,
        encoding="utf-8",
    )

    # Формат логов: время | уровень | сообщение
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    # Добавляем обработчик
    logger.addHandler(handler)

    # Также выводим в консоль (для режима разработки)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    logger.info("=" * 50)
    logger.info("Приложение запущено")
    logger.info(f"Директория приложения: {APP_DIR}")  # noqa: G004
    logger.info(f"Лог-файл: {log_file}")  # noqa: G004

    return logger


APP_DIR = get_app_directory()
DOWNLOAD_DIR = APP_DIR / "result"

logger = setup_logging()


def get_ffmpeg_path():
    """Получает путь к FFmpeg (ленивая инициализация)"""
    try:
        ffmpeg_path = resource_path("ffmpeg.exe")
        if ffmpeg_path.exists():
            logger.info(f"Найден bundled FFmpeg: {ffmpeg_path}")  # noqa: G004
            return str(ffmpeg_path)
    except (AttributeError, FileNotFoundError, TypeError) as e:
        logger.error(f"Ошибка: {e}")  # noqa: G004

    # Fallback
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        logger.info(f"Найден системный FFmpeg: {system_ffmpeg}")  # noqa: G004
        return system_ffmpeg

    logger.warning("FFmpeg не найден")
    return "ffmpeg"


def ensure_download_dir_exists():
    """
    Гарантирует что директория для загрузок существует.
    Создает её если нужно с полной обработкой ошибок.
    """  # noqa: RUF002
    try:
        if not DOWNLOAD_DIR.exists():
            logger.info(f"[*] Creating download directory: {DOWNLOAD_DIR}")  # noqa: G004
            DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
            logger.info("[+] Directory created successfully")

        # Проверяем разрешения
        if not os.access(DOWNLOAD_DIR, os.W_OK):
            logger.error("[!] No write permission")
            return False

    except PermissionError as e:
        logger.error(f"[!] Permission denied: {e}")  # noqa: G004
        return False
    except Exception as e:
        logger.error(f"[!] Error: {e}")  # noqa: G004
        return False
    else:
        return True


def is_valid_url(url: str) -> bool:
    """Простая валидация HTTP(S) URL."""
    try:
        parsed = urlparse(url.strip())
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


class YTDLPLogger:
    """
    Кастомный logger для yt-dlp, который перенаправляет
    все сообщения в Python logging.
    """

    def __init__(self, logger_instance):
        self.logger = logger_instance

    def debug(self, msg):
        """yt-dlp передаёт сюда информационные сообщения"""
        # yt-dlp использует debug для обычных info-сообщений
        if msg.startswith("[debug] "):
            self.logger.debug(msg)
        else:
            self.logger.info(msg)

    def info(self, msg):
        """Информационные сообщения"""
        self.logger.info(msg)

    def warning(self, msg):
        """Предупреждения (WARNING prefix от yt-dlp)"""
        self.logger.warning(msg)

    def error(self, msg):
        """Ошибки"""
        self.logger.error(msg)


class DropArea(QtWidgets.QListWidget):
    """
    Зона для drag & drop ссылок.

    ВАЖНО: экземпляр этого виджета должен использоваться только из GUI-потока.
    Все обращения к _url_set выполняются из потокобезопасного контекста Qt
    (основной поток с event loop), поэтому дополнительная синхронизация не требуется.
    """

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        # Множество для хранения уникальных URL
        self._url_set = set()

        # Минимальная высота — 50% экрана
        screen = QtWidgets.QApplication.primaryScreen()
        screen_size = screen.size()
        min_height = screen_size.height() // 5
        self.setMinimumHeight(min_height)

        # Разрешаем растягивание при ресайзе окна
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Expanding,
        )

    def clear(self):
        """Переопределяем очистку чтобы сбрасывать множество URL"""
        self._url_set.clear()
        return super().clear()

    def show_context_menu(self, pos):
        """Контекстное меню — удаление на элементах, вставка на пустой области"""
        menu = QtWidgets.QMenu(self)

        # Получаем элемент в позиции клика
        item_at_pos = self.itemAt(pos)

        if item_at_pos:
            # Если кликнули на элемент — показываем удаление
            delete_action = menu.addAction("Удалить")
            action = menu.exec_(self.mapToGlobal(pos))

            if action == delete_action:
                url = item_at_pos.data(QtCore.Qt.UserRole)
                if url:
                    self._url_set.discard(url)
                    logger.info(f"URL удален из списка: {url}")  # noqa: G004
                self.takeItem(self.row(item_at_pos))
        else:
            # Если кликули на пустую область — показываем вставку
            paste_action = menu.addAction("Вставить ссылку (Ctrl+V)")
            action = menu.exec_(self.mapToGlobal(pos))

            if action == paste_action:
                self.paste_from_clipboard()

    def dragEnterEvent(self, event):  # noqa: N802
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):  # noqa: N802
        if event.mimeData().hasUrls():
            event.setDropAction(QtCore.Qt.CopyAction)
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):  # noqa: N802
        event.setDropAction(QtCore.Qt.CopyAction)  # Действие "копировать"
        event.accept()
        # Если пришли URL (например, файл или ссылка)
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                url_str = url.toString().strip()
                if url_str.startswith("http"):
                    self.add_url(url_str)
                    logger.info(f"Добавлен URL через drag&drop: {url_str}")  # noqa: G004

    def add_url(self, url_str: str):
        """Добавляет ссылку в список с подсказкой"""
        if url_str in self._url_set:
            QtWidgets.QMessageBox.warning(
                self,
                "Дубликат ссылки",
                f"Ссылка уже добавлена в список:\n{url_str}",
                QtWidgets.QMessageBox.Ok,
            )
            logger.warning(f"Попытка добавить дубликат URL: {url_str}")  # noqa: G004
            return

        self._url_set.add(url_str)

        item = QtWidgets.QListWidgetItem(url_str)
        # Сохраняем «сырую» ссылку отдельно от отображаемого текста
        item.setData(QtCore.Qt.UserRole, url_str)

        logger.info(f"URL добавлен в список: {url_str}")  # noqa: G004
        item.setToolTip(
            "<p style='font-size:14pt; color:#444;'>"
            "Нажмите <b>правой кнопкой</b>, чтобы удалить ссылку из списка"
            "</p>",
        )
        self.addItem(item)

    def keyPressEvent(self, event):  # noqa: N802
        """Обработка Ctrl+V для вставки ссылок"""
        if (
            event.key() == QtCore.Qt.Key_V
            and event.modifiers() == QtCore.Qt.ControlModifier
        ):
            self.paste_from_clipboard()
            return
        super().keyPressEvent(event)

    def paste_from_clipboard(self):
        """Вставляет ссылку из буфера обмена"""
        clipboard = QtWidgets.QApplication.clipboard()
        clipboard_text = clipboard.text().strip()

        logger.debug(f"Попытка вставить из буфера обмена: {clipboard_text[:50]}...")  # noqa: G004

        if is_valid_url(clipboard_text):
            self.add_url(clipboard_text)
            logger.info(f"URL успешно вставлен из буфера обмена: {clipboard_text}")  # noqa: G004
        else:
            logger.warning(f"Невалидная ссылка в буфере обмена: {clipboard_text[:100]}")  # noqa: G004
            QtWidgets.QMessageBox.warning(
                self,
                "Ошибка",
                "В буфере обмена нет ссылки",  # noqa: RUF001
                QtWidgets.QMessageBox.Ok,
            )


class ClickableLabel(QtWidgets.QLabel):
    """QLabel с поддержкой клика для открытия директории"""

    clicked = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setCursor(QtCore.Qt.PointingHandCursor)

    def mousePressEvent(self, event):  # noqa: N802
        if event.button() == QtCore.Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(event)


class DownloadTask(QtCore.QRunnable):
    """
    Represents a single download task to be executed in a background thread.

    This class was refactored from using QThread to QRunnable to leverage the
    QThreadPool infrastructure provided by Qt. By inheriting from QRunnable and
    submitting instances to a QThreadPool, we can efficiently manage and execute
    multiple concurrent download tasks without the overhead of manually managing
    thread lifecycles.

    Using QThreadPool with QRunnable improves maintainability and scalability,
    as the thread pool automatically handles thread reuse and resource allocation.
    This approach is particularly beneficial when handling many downloads in
    parallel, as it avoids the pitfalls of creating and destroying QThread
    objects for each task.

    Signals are provided via the nested Signals class to communicate progress,
    completion, and errors back to the GUI thread.
    """

    class Signals(QtCore.QObject):
        """Сигналы для передачи данных в GUI"""

        progress = QtCore.pyqtSignal(int)  # процент загрузки текущего видео
        overall_progress = QtCore.pyqtSignal(int)  # общий прогресс (по списку)
        finished = QtCore.pyqtSignal()  # завершение всех загрузок
        error_occurred = QtCore.pyqtSignal(str)  # ошибка загрузки

    def __init__(self, urls, fmt, download_dir):
        super().__init__()
        self.urls = urls
        self.fmt = fmt
        self.download_dir = download_dir
        self.failed_videos = []
        self.signals = DownloadTask.Signals()

    def progress_hook(self, d):
        if d["status"] == "downloading":
            percent_str = d.get("_percent_str", "0.0%").strip().replace("%", "")
            percent_str = re.sub(r"\x1b\[[0-9;]*m", "", percent_str)
            try:
                percent = float(percent_str)
                self.signals.progress.emit(int(percent))
            except ValueError as e:
                self.signals.overall_progress.emit(0)
                logger.error(f"Ошибка парсинга процента загрузки: {e}")  # noqa: G004

        elif d["status"] == "finished":
            self.signals.progress.emit(100)
            logger.debug("Загрузка файла завершена, начинается обработка")

    def run(self):
        total = len(self.urls)

        ydl_opts = {
            "ffmpeg_location": get_ffmpeg_path(),
            "outtmpl": str(self.download_dir / "%(title)s.%(ext)s"),
            "format": self.fmt,  # "best[height<=1080]+bestaudio/best"
            "progress_hooks": [self.progress_hook],
            "socket_timeout": 30,
            "retries": 3,
            "quiet": False,
            "noprogress": True,
            "merge_output_format": "webm",
            "continuedl": True,
            "postprocessor_args": ["-v", "verbose"],
            "logger": YTDLPLogger(logger),
        }

        # Проверяем существование файла cookies

        cookies_path = APP_DIR / "cookies.txt"
        if cookies_path.exists():
            ydl_opts["cookiefile"] = str(cookies_path)
            logger.info(f"Используются cookies из {cookies_path}")  # noqa: G004
        else:
            logger.info("Файл cookies.txt не найден, продолжаем без cookies")

        for index, url in enumerate(self.urls, start=1):
            logger.info(f"Начало загрузки [{index}/{total}]: {url}")  # noqa: G004
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                logger.info(f"Успешно загружено [{index}/{total}]: {url}")  # noqa: G004
            except yt_dlp.utils.DownloadError as e:
                # Попытка сменить контейнер на mkv, если mp4 не сработал
                logger.warning(f"DownloadError для {url}, пробуем mkv: {e}")  # noqa: G004
                ydl_opts["merge_output_format"] = "mkv"
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])
                    logger.info(f"Успешно загружено (mkv) [{index}/{total}]: {url}")  # noqa: G004
                except Exception as e:
                    logger.error(f"Не удалось скачать {url}: {e}")  # noqa: G004
                    self.failed_videos.append(f"{url}")
                    self.signals.error_occurred.emit(url)

                self.signals.progress.emit(100)

            # Обновляем общий прогресс после завершения текущего видео
            overall_percent = int((index / total) * 100)
            self.signals.overall_progress.emit(overall_percent)

        if self.failed_videos:
            error_file = self.download_dir / "failed_downloads.txt"
            with error_file.open("a", encoding="utf-8") as f:
                for line in self.failed_videos:
                    f.write(line + "\n")
            logger.warning(f"Ошибки загрузки записаны в {error_file}")  # noqa: G004

        logger.info("Завершение задачи загрузки")
        self.signals.finished.emit()


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        logger.info("Инициализация главного окна приложения")

        self.setWindowTitle("YouTube Downloader")
        self.resize(1200, 800)
        font = self.font()
        font.setPointSize(DEAFULT_FONT_SIZE)
        self.setFont(font)
        self.error_flag = False
        self.download_dir = DOWNLOAD_DIR

        logger.info(
            f"Установлена директория загрузки по умолчанию: {self.download_dir}"  # noqa: G004
        )

        self.set_style()

        # --- GUI элементы ---

        # иконка
        icon_path = resource_path("resources/icon.ico")
        self.setWindowIcon(QtGui.QIcon(str(icon_path)))
        # Настройки
        settings_group = self.set_settings_block()
        # Ссылки
        links_group = self.set_urls_block()
        # Прогресс
        progress_group = self.set_progress_group()
        # Кнопка скачивания
        self.download_button = QtWidgets.QPushButton("Скачать все")
        self.download_button.setIcon(
            self.style().standardIcon(QtWidgets.QStyle.SP_DialogSaveButton),
        )
        # Основной layout
        main_layout = QtWidgets.QVBoxLayout()

        # Первый слой: Настройки и DropArea
        top_layout = QtWidgets.QHBoxLayout()
        top_layout.addWidget(links_group, 1)
        top_layout.addWidget(settings_group)

        main_layout.addLayout(top_layout)
        # Второй слой: Прогресс загрузки
        main_layout.addWidget(progress_group)

        # Кнопка скачивания
        main_layout.addWidget(self.download_button)
        self.setLayout(main_layout)

        # Сигналы
        self.download_button.clicked.connect(self.start_download)

        # Пул потоков автоматически управляет памятью!
        self.thread_pool = QThreadPool()
        self.thread_pool.setMaxThreadCount(1)  # 1 загрузка одновременно

        logger.info("Главное окно успешно инициализировано")

    def set_style(self) -> None:
        """Установка стилизации"""
        self.setStyleSheet("""
            QGroupBox {
                border: 1px solid #ccc;
                border-radius: 6px;
                margin-top: 12px;
                padding: 8px;
                font-weight: bold;
            }
            QListWidget {
                border: 1px solid #ccc;
                border-radius: 6px;
                padding: 4px;
                font-size: 12pt;
            }
            QListWidget::item {
                padding: 6px 8px;
                margin: 2px 0;
                border-radius: 4px;
            }
            QListWidget::item:selected {
                background-color: #4285f4;
                color: white;
            }
            QScrollBar:vertical {
                border: none;
                background: #f0f0f0;
                width: 20px;
                border-radius: 10px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: #c0c0c0;
                min-height: 20px;
                border-radius: 10px;
            }
            QScrollBar::handle:vertical:hover {
                background: #4285f4;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: none;
            }
            QScrollBar:horizontal {
                border: none;
                background: #f0f0f0;
                height: 20px;
                border-radius: 10px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:horizontal {
                background: #c0c0c0;
                min-width: 20px;
                border-radius: 10px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #4285f4;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
            QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
                background: none;
            }
            QPushButton {
                background-color: #4285f4;
                color: white;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton:disabled {
                background-color: #aaa;
            }
            QProgressBar {
                height: 20px;
                text-align: center;
                color: black;
            }
        """)

    def set_settings_block(self) -> QtWidgets.QGroupBox:
        """Блок настрок приложения"""
        self.spin = QtWidgets.QSpinBox()
        self.spin.setRange(12, 48)
        self.spin.setValue(DEAFULT_FONT_SIZE)
        self.spin.valueChanged.connect(self.change_font_size)

        self.dir_button = QtWidgets.QPushButton("Выбрать папку")
        self.dir_button.clicked.connect(self.choose_directory)

        self.dir_label = ClickableLabel(str(self.download_dir))
        self.dir_label.setWordWrap(True)
        self.dir_label.setStyleSheet("""
            background-color: #f0f0f0;
            border: 1px solid #ccc;
            border-radius: 4px;
            padding: 4px 6px;
            color: #333333;
            font-size: 12pt;
        """)
        self.dir_label.setToolTip("Нажмите, чтобы открыть директорию")
        self.dir_label.clicked.connect(self.open_directory)

        self.combo_quality = QtWidgets.QComboBox()
        self.combo_quality.addItems(["До 1080p", "До 720p", "До 480p"])
        self.combo_quality.setCurrentIndex(0)

        settings_group = QtWidgets.QGroupBox("Настройки")
        settings_layout = QtWidgets.QVBoxLayout()
        settings_layout.addWidget(QtWidgets.QLabel("Размер шрифта:"))
        settings_layout.addWidget(self.spin)
        settings_layout.addWidget(QtWidgets.QLabel("Папка для загрузки:"))
        settings_layout.addWidget(self.dir_button)
        settings_layout.addWidget(self.dir_label)
        settings_layout.addWidget(QtWidgets.QLabel("Максимальное качество видео:"))
        settings_layout.addWidget(self.combo_quality)
        settings_group.setLayout(settings_layout)
        return settings_group

    def set_urls_block(self) -> QtWidgets.QGroupBox:
        """Блок области с ссылками"""  # noqa: RUF002
        self.drop_area = DropArea()
        links_group = QtWidgets.QGroupBox("Ссылки")

        links_layout = QtWidgets.QVBoxLayout()
        links_layout.addWidget(QtWidgets.QLabel("Перетащи сюда YouTube ссылки:"))
        links_layout.addWidget(self.drop_area)
        links_layout.addWidget(
            QtWidgets.QLabel("<b>Правый клик по ссылке → удалить</b>"),
        )
        links_group.setLayout(links_layout)
        return links_group

    def set_progress_group(self) -> QtWidgets.QGroupBox:
        """Блок с прогрессом скачивания"""  # noqa: RUF002
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setTextVisible(True)
        self.overall_bar = QtWidgets.QProgressBar()
        self.overall_bar.setTextVisible(True)
        progress_group = QtWidgets.QGroupBox("Прогресс загрузки")
        progress_layout = QtWidgets.QVBoxLayout()
        progress_layout.addWidget(QtWidgets.QLabel("Прогресс текущего видео:"))
        progress_layout.addWidget(self.progress_bar)
        progress_layout.addWidget(QtWidgets.QLabel("Общий прогресс:"))
        progress_layout.addWidget(self.overall_bar)
        progress_group.setLayout(progress_layout)
        return progress_group

    def choose_directory(self):
        logger.info("Открыт диалог выбора директории")
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Выбрать папку")
        if path:  # если пользователь выбрал
            old_dir = self.download_dir
            self.download_dir = pathlib.Path(path)
            self.dir_label.setText(str(self.download_dir))
            self.dir_label.setToolTip("Нажмите, чтобы открыть директорию")
            logger.info(
                f"Директория загрузки изменена: {old_dir} -> {self.download_dir}"  # noqa: G004
            )
        else:
            logger.info("Выбор директории отменен пользователем")

    def open_directory(self):
        """Открывает директорию загрузки в файловом менеджере"""

        # Проверяем все условия сразу
        logger.info(f"Попытка открыть директорию: {self.download_dir}")  # noqa: G004

        if not self.download_dir.exists():
            error_msg = "Директория не существует"
            logger.error(f"{error_msg}: {self.download_dir}")  # noqa: G004
        elif not self.download_dir.is_dir():
            error_msg = "Указанный путь не является директорией"
            logger.error(f"{error_msg}: {self.download_dir}")  # noqa: G004
        elif not os.access(self.download_dir, os.R_OK | os.X_OK):
            error_msg = "Недостаточно прав для открытия директории"
            logger.error(f"{error_msg}: {self.download_dir}")  # noqa: G004
        else:
            error_msg = None

        if error_msg:
            QtWidgets.QMessageBox.warning(
                self,
                "Ошибка доступа",
                f"{error_msg}:\n{self.download_dir}",
                QtWidgets.QMessageBox.Ok,
            )
            return

        path = str(self.download_dir)

        try:
            system = platform.system()
            logger.debug(f"Открытие директории на платформе: {system}")  # noqa: G004

            if system == "Windows":
                os.startfile(path)
            elif system == "Darwin":  # macOS
                subprocess.Popen(["open", path])
            else:  # Linux
                subprocess.Popen(["xdg-open", path])

            logger.info(f"Директория успешно открыта: {path}")  # noqa: G004
        except Exception as e:
            logger.error(f"Не удалось открыть директорию {path}: {e}", exc_info=True)  # noqa: G004, G201
            QtWidgets.QMessageBox.warning(
                self,
                "Ошибка",
                f"Не удалось открыть директорию:\n{e}",
                QtWidgets.QMessageBox.Ok,
            )

    def change_font_size(self, size):
        font = self.font()  # получаем шрифт текущего окна
        font.setPointSize(size)
        self.setFont(font)
        for child in self.findChildren(QtWidgets.QWidget):
            child.setFont(font)
        logger.info(f"Размер шрифта изменен на {size}")  # noqa: G004

    def start_download(self):
        total = self.drop_area.count()
        if total == 0:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Нет ссылок для скачивания")
            logger.warning("Попытка запуска загрузки без ссылок")
            return

        choice = self.combo_quality.currentText()
        # Преобразуем выбор в формат yt-dlp
        if choice == "До 1080p":
            fmt = "bestvideo[height<=1080]+bestaudio/best"
        elif choice == "До 720p":
            fmt = "bestvideo[height<=720]+bestaudio/best"
        elif choice == "До 480p":
            fmt = "bestvideo[height<=480]+bestaudio/best"
        else:
            fmt = "video+bestaudio/best"

        logger.info(f"Запуск загрузки {total} видео, формат: {fmt}")  # noqa: G004

        # Обнуляем прогрессбары
        self.progress_bar.setValue(0)  # текущего видео
        self.overall_bar.setValue(0)  # общий прогресс

        # Собираем все ссылки
        urls = [self.drop_area.item(i).text() for i in range(total)]

        # Создаем задачу
        task = DownloadTask(urls, fmt, self.download_dir)

        # Подключаем сигналы
        task.signals.progress.connect(self.progress_bar.setValue)
        task.signals.overall_progress.connect(self.overall_bar.setValue)
        task.signals.finished.connect(self.on_finished)
        task.signals.error_occurred.connect(lambda url: self.handle_error(url))

        # QThreadPool reuses threads, but each task (QRunnable) is automatically deleted after completion.
        # This prevents memory leaks as long as tasks are set up for auto-deletion (the default in PyQt5).
        self.thread_pool.start(task)

        self.download_button.setEnabled(False)

    def handle_error(self, url):
        """Обработчик ошибок загрузки с логированием"""
        self.error_flag = True
        logger.error(f"Ошибка при загрузке видео: {url}")  # noqa: G004

    def on_finished(self):
        # Системный звук
        if sys.platform == "win32":
            import winsound  # noqa: PLC0415

            winsound.MessageBeep()
        else:
            logger.info("\a")  # Linux/macOS beep

        self.drop_area.clear()
        self.download_button.setEnabled(True)

        # Сообщение пользователю
        if self.error_flag:
            logger.warning("Загрузка завершена с ошибками")
            QtWidgets.QMessageBox.warning(
                self,
                "Завершено с ошибками",  # noqa: RUF001
                "Некоторые видео не удалось скачать. "
                "Список нескаченных ссылок сохранён в failed_downloads.txt",
            )
        else:
            logger.info("Все видео успешно загружены")
            QtWidgets.QMessageBox.information(
                self,
                "Готово",
                "Все видео скачаны успешно!",  # noqa: RUF001
            )

        # Сбрасываем флаг ошибок для следующего скачивания
        self.error_flag = False


def exception_hook(exctype, value, tb):
    """Ловит необработанные исключения Qt и логирует их"""

    tb_text = "".join(traceback.format_exception(exctype, value, tb))
    logger.critical(f"Необработанное исключение:\n{tb_text}")  # noqa: G004

    # Показываем пользователю
    QtWidgets.QMessageBox.critical(
        None,
        "Критическая ошибка",
        f"Произошла необработанная ошибка:\n{exctype.__name__}: {value}\n\n"
        f"Подробности сохранены в app.log",
    )

    # Вызываем стандартный обработчик
    sys.__excepthook__(exctype, value, tb)


if __name__ == "__main__":
    # Устанавливаем обработчик необработанных исключений
    sys.excepthook = exception_hook

    ensure_download_dir_exists()
    logger.info(f"Запуск приложения, версия PyQt5: {QtCore.PYQT_VERSION_STR}")  # noqa: G004

    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    logger.info("QApplication создан, стиль: Fusion")

    window = MainWindow()
    window.show()
    logger.info("Главное окно отображено")

    exit_code = app.exec_()
    logger.info(f"Приложение завершено с кодом: {exit_code}")  # noqa: G004
    sys.exit(exit_code)
