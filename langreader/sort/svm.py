import sys
import os
sys.path.insert(0, "")

import numpy as np
import langreader.sort.vectorize as v
from sklearn.svm import SVC
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.linear_model import SGDClassifier
from sklearn import preprocessing
import pickle
import os, psutil
import time

svm_model = None
indexed_global_vector = None
vectorizer = None

def make_and_test_model(name='langreader/sort/resources/svm_model_varied_size.p', samples=270):
    #TODO: scrape new texts for training/testing
    # get training data
    print("making training data:", flush=True)
    vectorizer = v.VLRSWNCVectorizer()
    X_train = []
    y_train = []
    X_test = []
    y_test = []
    for pair in ['time', 'wikipedia']:
        one, two, three, four = vectorizer.make_test_and_training_data(pair)
        X_train.extend(one)
        y_train.extend(two)
        X_test.extend(three)
        y_test.extend(four)

    X_train = np.asarray(X_train)
    y_train = np.asarray(y_train)
    X_test = np.asarray(X_test)
    y_test = np.asarray(y_test)
    print(X_train.shape, y_train.shape, X_test.shape, y_test.shape)

    # # normalize sentence length column for training
    # scaler = preprocessing.StandardScaler().fit(X_train[:, [0]])
    # X_train_slice = scaler.transform(X_train[:, [0]])
    # X_train = np.concatenate((X_train_slice, X_train[:, 1:]), axis=1)
    # print(X_train.shape)

    # # same thing for test
    # X_test_slice = scaler.transform(X_test[:, [0]])
    # X_test = np.concatenate((X_test_slice, X_test[:, 1:]), axis=1)
    # print(X_test.shape)

    print("done making training data")

    # make the svm go
    print("training svm:", flush=True)
    svm = train_on_kernel('rbf', X_train, X_test, y_train, y_test)
    print("done training svm")

    # store svm onto a binary file using pickle
    print("dumping svm... ", end='', flush=True)
    pickle.dump(svm, open(name, 'wb'))
    print("done")


def train_on_kernel(kern, X_train, X_test, y_train, y_test, degree=8):
    if kern == 'poly':
        svclassifier = SVC(kernel=kern, degree=degree)
    else:
        svclassifier = SVC(kernel=kern)

    print("fitting svm... ", end="", flush=True)
    svclassifier.fit(X_train, y_train)

    process = psutil.Process(os.getpid())
    print("done; used", process.memory_info().rss // 1000000, "MB memory")

    print("predicting svm... ", end="", flush=True)
    y_pred = svclassifier.predict(X_test)
    print("done")

    # tests how accurate the trained model is
    print("confusion matrix:\n", confusion_matrix(y_test, y_pred))
    print("classification report:\n", classification_report(y_test, y_pred))
    return svclassifier


# preferably make data_per_batch_times_two any integer of the factorization 5*2^n
def make_and_test_SGD_model(data_per_batch_times_two, n_iters, model_name="sgd_model"):
    clf = SGDClassifier()
    completion_time_list = [None] * 10
    completion_time_index = 0
    accuracy_list = [None] * 200
    accuracy_index = 0
    test_size = 0.333
    vectorizer = v.YieldSubtractionVectorizer()
    # rbf_feature = RBFSampler()

    try:
        for i in range(0, n_iters):
            print("iteration", i, ":")
            batch_number = 1
            # time the process
            start_time = time.time()

            for X_train, y_train, X_test, y_test in vectorizer.make_test_and_training_data(data_per_batch_times_two):
                # actual training
                print("partially fitting sgd... ", end="", flush=True)
                # X_features = rbf_feature.fit_transform(X_train)
                clf.partial_fit(X_train, y_train, classes=np.asarray([-1, 1]))

                # calculate average score
                total_tested = 0
                total_correct = 0
                # X_test_features = rbf_feature.fit_transform(X_test)
                accuracy_list[accuracy_index % 200] = clf.score(X_test, y_test)

                for j in accuracy_list:
                    if j is not None:
                        total_tested += 1
                        total_correct += j
                accuracy = total_correct / total_tested

                accuracy_index += 1

                # calculate time elapsed and estimated time till completion
                time_elapsed = time.time() - start_time
                batches_left = 563 * 641 / data_per_batch_times_two * (n_iters - i) - batch_number
                completion_time_list[completion_time_index % 10] = time_elapsed * batches_left
                total_no = 0
                total = 0
                for j in completion_time_list:
                    if j is not None:
                        total_no += 1
                        total += j
                completion_time = total / total_no

                batch_number += 1
                completion_time_index += 1

                # get memory and accuracy info
                process = psutil.Process(os.getpid())
                print("done; memory =", process.memory_info().rss // 1000000, "MB; score =", accuracy,
                      "; amount of data trained:", batch_number * data_per_batch_times_two * (1 - test_size),
                      "; estimated time left: ", "%02d:%02d:%02d" % (
                      completion_time // 3600, (completion_time % 3600 // 60), (completion_time % 60 // 1)), end="\n\r")

                # time the process
                start_time = time.time()
                # if (batch_number*data_per_batch_times_two*(1-test_size) > 6000 and accuracy > 0.999):
                #     print("training done, writing to file... ", end="", flush=True)
                #     pickle.dump(clf, open('sgd_model_1.p', 'wb'))
                #     print("done")
                #     quit()
            print()

        print("training done, writing to file... ", end="", flush=True)
        pickle.dump(clf, open('models/' + model_name + '.p', 'wb'))
        print("done")
    except (KeyboardInterrupt, Exception) as e:
        print(e)
        print("interrupted, writing to file... ", end="", flush=True)
        pickle.dump(clf, open('models/' + model_name + '_interrupted.p', 'wb'))
        print("done")


def load_model(file_path):
    return pickle.load(open(file_path, 'rb'))


def compare(rfv_text1, rfv_text2, file_path='langreader/sort/resources/svm_model.p'):
    global svm_model
    global indexed_global_vector
    global vectorizer

    if not svm_model:
        svm_model = load_model(file_path)
    if not indexed_global_vector:
        indexed_global_vector = v.get_indexed_global_vector()
    if not vectorizer:
        vectorizer = v.ReturnSubtractionVectorizer()
    
    return svm_model.predict(np.asarray(vectorizer.prepare_for_svm(rfv_text1, rfv_text2, indexed_global_vector)).reshape((1, -1)))


if __name__ == "__main__":
    make_and_test_model()
