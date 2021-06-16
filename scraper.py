import requests
from bs4 import BeautifulSoup
import re
from nltk.tokenize import word_tokenize
import sqlite3
from selenium import webdriver
import time
from selenium.webdriver.chrome.options import Options

# soup is the html (but transformed into a python-manipulatable object) 
# that comes from scraping a website
def get_soup_from_URL(URL):
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, 'html.parser')
    return soup

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
	links = soup.find_all('h2', class_ = "c-article-preview__title")
	for link in links:
		links_list.add(link.find('a').get('href'))

def get_times_articles(): # txt is what text file to put the scraped articles in
	# find the URLs to 600+ Time articles
	links_list = set() # making list into a set ensures no duplicates
	for section in ['us', 'politics', 'world', 'health', 'business', 'tech', 'entertainment', 'ideas',\
	'science', 'history', 'newsfeed', 'sports']:
		original_links_list_size = len(links_list)

		# the page 1 URL has no suffix
		scrape_time_links('https://time.com/section/' + section + '/', links_list)

		page = 2	
		# crawl each webpage until at least 50 articles come from that section
		while len(links_list) - original_links_list_size < 50: 
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
		for paragraph in soup.find_all('p')[:-1]: # omit the last paragraph, which is an email address
			article_string += paragraph.get_text() + "\n"
		text_list.append((article_string, 1, 'https://time.com' + link, None))
		number += 1


	# put the text in a database
	with sqlite3.connect("corpus.sqlite") as con:
		cur = con.cursor()
		cur.executemany("""
		INSERT OR IGNORE INTO TestAndTraining(article_text, difficult, article_url, grade_level)
		VALUES(?,?,?,?)
		""", text_list)


def get_times_for_kids_articles():

	# find URLs for 600+ webpages
	links_list = set()

	for grade in ['k1', 'g2', 'g34', 'g56']:
		original_links_list_size = len(links_list)
		page = 1

		# crawl each webpage until there are 150 articles in the grade
		while len(links_list) - original_links_list_size < 150:
			scrape_time_for_kids_links("https://www.timeforkids.com/" + grade + "/page/" + str(page) + "/", links_list)
			page += 1
			print('length of links list:', len(links_list))

	# from the URLs, scrape the text
	text_list = []
	number = 0

	for link in links_list:
		soup = get_soup_from_URL(link)
		main_body = soup.find('div', class_= 'article-show__content-article')
		article_string = ""
		for paragraph in main_body.find_all(['p', 'h2']):
			# finds highlighted words with dictionary definitions, which ruins the layout of the text, and deletes it
			for span in paragraph.find_all('span', class_='definition'): 
				span.extract()
			article_string += paragraph.get_text() + "\n"
		text_list.append((article_string, 0, link, link[29])) # denotes grade level: either 1, 2, 3, or 5, depending on whether it's 'k1', 'g2', 'g34', or 'g56'
		print("scraped link", number, "with values", 0, link, link[29])
		number += 1
	
	# put the text in a database
	with sqlite3.connect("corpus.sqlite") as con:
		cur = con.cursor()
		cur.executemany("""
		INSERT or IGNORE INTO TestAndTraining(article_text, difficult, article_url, grade_level)
		VALUES(?,?,?,?)
		""", text_list)

# get_times_articles()
# get_times_for_kids_articles()

# SCRAPING SPANISH LANGUAGE TEXTS

def try_scraping_spanish_site():
	chrome_options = Options()
	chrome_options.add_argument("--incognito")
	chrome_options.add_argument("--window-size=1920x1080")

	driver = webdriver.Chrome(chrome_options=chrome_options, executable_path="/Users/shawnduan/Documents/GitHub/langreader/chromedriver")
	
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
	



