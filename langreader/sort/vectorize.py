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
def get_training_texts(is_hard, pair_name, database_file_path="resources/sqlite/corpus.sqlite"):
    # returns list of tuples of all articles which are easy or hard
    with sqlite3.connect(database_file_path) as con:
        cur = con.cursor()
        cur.execute("""
        SELECT article_text FROM Training
        WHERE difficult=? AND pair=? AND language='English'
        """, (is_hard, pair_name))
        return cur.fetchall()


def preprocess(text):
    processed_text = text.lower()
    # replaces hyphens, em/en dashes, and horizontal bars with space
    processed_text = re.sub(r'[-–—―]', ' ', processed_text)
    # removes punctuation and numerals from the text
    processed_text = re.sub(r'[^\w\s]|[0-9]', '', processed_text)
    # tokenizes the string into an array of words
    processed_text = nltk.word_tokenize(processed_text)
    # runs words through snowball stemming algorithm
    processed_text = [stemmer.stem(word) for word in processed_text]
    return processed_text


def relative_frequency_vector(text, fv=None, ret_new_characteristics=False, normalize=True):
    if fv is None:
        fv = {}
    # preprocessing the texts before we add them to the dictionary
    processed_text = preprocess(text)
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
        if normalize:
            fv[key] = fv[key] / total / 0.07 # 0.07 is the rough relative frequency of the word 'the' globally, making this essentially a min-max normalization
        else:
            fv[key] = fv[key] / total

    if ret_new_characteristics:
        new_characteristics = get_new_characteristics(text, processed_text)
        return fv, new_characteristics
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

        for article in get_training_texts(False):
            real_words.update(preprocess(article[0]))

        for article in get_training_texts(True):
            real_words.update(preprocess(article[0]))

        # we have to make two for-loops because you can't delete a key in a dictionary while accessing it
        for key in js:
            if (key not in real_words) or (js[key] <= min_freq):
                spurious_words.add(key)
        for spurious_word in spurious_words:
            del js[spurious_word]

        print('done')

    print('making values log and fitting to training scale... ', end='', flush=True)
    min_val = 1000000000
    max_val = -1
    for key in js:
        min_val = min(min_val, js[key])
        max_val = max(max_val, js[key])
    min_val = math.log(min_val)
    max_val = math.log(max_val)

    for key in js:
        # min-max normalization of log values
        js[key] = (math.log(js[key]) - min_val) / (max_val - min_val)
    print('done')

    # store dictionary onto a binary file using pickle
    print("dumping dictionary... ", end='', flush=True)
    pickle.dump(js, open(result_file_path, 'wb'))
    print("done")


def get_new_characteristics(text, preprocessed_text):
    no_words = len(preprocessed_text)
    no_sentences = len(nltk.sent_tokenize(text))

    avg_sentence_length = no_words/no_sentences

    return (avg_sentence_length, )


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


