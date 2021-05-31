import pandas as pd
import numpy as np
import random # testing
import bisect # testing

df = pd.read_csv('all.csv')
poems = df["content"]

'''
initial sorting algorithm

theoretically, this should work for any data type, so for testing purposes, I will use an integer
list of length 10

k_max: 2*k_max + 1 = the maximum number of texts the algorithm will compare texts to every pass; it
should probably be 2 or more
'''

def init_sort(texts, k_max):
	sorted_texts = []
	for text in texts:
		insert(text, sorted_texts, k_max)
	return sorted_texts

def insert(text, sorted_texts, k_max):
	if len(sorted_texts) == 0:
		sorted_texts.append(text)
		return
	# print(bottom, middle, top, k) # debugging
	sorted_texts.insert(bin_search(text, sorted_texts, k_max), text)

def bin_search(text, sorted_texts, k_max):
	bottom = 0
	top = len(sorted_texts) - 1
	middle = (top + bottom) // 2
	k = k_max
	'''
	for every text in the (as of yet) unsorted list, we try to find the right 
	position by comparing the given text to a range of texts in unsorted list (ROTIULfor short)
	between (middle - k, middle + k) rather than a single text
	'''
	while top >= bottom:
		# if k is too big, which would make the index i out of bounds, then set k to the maximum 
		# value it can be
		# print(bottom, middle, top, k) # debugging
		if k > (top - bottom) // 2: 
			k = (top - bottom) // 2
		difficult_texts = 0 # i.e. texts in the ROTIUL more difficult than the text drawn from
							# the unsorted list
		for i in range(middle - k, middle + k + 1):
			if compare(text, sorted_texts[i]) < 0:
				difficult_texts += 1
		# print("difficult_texts:", difficult_texts)
		if difficult_texts > k: # i.e. majority of texts in ROTIUL more difficult than given text
			top = middle - 1
		else:
			bottom = middle + 1
		middle = (top + bottom) // 2
	return bottom

# algorithm by which texts are compared; the comparator

def compare(text1, text2):
	# TEMPORARY COMPARATOR FOR INTS:
	return text1 - text2

	# TEMPORARY COMPARATOR FOR STRS:
    # if (len(text1) > len(text2)):
    # 	return 1
    # else:
    # 	return -1




# TESTS
# ---------------

# SINGLE LIST TEST:
# testing
# test_int_list = [1,1,2,3,5,8,13,21,34,55]
# random.seed(0)
# random.shuffle(test_int_list)
# print("initially sort the texts:")
# print("initial list:", test_int_list)
# print(init_sort(test_int_list, 3)) # debug
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
test = [0,1,2,3,4,5,6,7, 8,9,10]
num = 8
print(insert(num, test, 2))
print(test)
print(bin_search(num, test, 2))