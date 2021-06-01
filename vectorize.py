import random
import numpy as np
random.seed(0) # testing
import sqlite3

def vectorize(string):
    # aadhityaa's function; should return integer frequency of words in specific article
    if string == "a":
        return {"the": 10, "and": 5, "of": 3, "a": 1, "to": 1, "dog": 1, "cat": 1, "fox": 1}
    else:
        return {"the": 15, "of": 3, "a": 1, "to": 2, "or": 8, "car": 1, "exhaust": 1, "pipe": 1}

def global_vector():
    # aadhityaa's function; should return global log frequency of words in English
    return {"the": 5.3, "and": 4.1, "of": 3.8, "a": 2.2, "to": 1.8, "or": 1.7}

# this method probably belongs in another file
# hard: 0/False = the text is not hard, 1/True = the text is hard
def time_get_str(isHard): # generator method for time and time for kids articles
    with sqlite3.connect("corpus.sqlite") as con:
        cur = con.cursor()
        cur.execute("""
        SELECT article_text FROM Training
        WHERE difficult=?
        """, (isHard,))
        return cur.fetchall()

# example code:
# for easy_article in time_get_str(0):
#     print(easy_article[0])
# for hard_article in time_get_str(1):
#     print(hard_article[0])

def make_indexed(vector):
    # add an index to the global vector keys
    indexed_vector = {}
    index = 0
    for key, value in vector.items():
        indexed_vector[key] = (value, index)
        index += 1
    return indexed_vector

def prepare_for_svm(text_vector_A, text_vector_B, indexed_global_vector): # produces a concatenated vector for the SVM
    '''
    text_vector_A and text_vector_B should have relative frequencies; the sum of their terms should be 1
    the vector has four parts: A_freq, global_A_freq, B_freq, global_B_freq; each part is one more than the length 
    of the global vector the last value will indicate the number of times that any word that is not in the global 
    vector is counted in the local frequency vectors
    value is 1 or -1, where 1 indicates that text_vector_A is more difficult than text_vector_B, and -1 is vice versa
    '''

    no_of_entries = len(indexed_global_vector) + 1
    svm_vector = [0] * (4 * no_of_entries) 

    for key, value in text_vector_A.items():
        if key in indexed_global_vector:
            svm_vector[indexed_global_vector[key][1]] = value
            svm_vector[indexed_global_vector[key][1] + no_of_entries] = indexed_global_vector[key][0]
        else:
            svm_vector[no_of_entries - 1] += value
        
    for key, value in text_vector_B.items():
        if key in indexed_global_vector:
            svm_vector[indexed_global_vector[key][1] + 2 * no_of_entries] = value
            svm_vector[indexed_global_vector[key][1] + 3 * no_of_entries] = indexed_global_vector[key][0]
        else:
            svm_vector[no_of_entries - 1 + 2 * no_of_entries] += value

    # print("indexed global vector:", indexed_global_vector)
    return svm_vector

# print("resulting svm vector:", prepare_for_svm(vectorize("a"), vectorize("b"), make_indexed(global_vector())))
# print("vector a:", vectorize('a'))
# print("vector b:", vectorize('b'))

def get_training_vector_indeces(length_A, length_B, n):
    random_values = random.sample(range(length_A*length_B), n)
    training_vector_indeces = set()
    for value in random_values:
        training_vector_indeces.add((value // length_B, value - value // length_B * length_B))
    return training_vector_indeces

# print(get_training_vector_indeces(7, 5, 10))

def make_training_data(n):
    easy_texts_list = []
    hard_texts_list = []
    svm_vectors_list = []
    results_list = []
    indexed_global_vector = make_indexed(global_vector())
    for article in time_get_str(False):
        easy_texts_list.append(vectorize(article[0]))
    for article in time_get_str(True):
        hard_texts_list.append(vectorize(article[0]))
    for a_index, b_index in get_training_vector_indeces(len(easy_texts_list), len(hard_texts_list), n):
        svm_vectors_list.append(prepare_for_svm(easy_texts_list[a_index], hard_texts_list[b_index], indexed_global_vector))
        results_list.append(-1)
        svm_vectors_list.append(prepare_for_svm(hard_texts_list[b_index], easy_texts_list[a_index], indexed_global_vector))
        results_list.append(1)
    return np.asarray(svm_vectors_list), np.asarray(results_list)

