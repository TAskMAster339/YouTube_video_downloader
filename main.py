import os


if __name__ == "__main__":

    links = []

    try:
        with open("links.txt", "r") as file:
            for line in file.readlines():
                links.append(line.strip())

        for video in links:
            os.system('.\\yt-dlp.exe -P ".\\result" ' + video)

        with open("links.txt", "w"):
            pass

    except Exception:
        print("Some error occurred")

        with open("error_copy_of_links.txt", "w") as file:
            for line in links:
                file.write(line + "\n")

    print("Process finished")
