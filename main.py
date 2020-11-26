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

import pandas as pd
import spacy
from spacy.matcher import PhraseMatcher
import openpyxl

from scrape import get_information_from_soup
import files


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
    from openpyxl import load_workbook

    import pandas as pd

    # ignore [engine] parameter if it was passed
    if 'engine' in to_excel_kwargs:
        to_excel_kwargs.pop('engine')

    writer = pd.ExcelWriter(filename, engine='openpyxl')

    # Python 2.x: define [FileNotFoundError] exception if it doesn't exist
    try:
        FileNotFoundError
    except NameError:
        FileNotFoundError = IOError


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

# Załadowanie silnika spacy
nlp = spacy.load("pl_core_news_sm")

# dane wejściowe
url_list = files.load_file_to_list("Input/url_list.txt")
phrase_database = pd.read_excel("Input/Raport Pozycje - medifem.pl.xlsx")


df_row = pd.DataFrame(columns=['URL źródłowy',
                               'URL docelowy',
                               'Słowo kluczowe',
                               'Kontekst'])

with pd.ExcelWriter('Output/Raport linkowania.xlsx') as writer:
    df_row.to_excel(writer, sheet_name='Raport')


# funkcja zwracająca podstawową formę danej frazy
def lemmatizer(phrase):
    doc = nlp(phrase['Słowo kluczowe'])
    result = ""
    for token in doc:
        result += f"{token.lemma_} "
    return result[:-1]


# Za pomocą ww funkcji dodajemy nową kolumnę z podstawową formą frazy
phrase_database['Lemma'] = phrase_database.apply(lemmatizer, axis=1)


def create_inlinks_report(source_url_list, database_df, input_class):

    counter = 0
    # wyodrębnienie wszystkich docelowych URLi
    destination_url_list = phrase_database['URL'].unique()

    for url in source_url_list:
        url_info = get_information_from_soup(url=url, input_class=input_class)
        tekst = url_info['Tekst']

        print(tekst)

        document = nlp(tekst)

        for d_url in destination_url_list:
            if url == d_url:
                continue
            # zainicjowanie pustego matchera z atrubutem lemma - szuka podstawowych form dla każdego tokenu
            matcher = PhraseMatcher(nlp.vocab, attr="LEMMA")
            # zrzutowanie fraz przyporządkowanych do danego URLa na urla
            phrase_list = list(phrase_database['Lemma'][phrase_database['URL'] == d_url])
            # tworzenie patternów na podstawie silnika nlp
            phrase_patterns = [nlp(text) for text in phrase_list]
            matcher.add('Szukacz', None, *phrase_patterns)

            # tworzymy obiekt ze znalezionymi (lub nie) frazami w tekście
            found_matches = matcher(document)
            print('***************')
            print(len(found_matches))

            if len(found_matches) != 0:

                for match_id, start, end in found_matches:  # tuple unpacking - potrzebujemy tylko start oraz end
                    counter += 1
                    phrase = document[start:end]     # fraza pokrewna znaleziona w tekście
                    span = document[start - 5:end + 6]   # tworzenie kontekstu dla znalezionej frazy

                    dict_row = {'URL źródłowy': url,
                                'URL docelowy': d_url,
                                'Słowo kluczowe': phrase.text,
                                'Kontekst': span.text}
                    list_row = [url, d_url, phrase.text, span.text]
                    # df_row = pd.DataFrame([url, d_url, phrase.text, span.text]).transpose()
                    print(dict_row)
                    print(df_row)

                    # mechanizm dopisujący dane do istniejącego excela
                    # with pd.ExcelWriter('Output/Raport linkowania.xlsx', engine='openpyxl', mode='a') as writer:
                    #     df_row.to_excel(writer, sheet_name='Raport', )
                    # append_df_to_excel(filename='Output/Raport linkowania.xlsx', df=df_row, sheet_name='Raport', )
                    append_list_to_excel(filename='Output/Raport linkowania.xlsx', list_name=list_row,
                                         sheet_name='Raport')


create_inlinks_report(url_list, phrase_database, input_class='page-content')
