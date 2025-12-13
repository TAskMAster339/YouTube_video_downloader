__all__ = []

import os
import pathlib
import platform
import re
import shutil
import subprocess
import sys
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


APP_DIR = get_app_directory()
DOWNLOAD_DIR = APP_DIR / "result"


def get_ffmpeg_path():
    """Получает путь к FFmpeg (ленивая инициализация)"""
    try:
        ffmpeg_path = resource_path("ffmpeg.exe")
        if ffmpeg_path.exists():
            print(f"Найден bundled FFmpeg: {ffmpeg_path}")
            return str(ffmpeg_path)
    except (AttributeError, FileNotFoundError, TypeError) as e:
        print(f"Ошибка: {e}")

    # Fallback
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        print(f"Найден системный FFmpeg: {system_ffmpeg}")
        return system_ffmpeg

    print("FFmpeg не найден")
    return "ffmpeg"


def ensure_download_dir_exists():
    """
    Гарантирует что директория для загрузок существует.
    Создает её если нужно с полной обработкой ошибок.
    """  # noqa: RUF002
    try:
        if not DOWNLOAD_DIR.exists():
            print(f"[*] Creating download directory: {DOWNLOAD_DIR}")
            DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
            print("[+] Directory created successfully")

        # Проверяем разрешения
        if not os.access(DOWNLOAD_DIR, os.W_OK):
            print("[!] No write permission")
            return False

    except PermissionError as e:
        print(f"[!] Permission denied: {e}")
        return False
    except Exception as e:
        print(f"[!] Error: {e}")
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
                    print("Dropped URL:", url_str)

    def add_url(self, url_str: str):
        """Добавляет ссылку в список с подсказкой"""
        if url_str in self._url_set:
            QtWidgets.QMessageBox.warning(
                self,
                "Дубликат ссылки",
                f"Ссылка уже добавлена в список:\n{url_str}",
                QtWidgets.QMessageBox.Ok,
            )
            print("URL уже есть в множестве:", url_str)
            return

        self._url_set.add(url_str)

        item = QtWidgets.QListWidgetItem(url_str)
        # Сохраняем «сырую» ссылку отдельно от отображаемого текста
        item.setData(QtCore.Qt.UserRole, url_str)

        print("URL добавлен в множество:", url_str)
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

        if is_valid_url(clipboard_text):
            self.add_url(clipboard_text)
        else:
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
            percent = float(percent_str)
            try:
                self.signals.progress.emit(int(percent))
            except ValueError as e:
                self.signals.overall_progress.emit(0)
                print(f"ERROR:\n\t{e}")

        elif d["status"] == "finished":
            self.signals.progress.emit(100)

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
        }

        # Проверяем существование файла cookies

        cookies_path = APP_DIR / "cookies.txt"
        if cookies_path.exists():
            ydl_opts["cookiefile"] = str(cookies_path)
            print(f"Используются cookies из {cookies_path}")
        else:
            print("Файл cookies.txt не найден, продолжаем без cookies")

        for index, url in enumerate(self.urls, start=1):
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
            except yt_dlp.utils.DownloadError:
                # Попытка сменить контейнер на mkv, если mp4 не сработал
                ydl_opts["merge_output_format"] = "mkv"
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])
                except Exception as e:
                    print(f"ERROR:\n\t{e}")
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

        self.signals.finished.emit()


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Downloader")
        self.resize(1200, 800)
        font = self.font()
        font.setPointSize(DEAFULT_FONT_SIZE)
        self.setFont(font)
        self.error_flag = False
        self.download_dir = DOWNLOAD_DIR

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
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Выбрать папку")
        if path:  # если пользователь выбрал
            self.download_dir = pathlib.Path(path)
            self.dir_label.setText(str(self.download_dir))
            self.dir_label.setToolTip("Нажмите, чтобы открыть директорию")

    def open_directory(self):
        """Открывает директорию загрузки в файловом менеджере"""

        # Проверяем все условия сразу

        if not self.download_dir.exists():
            error_msg = "Директория не существует"
        elif not self.download_dir.is_dir():
            error_msg = "Указанный путь не является директорией"
        elif not os.access(self.download_dir, os.R_OK | os.X_OK):
            error_msg = "Недостаточно прав для открытия директории"
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
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":  # macOS
                subprocess.Popen(["open", path])
            else:  # Linux
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
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

    def start_download(self):
        total = self.drop_area.count()
        if total == 0:
            QtWidgets.QMessageBox.warning(self, "Ошибка", "Нет ссылок для скачивания")
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

        print("Выбран формат:", fmt)

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
        task.signals.error_occurred.connect(self.handle_error)

        # QThreadPool reuses threads, but each task (QRunnable) is automatically deleted after completion.
        # This prevents memory leaks as long as tasks are set up for auto-deletion (the default in PyQt5).
        self.thread_pool.start(task)

        self.download_button.setEnabled(False)

    def handle_error(self):
        self.error_flag = True

    def on_finished(self):
        # Системный звук
        if sys.platform == "win32":
            import winsound  # noqa: PLC0415

            winsound.MessageBeep()
        else:
            print("\a")  # Linux/macOS beep

        self.drop_area.clear()
        self.download_button.setEnabled(True)

        # Сообщение пользователю
        if self.error_flag:
            QtWidgets.QMessageBox.warning(
                self,
                "Завершено с ошибками",  # noqa: RUF001
                "Некоторые видео не удалось скачать. "
                "Список нескаченных ссылок сохранён в failed_downloads.txt",
            )
        else:
            QtWidgets.QMessageBox.information(
                self,
                "Готово",
                "Все видео скачаны успешно!",  # noqa: RUF001
            )

        # Сбрасываем флаг ошибок для следующего скачивания
        self.error_flag = False


if __name__ == "__main__":
    ensure_download_dir_exists()
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
