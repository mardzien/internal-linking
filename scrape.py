import requests
from bs4 import BeautifulSoup


def get_information_from_soup(url, input_class):
    # creating dictionary with given url
    info = {"URL": url,
            "Linkuje na siebie": "Nie", }

    # creating soup object
    raw_html = requests.get(url)
    soup_object = BeautifulSoup(raw_html.content, 'lxml')
    raw_text = soup_object.find_all(class_=input_class)

    # getting text from soup object inside class
    text_result = ""
    for raw_text_iteration in raw_text:
        temp = raw_text_iteration.get_text()
        text_result += temp.replace("\n", "").replace("\t", "") + " "

    lower_text_result = text_result.lower()
    info["Tekst"] = lower_text_result
    info["Liczba znaków"] = len(lower_text_result)

    # getting all links
    # link_tags = raw_text[0].find_all('a')

    # number_of_paragraphs = len(raw_text[0].find_all('p'))
    # info["Liczba paragrafów"] = number_of_paragraphs
    # info["Liczba linków"] = len(link_tags)
    # # creating list of href
    # href_list = []
    # for link in link_tags:
    #     try:
    #         href_list.append(f"{link['href']} ---> {link.contents[0]}")
    #         if link['href'] == url:
    #             info["Linkuje na siebie"] = "Tak"
    #     except:
    #         continue
    #
    # info["Tablica linków"] = href_list

    return info
