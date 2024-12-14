import os

links = []

try:
    with open("links.txt", "r") as file:
        for line in file.readlines():
            links.append(line.strip())

    for video in links:
        os.system('.\\yt-dlp.exe -P ".\\result" ' + video)

except Exception:
    print("Some error occurred")

print("Process finished")