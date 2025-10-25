__all__ = []

import pathlib
import re
import sys

import yt_dlp
from PyQt5 import QtCore, QtWidgets

ROOT_PATH = pathlib.Path(__file__).parent.parent

DOWNLOAD_DIR = ROOT_PATH / "result"
DEAFULT_FONT_SIZE = 16


def resource_path(relative_path):
    """Получает абсолютный путь к ресурсу, работает для dev и PyInstaller"""  # noqa: RUF002
    try:
        # PyInstaller создает временную папку и сохраняет путь в _MEIPASS
        base_path = sys._MEIPASS  # noqa: SLF001
    except AttributeError:
        base_path = pathlib.Path.parent(pathlib.Path.resolve(__file__))
    return base_path / pathlib.Path(relative_path)


def get_ffmpeg_path():
    """Получает путь к FFmpeg (ленивая инициализация)"""
    try:
        ffmpeg_location = str(resource_path("ffmpeg.exe"))
        if pathlib.Path(ffmpeg_location).exists():
            return ffmpeg_location
    except (AttributeError, FileNotFoundError):
        pass
    # Fallback: попытаться использовать системный FFmpeg
    return "ffmpeg"


class DropArea(QtWidgets.QListWidget):
    """Зона для drag & drop ссылок"""

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

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

    def show_context_menu(self, pos):
        """Контекстное меню для удаления"""
        menu = QtWidgets.QMenu(self)
        delete_action = menu.addAction("Удалить")
        action = menu.exec_(self.mapToGlobal(pos))
        if action == delete_action:
            for item in self.selectedItems():
                self.takeItem(self.row(item))

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
        """Добавляет ссылку в список с подсказкой"""  # noqa: RUF002
        item = QtWidgets.QListWidgetItem(url_str)
        item.setToolTip(
            "<p style='font-size:14pt; color:#444;'>"
            "Нажмите <b>правой кнопкой</b>, чтобы удалить ссылку из списка"
            "</p>",
        )
        self.addItem(item)


class DownloadWorker(QtCore.QThread):
    # Сигналы для передачи данных в GUI
    progress_changed = QtCore.pyqtSignal(int)  # процент загрузки текущего видео
    overall_progress = QtCore.pyqtSignal(int)  # общий прогресс (по списку)
    finished = QtCore.pyqtSignal()  # завершение всех загрузок
    error_occurred = QtCore.pyqtSignal(str)

    def __init__(self, urls, fmt, download_dir):
        super().__init__()
        self.urls = urls
        self.fmt = fmt
        self.download_dir = download_dir
        self.failed_videos = []

    def run(self):
        total = len(self.urls)

        for index, url in enumerate(self.urls, start=1):

            def progress_hook(d):
                if d["status"] == "downloading":
                    percent_str = d.get("_percent_str", "0.0%").strip().replace("%", "")
                    percent_str = re.sub(r"\x1b\[[0-9;]*m", "", percent_str)
                    percent = float(percent_str)
                    try:
                        self.progress_changed.emit(int(percent))
                    except ValueError as e:
                        self.progress_changed.emit(0)
                        print(f"ERROR:\n\t{e}")

                elif d["status"] == "finished":
                    self.progress_changed.emit(100)

            ydl_opts = {
                "ffmpeg_location": get_ffmpeg_path(),
                "outtmpl": str(self.download_dir / "%(title)s.%(ext)s"),
                "format": self.fmt,  # "best[height<=1080]+bestaudio/best"
                "progress_hooks": [progress_hook],
                "socket_timeout": 30,
                "retries": 3,
                "quiet": False,
                "noprogress": True,
                "merge_output_format": "webm",
                "continuedl": True,
                "postprocessor_args": ["-v", "verbose"],
            }

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
            except Exception:
                # Попытка сменить контейнер на mkv, если mp4 не сработал
                ydl_opts["merge_output_format"] = "mkv"
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        ydl.download([url])
                except Exception as e:
                    print(f"ERROR:\n\t{e}")
                    self.failed_videos.append(f"{url}")
                    self.error_occurred.emit(url)

            # Обновляем общий прогресс после завершения текущего видео
            overall_percent = int((index / total) * 100)
            self.overall_progress.emit(overall_percent)

        # Сохраняем все неудачные видео в текстовый файл
        if self.failed_videos:
            error_file = self.download_dir / "failed_downloads.txt"
            with error_file.open("a", encoding="utf-8") as f:
                for line in self.failed_videos:
                    f.write(line + "\n")

        self.finished.emit()  # сигнал о завершении всех загрузок  # noqa: RUF003


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
        self.worker = None

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

        self.dir_label = QtWidgets.QLabel(str(self.download_dir))
        self.dir_label.setWordWrap(True)
        self.dir_label.setStyleSheet("""
            background-color: #f0f0f0;
            border: 1px solid #ccc;
            border-radius: 4px;
            padding: 4px 6px;
            color: #333333;
            font-size: 12pt;
        """)

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

        # Запускаем в отдельном потоке
        self.worker = DownloadWorker(urls, fmt, self.download_dir)
        self.worker.progress_changed.connect(self.progress_bar.setValue)
        self.worker.overall_progress.connect(self.overall_bar.setValue)
        self.worker.finished.connect(self.on_finished)
        self.worker.error_occurred.connect(self.handle_error)

        self.download_button.setEnabled(False)
        self.worker.start()

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
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
