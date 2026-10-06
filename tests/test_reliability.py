from pathlib import Path
from unittest.mock import MagicMock, patch

from src.app import DownloadTask
import yt_dlp
import pytest


def test_unexpected_error_always_finishes(tmp_path):
    task = DownloadTask(['https://example.com/video'], 'best', tmp_path)
    finished = []
    task.signals.finished.connect(lambda: finished.append(True))
    with patch.object(task, '_run_downloads', side_effect=OSError('disk')):
        task.run()
    assert finished == [True]
    assert task.failed_videos == task.urls


def test_report_write_error_does_not_abort(tmp_path):
    task = DownloadTask(['https://example.com/video'], 'best', tmp_path)
    finished = []
    task.signals.finished.connect(lambda: finished.append(True))
    with patch('yt_dlp.YoutubeDL') as mocked, patch.object(Path, 'open', side_effect=PermissionError()):
        mocked.return_value.__enter__.return_value.download.side_effect = yt_dlp.utils.DownloadError('offline')
        task.run()
    assert finished == [True]
    assert task.failed_videos == task.urls
    assert not task.failure_report_saved


def test_completion_preserves_failed_and_new_links(main_window):
    urls = ['https://example.com/success', 'https://example.com/failed', 'https://example.com/new']
    for url in urls:
        main_window.drop_area.add_url(url)
    task = DownloadTask(urls[:2], 'best', main_window.download_dir)
    task.successful_urls = urls[:1]
    task.failed_videos = urls[1:2]
    main_window.active_task = task
    main_window.error_flag = True
    with patch('PyQt5.QtWidgets.QMessageBox.warning'):
        main_window.on_finished()
    assert [main_window.drop_area.item(i).text() for i in range(main_window.drop_area.count())] == urls[1:]
    assert main_window.drop_area._url_set == set(urls[1:])


def test_cancel_before_start_never_downloads(tmp_path):
    task = DownloadTask(['https://example.com/video'], 'best', tmp_path)
    task.cancel()
    finished = []
    task.signals.finished.connect(lambda: finished.append(True))
    with patch('yt_dlp.YoutubeDL') as mocked:
        task.run()
    mocked.assert_not_called()
    assert finished == [True]
    assert not task.successful_urls


def test_video_with_playlist_does_not_expand(tmp_path):
    task = DownloadTask(['https://youtube.com/watch?v=video&list=playlist'], 'best', tmp_path)
    with patch('yt_dlp.YoutubeDL') as mocked:
        mocked.return_value.__enter__.return_value.download.return_value = 0
        task.run()
    assert mocked.call_args.args[0]['noplaylist'] is True


def test_logging_unwritable_directory_does_not_prevent_startup(tmp_path):
    from src import app
    with patch.object(app, 'DATA_DIR', tmp_path), patch.object(Path, 'mkdir', side_effect=PermissionError()):
        logger = app.setup_logging()
    assert logger is not None


def test_user_data_is_outside_executable_directory():
    from src.app import APP_DIR, DATA_DIR, DOWNLOAD_DIR
    assert DATA_DIR.parent != APP_DIR
    assert DOWNLOAD_DIR.parent != APP_DIR


def test_same_title_different_ids_have_distinct_filenames(tmp_path):
    task = DownloadTask(['https://example.com/video'], 'best', tmp_path)
    with patch('yt_dlp.YoutubeDL') as mocked:
        mocked.return_value.__enter__.return_value.download.return_value = 0
        task.run()
    with yt_dlp.YoutubeDL(mocked.call_args.args[0]) as ydl:
        first = ydl.prepare_filename({'title': 'Same title', 'id': 'one', 'extractor_key': 'Youtube', 'ext': 'webm'})
        second = ydl.prepare_filename({'title': 'Same title', 'id': 'two', 'extractor_key': 'Youtube', 'ext': 'webm'})
    assert first != second
    assert 'Youtube-one' in first


@pytest.mark.parametrize('error', [PermissionError('denied'), OSError('No space left on device'), yt_dlp.utils.DownloadError('connection timed out')])
def test_errors_do_not_trigger_container_retry_and_next_url_continues(tmp_path, error):
    task = DownloadTask(['https://example.com/one', 'https://example.com/two'], 'best', tmp_path)
    with patch('yt_dlp.YoutubeDL') as mocked:
        download = mocked.return_value.__enter__.return_value.download
        download.side_effect = [error, 0]
        task.run()
    assert download.call_count == 2
    assert task.failed_videos == task.urls[:1]
    assert task.successful_urls == task.urls[1:]
    assert task.errors[task.urls[0]]


def test_nonzero_download_status_is_failure(tmp_path):
    task = DownloadTask(['https://example.com/video'], 'best', tmp_path)
    with patch('yt_dlp.YoutubeDL') as mocked:
        mocked.return_value.__enter__.return_value.download.return_value = 1
        task.run()
    assert task.failed_videos == task.urls
    assert not task.successful_urls


def test_cancel_in_hook_preserves_remaining_queue(tmp_path):
    task = DownloadTask(['https://example.com/one', 'https://example.com/two'], 'best', tmp_path)
    finished = []
    task.signals.finished.connect(lambda: finished.append(True))
    def download(urls):
        task.cancel()
        task.progress_hook({'status': 'downloading'})
    with patch('yt_dlp.YoutubeDL') as mocked:
        mocked.return_value.__enter__.return_value.download.side_effect = download
        task.run()
    assert mocked.return_value.__enter__.return_value.download.call_count == 1
    assert not task.successful_urls
    assert not task.failed_videos
    assert finished == [True]


def test_close_can_be_declined(main_window):
    from PyQt5 import QtGui, QtWidgets
    task = DownloadTask(['https://example.com/video'], 'best', main_window.download_dir)
    main_window.active_task = task
    event = QtGui.QCloseEvent()
    with patch.object(QtWidgets.QMessageBox, 'question', return_value=QtWidgets.QMessageBox.No):
        main_window.closeEvent(event)
    assert not event.isAccepted()
    assert not task.cancel_event.is_set()
    main_window.active_task = None


@pytest.mark.parametrize('error, expected', [
    (PermissionError(), 'Нет доступа'), (OSError('No space left'), 'Недостаточно места'),
    (yt_dlp.utils.DownloadError('network timeout'), 'Проверьте интернет'),
    (yt_dlp.utils.DownloadError('Video unavailable'), 'Видео недоступно'),
    (yt_dlp.utils.DownloadError('ffmpeg codec error'), 'обработать видео'),
])
def test_error_message_matches_cause(error, expected):
    from src.app import describe_download_error
    assert expected in describe_download_error(error)


def test_close_requests_cancellation_and_waits(main_window):
    from PyQt5 import QtGui, QtWidgets
    task = DownloadTask(['https://example.com/video'], 'best', main_window.download_dir)
    main_window.active_task = task
    event = QtGui.QCloseEvent()
    with patch.object(QtWidgets.QMessageBox, 'question', return_value=QtWidgets.QMessageBox.Yes):
        main_window.closeEvent(event)
    assert not event.isAccepted()
    assert task.cancel_event.is_set()
    assert main_window.close_after_download
    main_window.on_finished()
    assert main_window.active_task is None
