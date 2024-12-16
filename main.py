import os


txt_list = [] # all txt files with links
def find_txt_files(path):
    for f in os.listdir(path):
        if f.endswith(".txt"):
            yield f

def check_link(link):
    if link[0:8] != "https://":
        return False
    if link[8:24] != "www.youtube.com/" and link[8:17] != "youtu.be/":
        return False
    return True

def read_links_from_txt_to_list(path):
    links = []

    for txt in find_txt_files(path):
        if txt == "error_copy_of_links.txt":
            continue

        links_length = len(links)

        with open(txt, "r") as file:
            for line in file.readlines():
                if check_link(line):
                    links.append(line.strip())
        if links_length != len(links):
            txt_list.append(txt) # append only when we download at least 1 link from this txt
    return links

def clean_txt_files():
    for txt_file in txt_list:
        with open(txt_file, "w"):
            pass

if __name__ == "__main__":
    try:
        links = read_links_from_txt_to_list("./")

        for video in links:
            os.system('.\\yt-dlp.exe -P ".\\result" ' + video)

        clean_txt_files()

    except Exception:
        print("Some error occurred")

    print("Process finished")
