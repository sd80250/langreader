def vectorize(string):
    # aadhityaa's function; should return integer frequency of words in specific article
    if string == "a":
        return {"the": 10, "and": 5, "of": 3, "a": 1, "to": 1, "dog": 1, "cat": 1, "fox": 1}
    else:
        return {"the": 15, "of": 3, "a": 1, "to": 2, "or": 8, "car": 1, "exhaust": 1, "pipe": 1}

def global_vector():
    # aadhityaa's function; should return global log frequency of words in English
    return {"the": 5.3, "and": 4.1, "of": 3.8, "a": 2.2, "to": 1.8, "or": 1.7}

def time_text_to_str(txt): # generator method for time and time for kids articles
    line = ""
    with open(txt, 'r') as file:
        article = ""
        while True:
            line = file.readline()
            if not line:
                break
            if line[:5] == "|||||":
                yield article
                article = line[5:]
            else:
                article += line
# example code:
# for article in time_text_to_str("time_for_kids_scraped.txt"):
#     print(article)

def prepare_for_svm(text_vector_A, text_vector_B, global_vector): # produces a concatenated vector for the SVM
    '''
    text_vector_A and text_vector_B should have relative frequencies; the sum of their terms should be 1
    the vector has four parts: A_freq, global_A_freq, B_freq, global_B_freq; each part is one more than the length 
    of the global vector the last value will indicate the number of times that any word that is not in the global 
    vector is counted in the local frequency vectors
    '''

    no_of_entries = len(global_vector) + 1
    svm_vector = [0] * (4 * no_of_entries) 

    # add an index to the global vector keys
    indexed_global_vector = {}
    index = 0
    for key, value in global_vector.items():
        indexed_global_vector[key] = (value, index)
        index += 1

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

# print("resulting svm vector:", prepare_for_svm(vectorize("a"), vectorize("b"), global_vector()))
# print("vector a:", vectorize('a'))
# print("vector b:", vectorize('b'))
