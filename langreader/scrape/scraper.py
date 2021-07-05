import requests
from bs4 import BeautifulSoup
import sqlite3
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

from gutenberg.acquire import load_etext
from gutenberg.cleanup import strip_headers
from gutenberg.query import get_etexts
from gutenberg.query import get_metadata
from gutenberg.acquire.text import _format_download_uri

import sys
import os
from os import path
sys.path.insert(0, "")

import langreader.app.corpus as corpus
import pickle
import wikipedia
import math


# soup is the html (but transformed into a python-manipulatable object)
# that comes from scraping a website
def get_soup_from_URL(URL):
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, 'html.parser')
    return soup


# --scraping Time and Time for Kids for training--
# for time.com specifcially
def scrape_time_links(URL, links_list: set):
    soup = get_soup_from_URL(URL)
    main_body = soup.find('section', class_="content left-rail")

    # add links to list
    for link in main_body.find_all('a'):
        href_str = link.get('href')
        # if the second digit of the string is a number, then it will lead to an article on time.com
        if href_str[1].isdigit():
            links_list.add(href_str)


# for timeforkids.com specifically
def scrape_time_for_kids_links(URL, links_list: set):
    soup = get_soup_from_URL(URL)
    # get every 'a' within every 'h2', which provide the links to the article
    links = soup.find_all('h2', class_="c-article-preview__title")
    for link in links:
        links_list.add(link.find('a').get('href'))


def get_times_articles():  # txt is what text file to put the scraped articles in
    # find the URLs to 2400+ Time articles
    links_list = set()  # making list into a set ensures no duplicates
    for section in ['us', 'politics', 'world', 'health', 'business', 'tech', 'entertainment', 'ideas', \
                    'science', 'history', 'newsfeed', 'sports']:
        original_links_list_size = len(links_list)

        # the page 1 URL has no suffix
        scrape_time_links('https://time.com/section/' + section + '/', links_list)

        page = 2
        # crawl each webpage until at least 200 articles come from that section
        while len(links_list) - original_links_list_size < 200:
            scrape_time_links('https://time.com/section/' + section + '/?page=' + str(page), links_list)
            page += 1
            print('length of links list:', len(links_list))

    # from those URLs, scrape the text
    text_list = []
    number = 0

    for link in links_list:
        soup = get_soup_from_URL('https://time.com' + link)
        print('scraping link', number, link)
        article_string = ""
        for paragraph in soup.find_all('p')[:-1]:  # omit the last paragraph, which is an email address
            article_string += paragraph.get_text() + "\n"
        text_list.append((article_string, 1, 'https://time.com' + link, None, "English", 'time'))
        number += 1

    # put the text in a database
    with sqlite3.connect("resources/sqlite/corpus.sqlite") as con:
        cur = con.cursor()
        cur.executemany("""
		INSERT OR IGNORE INTO Training
		VALUES(?,?,?,?,?,?)
		""", text_list)


def get_times_for_kids_articles():
    # find URLs for 2400+ webpages
    links_list = set()

    for grade in ['k1', 'g2', 'g34', 'g56']:
        original_links_list_size = len(links_list)
        page = 1

        # crawl each webpage until there are 600 articles in the grade
        while len(links_list) - original_links_list_size < 600:
            prev_size = len(links_list)
            scrape_time_for_kids_links("https://www.timeforkids.com/" + grade + "/page/" + str(page) + "/", links_list)
            if (prev_size == len(links_list)): # if the grade level doesn't have enough pages, then break
                break
            page += 1
            print('length of links list:', len(links_list))
            

    # from the URLs, scrape the text
    text_list = []
    number = 0

    for link in links_list:
        soup = get_soup_from_URL(link)
        main_body = soup.find('div', class_='article-show__content-article')
        article_string = ""
        for paragraph in main_body.find_all(['p', 'h2']):
            # finds highlighted words with dictionary definitions, which ruins the layout of the text, and deletes it
            for span in paragraph.find_all('span', class_='definition'):
                span.extract()
            article_string += paragraph.get_text() + "\n"
        text_list.append((article_string, 0, link, link[
            29], 'English', 'time'))  # denotes grade level: either 1, 2, 3, or 5, depending on whether it's 'k1', 'g2', 'g34', or 'g56'
        print("scraped link", number, "with values", 0, link, link[29])
        number += 1

    # put the text in a database
    with sqlite3.connect("resources/sqlite/corpus.sqlite") as con:
        cur = con.cursor()
        cur.executemany("""
		INSERT or IGNORE INTO Training
		VALUES(?,?,?,?,?,?)
		""", text_list)