class SubtractionWithNewCharacteristicsVectorizer(SubtractionVectorizer):
    def prepare_for_svm(self, text_vector_A, text_vector_B, indexed_global_vector, new_characteristics_A=None, new_characteristics_B=None):
        # new characteristics A and B should both be tuples of length 1 in this order:
        # (average sentence length, )
        # this characteristic comes first in the svm_vector

        if not new_characteristics_A or not new_characteristics_B:
            raise Exception('subtraction with new charcateristics vectorizer should have new_characteristics arguments!')
        no_of_entries = len(indexed_global_vector)
        no_chars = len(new_characteristics_A)
        svm_vector = [0] * (no_chars + 2 * no_of_entries)

        i = 0
        for characteristic in new_characteristics_A:
            svm_vector[i] = characteristic
            i += 1 

        for key, value in text_vector_A.items():
            if key in indexed_global_vector:
                svm_vector[indexed_global_vector[key][1] + no_chars] = value
                svm_vector[indexed_global_vector[key][1] + no_chars + no_of_entries] = indexed_global_vector[key][0]

        i = 0
        for characteristic in new_characteristics_B:
            svm_vector[i] -= characteristic
            i += 1 
        
        for key, value in text_vector_B.items():
            if key in indexed_global_vector:
                svm_vector[indexed_global_vector[key][1] + no_chars] -= value
                svm_vector[indexed_global_vector[key][1] + no_chars + no_of_entries] -= indexed_global_vector[key][0]

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
        for article in get_training_texts(False):
            easy_texts_list.append(relative_frequency_vector(article[0]))
        for article in get_training_texts(True):
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

    def make_training_data(self, batch_size_times_two):
        easy_texts_list = []
        hard_texts_list = []

        # make an indexed_global_vector
        igv = get_indexed_global_vector()

        # add the vectors to the easy and hard lists
        print('getting articles... ', end='', flush=True)
        for article in get_training_texts(False):
            easy_texts_list.append(relative_frequency_vector(article[0]))
        for article in get_training_texts(True):
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

    def get_training_and_test_vector_indeces(self, length_A, length_B, n,
                                             test_train_split=.667):  # test split is the proportion of values in list A and list B which will be partitioned off for training
        a_list = range(length_A)
        b_list = range(length_B)
        a_training = random.sample(a_list, int(length_A * test_train_split))
        b_training = random.sample(b_list, int(length_B * test_train_split))
        a_test = [a for a in a_list if a not in a_training]
        b_test = [b for b in b_list if b not in b_training]

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
        for article in get_training_texts(False):
            easy_texts_list.append(relative_frequency_vector(article[0]))
        for article in get_training_texts(True):
            hard_texts_list.append(relative_frequency_vector(article[0]))
        print('done')

        for i in self.yield_vectors(easy_texts_list, hard_texts_list, igv, batch_size_times_two, test_train_split):
            yield i
    
    def yield_vectors(self, easy_texts_list, hard_texts_list, igv, batch_size_times_two, test_train_split):
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


