__all__ = []

import re
import sys

import yt_dlp
from PyQt5 import QtCore, QtWidgets

from main import ROOT_PATH

DOWNLOAD_DIR = ROOT_PATH / "result"
DEAFULT_FONT_SIZE = 20


class DropArea(QtWidgets.QListWidget):
    """Зона для drag & drop ссылок"""

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)

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
                    self.addItem(url_str)
                    print("Dropped URL:", url_str)


class DownloadWorker(QtCore.QThread):
    # Сигналы для передачи данных в GUI
    progress_changed = QtCore.pyqtSignal(int)  # процент загрузки текущего видео
    overall_progress = QtCore.pyqtSignal(int)  # общий прогресс (по списку)
    finished = QtCore.pyqtSignal()  # завершение всех загрузок
    error_occurred = QtCore.pyqtSignal(str)

    def __init__(self, urls, fmt):
        super().__init__()
        self.urls = urls
        self.fmt = fmt
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
                "outtmpl": str(DOWNLOAD_DIR / "%(title)s.%(ext)s"),
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
            error_file = DOWNLOAD_DIR / "failed_downloads.txt"
            with error_file.open("a", encoding="utf-8") as f:
                for line in self.failed_videos:
                    f.write(line + "\n")

        self.finished.emit()  # сигнал о завершении всех загрузок  # noqa: RUF003


class MainWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Downloader")
        self.resize(1000, 1000)
        font = self.font()
        font.setPointSize(DEAFULT_FONT_SIZE)
        self.setFont(font)

        self.error_flag = False

        # GUI элементы
        self.spin = QtWidgets.QSpinBox()
        self.spin.setRange(
            12,
            48,
        )  # Минимальный и максимальный размер шрифта
        self.spin.setValue(DEAFULT_FONT_SIZE)  # Начальный размер
        self.spin.valueChanged.connect(self.change_font_size)

        self.combo_quality = QtWidgets.QComboBox()
        self.combo_quality.addItems(
            ["До 1080p", "До 720p", "До 480p"],
        )
        self.combo_quality.setCurrentIndex(0)

        self.drop_area = DropArea()
        self.download_button = QtWidgets.QPushButton("Скачать все")

        self.progress_bar = QtWidgets.QProgressBar()  # Прогресс текущего видео
        self.progress_bar.setValue(0)

        self.overall_bar = QtWidgets.QProgressBar()  # Общий прогресс
        self.overall_bar.setValue(0)

        layout = QtWidgets.QVBoxLayout()
        layout.addWidget(QtWidgets.QLabel("Размер шрифта:"))
        layout.addWidget(self.spin)
        layout.addWidget(QtWidgets.QLabel("Перетащи YouTube ссылки сюда:"))
        layout.addWidget(self.drop_area)
        layout.addWidget(QtWidgets.QLabel("Прогресс текущего видео:"))
        layout.addWidget(self.progress_bar)
        layout.addWidget(QtWidgets.QLabel("Общий прогресс:"))
        layout.addWidget(self.overall_bar)
        layout.addWidget(self.combo_quality)
        layout.addWidget(self.download_button)
        self.setLayout(layout)

        self.download_button.clicked.connect(self.start_download)

        self.worker = None  # ссылка на поток

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
        self.worker = DownloadWorker(urls, fmt)
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
            import winsound

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
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
