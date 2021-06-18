import random
import numpy as np
import sqlite3
import nltk
from nltk.stem import SnowballStemmer
import re
import json
import math
import pickle
from abc import ABC, abstractmethod
import os
from os import path

stemmer = SnowballStemmer('english')

# this method probably belongs in another file
# hard: 0/False = the text is not hard, 1/True = the text is hard
def time_get_str(is_hard, database_file_path="langreader/sort/resources/sqlite/corpus.sqlite"):
    # returns list of tuples of all articles which are easy or hard
    with sqlite3.connect(database_file_path) as con:
        cur = con.cursor()
        cur.execute("""
        SELECT article_text FROM Training
        WHERE difficult=?
        """, (is_hard,))
        return cur.fetchall()


def preprocess(text):
    text = text.lower()
    # replaces hyphens, em/en dashes, and horizontal bars with space
    text = re.sub(r'[-–—―]', ' ', text)
    # removes punctuation and numerals from the text
    text = re.sub(r'[^\w\s]|[0-9]', '', text)
    # tokenizes the string into an array of words
    text = nltk.word_tokenize(text)
    # runs words through snowball stemming algorithm
    text = [stemmer.stem(word) for word in text]
    return text


def relative_frequency_vector(text, fv=None):
    if fv is None:
        fv = {}
    # preprocessing the texts before we add them to the dictionary
    text = preprocess(text)
    for word in text:
        # if not already in frequency vector, initialize a value of 1
        if word not in fv:
            fv[word] = 1
        # if its already in there, increment the value
        else:
            fv[word] += 1

    total = 0
    for value in fv.values():
        total += value
    for key in fv:
        fv[key] = fv[key] / total
    return fv


def get_indexed_global_vector(file_path="langreader/sort/resources/global_vector.p"):  # run make_global_vector first before running global_vector!!!
    if not path.exists(file_path):
        make_global_vector()
    vector = pickle.load(open(file_path, "rb"))
    print('making indexed... ', end='', flush=True)
    index = 0
    for key, value in vector.items():
        vector[key] = (value, index)
        index += 1
    print('done')
    return vector


def make_global_vector(delete_spurious_values=True, min_freq=1,
                       dict_list_file_path='langreader/sort/resources/fv_stemmed.txt',
                       result_file_path="langreader/sort/resources/global_vector.p"):  # puts this in a pickle file
    # should return global log frequency of words in English
    print('opening file... ', end='', flush=True)
    with open(dict_list_file_path) as f:
        data = f.read()
    print('done')

    print('loading data... ', end='', flush=True)
    js = json.loads(data)
    print('done')

    if delete_spurious_values:  # spurious values defined as words not in training data
        print('deleting spurious values... ', end='', flush=True)
        spurious_words = set()
        real_words = set()

        for article in time_get_str(False):
            real_words.update(preprocess(article[0]))

        for article in time_get_str(True):
            real_words.update(preprocess(article[0]))

        # we have to make two for-loops because you can't delete a key in a dictionary while accessing it
        for key in js:
            if (key not in real_words) or (js[key] <= min_freq):
                spurious_words.add(key)
        for spurious_word in spurious_words:
            del js[spurious_word]

        print('done')

    print('making values log and fitting to training scale... ', end='', flush=True)
    for key in js:
        # scale the global vector to values closer to the values of input data; 0.07 is the avg. relative freq of the
        # word 'the', while 18.03 is the log freq of the word 'the' all dictionary values should lie between 0 and
        # 0.07, about the same range as the relative frequencies of texts
        js[key] = (math.log(js[key]) - math.log(min_freq - .5)) * 0.07 / (18.03 - math.log(min_freq - .5))
    print('done')

    # store dictionary onto a binary file using pickle
    print("dumping dictionary... ", end='', flush=True)
    pickle.dump(js, open(result_file_path, 'wb'))
    print("done")


class Vectorizer(ABC):
    @abstractmethod
    def prepare_for_svm(self, text_vector_A, text_vector_B, indexed_global_vector):
        pass

    @abstractmethod
    def get_training_vector_indeces(self, length_A, length_B, n):
        pass

    @abstractmethod
    def make_training_data(self, n):
        pass


