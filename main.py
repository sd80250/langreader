import pandas as pd
import numpy as np

df = pd.read_csv('all.csv')
poems = df["content"]

def random(poems):
    return poems[0]

print("Welcome to Langreader's Wonderful World of Language Learning\u2122")


poem_url = input("gimme url for text:")
print("here is a poem of similary difficulty:")
print(random(poems))