# --scraping Project Gutenburg texts--
def scrape_christian_texts():
    # urls = set()
    # for start_index in range(1, 177, 25):
    #     soup = get_soup_from_URL('https://www.gutenberg.org/ebooks/bookshelf/119?start_index=' + str(start_index))
    #     booklinks = soup.find_all('li', class_='booklink')
    #     for booklink in booklinks:
    #         urls.add(booklink.find('a').get('href'))

    urls = pickle.load(open('resources/poems/gutenberg_urls.p', 'rb'))
    
    index = 0
    for stub in urls:
        ebook_code = int(stub[8:]) # gets rid of the initial '/ebook/' in string
        print('index', index, 'scraping', str(ebook_code) + '...', end=' ', flush=True)

        try:
            # see if the book is in English
            if 'en' not in get_metadata('language', ebook_code):
                raise NameError('english not in language')
            
            # get text and insert the url within the corpus
            text = strip_headers(load_etext(ebook_code)).strip()
            title = list(get_metadata('title', ebook_code))[0]
            author = list(get_metadata('author', ebook_code))
            author = author[0] if len(author) > 0 else None
            corpus.insert_in_corpus(title, text, 2, \
                url=ebook_code, \
                author=author, exclude_text=True, text_type='gutenberg')
        except Exception as e:

            print(e, 'continue')
            index += 1
            continue
        
        print('done')
        index += 1

    corpus.conn.commit()
    print('changes committed')

# --scraping Spanish texts--
def try_scraping_spanish_site():
    chrome_options = Options()
    chrome_options.add_argument("--incognito")
    chrome_options.add_argument("--window-size=1920x1080")

    driver = webdriver.Chrome(chrome_options=chrome_options, executable_path="resources/chromedriver")

    url = "https://www.newsinslowspanish.com/home/news/beginner"
    usern = "sd80250@gmail.com"
    passw = "$8ppN5DcUW4dk73"

    driver.get(url)
    time.sleep(3)

    elements = driver.find_elements_by_css_selector(".signin")
    signin_button = elements[0]
    signin_button.click()

    elements = driver.find_elements_by_css_selector("#username")
    username = elements[0]
    username.clear()
    username.send_keys(usern)

    elements = driver.find_elements_by_css_selector("#password")
    password = elements[0]
    password.clear()
    password.send_keys(passw)

    elements = driver.find_elements_by_css_selector(".primary")
    login = elements[0]
    login.click()
    
    for element in driver.find_elements_by_css_selector(".story"):
        time.sleep(1)
        element.click()
        
        # driver.back()
        # time.sleep(1)
    # browser = mechanicalsoup.StatefulBrowser()
    # browser.open("https://www.newsinslowspanish.com/home/news/beginner")
    # browser.select_form()
    # soup = browser.form.form

    # username_tag = soup.select(".login-username")[0]
    # password_tag = soup.select(".login-password")[0]

    # username_tag['name'] = 'username'
    # password_tag['name'] = 'password'

    # browser.form.set_input({"username": username, "password": password})
    # browser.launch_browser()
    # # print(browser.page)
    # # print("\n\n")


    # response = browser.submit_selected()
    # browser.launch_browser()

# --scraping Wikipedia and Simple Wikipedia--
def find_and_append_random_texts(n, to_insert, difficult):
    if difficult:
        wikipedia.set_lang('en')
    else:
        wikipedia.set_lang('simple')

    
    texts = wikipedia.random(n)
    if n == 1:
        texts = [texts]
    for text in texts:
        try:
            page = wikipedia.page(text)
        except:
            print('\nfinding another text')
            find_and_append_random_texts(1, to_insert, difficult)
            continue
        to_insert.append((page.content, 1 if difficult else 0, page.url, None, "English", "wikipedia"))
        print(len(to_insert), end='\r', flush=True)


def scrape_wikipedia():
    hard_insert = []
    easy_insert = []
    if path.exists('langreader/scrape/wiki.p'):
        hard_insert = pickle.load(open('langreader/scrape/wiki.p','rb'))
    if path.exists('langreader/scrape/simple_wiki.p'):
        easy_insert = pickle.load(open('langreader/scrape/simple_wiki.p', 'rb'))
    try:
        print("scraping hard texts")
        target = 1400 - len(hard_insert)
        division = math.ceil(target/500)
        for i in range(division):
            find_and_append_random_texts(target//division, hard_insert, True)
        print('\ndone\nscraping easy texts')

        target = 1400 - len(easy_insert)
        division = math.ceil(target/500)
        for i in range(division):
            find_and_append_random_texts(target//division, easy_insert, False)
        print('\ndone')

        to_insert = hard_insert + easy_insert
        
        with sqlite3.connect('resources/sqlite/corpus.sqlite') as con:
            cur = con.cursor()
            cur.executemany("INSERT OR IGNORE INTO Training VALUES (?, ?, ?, ?, ?, ?)", to_insert)
    except Exception as e:
        print("dumping because", e)
        pickle.dump(hard_insert, open('langreader/scrape/wiki.p', 'wb'))
        pickle.dump(easy_insert, open('langreader/scrape/simple_wiki.p', 'wb'))
    

    


if __name__ == '__main__':
    # get_times_articles()
    # get_times_for_kids_articles()
    scrape_wikipedia()
