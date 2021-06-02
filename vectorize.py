import random
import numpy as np
import sqlite3
import string
import nltk
import re
import json
import math

def preprocess(text):
    text = text.lower()
    # replaces em/en dashes with space
    text = re.sub(r'[–—]', ' ', text)
    # removes punctuation from the text, except the hyphen, of course
    text = re.sub(r'[^\w\s-]', '', text)
    # tokenizes the string into an array of words
    text = nltk.word_tokenize(text)
    return text
    
def frequency_vector(text, fv = None):
    if fv is None:
        fv = {}
    # preprocessing the texts before we add them to the dictionary
    text = preprocess(text)
    for word in text:
        # if not already in frequency vector, initialize a value of 1
        if not word in fv:
            fv[word] = 1
        # if its already in there, increment the value
        else:
            fv[word] += 1
    return fv

# makes a frequency vector relative (IN PLACE!!! the original vector is itself modified)
def make_relative(fv):
    total = 0
    for value in fv.values():
        total += value
    for key in fv:
        fv[key] = fv[key] / total
    return fv

def global_vector(delete_spurious_values=True):
    # aadithyaa's function; should return global log frequency of words in English
    print('opening file... ', end='', flush=True)
    with open('fv.txt') as f:
        data = f.read()
    print('done')

    print('loading data... ', end='', flush=True)
    js = json.loads(data)
    print('done')

    # deletes em and en dashes ;)
    del js['\u2013']
    del js['\u2014']

    if delete_spurious_values: # spurious values defined as words that only appear once in the dataset; cuts vector by a factor of 6
        print('deleting spurious values... ', end='', flush=True)
        spurious_words = []
        for key in js:
            if js[key] == 1:
                spurious_words.append(key)

        for spurious_word in spurious_words:
            del js[spurious_word]
        print('done')
    
    print('making values log... ', end='', flush=True)
    for key in js:
        js[key] = math.log(js[key])
    print('done')

    return js

# this method probably belongs in another file
# hard: 0/False = the text is not hard, 1/True = the text is hard
def time_get_str(isHard): # returns list of tuples of all articles which are easy or hard
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
    # THIS IS DONE IN PLACE!!! i.e. the original vector itself is modified
    # add an index to the global vector keys
    # this is done so that the global vector dictionary can also have a consistent and known index to work with
    # when making the svm vector
    print('making indexed... ', end='', flush=True)
    index = 0
    for key, value in vector.items():
        vector[key] = (value, index)
        index += 1
    print('done')

    return vector

def prepare_for_svm(text_vector_A, text_vector_B, indexed_global_vector): # produces a concatenated vector for the SVM
    '''
    text_vector_A and text_vector_B should have relative frequencies; the sum of their terms should be 1.
    The vector has four parts: A_freq, global_A_freq, B_freq, global_B_freq; each part is one more than the length 
    of the global vector the last value will indicate the number of times that any word that is not in the global 
    vector is counted in the local frequency vectors. Refer back to the paper for more info.
    value is 1 or -1, where 1 indicates that text_vector_A is more difficult than text_vector_B, and -1 is vice versa
    '''

    no_of_entries = len(indexed_global_vector) + 1 # the last entry will indicate the frequency of any word found not in the global vector
    svm_vector = [0] * (4 * no_of_entries) # makes a vector of 0's (like this: [0, 0, 0, ...]) with length of 4*no_of_entries

    for key, value in text_vector_A.items():
        # if the key of vector A can be found in the global vector, then add those values to the svm vector
        # otherwise, sum the value with the last entry of the A part of the svm vector
        if key in indexed_global_vector:
            svm_vector[indexed_global_vector[key][1]] = value
            svm_vector[indexed_global_vector[key][1] + no_of_entries] = indexed_global_vector[key][0] 
        else:
            svm_vector[no_of_entries - 1] += value
            # print("I have no home (vector A):", key, value)
        
    # do a similar thing with vector B
    for key, value in text_vector_B.items():
        if key in indexed_global_vector:
            svm_vector[indexed_global_vector[key][1] + 2 * no_of_entries] = value
            svm_vector[indexed_global_vector[key][1] + 3 * no_of_entries] = indexed_global_vector[key][0]
        else:
            svm_vector[no_of_entries - 1 + 2 * no_of_entries] += value
            # print("I have no home (vector B):", key, value)
    return svm_vector

# basic test for svm:
# indexed_global_vector = make_indexed(global_vector())
# print("indexed global vector:", indexed_global_vector)
# print("vector a:", frequency_vector('a'))
# print("vector b:", frequency_vector('b'))
# print("resulting svm vector:", prepare_for_svm(frequency_vector("a"), frequency_vector("b"), indexed_global_vector))

