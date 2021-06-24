# the main algorithms for getting and entering articles/books/other media into the database
import sqlite3

# DB Management
conn = sqlite3.connect("resources/sqlite/corpus.sqlite", check_same_thread=False)
c = conn.cursor()

import sys
import os
sys.path.insert(0, "")

import langreader.sort.svm as svm
from bs4 import BeautifulSoup
import requests

from gutenberg.acquire import load_etext
from gutenberg.query import get_metadata
from gutenberg.cleanup import strip_headers

# --get methods--
def get_corpus_length(language='english'):
    c.execute('SELECT COUNT(order_string) FROM Repository WHERE language = ?', (language,))
    # c.execute('SELECT COUNT(order_string) FROM Repository WHERE language = ? AND text_type = "gutenberg"', (language,))
    print('get_corpus_length')
    return c.fetchone()[0]


def get_text_from_index(index):
    c.execute('SELECT article_text, article_url, text_type FROM Repository WHERE order_string IS NOT null ORDER BY order_string LIMIT 1 OFFSET ?', (index,))
    # c.execute('SELECT article_text, article_url, text_type FROM Repository WHERE order_string IS NOT null AND text_type = "gutenberg" ORDER BY order_string LIMIT 1 OFFSET ?', (index,))
    print('get_text_from_index', end=' ', flush=True)
    result = c.fetchone()
    # 0 is the text
    # 1 is the url
    # 2 is the text type

    if result[2] == 'gutenberg':
        print(result[1])
        return strip_headers(load_etext(int(result[1]))).strip()
    
    if result[0] is None:
        print(result[1])
        page = requests.get(result[1])
        soup = BeautifulSoup(page.content, 'html.parser')
        return soup.get_text()

    print()
    
    return result[0]


def get_title_from_index(index):
    c.execute('SELECT article_title FROM Repository WHERE order_string IS NOT null ORDER BY order_string LIMIT 1 OFFSET ?', (index,))
    # c.execute('SELECT article_title FROM Repository WHERE order_string IS NOT null AND text_type = "gutenberg" ORDER BY order_string LIMIT 1 OFFSET ?', (index,))
    print('get_title_from_index')
    return c.fetchone()[0]


def get_all_from_index(index):
    # c.execute('SELECT * FROM Repository WHERE order_string IS NOT null ORDER BY order_string LIMIT 1 OFFSET ?', (index,))
    c.execute('SELECT * FROM Repository WHERE order_string IS NOT null AND text_type = "gutenberg" ORDER BY order_string LIMIT 1 OFFSET ?', (index,))
    print('get_all_from_index')
    return c.fetchone()


def get_order_string_from_index(index):
    c.execute('SELECT order_string FROM Repository WHERE order_string IS NOT null ORDER BY order_string LIMIT 1 OFFSET ?', (index,))
    # c.execute('SELECT order_string FROM Repository WHERE order_string IS NOT null AND text_type = "gutenberg" ORDER BY order_string LIMIT 1 OFFSET ?', (index,))
    print('get_order_string_from_index')
    return c.fetchone()[0]


def get_two_order_strings_from_index(index):
    c.execute('SELECT order_string FROM Repository WHERE order_string IS NOT null ORDER BY order_string LIMIT 2 OFFSET ?', (index-1,))
    # c.execute('SELECT order_string FROM Repository WHERE order_string IS NOT null AND text_type = "gutenberg" ORDER BY order_string LIMIT 2 OFFSET ?', (index-1,))
    print('get_two_order_strings_from_index')
    return [i[0] for i in c.fetchall()]


def get_text(text_order_index):
    c.execute('SELECT article_text FROM Repository WHERE order_string = ?', (text_order_index,))
    return c.fetchone()[0]


def get_order_strings():
    c.execute('SELECT order_string FROM Repository ORDER BY order_string')
    # c.execute('SELECT order_string FROM Repository WHERE text_type = "gutenberg" ORDER BY order_string')
    return [i[0] for i in c.fetchall()]


# --insert methods--
def insert_with_order_string(article_title, article_text, order_string, article_url=None, article_author=None, language='english', text_type=None):
    if not article_url and not article_author:
        c.execute('INSERT OR IGNORE INTO Repository(article_title, article_text, order_string, language, text_type) VALUES (?, ?, ?, ?, ?)', (article_title, article_text, order_string, language, text_type))
    else:
        c.execute('INSERT OR IGNORE INTO Repository(article_title, article_text, order_string, article_url, article_author, language, text_type) VALUES (?, ?, ?, ?, ?, ?, ?)', (article_title, article_text, order_string, article_url, article_author, language, text_type))
    print('insert_with_order_string')
    # THIS METHOD DOES NOT COMMIT BY ITSELF; A SEPARATE CALL TO conn.commit() IS REQUIRED


# --sorting methods--
def reindex(): # unfinished
    c.execute('SELECT article_id FROM Repository WHERE order_string IS NOT NULL ORDER BY order_string')
    article_ids = [i[0] for i in c.fetchall()]

    for article_id, index in zip(article_ids, get_equally_spaced_indices(len(article_ids))):
        c.execute('UPDATE Repository SET order_string = ? WHERE article_id = ?', (index, article_id))
    
    conn.commit()
    

