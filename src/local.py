__all__ = []


import os
import pathlib

ROOT_PATH = pathlib.Path(__file__).parent.parent


def find_txt_files(path: str):
    for f in pathlib.Path.iterdir(path):
        if f.name.endswith(".txt"):
            yield f


def check_link(link: str) -> bool:
    if link[0:8] != "https://":
        return False
    return not (link[8:24] != "www.youtube.com/" and link[8:17] != "youtu.be/")


def read_links_from_txt_to_list(path: str, txt_names: list[str]) -> list[str]:
    links = []

    for txt in find_txt_files(path):
        if txt == "error_copy_of_links.txt":
            continue

        links_length = len(links)

        file_path = pathlib.Path(txt)

        with file_path.open() as file:
            for line in file.readlines():
                if check_link(line):
                    links.append(line.strip())  # noqa: PERF401
        if links_length != len(links):
            txt_names.append(
                txt,
            )  # append only when we download at least 1 link from this txt
    return links


def clean_txt_files(txt_files_list: list[str]) -> None:
    for txt_file in txt_files_list:
        file_path = pathlib.Path(txt_file)
        with file_path.open("w"):
            pass


if __name__ == "__main__":
    print(ROOT_PATH)
    txt_list = []  # all txt files names with links
    try:
        video_links = read_links_from_txt_to_list(ROOT_PATH, txt_list)

        for video in video_links:
            os.system(f'{ROOT_PATH}\\yt-dlp.exe -P "{ROOT_PATH}\\result" ' + video)  # noqa: S605

        clean_txt_files(txt_list)

    except Exception as e:
        print("Some error occurred:\n")
        print(e)

    print("Process finished")
