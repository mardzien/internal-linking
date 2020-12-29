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
from functools import partial

import pandas as pd
import spacy
from spacy.matcher import PhraseMatcher
import openpyxl
import time

from scrape import get_information_from_soup
import files
from openpyxl import load_workbook

import multiprocessing as mp

import metrics as m


def load_nlp_model(name: str):
    """
    Args:
        name: Language model name
    Returns: Language model object
    """
    nlp_start = time.time()
    nlp = spacy.load(name)
    nlp_end = time.time()
    nlp_time = nlp_end - nlp_start
    print(f"Wczytano silnik nlp w {nlp_time} s.")
    return nlp


def load_url_list(filepath: str):
    return files.load_file_to_list(filepath)


# funkcja zwracająca podstawową formę danej frazy
def lemmatizer(nlp_model, phrase):
    doc = nlp_model(str(phrase['Słowo kluczowe']))    # rzutowanie na stringa. Wartości liczbowe mogą być wczytywane jako float.
    result = ""
    for token in doc:
        result += f"{token.lemma_} "
    return result[:-1]


def prepare_input_phrases_with_lemmas(nlp_model, filepath: str):
    """
    Loads xlsx file into pandas dataframe and adds lemmas in new column.

    Args:
        nlp_model: Language model
        filepath: Path to xlsx file

    Returns: Pandas dataframe
    """
    phrase_database = pd.read_excel(filepath, engine="openpyxl")
    phrase_database['Lemma'] = phrase_database.apply(partial(lemmatizer, nlp_model), axis=1)
    phrase_database = phrase_database.drop_duplicates(subset=['URL', 'Lemma'])
    phrase_database.to_excel("Tmp/Lemmas.xlsx")
    return phrase_database


def prepare_output_sheet(filepath):
    df_row = pd.DataFrame(columns=['URL źródłowy', 'URL docelowy', 'Słowo kluczowe', 'Kontekst'])
    with pd.ExcelWriter(filepath) as writer:
        df_row.to_excel(writer, sheet_name='Raport')


# TODO: Excel and dataframe part

def append_list_to_excel(filename, list_name, sheet_name):
    columns = "BCDE"
    wb = openpyxl.load_workbook(filename)
    sheet = wb.get_sheet_by_name(sheet_name)
    row_number = sheet.max_row
    sheet[f'A{row_number+1}'] = row_number
    for i, column in enumerate(columns):
        sheet[f'{column}{row_number+1}'] = list_name[i]
    wb.save(filename)


def append_df_to_excel(filename, df, sheet_name='Sheet1', startrow=None,
                       truncate_sheet=False,
                       **to_excel_kwargs):
    """
    Append a DataFrame [df] to existing Excel file [filename]
    into [sheet_name] Sheet.
    If [filename] doesn't exist, then this function will create it.

    Parameters:
      filename : File path or existing ExcelWriter
                 (Example: '/path/to/file.xlsx')
      df : dataframe to save to workbook
      sheet_name : Name of sheet which will contain DataFrame.
                   (default: 'Sheet1')
      startrow : upper left cell row to dump data frame.
                 Per default (startrow=None) calculate the last row
                 in the existing DF and write to the next row...
      truncate_sheet : truncate (remove and recreate) [sheet_name]
                       before writing DataFrame to Excel file
      to_excel_kwargs : arguments which will be passed to `DataFrame.to_excel()`
                        [can be dictionary]

    Returns: None
    """

    # ignore [engine] parameter if it was passed
    if 'engine' in to_excel_kwargs:
        to_excel_kwargs.pop('engine')

    writer = pd.ExcelWriter(filename, engine='openpyxl')

    try:
        # try to open an existing workbook
        writer.book = load_workbook(filename)

        # get the last row in the existing Excel sheet
        # if it was not specified explicitly
        if startrow is None and sheet_name in writer.book.sheetnames:
            startrow = writer.book[sheet_name].max_row

        # truncate sheet
        if truncate_sheet and sheet_name in writer.book.sheetnames:
            # index of [sheet_name] sheet
            idx = writer.book.sheetnames.index(sheet_name)
            # remove [sheet_name]
            writer.book.remove(writer.book.worksheets[idx])
            # create an empty sheet [sheet_name] using old index
            writer.book.create_sheet(sheet_name, idx)

        # copy existing sheets
        writer.sheets = {ws.title:ws for ws in writer.book.worksheets}
    except FileNotFoundError:
        # file does not exist yet, we will create it
        pass

    if startrow is None:
        startrow = 0

    # write out the new sheet
    df.to_excel(writer, sheet_name, startrow=startrow, **to_excel_kwargs)

    # save the workbook
    writer.save()


