# the main algorithms for getting and entering articles/books/other media into the database
import sqlite3

# DB Management
conn = sqlite3.connect("resources/sqlite/corpus.sqlite")
c = conn.cursor()

import sys
import os
sys.path.insert(0, "")

import langreader.sort.svm as svm

def get_corpus_length(language='english'):
    c.execute('SELECT COUNT(order_string) FROM Repository WHERE language = ?', (language,))
    print('get_corpus_length')
    return c.fetchone()[0]


def get_text_from_index(index):
    c.execute('SELECT article_text from Repository WHERE order_string IS NOT null ORDER BY order_string LIMIT 1 OFFSET ?', (index,))
    print('get_text_from_index')
    return c.fetchone()[0]


def get_order_string_from_index(index):
    c.execute('SELECT order_string from Repository WHERE order_string IS NOT null ORDER BY order_string LIMIT 1 OFFSET ?', (index,))
    print('get_order_string_from_index')
    return c.fetchone()[0]


def get_two_order_strings_from_index(index):
    c.execute('SELECT order_string from Repository WHERE order_string IS NOT null ORDER BY order_string LIMIT 2 OFFSET ?', (index-1,))
    print('get_two_order_strings_from_index')
    return [i[0] for i in c.fetchall()]


def insert_with_order_string(article_title, article_text, order_string):
    c.execute('INSERT INTO Repository(article_title, article_text, order_string) VALUES (?, ?, ?)', (article_title, article_text, order_string))
    print('insert_with_order_string')
    conn.commit()


def insert_in_corpus(title, text, k_max, language='english'):
    insert_at_index(title, text, bin_search_corpus(text, k_max, language))


def insert_at_index(title, text, index):
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
        
        insert_with_order_string(title, text, find_middle_index(bottom_order, top_order))


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

if __name__ == '__main__':
    #testing purposes
    insert_in_corpus('A VERY DELICIOUS TEST','testing, testing, testing', 2)