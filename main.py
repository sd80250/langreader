import pandas as pd
import numpy as np

df = pd.read_csv('all.csv')
poems = df["content"]

# testing
test_int_list = [1,1,2,3,5,8,13,21,34,55]
import random
random.seed(0)
random.shuffle(test_int_list)

'''
initial sorting algorithm

theoretically, this should work for any data type, so for testing purposes, I will use an integer
list of length 10

k_max: 2*k_max + 1 = the maximum number of texts the algorithm will compare texts to every pass; it
should probably be 3 or more
'''

def init_sort(texts, k_max):
	sorted_texts = []
	for text in texts:
		if len(sorted_texts) == 0:
			sorted_texts.append(text)
			continue
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
			print(bottom, middle, top, k) # debugging

			if k > (top - bottom) // 2: 
				k = (top - bottom) // 2


			difficult_texts = 0 # i.e. texts in the ROTIUL more difficult than the text drawn from
								# the unsorted list
			for i in range(middle - k, middle + k + 1):
				if algo(text, sorted_texts[i]) < 0:
					difficult_texts += 1
			print("difficult_texts:", difficult_texts)
			if difficult_texts > k: # i.e. majority of texts in ROTIUL more difficult than given text
				top = middle - 1
			else:
				bottom = middle + 1
			middle = (top + bottom) // 2

		print(bottom, middle, top, k) # debugging
		sorted_texts.insert(bottom, text)
		print(text, sorted_texts) # debugging
	return sorted_texts




# algorithm by which texts are compared; the comparator

def algo(text1, text2):
	return text1 - text2
    # if (len(text1) > len(text2)):
    # 	return 1
    # else:
    # 	return -1

print("initially sort the texts:")
print("initial list:", test_int_list)
print(init_sort(test_int_list, 3)) # debug
# print(init_sort(poems, 3))



