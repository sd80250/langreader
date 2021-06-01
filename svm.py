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

def preprocess(text):
    text = text.lower()
    # removes punctuation from the text
    for char in text:
        if char in string.punctuation:
            text = text.replace(char, "")
    # tokenizes the string into an array of words
    text = nltk.word_tokenize(text)
    return text
    

def frequency_vector(texts):
    fv = {}
    for text in texts:
        # preprocessing the texts before we add them to the dictionary
        text = preprocess(text)
        for word in text:
            # if not already in frequency vector, initialize a value of 0
            if not word in fv.keys():
                fv[word] = 0
            # if its already in there, increment the value
            else:
                fv[word] += 1
    return fv

global svm

def predict(values):
    return svm.predict(values)

def make_and_test_model(easy_texts_path, hard_texts_path, amount_of_test_data):
    X, y = vectorize.make_training_data(easy_texts_path, hard_texts_path, amount_of_test_data)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.20)
    svm = train_on_kernel('linear', X_train, X_test, y_train, y_test)
    train_on_kernel('poly', X_train, X_test, y_train, y_test)
    train_on_kernel('rbf', X_train, X_test, y_train, y_test)
    train_on_kernel('sigmoid', X_train, X_test, y_train, y_test)

def train_on_kernel(kern, X_train, X_test, y_train, y_test, degree=8):
    if kern == 'poly':
        svclassifier = SVC(kernel = kern, degree = degree)
    else:
        svclassifier = SVC(kernel = kern)
    svclassifier.fit(X_train, y_train)
    y_pred = svclassifier.predict(X_test)
    print("confusion matrix:", confusion_matrix(y_test, y_pred))
    print("classification report", classification_report(y_test, y_pred))
    return svclassifier
