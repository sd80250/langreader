import pandas as pd
import csv
import sqlite3
import nltk
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import vectorize
from sklearn.svm import SVC
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split
from sklearn.linear_model import SGDClassifier
import pickle
import os, psutil
import time

def make_and_test_model(amount_of_test_data_times_two):
    # get training data
    print("making training data:", flush=True)
    X, y = vectorize.make_training_data(amount_of_test_data_times_two)
    print("done making training data")

    # split data into training and test data
    print("spliting training data... ", end='', flush=True)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.20)
    print("done")

    # make the svm go
    print("training svm:", flush=True)
    svm = train_on_kernel('linear', X_train, X_test, y_train, y_test)
    print("done training svm")

    # store svm onto a binary file using pickle
    print("dumping svm... ", end='', flush=True)
    pickle.dump(svm, open('svm_model.p', 'wb'))
    print("done")

    # train_on_kernel('poly', X_train, X_test, y_train, y_test)
    # train_on_kernel('rbf', X_train, X_test, y_train, y_test)
    # train_on_kernel('sigmoid', X_train, X_test, y_train, y_test)

def train_on_kernel(kern, X_train, X_test, y_train, y_test, degree=8):
    if kern == 'poly':
        svclassifier = SVC(kernel = kern, degree = degree)
    else:
        svclassifier = SVC(kernel = kern)
    
    print("fitting svm... ", end = "", flush=True)
    svclassifier.fit(X_train, y_train)
    
    process = psutil.Process(os.getpid())
    print("done; used", process.memory_info().rss // 1000000, "MB memory")

    print("predicting svm... ", end = "", flush=True)
    y_pred = svclassifier.predict(X_test)
    print("done")

    # tests how accurate the trained model is
    print("confusion matrix:\n", confusion_matrix(y_test, y_pred))
    print("classification report\n", classification_report(y_test, y_pred))
    return svclassifier

# preferably make data_per_batch_times_two any integer of the factorization 5*2^n 
def make_and_test_SGD_model(data_per_batch_times_two, n_iters):
    clf = SGDClassifier(shuffle=True, loss='hinge')
    completion_time_list = [None] * 10
    completion_time_index = 0
    total_tested = 0
    total_correct = 0
    test_size = 0.20
    try:
        for i in range(0, n_iters):
            print("iteration", i, ":")
            batch_number = 1
            # time the process
            start_time = time.time()

            for X, y in vectorize.yield_training_data(data_per_batch_times_two):
                # split batch in two
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size)
                
                # actual training
                print("partially fitting sgd... ", end="", flush=True)
                clf.partial_fit(X_train, y_train, classes=np.unique(y))

                # calculate average score
                total_tested += 1
                total_correct += clf.score(X_test, y_test)

                # calculate time elapsed and estimated time till completion
                time_elapsed = time.time()-start_time
                batches_left = 563*641/data_per_batch_times_two*(n_iters-i)-batch_number
                completion_time_list[completion_time_index % 10] = time_elapsed*batches_left
                total_no = 0
                total = 0
                for j in completion_time_list:
                    if j is not None:
                        total_no += 1
                        total += j
                completion_time = total / total_no

                # get memory and accuracy info
                process = psutil.Process(os.getpid())
                print("done; memory =", process.memory_info().rss // 1000000, "MB; score =", total_correct/total_tested, "estimated time left: ", "%02d:%02d:%02d" % (completion_time // 3600, (completion_time % 3600 // 60), (completion_time % 60 // 1)))
                batch_number += 1
                completion_time_index += 1
                
                # time the process
                start_time = time.time()
            print()
            pickle.dump(clf, open('sgd_model_' + str(i) + '.p', 'wb'))
        
        print("training done, writing to file... ", end="", flush=True)
        pickle.dump(clf, open('sgd_model.p', 'wb'))
        print("done")
    except:
        print("interrupted, writing to file... ", end="", flush=True)
        pickle.dump(clf, open('sgd_model_interrupted.p', 'wb'))
        print("done")
# make_and_test_model(400)

make_and_test_SGD_model(160, 5)