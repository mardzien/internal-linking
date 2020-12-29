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
    lemmatizer_start = time.time()

    phrase_database = pd.read_excel(filepath, engine="openpyxl")
    phrase_database['Lemma'] = phrase_database.apply(partial(lemmatizer, nlp_model), axis=1)
    phrase_database = phrase_database.drop_duplicates(subset=['URL', 'Lemma'])
    phrase_database.to_excel("Lemmas.xlsx")

    print("Stworzono df z frazami lemma.")

    lemmatizer_end = time.time()
    lemmatizer_time = lemmatizer_end - lemmatizer_start

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


def process_url(nlp_model, database_df, destination_url_list, input_class, url):
    tokenization_start = time.time()

    # print(f'URL {url_idx} z {urls_count}')
    # print(f'Zapisano {counter} wierszy w raporcie.')

    # http_start = time.time()
    url_info = get_information_from_soup(url=url, input_class=input_class)
    # http_stop = time.time()
    # http_delta = http_stop - http_start
    # print(f"HTTP DELTA: {http_delta}s")
    text = url_info['Tekst']

    document = nlp_model(text)

    # tokenization_stop = time.time()
    # tokenization_delta = tokenization_stop - tokenization_start
    # print("Tokenization delta:", tokenization_delta)
    # tokenization_time += tokenization_delta

    for d_url in destination_url_list:
        # TODO: Context of measuring finding a match
        # finding_match_time_start = time.time()

        if url == d_url:
            continue  # przerwanie pętli, żeby nie szukać dopasowań na siebie.

        # zrzutowanie fraz przyporządkowanych do danego URLa na urla
        # tworzenie patternów na podstawie silnika nlp
        phrase_list = list(database_df['Lemma'][database_df['URL'] == d_url])
        phrase_patterns = [nlp_model(text) for text in phrase_list]

        # zainicjowanie pustego matchera z atrubutem lemma - szuka podstawowych form dla każdego tokenu
        matcher = PhraseMatcher(nlp_model.vocab, attr="LEMMA")
        # TODO: A może matcher powinien mieć id = d_url i nie musimy go inicjalizować za każdym razem w pętli?
        matcher.add('Szukacz', None, *phrase_patterns)

        # tworzymy obiekt ze znalezionymi (lub nie) frazami w tekście
        found_matches = matcher(document)
        # finding_match_time_stop = time.time()
        # finding_match_time += finding_match_time_stop - finding_match_time_start
        # TODO: Close context of measuring finding a match

        # TODO: Context of measuring writing to excel (writing what?)
        # writing_to_excel_start = time.time()

        if len(found_matches) == 0:
            pass
        else:
            # TODO: Looks like match_id is not used anywhere
            rows = []
            for match_id, start, end in found_matches:  # tuple unpacking - potrzebujemy tylko start oraz end
                # TODO: lock! Removed counter for now to simplify the process

                phrase = document[start:end]  # fraza pokrewna znaleziona w tekście
                span = document[start - 5:end + 6]  # tworzenie kontekstu dla znalezionej frazy

                # TODO: Probably the result of incoming process
                list_row = [url, d_url, phrase.text, span.text]
                rows.append(list_row)

                # TODO: LOCK or send to synchronized queue
                # append_list_to_excel(filename='Output/Raport linkowania.xlsx',
                #                      list_name=list_row,
                #                      sheet_name='Raport')

        # writing_to_excel_stop = time.time()
        # writing_to_excel_time += writing_to_excel_stop - writing_to_excel_start
        # TODO: End context of measuring writing to excel (writing what?)



# append_list_to_excel(filename='Output/Raport linkowania.xlsx',
#                      list_name=list_row,
#                      sheet_name='Raport')


def create_inlinks_report(nlp_model, source_url_list, database_df, input_class):
    # counter = 0

    # wyodrębnienie wszystkich docelowych URLi
    destination_url_list = database_df['URL'].unique()

    # TODO: Determine shared state between processes
    # tokenization_time = 0
    # finding_match_time = 0
    # writing_to_excel_time = 0

    target = partial(
        process_url,
        nlp_model, database_df, destination_url_list, input_class
    )

    proc_num = mp.cpu_count() - 1

    # results = list(map(target, source_url_list))

    mp.set_start_method('spawn', True)

    with mp.Pool(8) as p:
        results = p.map(target, source_url_list)

    print(f'Processed {len(results)} results')

    return results
    # return tokenization_time, finding_match_time, writing_to_excel_time


if __name__ == '__main__':
    overall_start = time.time()

    lang_model = load_nlp_model("pl_core_news_sm")
    url_list = load_url_list("Input/url_list2.txt")
    df_phrases = prepare_input_phrases_with_lemmas(lang_model, "Input/asd.xlsx")
    prepare_output_sheet('Output/Raport linkowania.xlsx')

    # tokenization_time, finding_match_time, writing_to_excel_time = \
    #     create_inlinks_report(queue, lang_model, url_list, df_phrases, input_class='entry-content')

    create_inlinks_report(lang_model, url_list, df_phrases, input_class='entry-content')

    print("Finished multiprocessing!")

    overall_stop = time.time()
    overall_time = overall_stop - overall_start

    print(f"Całkowity czas działania: {overall_time} s.")


# TODO: Collect metrics and report them
# print(f"Czas wczytania silnika nlp: {nlp_time} s.")
# print(f"Czas stworzenia kolumny z podstawową formą frazy: {lemmatizer_time} s.")
# print(f"Czas wczytania tekstu z URLa wraz z tokenizacją: {tokenization_time} s.")
# print(f"Czas działania matchera: {finding_match_time} s.")
# print(f"Czas zapisytania do excela: {writing_to_excel_time} s.")
