import sqlite3
import vectorize as v
import pickle
from sklearn.svm import SVC
from sklearn.metrics import classification_report, confusion_matrix
import numpy as np

def time_for_kids_get_data(): # returns list of tuples of all articles which are easy or hard
    with sqlite3.connect("corpus.sqlite") as con:
        cur = con.cursor()
        cur.execute("""
        SELECT * FROM TestAndTraining
        WHERE difficult=0
        """)
        return cur.fetchall()

def analyse(): # oops i'm not british i swear
    print("getting data... ", end = "", flush=True)
    data = time_for_kids_get_data()
    print("done")

    # print(data)
    # quit()

    k1_list = []
    g2_list = []
    g34_list = []
    g56_list = []

    print("sorting data by grade level... ", end="", flush=True)
    for article_text, difficult, article_url, grade_level in data:
        if grade_level == 1:
            k1_list.append(v.make_relative(v.frequency_vector(article_text)))
        elif grade_level == 2:
            g2_list.append(v.make_relative(v.frequency_vector(article_text)))
        elif grade_level == 3:
            g34_list.append(v.make_relative(v.frequency_vector(article_text)))
        elif grade_level == 5:
            g56_list.append(v.make_relative(v.frequency_vector(article_text)))
    print("done")
    
    print("loading svm... ", end = "", flush=True)
    svclassifier = pickle.load(open('models/svm_model563.p', 'rb'))
    print("done")

    pair_data(k1_list, g2_list, g34_list, g56_list, svclassifier)

    
def pair_data(list1, list2, list3, list4, svclassifier): # lists should be in order from easiest to hardest
    vectorizer = v.SVMSubtractionVectorizer()
    indexed_global_vector = v.make_indexed(v.global_vector())
    for name, easy_list, hard_list in [("1v2", list1, list2), ("1v3", list1, list3), ("1v5", list1, list4), ("2v3", list2, list3), ("2v5", list2, list4), ("3v5", list3, list4)]:
        X_test, y_test = pair_data_pair(vectorizer, easy_list, hard_list, indexed_global_vector)
        print("predicting results for", name, "pair... ", end="", flush=True)
        y_pred = svclassifier.predict(X_test)
        print("done")

        # tests how accurate the trained model is
        print("confusion matrix:\n", confusion_matrix(y_test, y_pred))
        print("classification report:\n", classification_report(y_test, y_pred))

def pair_data_pair(vectorizer, list1, list2, indexed_global_vector): # list1 = easier texts, list2 = harder texts
    svm_vectors_list = []
    results_list = []
    for list1_index, list2_index in vectorizer.get_training_vector_indeces(len(list1), len(list2), min(len(list1), len(list2))):
        svm_vectors_list.append(vectorizer.prepare_for_svm(list1[list1_index], list2[list2_index], indexed_global_vector))
        results_list.append(-1)

        svm_vectors_list.append(vectorizer.prepare_for_svm(list2[list2_index], list1[list1_index], indexed_global_vector))
        results_list.append(1)
    return svm_vectors_list, results_list