class ConcatenationVectorizer(Vectorizer):
    def prepare_for_svm(self, text_vector_A, text_vector_B,
                        indexed_global_vector):  # produces a concatenated vector for the SVM
        """
        text_vector_A and text_vector_B should have relative frequencies; the sum of their terms should be 1.
        The vector has four parts: A_freq, global_A_freq, B_freq, global_B_freq; any value that does not appear
        in the global vector will not be counted. Refer back to the paper for more info.
        value is 1 or -1, where 1 indicates that text_vector_A is more difficult than text_vector_B, and -1 is vice versa
        """

        no_of_entries = len(indexed_global_vector)
        svm_vector = [0] * (
                4 * no_of_entries)  # makes a vector of 0's (like this: [0, 0, 0, ...]) with length of
        # 4*no_of_entries

        for key, value in text_vector_A.items():
            # if the key of vector A can be found in the global vector, then add those values to the svm vector
            # otherwise, sum the value with the last entry of the A part of the svm vector
            if key in indexed_global_vector:
                svm_vector[indexed_global_vector[key][1]] = value
                svm_vector[indexed_global_vector[key][1] + no_of_entries] = indexed_global_vector[key][0]
                # else:
            #     svm_vector[no_of_entries - 1] += value
            # print("I have no home (vector A):", key, value)

        # do a similar thing with vector B
        for key, value in text_vector_B.items():
            if key in indexed_global_vector:
                svm_vector[indexed_global_vector[key][1] + 2 * no_of_entries] = value
                svm_vector[indexed_global_vector[key][1] + 3 * no_of_entries] = indexed_global_vector[key][0]
            # else:
            #     svm_vector[no_of_entries - 1 + 2 * no_of_entries] += value
            # print("I have no home (vector B):", key, value)
        return svm_vector


class SubtractionVectorizer(Vectorizer):
    def prepare_for_svm(self, text_vector_A, text_vector_B,
                        indexed_global_vector):  # produces SVM vector that's subtracted
        no_of_entries = len(indexed_global_vector)
        svm_vector = [0] * (2 * no_of_entries)

        for key, value in text_vector_A.items():
            if key in indexed_global_vector:
                svm_vector[indexed_global_vector[key][1]] = value
                svm_vector[indexed_global_vector[key][1] + no_of_entries] = indexed_global_vector[key][0]

        # subtracts rather than concatenates vector B
        for key, value in text_vector_B.items():
            if key in indexed_global_vector:
                svm_vector[indexed_global_vector[key][1]] -= value
                svm_vector[indexed_global_vector[key][1] + no_of_entries] -= indexed_global_vector[key][0]

        return svm_vector


class ReturnVectorizer(Vectorizer):
    # randomly pairs up the indeces of the values in vector A with the indeces of the values in vector B
    # n is the number of pairs that we would like
    # the output is guaranteed no duplicate pairs thanks to the random.sample method
    def get_training_vector_indeces(self, length_A, length_B, n):
        # random_values = random.sample(range(length_A*length_B), n)
        # training_vector_indeces = set()
        # for value in random_values:
        #     training_vector_indeces.add((value // length_B, value - value // length_B * length_B))
        # return training_vector_indeces

        # how the paper implemented it
        random_values_A = random.sample(range(length_A), n)
        random_values_B = random.sample(range(length_B), n)
        training_vector_indeces = set()
        for i in range(0, n):
            training_vector_indeces.add((random_values_A[i], random_values_B[i]))
        return training_vector_indeces

    # makes the two arrays needed for the svm to train: the first is the word vector itself, the second is the result
    # expected from the vector; each will be length 2n
    def make_training_data(self, n):
        # putting everything in lists works because the training data is relatively small
        easy_texts_list = []
        hard_texts_list = []
        svm_vectors_list = []
        results_list = []

        # make an indexed_global_vector
        igv = get_indexed_global_vector()

        # add the vectors to the easy and hard lists
        print('getting articles... ', end='', flush=True)
        for article in time_get_str(False):
            easy_texts_list.append(relative_frequency_vector(article[0]))
        for article in time_get_str(True):
            hard_texts_list.append(relative_frequency_vector(article[0]))
        print('done')

        # from the vector indeces, form svm vectors, and pass them onto numpy arrays to be processed by the svm
        # print('forming svm vector:', flush=True)
        # index = 1
        for easy_index, hard_index in self.get_training_vector_indeces(len(easy_texts_list), len(hard_texts_list), n):
            # process = psutil.Process(os.getpid())
            # print("adding n =", index, "; using", process.memory_info().rss // 1000000, "MB... ", end="", flush=True)
            svm_vectors_list.append(
                self.prepare_for_svm(easy_texts_list[easy_index], hard_texts_list[hard_index], igv))
            results_list.append(-1)  # -1 means the difficulty of text1 < the difficulty of text2
            # same thing as previous two lines but swapped (the algorithm is not necessarily reversible, so it should
            # be trained that way)
            svm_vectors_list.append(
                self.prepare_for_svm(hard_texts_list[hard_index], easy_texts_list[easy_index], igv))
            results_list.append(1)  # 1 means the difficulty of text1 > the difficulty of text2
            # print("done")
            # index += 1

            # print('easy text', len(easy_texts_list))
            # print('hard text', len(hard_texts_list))
        # print('done forming svm vector; now converting to numpy arrays')

        return np.asarray(svm_vectors_list), np.asarray(results_list)