class VariedLengthReturnVectorizer(ReturnVectorizer):
    def make_test_and_training_data(self, test_train_split=.9):
        igv = get_indexed_global_vector()

        print('getting articles... ', end='', flush=True)
        easy_texts_list = [article[0] for article in get_training_texts(False)]
        hard_texts_list = [article[0] for article in get_training_texts(True)]
        print(len(easy_texts_list), len(hard_texts_list))

        # splits texts up into short, normal, and long groups randomly
        random.shuffle(easy_texts_list)
        random.shuffle(hard_texts_list)
        
        test_amount = int(min(len(easy_texts_list), len(hard_texts_list))*(1-test_train_split))
        easy_texts_list_test = easy_texts_list[:test_amount]
        hard_texts_list_test = hard_texts_list[:test_amount]

        easy_texts_list = easy_texts_list[test_amount:]
        hard_texts_list = hard_texts_list[test_amount:]

        short_amount = int(len(easy_texts_list)/6.2/5)
        normal_amount = int(len(easy_texts_list)/6.2)

        easy_short_texts_list = easy_texts_list[:short_amount]
        easy_normal_texts_list = easy_texts_list[short_amount:short_amount+normal_amount]
        easy_long_texts_list = easy_texts_list[short_amount+normal_amount:]

        short_amount = int(len(hard_texts_list)/6.2/5)
        normal_amount = int(len(hard_texts_list)/6.2)

        hard_short_texts_list = hard_texts_list[:short_amount]
        hard_normal_texts_list = hard_texts_list[short_amount:short_amount+normal_amount]
        hard_long_texts_list = hard_texts_list[short_amount+normal_amount:]
        
        easy_texts_list = []
        hard_texts_list = []

        # process short texts
        for text in easy_short_texts_list:
            parts = random.randint(3, 8)
            word_list = nltk.word_tokenize(text)

            i = 0
            for part in range(1, parts + 1):
                j = int(part/parts*len(word_list))
                easy_texts_list.append(relative_frequency_vector(' '.join(word_list[i:j])))
                i = j


        for text in hard_short_texts_list:
            parts = random.randint(3, 8)
            word_list = nltk.word_tokenize(text)

            i = 0
            for part in range(1, parts + 1):
                j = int(part/parts*len(word_list))
                hard_texts_list.append(relative_frequency_vector(' '.join(word_list[i:j])))
                i = j


        # process normal texts
        easy_texts_list.extend([relative_frequency_vector(text) for text in easy_normal_texts_list])
        hard_texts_list.extend([relative_frequency_vector(text) for text in hard_normal_texts_list])

        # process long texts
        index = 0
        while index < len(easy_long_texts_list):
            jndex = index + random.randint(2, 8)
            text_string = '\n'.join(easy_long_texts_list[index:jndex])
            easy_texts_list.append(relative_frequency_vector(text_string))
            index = jndex

        index = 0
        while index < len(hard_long_texts_list):
            jndex = index + random.randint(2, 8)
            text_string = '\n'.join(hard_long_texts_list[index:jndex])
            hard_texts_list.append(relative_frequency_vector(text_string))
            index = jndex
        
        print("done")

        # create the vectors
        random.shuffle(easy_texts_list)
        random.shuffle(hard_texts_list)
        random.shuffle(easy_texts_list_test)
        random.shuffle(hard_texts_list_test)

        sgd_vectors_list = []
        training_results_list = []

        test_vectors_list = []
        test_results_list = []

        for easy_text, hard_text in zip(easy_texts_list, hard_texts_list):
            

            sgd_vectors_list.append(self.prepare_for_svm(easy_text, hard_text, igv))
            training_results_list.append(-1)  

            sgd_vectors_list.append(self.prepare_for_svm(hard_text, easy_text, igv))
            training_results_list.append(1)

        easy_texts_list_test = [relative_frequency_vector(a) for a in easy_texts_list_test]
        hard_texts_list_test = [relative_frequency_vector(a) for a in hard_texts_list_test]

        for easy_texts_test, hard_texts_test in zip(easy_texts_list_test, hard_texts_list_test):


            test_vectors_list.append(self.prepare_for_svm(easy_texts_test, hard_texts_test, igv))
            test_results_list.append(-1)

            test_vectors_list.append(self.prepare_for_svm(hard_texts_test, easy_texts_test, igv))
            test_results_list.append(1)
        
        return np.asarray(sgd_vectors_list), np.asarray(training_results_list), np.asarray(test_vectors_list), np.asarray(test_results_list)   


class ReturnSubtractionWithNewCharacteristicsVectorizer(ReturnVectorizer, SubtractionWithNewCharacteristicsVectorizer):
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
        for article in get_training_texts(False):
            easy_texts_list.append(article[0])
        for article in get_training_texts(True):
            hard_texts_list.append(article[0])
        print('done')

        # from the vector indeces, form svm vectors, and pass them onto numpy arrays to be processed by the svm
        for easy_index, hard_index in self.get_training_vector_indeces(len(easy_texts_list), len(hard_texts_list), n):
            easy_article = easy_texts_list[easy_index]
            hard_article = hard_texts_list[hard_index]

            easy_vector, easy_chars = relative_frequency_vector(easy_texts_list[easy_index], ret_new_characteristics=True)
            hard_vector, hard_chars = relative_frequency_vector(hard_texts_list[hard_index], ret_new_characteristics=True)

            vector = self.prepare_for_svm(easy_vector, hard_vector, igv, new_characteristics_A=easy_chars, new_characteristics_B=hard_chars)
            svm_vectors_list.append(vector)
            results_list.append(-1)  # -1 means the difficulty of text1 < the difficulty of text2
            # same thing as previous two lines but swapped (the algorithm is not necessarily reversible, so it should
            # be trained that way)
            svm_vectors_list.append([i * -1 for i in vector])
            results_list.append(1)  # 1 means the difficulty of text1 > the difficulty of text2

        return np.asarray(svm_vectors_list), np.asarray(results_list)


