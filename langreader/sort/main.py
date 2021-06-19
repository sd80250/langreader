import sys
import os
sys.path.insert(0, "")

import pandas as pd
import numpy as np
import svm
import vectorize as v
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
    start_time = time.time()
    sorted_indeces = []
    for index in indeces:
        print(len(sorted_indeces))
        insert(index, sorted_indeces, k_max)
    print("it took", str(datetime.timedelta(seconds=time.time() -
          start_time)), "to sort", len(indeces), "texts")
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
            if compare(index, sorted_indeces[i]) < 0:
                difficult_texts += 1
        # print("difficult_texts:", difficult_texts)
        if difficult_texts > k:  # i.e. majority of texts in ROTISL more difficult than given text
            top = middle - 1
        else:
            bottom = middle + 1
        middle = (top + bottom) // 2
    return bottom


# algorithm by which texts (referenced by index, according to index_list) are compared; the comparator
def compare(index1, index2, print_=False):
    text1_fv = v.relative_frequency_vector(index_list[index1][0])
    text2_fv = v.relative_frequency_vector(index_list[index2][0])
    if print_:
        for key, value in text1_fv.items():
            print(key, value, indexed_global_vector.get(key, ("NONE",))[0])
        print()
        for key, value in text2_fv.items():
            print(key, value, indexed_global_vector.get(key, ("NONE",))[0])
    return svm_model.predict(np.asarray(vectorizer.prepare_for_svm(text1_fv, text2_fv, indexed_global_vector)).reshape((1, -1)))


def test(poem_path, model_path=None):
    global svm_model
    global indexed_global_vector
    global vectorizer
    global index_list

    svm_model = svm.load_model(model_path)
    indexed_global_vector = v.get_indexed_global_vector()
    vectorizer = v.ReturnSubtractionVectorizer()

    if model_path:
        poems = pd.DataFrame(pd.read_csv(
            '../../resources/poems/PoetryFoundationData.csv'), columns=['Poem', 'Title'])
        index_list = list(poems.to_records(index=False))[0:100]
        indeces = list(range(0, len(index_list)))
        print(indeces)
        print(len(index_list))
        sorted_indeces = init_sort(indeces, 2)
        sorted_list = [index_list[i] for i in sorted_indeces]
        pickle.dump(sorted_list, open(poem_path, 'wb'))

    # poem_list = [(y[0], 'Hard') for y in v.time_get_str(True)[0:50]] + [(y[0], 'Easy') for y in v.time_get_str(False)[0:50]]

    sorted_list = pickle.load(open(poem_path, 'rb'))
    # sorted_list = init_sort(poem_list, 2)
    index = 0
    for i in sorted_list:
        print('{0} {1}'.format(index, i[1].strip()))
        index += 1
    # pickle.dump(sorted_list, open('sorted_articles.p', 'wb'))

    while True:
        try:
            print('enter input: ', end='', flush=True)
            index = int(input())
            print(sorted_list[index][0].strip())
        except Exception as e:
            print(e)

    # TESTS
    # ---------------

    # SINGLE LIST TEST:
    # testing
    # test_int_list = [1,1,2,3,5,8,13,21,34,55]
    # random.seed(0)
    # random.shuffle(test_int_list)
    # print("initially sort the texts:")
    # print("initial list:", test_int_list)
    # print(init_sort(test_int_list, 3))
    # print(init_sort(poems, 3))

    # # 100 RANDOM TESTS INITIAL LIST TEST:
    # print("running 100 random tests:")
    # for i in range(0, 100):
    # 	# make a random list of 1 - 20 integers with values between 0 and 100
    # 	random_list = random.sample(range(0, 100), random.randint(1, 20))
    # 	print("initial list:", random_list)
    # 	# list that's sorted by our algorithm with random k value between 3 and 10
    # 	init_sorted = init_sort(random_list, random.randint(3, 10))
    # 	print("list sorted by init_sort:", init_sorted)
    # 	# list sorted by python algorithm
    # 	python_sorted = sorted(random_list)
    # 	print("list sorted by python:", python_sorted)
    # 	# checks if two sorted lists equal
    # 	for i in range(0, len(random_list)):
    # 		if (init_sorted[i] != python_sorted[i]):
    # 			print("INIT_SORTED NOT EQUAL TO PYTHON_SORTED")
    # 			quit()
    # 	print("init_sorted == python_sorted")

    # 100 RANDOM TESTS INSERT VALUE TEST:
    # print("running 100 random tests:")
    # for i in range(0, 100):
    # 	# make a random, sorted list of 1 - 20 integers with values between 0 and 100
    # 	random_sorted_list = sorted(random.sample(range(0, 100), random.randint(1, 20)))
    # 	print("initial list:", random_sorted_list)
    # 	# make a random integer between 0 and 100
    # 	random_int = random.randint(0, 100)
    # 	print("initial integer:", random_int)
    # 	# insert that integer with random k value between 3 and 10 using our algorithm
    # 	inserted_list = random_sorted_list[:] # makes a copy of random_sorted_list
    # 	insert(random_int, inserted_list, random.randint(3, 10))
    # 	print("list with integer inserted by algorithm:", inserted_list)
    # 	# insert integer with python's bisect algorithm
    # 	bisected_list = random_sorted_list[:]
    # 	bisect.insort(bisected_list, random_int)
    # 	print("list with integer inserted by bisect:", bisected_list)
    # 	# checks if two sorted lists equal
    # 	for i in range(0, len(random_sorted_list)):
    # 		if (inserted_list[i] != bisected_list[i]):
    # 			print("INESRTED_LIST NOT EQUAL TO BISECTED_LIST")
    # 			quit()
    # 	print("inserted_list == bisected_list")

    # TESTING 100 RANDOM binary search integers
    # test = [0,1,2,3,4,5,6,7, 8,9,10]
    # num = 8
    # print(insert(num, test, 2))
    # print(test)
    # print(bin_search(num, test, 2))


def init_variables(text_list):
    global svm_model
    global indexed_global_vector
    global vectorizer
    global index_list

    svm_model = svm.load_model('langreader/sort/resources/svm_model.p')
    indexed_global_vector = v.get_indexed_global_vector()
    vectorizer = v.ReturnSubtractionVectorizer()
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
    if not path.exists('langreader/sort/resources/global_vector.p'):
        print('path does not exist.')
        import time
        time.sleep(5)
        v.make_global_vector()
    if not path.exists('langreader/sort/resources/svm_model.p'):
        svm.make_and_test_model(563)
    if not path.exists('langreader/sort/resources/poems.p'):
        df = pd.DataFrame(pd.read_csv('resources/poems/PoetryFoundationData.csv'), columns=['Poem', 'Title', 'Poet'])
        init_variables(list(df.to_records(index=False))[0:100])
        sorted_poems = [index_list[i] for i in init_sort(list(range(0, 100)), k_max=2)]
        pickle.dump(sorted_poems, open('langreader/sort/resources/poems.p', 'wb'))
    a = pickle.load(open('langreader/sort/resources/poems.p', 'rb'))

    i = 0
    for text, title, author in a:
        if i > 5:
            break
        i += 1
        print(text.strip(), title.strip(), author)
