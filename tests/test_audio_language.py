import pytest
import yt_dlp

from src.app import prefer_russian_audio


def audio(name, language=None, note=None):
    return dict(format_id=name, url='https://example.com/' + name, ext='webm',
                vcodec='none', acodec='opus', language=language, format_note=note)


@pytest.mark.parametrize('tracks, expected', [
    ([audio('ru', 'ru'), audio('en', 'en', 'original')], 'ru'),
    ([audio('ru', 'ru-RU'), audio('en', 'en', 'original')], 'ru'),
    ([audio('en', 'en', 'original'), audio('fr', 'fr')], 'en'),
    ([audio('unknown')], 'unknown'),
    ([audio('original', 'ru', 'original')], 'original'),
])
@pytest.mark.parametrize('height', [480, 720, 1080])
def test_audio_language_preference(tracks, expected, height):
    formats = [dict(format_id='video', url='https://example.com/video', ext='mp4',
                    vcodec='avc1', acodec='none', height=height)] + tracks
    with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
        selector = ydl.build_format_selector(prefer_russian_audio(f'bestvideo[height<={height}]+bestaudio/best'))
        selected = list(selector({'formats': formats, 'incomplete_formats': False, 'has_merged_format': False}))
    assert len(selected) == 1
    assert selected[0]['requested_formats'][1]['format_id'] == expected


def test_single_stream_without_language_still_works():
    formats = [dict(format_id='single', url='https://example.com/video', ext='mp4',
                    vcodec='avc1', acodec='aac', height=480)]
    with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
        selector = ydl.build_format_selector(prefer_russian_audio('bestvideo[height<=480]+bestaudio/best'))
        selected = list(selector({'formats': formats, 'incomplete_formats': False, 'has_merged_format': True}))
    assert selected[0]['format_id'] == 'single'
