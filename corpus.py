# the main algorithms for getting and entering articles/books/other media into the database
import sqlite3

def naive_init_sort_in_corpus(k_max):
    texts = []
    with sqlite3.connect("corpus.sqlite") as con:
		cur = con.cursor()
		cur.execute("""
		SELECT article_text
        FROM Repository
		""")
        for tup in cur.fetchall():
            texts.append(tup[0])
    texts = init_sort(texts, k_max)
    with sqlite3.connect("corpus.sqlite") as con:
        cur = con.cursor()
        index = 0
        for text in texts:
            cur.execute("""
            UPDATE Repositiory
            SET order_number = ?
            WHERE article_text = ?
            """, (index, text))
            index += 1

def get_repo_length():
    with sqlite3.connect("corpus.sqlite") as con:
        cur = con.cursor()
        cur.execute(""" 
        SELECT COUNT(*) FROM Repository
        """)
        return cur.fetchone()[0]

def get_text_from_repo(index): # assumes the repo is already sorted
    with sqlite3.connect("corpus.sqlite") as con:
        cur = con.cursor()
        cur.execute(""" 
        SELECT article_text FROM Repository
        WHERE order_number = ?
        """, (index + 1,))
        return cur.fetchone()[0]

def naive_binary_search_in_corpus(text, k_max):
    bottom = 0
	top = get_repo_length() - 1
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
			if compare(text, get_text_from_repo(i)) < 0:
				difficult_texts += 1
		# print("difficult_texts:", difficult_texts)
		if difficult_texts > k: # i.e. majority of texts in ROTISL more difficult than given text
			top = middle - 1
		else:
			bottom = middle + 1
		middle = (top + bottom) // 2
	return bottom