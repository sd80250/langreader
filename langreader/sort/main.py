import sys
import os
sys.path.insert(0, "")

import pandas as pd
import numpy as np
import langreader.sort.svm as svm
import langreader.sort.vectorize as v
import pickle
import time
import datetime
from os import path

'''
initial sorting algorithm

k_max: 2*k_max + 1 = the maximum number of texts the algorithm will compare texts to every pass; it
should probably be 2 or more
'''
global svm_model
global indexed_global_vector
global vectorizer
global index_list


def init_sort(indeces, k_max):
    sorted_indeces = []
    for index in indeces:
        print(len(sorted_indeces))
        insert(index, sorted_indeces, k_max)
    return sorted_indeces


def insert(index, sorted_indeces, k_max):
    if len(sorted_indeces) == 0:
        sorted_indeces.append(index)
        return
    # print(bottom, middle, top, k) # debugging
    sorted_indeces.insert(bin_search(index, sorted_indeces, k_max), index)


def bin_search(index, sorted_indeces, k_max):
    bottom = 0
    top = len(sorted_indeces) - 1
    middle = (top + bottom) // 2
    k = k_max
    rfv1, nc1 = v.relative_frequency_vector(index_list[index][0], ret_new_characteristics=True)
    '''
	for every text in the sorted list, we try to find the right
	position by comparing the given text to a range of texts in sorted list (ROTISL for short)
	between (middle - k, middle + k) rather than a single text
	'''
    while top >= bottom:
        # if k is too big, which would make the index i out of bounds, then set k to the maximum
        # value it can be
        # print(bottom, middle, top, k) # debugging
        if k > (top - bottom) // 2:
            k = (top - bottom) // 2
        difficult_texts = 0  # i.e. texts in the ROTISL more difficult than the text drawn from
                                              # the unsorted list
        for i in range(middle - k, middle + k + 1):
            if compare(rfv1, nc1, sorted_indeces[i]) < 0:
                difficult_texts += 1
        # print("difficult_texts:", difficult_texts)
        if difficult_texts > k:  # i.e. majority of texts in ROTISL more difficult than given text
            top = middle - 1
        else:
            bottom = middle + 1
        middle = (top + bottom) // 2
    return bottom


# algorithm by which texts (referenced by index, according to index_list) are compared; the comparator
def compare(rfv1, nc1, index2, print_=False):
    start = time.time()
    comparison = svm.compare(rfv1, nc1, index_list[index2][0])
    print('compare:', time.time()-start)
    return comparison # 0 > text


def test(n):
    df = pd.DataFrame(pd.read_csv('resources/poems/PoetryFoundationData.csv'), columns=['Poem', 'Title', 'Poet'])
    init_variables(list(df.to_records(index=False))[0:n])
    start = time.time()
    sorted_poems = [index_list[i] for i in init_sort(list(range(0, n)), k_max=2)]
    print(time.time() - start)


def init_variables(text_list):
    global svm_model
    global indexed_global_vector
    global vectorizer
    global index_list

    svm_model = svm.load_model('langreader/sort/resources/svm_model_varied_size.p')
    indexed_global_vector = v.get_indexed_global_vector()
    vectorizer = v.VLRSWNCVectorizer()
    index_list = text_list


def init_model(text_list=None):
    v.make_global_vector()
    svm.make_and_test_model(pairs_of_test_data=563)


def App(filepath, language="English"):
    poems = pickle.load(open(filepath, 'rb'))
    print(
        f"Welcome to Langreader! We will show you a random text in the {language} language")
    print("Enter '0' to quit the program")
    input("Press enter to continue: ")
    while input() != '0':
        rand = np.random.randint(0, high=len(poems))
        print("Title:", poems[rand][1], "\n\n", poems[rand][0])
        print("\n\n(^scroll up) Was that too hard, too easy, or just right?")
        result = None
        first_time = True
        switch = {
            1: 3,
            2: -7,
            3: 1,
        }
        while not result:
            if not first_time:
                print("Oops, try again!")
            ans = input("[1] EASY \n [2] HARD \n [3] RIGHT\n")
            result = switch.get(int(ans))
            first_time = False
        rand += result
        if rand >= len(poems):
            rand = len(poems) - 1
            print("You've reached the hardest text.")
        if rand < 0:
            rand = 0
            print("You suck at English.")
        print("Here's another one!")


if __name__ == '__main__':
    pass
    # pickle.dump(sorted_poems, open('langreader/sort/resources/poems_varied_length.p', 'wb'))
    
    # a = pickle.load(open('langreader/sort/resources/poems_varied_length.p', 'rb'))

    # i = 0
    # for text, title, author in a:
    #     print('{} {}'.format(title.strip(), i))
    #     i += 1
