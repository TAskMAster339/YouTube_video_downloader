from main import *
import os


def test_find_txt_files():
    txt_files = {"links.txt"}

    for i in range(1, 100):
        name = f"test{i}.txt"
        with open(name, 'w'):
            pass
        txt_files.add(name)

    for txt in find_txt_files('./'):
        assert txt in txt_files

    for i in range(1, 100):
        os.remove(f"./test{i}.txt")


def test_check_links():
    correct_links = [
        "https://www.youtube.com/watch?v=Fbw3gcSuKfg",
        "https://www.youtube.com/watch?v=JO1xmXv66SI",
        "https://www.youtube.com/watch?v=zIcGmZi0GTE",
        "https://www.youtube.com/watch?v=WkmrTY7Qv28&t=10s",
        "https://www.youtube.com/watch?v=oQS3zpFarWE",
        "https://youtu.be/QmgPhe7pE7Q?si=NuRULxlhqIEzSx6N&t=334",
        "https://youtu.be/Lf96N0zC5hk?si=EtoU6ltjdMYZSudx",
        "https://youtu.be/7Ww30VkgvMI?si=3gh6YrH8BVrbjhSH",
        "https://youtu.be/fNwIbJGq_ug?si=owNyuY7Alu5sDHbK",
        "https://youtu.be/mYECrRYbzbQ?si=HNdlFGLk-rOdXwtB"
    ]
    incorrect_links = [
        "http://www.youtube.com/jfkaljf;af",
        "https;//youtu.be/afjkalsfja;sf",
        "https:\\\\yotu.be/fdjalf;af",
        "https://www.youtube.ru",
        "https://www.youtube.сom",
        "https://youtu,be/com"
        "https://youtu.be.com/djfla"
        "",
        "fajsfhasfasj;fasfjkas;fjaskfajgkjsdkgl;asgjk",
        " https://youtu.be/cofjdafja",
        "     "
    ]
    for link in correct_links:
        assert check_link(link)

    for link in incorrect_links:
        assert not check_link(link)


def test_read_links_from_txt_to_list():
    links_from_txt_files = set()
    correct_list_of_txt_files = set()
    list_of_txt_files = []

    for i in range(100):
        name = f"test{i}.txt"
        with open(name, 'w') as file:
            text = ""
            if i % 3 == 0:  # other text
                text = "some text for example"
            elif i % 3 == 1:  # correct link
                text = "https://youtu.be/mYECrRYbzbQ?si=HNdlFGLk-rOdXwtB"
            else:  # incorrect link
                text = "https://www.youtube.ru"

            file.write(text)

        if i % 3 == 1:
            links_from_txt_files.add(text)
            correct_list_of_txt_files.add(name)

    read_links = read_links_from_txt_to_list("./", list_of_txt_files)

    for url in read_links:
        assert url in links_from_txt_files

    for file in list_of_txt_files:
        assert file in correct_list_of_txt_files

    for txt in range(100):
        name = f"test{txt}.txt"
        os.remove("./" + name)


def test_clean_txt_files():
    txt_files = []
    for i in range(100):
        name = f"test{i}.txt"
        with open(name, 'w') as file:
            if i % 3 == 0:  # other text
                text = "some text for example"
            elif i % 3 == 1:  # correct link
                text = "https://youtu.be/mYECrRYbzbQ?si=HNdlFGLk-rOdXwtB"
            else:  # incorrect link
                text = "https://www.youtube.ru"

            file.write(text)
        txt_files.append(name)

    clean_txt_files(txt_files)

    for i in range(100):
        name = f"test{i}.txt"
        with open(name, "r") as file:
            assert file.read() == ""

    for i in range(100):
        name = f"test{i}.txt"
        os.remove("./" + name)