def get_equally_spaced_indices(corpus_length):
    # find the nearest maximum number of values that strings of max length n can represent
    letters_length = 1
    number_of_values = 26
    while number_of_values < corpus_length + 1:
        letters_length += 1 
        number_of_values = 27**letters_length - 27**(letters_length-1)
    
    # do integer division
    indices = []
    a_value = 27**(letters_length-1)
    for i in range(1, corpus_length + 1):
        indices.append(convert_from_base_27(int(number_of_values / (corpus_length + 1) * i) + a_value))
    return indices


def insert_texts(texts_list, exclude_text=False, index=0): # should be list of tuples length 10
    index_real = index
    for article_id, title, text, url, date_time_added, publisher_name, order_string, language, added_by, author in texts_list:
        insert_in_corpus(title, text, 2, language=language, url=url, author=author, exclude_text=False)
        print(index_real)
        index_real += 1
    conn.commit()


def insert_in_corpus(title, text, k_max, language='english', url=None, author=None, exclude_text=False, text_type=None):
    insert_at_index(title, text, bin_search_corpus(text, k_max, language), language=language, url=url, author=author, exclude_text=exclude_text, text_type=text_type)


def insert_at_index(title, text, index, language='english', url=None, author=None, exclude_text=False, text_type=None):
    corpus_length = get_corpus_length()
    if corpus_length == 0:
        insert_with_order_string(text, 'm')
    else:
        bottom_order = ''
        top_order = ''

        if index == 0:
            bottom_order = 'a'
            top_order = get_order_string_from_index(index)     
        elif index == corpus_length:
            bottom_order = get_order_string_from_index(index - 1)
            top_order = 'z' * len(bottom_order)
        else:
            order_strings = get_two_order_strings_from_index(index)
            bottom_order = order_strings[0]
            top_order = order_strings[1]
        
        if exclude_text:
            actual_text = None
        else:
            actual_text = text
        insert_with_order_string(title, actual_text, find_middle_index(bottom_order, top_order), article_url=url, article_author=author, language=language, text_type=text_type)


def find_middle_index(index1, index2): # index1 and index2 are strings!!
    if index1 == index2:
        raise Exception('index1 and index2 should not be the same index')
    
    max_length = max(len(index1), len(index2))
    integer1 = convert_to_base_27(index1, max_length)
    integer2 = convert_to_base_27(index2, max_length)
    if abs(integer1 - integer2) == 1:
        integer1 *= 27
        integer2 *= 27

    return convert_from_base_27((integer1 + integer2) // 2)


def bin_search_corpus(text, k_max, language='english'):
    bottom = 0
    top = get_corpus_length(language=language) - 1
    middle = (top + bottom) // 2
    k = k_max
    rfv_text = v.relative_frequency_vector(text)
    
    while top >= bottom:
        # if k is too big, which would make the index i out of bounds, then set k to the maximum
        # value it can be
        if k > (top - bottom) // 2:
            k = (top - bottom) // 2
        difficult_texts = 0 
        for i in range(middle - k, middle + k + 1):
            if compare(rfv_text, v.relative_frequency_vector(get_text_from_index(i))) < 0:
                difficult_texts += 1
        if difficult_texts > k: 
            top = middle - 1
        else:
            bottom = middle + 1
        middle = (top + bottom) // 2
    
    # print('result: ' + str(bottom))
    return bottom


def compare(rfv_text1, rfv_text2):
    return svm.compare(rfv_text1, rfv_text2)


# --helper methods--
def find_gutenberg_url(ebook_code):
    url_list = get_metadata('formaturi', ebook_code)
    url = [s for s in url_list if ".html.images" in s]
    if len(url) == 0:
        url = [s for s in url_list if ".html" in s]
    if len(url) == 0:
        url = [s for s in url_list if ".htm" in s]
    print(url, end=' ', flush=True)
    if len(url) == 0:
        # print(get_metadata('formaturi', ebook_code), end=' ')
        raise NameError('no html files found')
    return url[0]


def convert_from_base_27(integer):
    string = ''
    real_integer = integer
    while real_integer > 0:
        string = value_letter(real_integer % 27) + string
        real_integer //= 27
    return string.strip()


def convert_to_base_27(string, total_length):
    if (len(string) > total_length):
        raise Exception('the total_length of the string should be bigger than the length of the string')
    real_string = string
    real_string += ' ' * (total_length - len(string))
    total = 0
    for letter in real_string:
        total *= 27
        total += letter_value(letter)
    return total
        

def letter_value(char):
    if char not in ' abcdefghijklmnopqrstuvwxyz':
        raise Exception('this char is not supported')
    if char == ' ':
        return 0
    else:
        return ord(char) - 96


def value_letter(integer):
    if integer > 26 or integer < 0:
        raise Exception('letter should be between 0 and 26 inclusive')
    if integer == 0:
        return ' '
    else:
        return chr(integer + 96)


# --temporary methods--
# remove all the whitespace from the poem titles
def update_titles():
    c.execute('SELECT article_title FROM Repository')
    titles_list = c.fetchall()

    c.executemany('UPDATE Repository SET article_title = ? WHERE article_title = ?', [(title[0].strip(),title[0]) for title in titles_list])
    conn.commit()


if __name__ == '__main__':
    # testing purposes
    pass