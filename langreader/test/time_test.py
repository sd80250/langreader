import numpy as np
import time
import langreader.app.corpus as corpus
import pandas as pd
import sqlite3

def dot_test(n, words):
    user_prof = np.random.uniform(-1, 1, (words,))
    texts_list = []
    for i in range(n):
        random_list = np.random.random_sample(size=(words,))
        adjusted_list = random_list / np.sum(random_list)
        texts_list.append(adjusted_list)
    results = []
    for text in texts_list:
        x = np.dot(user_prof, text)
        if x >= .95:
            result = 1 - (.95 - x)**2
        else:
            result = 1 - 16*(.95 - x)**2
        results.append(result)
    results.sort()

def time_dot_test(n, words):
    start = time.time()
    dot_test(n, words)
    print(time.time()-start)

def test_svm(n):
    corpus.c.execute('DELETE FROM Repository WHERE text_type = "poem" OR text_type = "test"')

    df = pd.DataFrame(pd.read_csv('resources/poems/PoetryFoundationData.csv'), columns=['Poem', 'Title', 'Poet'])
    texts_list = [[None, i[1], i[0], None, None, None, None, 'english', 1, i[2], "test"] for i in list(df.to_records(index=False))[0:n]]
    
    corpus.order_strings = corpus.get_order_strings('test')
    print(corpus.order_strings)
    corpus.corpus_length = corpus.get_corpus_length('test')

    index_real = 0
    for parameters in texts_list:
        index_real += 1
        print('inserting:', index_real, flush=True)
        corpus.insert_in_corpus(parameters, 2)

def time_test_svm(n):
    start = time.time()
    test_svm(n)
    print(time.time()-start)

