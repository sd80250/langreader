import pandas as pd
import csv
import sqlite3
import nltk


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