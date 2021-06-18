import sqlite3
import pickle

def get_str_index(index):
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

conn = sqlite3.connect("corpus.sqlite")
c = conn.cursor()

a = pickle.load(open('../../resources/poems/poems.p', 'rb'))

index = 0
for text, title in a:
    c.execute('INSERT INTO Repository(article_title, article_text, order_string) VALUES (?, ?, ?)', (title, text, get_str_index(index)))
    index += 1
    conn.commit()
    print('inserted', index)
print('done')