class YieldSubtractionVectorizer(SubtractionVectorizer, YieldVectorizer):
    def yield_vectors(self, easy_texts_list, hard_texts_list, igv, batch_size_times_two, test_train_split):
        # copied and modified from YieldVectorizer
        for training_batch, test_batch in self.get_training_and_test_vector_indeces(len(easy_texts_list),
                                                                                    len(hard_texts_list),
                                                                                    batch_size_times_two,
                                                                                    test_train_split=test_train_split):
            sgd_vectors_list = []
            training_results_list = []

            test_list = []
            test_results_list = []

            for easy_index, hard_index in training_batch:
                vect = self.prepare_for_svm(easy_texts_list[easy_index], hard_texts_list[hard_index], igv)

                sgd_vectors_list.append(vect)
                training_results_list.append(-1) 

                sgd_vectors_list.append([v * -1 for v in vect])
                training_results_list.append(1)

            for easy_index, hard_index in test_batch:
                vect = self.prepare_for_svm(easy_texts_list[easy_index], hard_texts_list[hard_index], igv)

                test_list.append()
                test_results_list.append(-1)  

                test_list.append([v * -1 for v in vect])
                test_results_list.append(1)

            yield np.array(sgd_vectors_list), np.array(training_results_list), np.array(test_list), np.array(
                test_results_list)


