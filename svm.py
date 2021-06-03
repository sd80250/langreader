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
import pickle
import os, psutil

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

make_and_test_model(400)