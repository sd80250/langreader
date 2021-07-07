"""
preliminary classification of texts, given that the user knows (and only knows) top n words, where
n is an element of {100, 250, 500, 1000, 2000, 3000, ..., 10000}
"""
import vectorize as v
import sqlite3

def get_sorted_global_vector():
    igv = v.get_indexed_global_vector()
    return dict([(sgv[0], (sgv[1][0], new_index)) for sgv, new_index in zip(sorted(igv.items(), key=lambda item: item[1][0], reverse=True), range(len(igv)))])

def get_top_n_user_profile(n, length):
    return [1] * n + [-1] * (length - n)

def get_word_vector_from_text(sgv, text):
    rfv = v.relative_frequency_vector(text, normalize=False)
    wv = [0] * len(sgv)

    print(rfv)
    quit()

    for key, value in rfv.items():
        wv[sgv[key][1]] = value
    return wv

def get_readability(user_prof, word_vector):
    x = np.dot(user_prof, word_vector)
    if x >= .95:
        result = 1 - (.95 - x)**2
    else:
        result = 1 - 16*(.95 - x)**2
    return result

def record_thousand_most_readable_texts(n, exec_stmt):
    sgv = get_sorted_global_vector()
    up = get_top_n_user_profile(n, len(sgv))

    conn = sqlite3.connect("resources/sqlite/corpus.sqlite")
    c = conn.cursor()
    c.execute("SELECT * FROM Repository " + exec_stmt)
    all_texts = c.fetchall()

    return sorted(all_texts, key=lambda tuple: get_readability(up, get_word_vector_from_text(sgv, tuple[2])), reverse=True)[:100]



if __name__ == '__main__':
    print(record_thousand_most_readable_texts(100, "where text_type = 'short_story'"))