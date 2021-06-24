import sqlite3
import pickle

import sys
import os
sys.path.insert(0, "")

import langreader.app.corpus as corpus
import pandas as pd

def get_str_index(index):
    if index == 0:
        return 'ac'
    initial_int = 97 # corresponds to 'a'
    index1 = index // 4
    index2 = index % 4
    char2 = ''
    if index2 == 1:
        char2 = 'f'
    elif index2 == 2:
        char2 = 'm'
    elif index2 == 3:
        char2 = 's'
    return chr(initial_int + index1) + char2

if __name__ == '__main__':
    # conn = sqlite3.connect("resources/sqlite/corpus.sqlite")
    # c = conn.cursor()

    # a = pickle.load(open('langreader/sort/resources/poems.p', 'rb'))

    # index = 0
    # for text, title, author in a:
    #     c.execute('INSERT INTO Repository(article_title, article_text, order_string, article_author) VALUES (?, ?, ?, ?)', (title.strip(), text, get_str_index(index), author))
    #     index += 1
    #     conn.commit()
    #     print('inserted', index)
    # print('done')
    df = pd.DataFrame(pd.read_csv('resources/poems/PoetryFoundationData.csv'), columns=['Poem', 'Title', 'Poet'])
    index = 945
    for text, title, author in list(df.to_records(index=False))[945:]:
        corpus.insert_in_corpus(title, text, 2, author=author)
        print(index)
        index += 1