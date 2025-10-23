from pathlib import Path

import yt_dlp



def read_links(filename: str = "links.txt") -> list[str]:
    """
    Читает ссылки из файла.

    Args:
        filename: Путь к файлу со ссылками

    Returns:
        Список ссылок
    """  # noqa: RUF002
    if not Path.exists(filename):
        raise FileNotFoundError(f"File {filename} not found")  # noqa: TRY003

    with Path.open(filename) as f:
        content = f.read()
        # Поддержка разделителей: переносы и пробелы
        links = content.replace("\n", " ").split()
        return [link.strip() for link in links if link.strip()]


def download_video(url: str, output_dir: str = "result") -> bool:
    """
    Скачивает видео по URL.

    Args:
        url: URL видео
        output_dir: Директория для сохранения

    Returns:
        True если успешно, False иначе
    """
    ydl_opts = {
        "format": "best",
        "outtmpl": f"{output_dir}/%(title)s.%(ext)s",
        "quiet": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        return False
    else:
        return True


def clear_links_file(filename: str = "links.txt") -> None:
    """
    Очищает файл со ссылками.

    Args:
        filename: Путь к файлу
    """  # noqa: RUF002
    with Path.open(filename, "w") as f:
        f.write("")


def ensure_result_directory(directory: str = "result") -> None:
    """
    Создаёт директорию для результатов, если её нет.

    Args:
        directory: Путь к директории
    """
    Path(directory).mkdir(exist_ok=True)


def main():
    """Главная функция."""
    try:
        # Создаём директорию для результатов
        ensure_result_directory()

        # Читаем ссылки
        links = read_links()

        if not links:
            print("No links found in links.txt")
            return

        print(f"Found {len(links)} links to download")

        # Скачиваем каждое видео
        successful = 0
        failed = 0

        for i, link in enumerate(links, 1):
            print(f"Downloading {i}/{len(links)}: {link}")
            if download_video(link):
                successful += 1
            else:
                failed += 1

        print("\nDownload complete!")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")

        # Очищаем файл ссылок
        clear_links_file()
        print("Links file cleared")

    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


if __name__ == "__main__":
    main()
