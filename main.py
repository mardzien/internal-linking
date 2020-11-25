"""
Wejście:
1. Lista URLi
2. Baza fraz - para: fraza - URL

Przetwarzanie:
1. Wyciągamy podstawowe informacje z URLa z pkt 1, zwłaszcza tekst
2. Tworzymy pusty słownik z kolumnami jakie chcemy na wyjściu
3. Tworzymy nową kolumnę w bazie fraz z pkt 2, będącą kopią listy fraz
4. Wrzucamy kolumnę z kopią fraz w funkcję do wyciągnięcia podstawowej formy frazy - lemmatizer
5. Grupujemy frazy z pkt 2 po URLach (dla 1 URLa wyciągamy wszystkie frazy przypisane do niego)
6. Tworzymy Matcher z ww. punktu w formie listy
7. Na podstawie wcześniej uzyskanych danych (1.) oraz matchera  tworzymy wiersz wynikowy dla 2 sparowanych URLi
   dla słownika z pkt 2.
8. Zapisujemy

"""
import requests
import pandas as pd
import spacy
from spacy.matcher import PhraseMatcher
from bs4 import BeautifulSoup


# Załadowanie silnika spacy
nlp = spacy.load("pl_core_news_sm")

# url_list = []
phrase_database = pd.read_excel('Input/')


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


# funkcja zwracająca podstawową formę danej frazy
def lemmatizer(phrase):
    doc = nlp(phrase['Fraza'])
    result = ""
    for token in doc:
        result += f"{token.lemma_} "
    return result[:-1]


# Za pomocą ww funkcji dodajemy nową kolumnę z podstawową formą frazy
phrase_database['Lemma'] = phrase_database.apply(lemmatizer, axis=1)

# wyodrębnienie wszystkich docelowych URLi
destination_url_list = phrase_database['URL'].unique()


for d_url in destination_url_list:
    # zainicjowanie pustego matchera z atrubutem lemma - szuka podstawowych form dla każdego tokenu
    matcher = PhraseMatcher(nlp.vocab, attr="LEMMA")
    # zrzutowanie fraz przyporządkowanych do danego URLa na urla
    phrase_list = list(phrase_database['Lemma'][phrase_database['URL'] == d_url])
    # tworzenie patternów na podstawie silnika nlp
    phrase_patterns = [nlp(text) for text in phrase_list]

    placeholder = ""
    doc = nlp(placeholder)

    # tworzymy obiekt ze znalezionymi (lub nie) frazami w tekście
    found_matches = matcher(doc)

    for match_id, start, end in found_matches:  # tuple unpacking - potrzebujemy tylko start oraz end
        phrase = doc[start:end]     # fraza pokrewna znaleziona w tekście
        span = doc[start - 5:end + 6]   # tworzenie kontekstu dla znalezionej frazy
        print(phrase, span.text)

# mechanizm dopisujący dane do istniejącego excela
# with pd.ExcelWriter('path_to_file.xlsx', mode='a') as writer:
#     df.to_excel(writer, sheet_name='Scheet1')