class VLRSWNCVectorizer(SubtractionWithNewCharacteristicsVectorizer, VariedLengthReturnVectorizer):
    def add_fv_and_chars(self, text, fv_list, chars_list):
        fv, chars = relative_frequency_vector(text, ret_new_characteristics=True)
        fv_list.append(fv)
        chars_list.append(chars)
        

    def make_test_and_training_data(self, pair, test_train_split=.9):
        igv = get_indexed_global_vector()

        print('getting articles... ', end='', flush=True)
        easy_texts_list = [article[0] for article in get_training_texts(False, pair)]
        hard_texts_list = [article[0] for article in get_training_texts(True, pair)]
        print(len(easy_texts_list), len(hard_texts_list))

        # splits texts up into short, normal, and long groups randomly
        random.shuffle(easy_texts_list)
        random.shuffle(hard_texts_list)
        
        test_amount = int(min(len(easy_texts_list), len(hard_texts_list))*(1-test_train_split))
        easy_texts_list_test_ = easy_texts_list[:test_amount]
        hard_texts_list_test_ = hard_texts_list[:test_amount]
        

        easy_texts_list = easy_texts_list[test_amount:]
        hard_texts_list = hard_texts_list[test_amount:]

        short_amount = int(len(easy_texts_list)/6.2/5)
        normal_amount = int(len(easy_texts_list)/6.2)

        easy_short_texts_list = easy_texts_list[:short_amount]
        easy_normal_texts_list = easy_texts_list[short_amount:short_amount+normal_amount]
        easy_long_texts_list = easy_texts_list[short_amount+normal_amount:]

        short_amount = int(len(hard_texts_list)/6.2/5)
        normal_amount = int(len(hard_texts_list)/6.2)

        hard_short_texts_list = hard_texts_list[:short_amount]
        hard_normal_texts_list = hard_texts_list[short_amount:short_amount+normal_amount]
        hard_long_texts_list = hard_texts_list[short_amount+normal_amount:]
        
        easy_texts_list = []
        easy_chars_list = []
        hard_texts_list = []
        hard_chars_list = []

        # process short texts
        print('processing short texts...', end=' ', flush=True)
        for text in easy_short_texts_list:
            sent_list = nltk.sent_tokenize(text)
            parts = min(random.randint(3, 8), len(sent_list))
            
            i = 0
            for part in range(1, parts + 1):
                j = int(part/parts*len(sent_list))
                self.add_fv_and_chars(' '.join(sent_list[i:j]), easy_texts_list, easy_chars_list)
                i = j

        for text in hard_short_texts_list:
            sent_list = nltk.sent_tokenize(text)
            parts = min(random.randint(3, 8), len(sent_list))
            
            i = 0
            for part in range(1, parts + 1):
                j = int(part/parts*len(sent_list))
                self.add_fv_and_chars(' '.join(sent_list[i:j]), hard_texts_list, hard_chars_list)
                i = j

        print('done', len(easy_texts_list), len(hard_texts_list))

        # process normal texts
        print('processing normal texts...', end=' ', flush=True)
        for text in easy_normal_texts_list:
            self.add_fv_and_chars(text, easy_texts_list, easy_chars_list)
        
        for text in hard_normal_texts_list:
            self.add_fv_and_chars(text, hard_texts_list, hard_chars_list)
        print("done", len(easy_texts_list), len(hard_texts_list))

        # process long texts
        print('processing long texts...', end=' ', flush=True)
        index = 0
        while index < len(easy_long_texts_list):
            jndex = index + random.randint(2, 8)
            text_string = '\n'.join(easy_long_texts_list[index:jndex])
            self.add_fv_and_chars(text_string, easy_texts_list, easy_chars_list)
            index = jndex

        index = 0
        while index < len(hard_long_texts_list):
            jndex = index + random.randint(2, 8)
            text_string = '\n'.join(hard_long_texts_list[index:jndex])
            self.add_fv_and_chars(text_string, hard_texts_list, hard_chars_list)
            index = jndex
        print("done", len(easy_texts_list), len(hard_texts_list))
        print("done")

        # create the vectors
        print('creating training vectors...', end=' ', flush=True)
        random.shuffle(easy_texts_list)
        random.shuffle(hard_texts_list)
        random.shuffle(easy_texts_list_test_)
        random.shuffle(hard_texts_list_test_)

        sgd_vectors_list = []
        training_results_list = []

        test_vectors_list = []
        test_results_list = []

        for easy_text, easy_char, hard_text, hard_char in zip(easy_texts_list, easy_chars_list, hard_texts_list, hard_chars_list):
            
            vector = self.prepare_for_svm(easy_text, hard_text, igv, new_characteristics_A=easy_char, new_characteristics_B=hard_char)
            sgd_vectors_list.append(vector)
            training_results_list.append(-1)  

            sgd_vectors_list.append([i * -1 for i in vector])
            training_results_list.append(1)
        print("done")

        # make test vectors
        print('creating test vectors...', end=' ', flush=True)
        easy_texts_list_test = []
        easy_chars_list_test = []
        hard_texts_list_test = []
        hard_chars_list_test = []

        for a in easy_texts_list_test_:
            self.add_fv_and_chars(a, easy_texts_list_test, easy_chars_list_test)

        for a in hard_texts_list_test_:
            self.add_fv_and_chars(a, hard_texts_list_test, hard_chars_list_test)

        for easy_text, easy_char, hard_text, hard_char in zip(easy_texts_list_test, easy_chars_list_test, hard_texts_list_test, hard_chars_list_test):

            vector = self.prepare_for_svm(easy_text, hard_text, igv, new_characteristics_A=easy_char, new_characteristics_B=hard_char)
            test_vectors_list.append(vector)
            test_results_list.append(-1)

            test_vectors_list.append([i * -1 for i in vector])
            test_results_list.append(1)
        print("done")
        
        return sgd_vectors_list, training_results_list, test_vectors_list, test_results_list   
 


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
    text = """
    Local elections was held in  Cabuyao City on May 9, 2016 within the Philippine general election. The voters elected for the elective local posts in the city: the mayor, vice mayor, and ten councilors.


== Overview ==
Incumbent Mayor Isidro "Jun" L. Hemedes, Jr. decided not to run for mayor his son, Councilor Ismael Hemedes is running for Mayor under the Nacionalista Party, His opponents were Julio Alcasabas of the Liberal Party, Incumbent Vice Mayor Rommel Gecolea of PDP–Laban and Councilor Jaime Batallones of the United Nationalist Alliance.
Vice Mayor Rommel Gecolea is term-limited, Incumbent Mayor Jun Hemedes, Jr. is running in that position, His opponents were councilors Jose Benson "Sonny" Aguillo, son of Proceso and Nila Aguillo and Benjamin Del Rosario.


== Candidates ==
^1  Running as an Independent candidate


=== Mayor ===


=== Vice Mayor ===


=== Councilors ===


== References ==
    """
    print(get_new_characteristics(text, preprocess(text)))