# TODO: The function name is bad, because it doesn't tell too much about what it's doing FIXME.
def process_url(nlp_model, matchers, destination_url_list, input_class, url):
    # print("Processing url:", url)
    url_info = get_information_from_soup(url=url, input_class=input_class)
    text = url_info['Tekst']
    document = nlp_model(text)

    for d_url in destination_url_list:
        # print("Checking url:", d_url)
        if url == d_url:
            print(">>>>>>>>>> Self matched!")
            continue  # przerwanie pętli, żeby nie szukać dopasowań na siebie.

        matcher = matchers[d_url]
        found_matches = matcher(document)

        if len(found_matches) == 0:
            # print("Not found!")
            pass
        else:
            rows = []
            for match_id, start, end in found_matches:  # tuple unpacking - potrzebujemy tylko start oraz end
                phrase = document[start:end]  # fraza pokrewna znaleziona w tekście
                span = document[start - 5:end + 6]  # tworzenie kontekstu dla znalezionej frazy
                list_row = [url, d_url, phrase.text, span.text]
                rows.append(list_row)
                # append_list_to_excel(filename='Output/Raport linkowania.xlsx',
                #                      list_name=list_row,
                #                      sheet_name='Raport')
            print(f">>>>>>>>>> Found {len(found_matches)} matches!")
    # print("Done")


def init_matchers(nlp_model, database_df, destination_urls):
    d = dict()
    mtr = m.Metrics('matcher')
    for url in destination_urls:
        mtr.start()
        phrase_list = list(database_df['Lemma'][database_df['URL'] == url])
        phrase_patterns = [nlp_model(text) for text in phrase_list]
        matcher = PhraseMatcher(nlp_model.vocab, attr="LEMMA")
        matcher.add(url, None, *phrase_patterns)
        d[url] = matcher
        mtr.stop()
    mtr.report()
    return d


def create_inlinks_report(nlp_model, source_url_list, database_df, input_class):
    mp.set_start_method('spawn', True)

    destination_url_list = database_df['URL'].unique()

    print("Initializing matchers")
    matchers = init_matchers(nlp_model, database_df, destination_url_list)
    print("Matchers initialized")

    target = partial(process_url, nlp_model, matchers, destination_url_list, input_class)

    # proc_num = mp.cpu_count() - 1

    with mp.Pool(10) as p:
        results = p.map(target, source_url_list)

    return results


if __name__ == '__main__':
    mo = m.Metrics('overall')
    mo.start()

    lang_model = load_nlp_model("pl_core_news_sm")
    url_list = load_url_list("Input1/url_list.txt")
    df_phrases = prepare_input_phrases_with_lemmas(lang_model, "Input1/Morele_ahrefs.xlsx")
    prepare_output_sheet('Output/report.xlsx')

    create_inlinks_report(lang_model, url_list, df_phrases, input_class='single-news-container')

    mo.stop()
    mo.report()



# TODO: Collect metrics and report them
# print(f"Czas wczytania silnika nlp: {nlp_time} s.")
# print(f"Czas stworzenia kolumny z podstawową formą frazy: {lemmatizer_time} s.")
# print(f"Czas wczytania tekstu z URLa wraz z tokenizacją: {tokenization_time} s.")
# print(f"Czas działania matchera: {finding_match_time} s.")
# print(f"Czas zapisytania do excela: {writing_to_excel_time} s.")