class YieldVectorizer(Vectorizer):
    def get_training_vector_indeces(self, length_A, length_B, n):
        random_values = list(range(length_A * length_B))
        random.shuffle(random_values)
        training_vector_indeces = []
        for value in random_values:
            training_vector_indeces.append((value // length_B, value - value // length_B * length_B))
        for i in range(0, len(training_vector_indeces), n):
            yield training_vector_indeces[i:i + n]

    def get_training_and_test_vector_indeces(self, length_A, length_B, n,
                                             test_train_split=.667):  # test split is the proportion of values in list A and list B which will be partitioned off for training
        a_list = range(length_A)
        b_list = range(length_B)
        a_training = random.sample(a_list, int(length_A * test_train_split))
        b_training = random.sample(b_list, int(length_B * test_train_split))
        a_test = []
        b_test = []

        for a in a_list:
            if a not in a_training:
                a_test.append(a)
        for b in b_list:
            if b not in b_training:
                b_test.append(b)

        for training_indeces, test_indeces in zip(
                self.get_training_vector_indeces(len(a_training), len(b_training), int(n * test_train_split)),
                self.get_training_vector_indeces(len(a_test), len(b_test), int(n * (1 - test_train_split)))):
            yield [(a_training[a_index], b_training[b_index]) for a_index, b_index in training_indeces], [
                (a_test[a_index], b_test[b_index]) for a_index, b_index in test_indeces]

    def make_test_and_training_data(self, batch_size_times_two, test_train_split=.667):
        easy_texts_list = []
        hard_texts_list = []

        igv = get_indexed_global_vector()

        print('getting articles... ', end='', flush=True)
        for article in time_get_str(False):
            easy_texts_list.append(relative_frequency_vector(article[0]))
        for article in time_get_str(True):
            hard_texts_list.append(relative_frequency_vector(article[0]))
        print('done')

        for training_batch, test_batch in self.get_training_and_test_vector_indeces(len(easy_texts_list),
                                                                                    len(hard_texts_list),
                                                                                    batch_size_times_two,
                                                                                    test_train_split=test_train_split):
            sgd_vectors_list = []
            training_results_list = []

            test_list = []
            test_results_list = []
            # print(training_batch)
            # print(test_batch)
            for easy_index, hard_index in training_batch:
                # prepares vectors as arrays
                sgd_vectors_list.append(self.prepare_for_svm(easy_texts_list[easy_index], hard_texts_list[hard_index],
                                                             igv))
                training_results_list.append(-1)  # -1 means the difficulty of text1 < the difficulty of text2

                # same thing as previous two lines but swapped (the algorithm is not necessarily reversible,
                # so it should be trained that way)
                sgd_vectors_list.append(self.prepare_for_svm(hard_texts_list[hard_index], easy_texts_list[easy_index],
                                                             igv))
                training_results_list.append(1)

            for easy_index, hard_index in test_batch:
                test_list.append(self.prepare_for_svm(easy_texts_list[easy_index], hard_texts_list[hard_index],
                                                      igv))
                test_results_list.append(-1)  # -1 means the difficulty of text1 < the difficulty of text2
                # same thing as previous two lines but swapped (the algorithm is not necessarily reversible,
                # so it should be trained that way)
                test_list.append(self.prepare_for_svm(hard_texts_list[hard_index], easy_texts_list[easy_index],
                                                      igv))
                test_results_list.append(1)

            yield np.array(sgd_vectors_list), np.array(training_results_list), np.array(test_list), np.array(
                test_results_list)

    def make_training_data(self, batch_size_times_two):
        easy_texts_list = []
        hard_texts_list = []

        # make an indexed_global_vector
        igv = get_indexed_global_vector()

        # add the vectors to the easy and hard lists
        print('getting articles... ', end='', flush=True)
        for article in time_get_str(False):
            easy_texts_list.append(relative_frequency_vector(article[0]))
        for article in time_get_str(True):
            hard_texts_list.append(relative_frequency_vector(article[0]))
        print('done')
        # print('easy text', len(easy_texts_list))
        # print('hard text', len(hard_texts_list))

        # from the vector indeces, form svm vectors, and pass them onto numpy arrays to be processed by the svm
        # index = 1
        for batch in self.get_training_vector_indeces(len(easy_texts_list), len(hard_texts_list), batch_size_times_two):

            # reset svm_vector and result_list
            svm_vectors_list = []
            results_list = []

            for easy_index, hard_index in batch:
                # print('forming a batch of svm vectors:', flush=True)

                # print index and memory usage
                # process = psutil.Process(os.getpid())
                # print("adding n =", index, "; using", process.memory_info().rss // 1000000, "MB... ", end="", flush=True)

                # prepares vectors as arrays
                svm_vectors_list.append(self.prepare_for_svm(easy_texts_list[easy_index], hard_texts_list[hard_index],
                                                             igv))
                results_list.append(-1)  # -1 means the difficulty of text1 < the difficulty of text2
                # same thing as previous two lines but swapped (the algorithm is not necessarily reversible, so it should be trained that way)
                svm_vectors_list.append(self.prepare_for_svm(hard_texts_list[hard_index], easy_texts_list[easy_index],
                                                             igv))
                results_list.append(1)  # 1 means the difficulty of text1 > the difficulty of text2

                # print("done")
                # index += 1

            # print('done forming svm vector; now converting to numpy arrays')
            yield np.array(svm_vectors_list), np.array(results_list)


class ReturnConcatenationVectorizer(ConcatenationVectorizer, ReturnVectorizer):  # multiple inheritance!!!!
    pass


class YieldConcatenationVectorizer(ConcatenationVectorizer, YieldVectorizer):
    pass


class ReturnSubtractionVectorizer(SubtractionVectorizer, ReturnVectorizer):
    pass


class YieldSubtractionVectorizer(SubtractionVectorizer, YieldVectorizer):
    pass


# temporary functions to make fv.txt conform with text preprocessing:

def stem_fv():
    print('opening file... ', end='', flush=True)
    with open('resources/fv_updated.txt') as f:
        data = f.read()
    print('done')

    print('loading data... ', end='', flush=True)
    js_dict = json.loads(data)
    js_len = len(js_dict)
    print('done')

    print('loading acceptable words... ', end='', flush=True)
    with open('resources/words.txt') as f:
        data = f.read()
    acceptable_words_list = set(preprocess(data))
    print('done')

    print('updating dictionary... ', end='\r', flush=True)
    stemmer = SnowballStemmer('english')
    words_to_change = {}
    index = 0
    for key in js_dict:
        index += 1
        print('updating dictionary... ' + str(index) + '/' + str(js_len) + " words to change: " + str(
            len(words_to_change)), end='\r', flush=True)
        fixed = stemmer.stem(key)
        if fixed == key:
            continue
        else:
            if fixed not in words_to_change:
                words_to_change[fixed] = js_dict[key]
            else:
                words_to_change[fixed] += js_dict[key]

            if key not in words_to_change:
                words_to_change[key] = js_dict[key] * -1
            else:
                words_to_change[key] -= js_dict[key]

    for word in words_to_change:
        if word not in js_dict:
            js_dict[word] = words_to_change[word]
        else:
            js_dict[word] += words_to_change[word]

    to_delete = set()

    for word in js_dict:
        if (word not in acceptable_words_list) or js_dict[word] < 10:
            to_delete.add(word)
    print('updating dictionary... deleting ' + str(len(to_delete)) + ' words', end='\r', flush=True)

    for word in to_delete:
        del js_dict[word]

    print('updating dictionary... done')

    print('writing to file... ', end='', flush=True)
    with open('resources/fv_stemmed.txt', 'w') as f:
        f.write(json.dumps(js_dict))
    print('done')


def fix_fv():
    print('opening file... ', end='', flush=True)
    with open('resources/fv.txt') as f:
        data = f.read()
    print('done')

    print('loading data... ', end='', flush=True)
    js_dict = json.loads(data)
    js_len = len(js_dict)
    print('done')

    print('updating dictionary... ', end='\r', flush=True)
    new_words = {}
    words_to_delete = set()
    index = 0
    for key in js_dict:
        index += 1
        print('updating dictionary... ' + str(index) + '/' + str(js_len) + " new words: " + str(
            len(new_words)) + " words to delete: " + str(len(words_to_delete)), end='\r', flush=True)
        fixed = preprocess(key)
        if len(fixed) == 1 and fixed[0] == key:
            continue
        else:
            for new_word in fixed:
                if new_word not in js_dict:
                    new_words[new_word] = js_dict[key]
                else:
                    js_dict[new_word] += js_dict[key]
            words_to_delete.add(key)

    for word in words_to_delete:
        del js_dict[word]
    js_dict.update(new_words)
    print('updating dictionary... done')

    print('writing to file... ', end='', flush=True)
    with open('resources/fv_updated.txt', 'w') as f:
        f.write(json.dumps(js_dict))
    print('done')


if __name__ == '__main__':
    print(__file__)
