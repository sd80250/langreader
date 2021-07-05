'''
Application ID: 	b7ab0cc5
App Key: 	5fe7ff170dace016d7f4576e2cfcc862
'''

import requests
import json
import streamlit as st

@st.cache
def find_def(word):
    APP_ID = 'b7ab0cc5'
    APP_KEY = '5fe7ff170dace016d7f4576e2cfcc862'
    language = 'en-gb'
    url = 'https://od-api.oxforddictionaries.com/api/v2/entries/'  + language + '/'  + word.lower()
    r = requests.get(url, headers = {'app_id' : APP_ID, 'app_key' : APP_KEY})

    if r.status_code == 200:

        #print("Code {}\n".format(r.status_code))
        #print("Text: ", r.text)
        #print("Json: ", json.dumps(r.json()))

        output_text = ""

        count = 1
        word_dict = json.loads(r.text.encode('utf8').decode('ascii', 'ignore'))
        for one in word_dict["results"]:
            for two in one["lexicalEntries"]:
                for three in two["entries"]:
                    for definition in three["senses"]: 
                        if "definitions" in definition:
                            output_text += "{}. {}\n\n".format(count, definition["definitions"][0])
                            count += 1
        return output_text
    else:
        print(r.status_code)
        return False
        

if __name__ == "__main__":
    print(find_def("test"))