# randomly pairs up the indeces of the values in vector A with the indeces of the values in vector B
# n is the number of pairs that we would like
# the output is guaranteed no duplicate pairs thanks to the random.sample method
def get_training_vector_indeces(length_A, length_B, n):
    random_values = random.sample(range(length_A*length_B), n)
    training_vector_indeces = set()
    for value in random_values:
        training_vector_indeces.add((value // length_B, value - value // length_B * length_B))
    return training_vector_indeces

# print(get_training_vector_indeces(7, 5, 10))

# makes the two arrays needed for the svm to train: the first is the word vector itself, the second is the result
# expected from the vector; each will be length 2n
def make_training_data(n):
    # putting everything in lists works because the training data is relatively small
    easy_texts_list = [] 
    hard_texts_list = []
    svm_vectors_list = []
    results_list = []

    # make an indexed_global_vector
    indexed_global_vector = make_indexed(global_vector())

    # add the vectors to the easy and hard lists
    print('getting articles... ', end='', flush=True)
    for article in time_get_str(False):
        easy_texts_list.append(make_relative(frequency_vector(article[0])))
    for article in time_get_str(True):
        hard_texts_list.append(make_relative(frequency_vector(article[0])))
    print('done')

    # from the vector indeces, form svm vectors, and pass them onto numpy arrays to be processed by the svm
    print('forming svm vector:', flush=True)
    index = 1
    for a_index, b_index in get_training_vector_indeces(len(easy_texts_list), len(hard_texts_list), n):
        print("adding n =", index, "... ", end="", flush=True)
        svm_vectors_list.append(prepare_for_svm(easy_texts_list[a_index], hard_texts_list[b_index], indexed_global_vector))
        results_list.append(-1) # -1 means the difficulty of text1 < the difficulty of text2
        # same thing as previous two lines but swapped (the algorithm is not necessarily reversible, so it should be trained that way)
        svm_vectors_list.append(prepare_for_svm(hard_texts_list[b_index], easy_texts_list[a_index], indexed_global_vector))
        results_list.append(1) # 1 means the difficulty of text1 > the difficulty of text2
        print("done")
        index += 1

        # print('easy text', easy_texts_list[a_index])
        # print('hard text', hard_texts_list[b_index])
    print('done forming svm vector')

    
    return np.asarray(svm_vectors_list), np.asarray(results_list)

#TESTING
# i = 0
# for a in time_get_str(True):
#     print(frequency_vector(a[0]))
#     i += 1
#     if i == 4:
#         quit()

# TEST 1:
# global_vector = make_indexed(global_vector())
# no_of_entries = len(global_vector) + 1
# print(no_of_entries)
# # print(len(global_vector))
# # index = 0
# # for indexed_value in make_indexed(global_vector):
# #     if index == 100:
# #         break
# #     print(indexed_value, global_vector[indexed_value])
# #     index += 1
# a = "Hello, my name is Shawn Duan, and I would like to say that I love to code, World."
# b = "My only concern with this program is that it will crash."
# fq_a = make_relative(frequency_vector(a))
# print(fq_a)
# fq_b = make_relative(frequency_vector(b))
# print(fq_b)
# # print(make_relative(fq_a))
# # print(make_relative(fq_b))
# svm_vector = prepare_for_svm(fq_a, fq_b, global_vector)
# hello_index = global_vector['hello'][1]
# print(hello_index)
# my_index = global_vector['my'][1]
# print(my_index)
# only_index = global_vector['only'][1]
# print(only_index)
# for index in hello_index, my_index, only_index:
#     for n in range(0,4):
#         print(svm_vector[index + n * no_of_entries], end=" ")
#     print()
# 



# TEST 2:
# X, y, gv = make_training_data(1)
# no_of_entries = len(gv) + 1
# print(no_of_entries)
# print(X.shape) # should be (2, 6988140)
# print(y.shape) # should be 2
# the_index = gv.get('the')
# sports_index = gv.get('sports')
# connection_index = gv.get('connection')
# zhihu_index = gv.get('zhihu') # bluh how does this guy have 92 mentions in the global vector
# for index in the_index, sports_index, connection_index, zhihu_index:
#     a = index[1]
#     if a is not None:
#         for n in range(0,4):
#             print("for index 0,", a, "; n =", n, ":", X[0, a + n * no_of_entries])
#         print()

#         for n in range(0,4):
#             print("for index 1,", a, ":", X[1, a + n * no_of_entries])
#         print()
# for n in range(0,4):
#     print("for index 0,", no_of_entries - 1, "; n =", n, ":", X[0, no_of_entries - 1 + n * no_of_entries])

# for n in range(0,4):
#     print("for index 1,", no_of_entries - 1, "; n =", n, ":", X[1, no_of_entries - 1 + n * no_of_entries])

