import requests
import pandas as pd
from bs4 import BeautifulSoup


list_of_keywords = ['skupszop', 'książki dla dzieci']
url1 = "https://www.renee.pl/blog/renee/z-czym-nosic-polbuty"
input_class1 = "eltd-post-content"


def get_information_from_soup(url, input_class):
    # creating dictionary with given url
    info = {"URL": url, "Linkuje na siebie": "Nie", }

    # creating soup object
    raw_html = requests.get(url)
    soup_object = BeautifulSoup(raw_html.content, 'lxml')
    raw_text = soup_object.find_all(class_=input_class)

    # getting text from soup object inside class
    text_result = ""
    for raw_text_iteration in raw_text:
        temp = raw_text_iteration.get_text()
        if temp == "\n" or temp == "\t":
            text_result += temp + " "

    lower_text_result = text_result.lower()
    info["Tekst"] = lower_text_result
    info["Liczba znaków"] = len(lower_text_result)

    # getting all links
    link_tags = raw_text[0].find_all('a')

    number_of_paragraphs = len(raw_text[0].find_all('p'))
    info["Liczba paragrafów"] = number_of_paragraphs
    info["Liczba linków"] = len(link_tags)
    # creating list of href
    href_list = []
    for link in link_tags:
        try:
            href_list.append(f"{link['href']} ---> {link.contents[0]}")
            if link['href'] == url:
                info["Linkuje na siebie"] = "Tak"
        except:
            continue

    info["Tablica linków"] = href_list

    return info


# def get_clean_text(raw_text):
#     text_result = ""
#     for raw_text_iteration in raw_text:
#         temp = raw_text_iteration.get_text()
#         text_result += temp + " "
#
#     lower_text_result = text_result.lower()
#     return lower_text_result


def find_keywords(keywords, clean_text):
    found_keywords = []
    for keyword in list_of_keywords:
        counter = 0
        for x in range(len(clean_text)):
            if clean_text[x:].startswith(keyword.lower()):
                counter += 1
        if counter != 0:
            found_keywords.append(f'{keyword} [{counter}]')
    return found_keywords


# print(text_result, len(text_result))
# print(found_keywords)
print(get_information_from_soup(url1, input_class1))
