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


# --get methods--
def get_corpus_length(language='english'):
    c.execute('SELECT COUNT(order_string) FROM Repository WHERE language = ?', (language,))
    print('get_corpus_length')
    return c.fetchone()[0]


def get_text_from_index(index):
    print('SELECT article_text, article_url from Repository WHERE order_string IS NOT null ORDER BY order_string LIMIT 1 OFFSET ' + str(index))
    c.execute('SELECT article_text, article_url from Repository WHERE order_string IS NOT null ORDER BY order_string LIMIT 1 OFFSET ?', (index,))
    print('get_text_from_index')
    result = c.fetchone()
    # 0 is the text
    # 1 is the url
    if c.fetchone()[0] is None:
        page = requests.get(c.fetchone[1])
        soup = BeautifulSoup(page.content, 'html.parser')
        return soup.get_text()
    return c.fetchone()[0]


def get_title_from_index(index):
    c.execute('SELECT article_title from Repository WHERE order_string IS NOT null ORDER BY order_string LIMIT 1 OFFSET ?', (index,))
    print('get_title_from_index')
    return c.fetchone()[0]


def get_all_from_index(index):
    c.execute('SELECT * from Repository WHERE order_string IS NOT null ORDER BY order_string LIMIT 1 OFFSET ?', (index,))
    print('get_all_from_index')
    return c.fetchone()


def get_order_string_from_index(index):
    c.execute('SELECT order_string from Repository WHERE order_string IS NOT null ORDER BY order_string LIMIT 1 OFFSET ?', (index,))
    print('get_order_string_from_index')
    return c.fetchone()[0]


def get_two_order_strings_from_index(index):
    c.execute('SELECT order_string from Repository WHERE order_string IS NOT null ORDER BY order_string LIMIT 2 OFFSET ?', (index-1,))
    print('get_two_order_strings_from_index')
    return [i[0] for i in c.fetchall()]


def get_text(text_order_index):
    c.execute('SELECT article_text FROM Repository WHERE order_string = ?', (text_order_index,))
    return c.fetchone()[0]


def get_order_strings():
    c.execute('SELECT order_string FROM Repository ORDER BY order_string')
    return [i[0] for i in c.fetchall()]


# --insert methods--
def insert_with_order_string(article_title, article_text, order_string, article_url=None, article_author=None, language='english'):
    if not article_url and not article_author:
        c.execute('INSERT INTO Repository(article_title, article_text, order_string, language) VALUES (?, ?, ?, ?)', (article_title, article_text, order_string, language))
    else:
        c.execute('INSERT INTO Repository(article_title, article_text, order_string, article_url, article_author, language) VALUES (?, ?, ?, ?, ?, ?)', (article_title, article_text, order_string, article_url, article_author, language))
    print('insert_with_order_string')
    conn.commit()


# --sorting methods--
def insert_in_corpus(title, text, k_max, language='english', url=None, author=None, exclude_text=False):
    insert_at_index(title, text, bin_search_corpus(text, k_max, language), language=language, url=url, author=author, exclude_text=exclude_text)


def insert_at_index(title, text, index, language='english', url=None, author=None, exclude_text=False):
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
        insert_with_order_string(title, actual_text, find_middle_index(bottom_order, top_order), article_url=url, article_author=author, language=language)


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
    
    while top >= bottom:
        # if k is too big, which would make the index i out of bounds, then set k to the maximum
        # value it can be
        if k > (top - bottom) // 2:
            k = (top - bottom) // 2
        difficult_texts = 0 
        for i in range(middle - k, middle + k + 1):
            if compare(text, get_text_from_index(i)) < 0:
                difficult_texts += 1
        if difficult_texts > k: 
            top = middle - 1
        else:
            bottom = middle + 1
        middle = (top + bottom) // 2
    
    print('result: ' + str(bottom))
    return bottom


def compare(text1, text2):
    return svm.compare(text1, text2)


# --helper methods--
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