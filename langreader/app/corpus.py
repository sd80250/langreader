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

# from gutenberg.acquire import load_etext
# from gutenberg.query import get_metadata
# from gutenberg.cleanup import strip_headers

import langreader.sort.vectorize as v

order_strings = None
corpus_length = -1
# --get methods--

# returns an integer of the number of rows with an order_string
def get_corpus_length(text_type, language='english'):
    c.execute('SELECT COUNT(order_string) FROM Repository WHERE language = ? AND text_type = ? ', (language, text_type))
    print('get_corpus_length')
    return c.fetchone()[0]


# returns a tuple of the index in question
def get_all_from_index(text_type, index, language='english'):
    c.execute('SELECT * FROM Repository WHERE language = ? AND text_type = ? AND order_string IS NOT null ORDER BY order_string LIMIT 1 OFFSET ?', (language, text_type, index))
    print('get_all_from_index')
    return c.fetchone()


# returns a tuple of the order_string in question (faster this way)
def get_all(text_type, order_string, language='english'):
    c.execute('SELECT * FROM Repository WHERE language = ? AND text_type = ? AND order_string = ?', (language, text_type, order_string))
    # print('get_all')
    return c.fetchone()


# returns a list of order strings in order (convert index to order_string)
def get_order_strings(text_type, language='english'):
    c.execute('SELECT order_string FROM Repository WHERE language = ? AND text_type = ? ORDER BY order_string', (language, text_type))
    print('get_order_strings')
    return [i[0] for i in c.fetchall()]


# --insert methods--
def resort(text_type, language = 'english'):
    # get all values from text_type
    c.execute('SELECT * FROM Repository WHERE language = ? AND text_type = ?', (language, text_type))
    texts_list = [list(i) for i in c.fetchall()]
    # print(texts_list[0])
    # quit()

    # delete text_type
    c.execute('DELETE FROM Repository WHERE language = ? AND text_type = ?', (language, text_type))
    
    # reinsert text_type
    print('inserting texts... ', end='', flush=True)
    insert_texts(texts_list, text_type)
    print('done')

    conn.commit()


# values should be an 11-tuple
# THIS METHOD DOES NOT COMMIT BY ITSELF; A SEPARATE CALL TO conn.commit() IS REQUIRED
def insert(values): # returns true if command executed successfully; else returns false
    values_modified = (values[1], values[2], values[3], values[5], \
        values[6], values[7], values[8], values[9], values[10])
    try:
        c.execute('INSERT INTO Repository VALUES (null, ?, ?, ?, datetime("now"), ?, ?, ?, ?, ?, ?)', values_modified)
        return True
    except Exception as e:
        print('insert failed:', repr(e))
        return False
    # print('insert')


# --sorting methods--
def reindex(text_type):
    c.execute('SELECT article_id FROM Repository WHERE order_string IS NOT NULL AND text_type = ? ORDER BY order_string', (text_type,))
    article_ids = [i[0] for i in c.fetchall()]

    for article_id, index in zip(article_ids, get_equally_spaced_indices(len(article_ids))):
        c.execute('UPDATE Repository SET order_string = ? WHERE article_id = ? AND text_type = ?', (index, article_id, text_type))
    
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


# ALL TEXTS SHOULD BE OF THE SAME TEXT TYPE
def insert_texts(texts_list, text_type, exclude_text=False, index=0): # should be an iterable of lists length 11
    global order_strings
    order_strings = get_order_strings(text_type)
    global corpus_length
    corpus_length = get_corpus_length(text_type)

    index_real = index
    for parameters in texts_list:
        index_real += 1
        print('inserting', text_type + ":", index_real, flush=True)
        insert_in_corpus(parameters, 2, exclude_text=exclude_text)
    print('done\n')
    conn.commit()


# order_strings AND corpus_length SHOULD BE SET BEFORE THIS METHOD IS CALLED!
# THIS METHOD DOES NOT COMMIT BY ITSELF; A SEPARATE CALL TO conn.commit() IS REQUIRED
def insert_in_corpus(parameters, k_max, exclude_text=False):
    # 2 > article_text; 10 > text_type
    insert_at_index(parameters, bin_search_corpus(parameters[2], k_max, parameters[10]), exclude_text=exclude_text)


# order_strings AND corpus_length SHOULD BE SET BEFORE THIS METHOD IS CALLED!
# THIS METHOD DOES NOT COMMIT BY ITSELF; A SEPARATE CALL TO conn.commit() IS REQUIRED
def insert_at_index(parameters, index, exclude_text=False):
    global order_strings
    global corpus_length
    if corpus_length == 0:
        parameters[6] = 'm' # 6 > order_string
        if insert(parameters):
            order_strings = ['m']
            corpus_length = len(order_strings)
    else:
        # EXAMPLE:
        #  0 1 2 3 4
        # ^
        # if index == 0, I would want to insert text there
        #  0 1 2 3 4
        #           ^
        # if index == 5, I would want to insert text there
        #  0 1 2 3 4
        #   ^
        # if index == 1, I would want to insert text there
        if index == 0:
            bottom_order = 'a'
            top_order = order_strings[index]     
        elif index == corpus_length:
            bottom_order = order_strings[index-1]
            top_order = 'z' * len(bottom_order)
        else:
            bottom_order = order_strings[index-1]
            top_order = order_strings[index]
        
        new_string = find_middle_index(bottom_order, top_order)
        parameters[6] = new_string # 6 > order_string
        
        if exclude_text:
            parameters[2] = None # 2 > article_text

        if insert(parameters):
            order_strings.insert(index, new_string)
            corpus_length = len(order_strings)


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


# order_strings AND corpus_length SHOULD BE SET BEFORE THIS METHOD IS CALLED!
def bin_search_corpus(text, k_max, text_type, language='english'):
    global order_strings
    global corpus_length

    bottom = 0
    top = corpus_length - 1
    middle = (top + bottom) // 2
    k = k_max
    rfv_text = v.relative_frequency_vector(text)
    new_characteristics = v.get_new_characteristics(text, v.preprocess(text))
    
    while top >= bottom:
        # if k is too big, which would make the index i out of bounds, then set k to the maximum
        # value it can be
        if k > (top - bottom) // 2:
            k = (top - bottom) // 2
        difficult_texts = 0 
        for i in range(middle - k, middle + k + 1):
            if svm.compare(rfv_text, new_characteristics, get_all(text_type, order_strings[i])[2]) < 0: # 2 > article_text
                difficult_texts += 1
        if difficult_texts > k: 
            top = middle - 1
        else:
            bottom = middle + 1
        middle = (top + bottom) // 2
    
    # print('result: ' + str(bottom))
    return bottom



# --helper methods--
# def find_gutenberg_url(ebook_code):
#     url_list = get_metadata('formaturi', ebook_code)
#     url = [s for s in url_list if ".html.images" in s]
#     if len(url) == 0:
#         url = [s for s in url_list if ".html" in s]
#     if len(url) == 0:
#         url = [s for s in url_list if ".htm" in s]
#     print(url, end=' ', flush=True)
#     if len(url) == 0:
#         # print(get_metadata('formaturi', ebook_code), end=' ')
#         raise NameError('no html files found')
#     return url[0]


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
def update_titles(text_type):
    c.execute('SELECT article_title FROM Repository WHERE text_type = ?', (text_type,))
    titles_list = c.fetchall()

    c.executemany('UPDATE Repository SET article_title = ? WHERE article_title = ? AND text_type = ?', [(title[0].strip(),title[0], text_type) for title in titles_list])
    conn.commit()


if __name__ == '__main__':
    # testing purposes
    reindex('short_story')