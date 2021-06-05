import pandas as pd
import numpy as np
import random # testing
import bisect # testing
import svm
import vectorize as v
import pickle

'''
initial sorting algorithm

theoretically, this should work for any data type, so for testing purposes, I will use an integer
list of length 10

k_max: 2*k_max + 1 = the maximum number of texts the algorithm will compare texts to every pass; it
should probably be 2 or more
'''
global sgd_model 
global indexed_global_vector 

def init_sort(texts, k_max):
	sorted_texts = []
	for text in texts:
		insert(text, sorted_texts, k_max)
	return sorted_texts

def insert(text, sorted_texts, k_max):
	print(len(sorted_texts))
	if len(sorted_texts) == 0:
		sorted_texts.append(text)
		return
	# print(bottom, middle, top, k) # debugging
	sorted_texts.insert(bin_search(text[0], [j[0] for j in sorted_texts], k_max), text) # TODO: switch text[0] and [j[0]...] back text and sorted_texts

def bin_search(text, sorted_texts, k_max):
	bottom = 0
	top = len(sorted_texts) - 1
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
		difficult_texts = 0 # i.e. texts in the ROTISL more difficult than the text drawn from
							# the unsorted list
		for i in range(middle - k, middle + k + 1):
			if compare(text, sorted_texts[i]) < 0:
				difficult_texts += 1
		# print("difficult_texts:", difficult_texts)
		if difficult_texts > k: # i.e. majority of texts in ROTISL more difficult than given text
			top = middle - 1
		else:
			bottom = middle + 1
		middle = (top + bottom) // 2
	return bottom

# algorithm by which texts (in the form of strings) are compared; the comparator
def compare(text1, text2, print_=False):
	text1_fv = v.make_relative(v.frequency_vector(text1))
	text2_fv = v.make_relative(v.frequency_vector(text2))
	if print_:
		for key, value in text1_fv.items():
			print(key, value, indexed_global_vector.get(key, ("NONE",))[0])
		print()
		for key, value in text2_fv.items():
			print(key, value, indexed_global_vector.get(key, ("NONE",))[0])
	return sgd_model.predict(np.asarray(v.prepare_for_svm(text1_fv, text2_fv,indexed_global_vector)).reshape((1, -1)))
	
	# TEMPORARY COMPARATOR FOR INTS:
	# return text1 - text2

	# TEMPORARY COMPARATOR FOR STRS:
    # if (len(text1) > len(text2)):
    # 	return 1
    # else:
    # 	return -1

def test():
	sgd_model = svm.load_model('svm_model563.p')
	indexed_global_vector = v.make_indexed(v.global_vector())

	# poems = pd.DataFrame(pd.read_csv('PoetryFoundationData.csv'), columns=['Poem', 'Title'])
	# poem_list = list(poems.to_records(index=False))[0:100]
	# print(len(poem_list))
	# sorted_list = init_sort(poem_list, 2)
	# sgd_sorted_poems = pickle.load(open('sorted_poems.p', 'rb'))
	# pickle.dump(sorted_list, open('svm563_poems.p', 'wb'))



	# poem_list = [(y[0], 'Hard') for y in v.time_get_str(True)[0:50]] + [(y[0], 'Easy') for y in v.time_get_str(False)[0:50]]

	sorted_list = pickle.load(open('svm563_poems.p', 'rb'))
	sgd_sorted_poems = pickle.load(open('sorted_poems.p', 'rb'))
	# sorted_list = init_sort(poem_list, 2)
	index = 0
	for i, j in zip(sorted_list, sgd_sorted_poems):
		print('{0} {1:50} {2}'.format(index, j[1].strip(), len(v.preprocess(j[0]))))
		index += 1
	# pickle.dump(sorted_list, open('sorted_articles.p', 'wb'))


	while True:
		try:
			print('enter input: ', end='', flush=True)
			index = int(input())
			print(sgd_sorted_poems[index][0].strip())
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