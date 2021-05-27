

import requests
from bs4 import BeautifulSoup
import re

# soup is the html (but transformed into a python-manipulatable object) 
# that comes from scraping a website
def get_soup_from_URL(URL):
    page = requests.get(URL)
    soup = BeautifulSoup(page.content, 'html.parser')
    return soup

def scrape_time_links(URL, links_list: set):
	soup = get_soup_from_URL(URL)
	main_body = soup.find('section', class_="content left-rail") 

	# add links to list
	for link in main_body.find_all('a'):
		href_str = link.get('href')
		# if the second digit of the string is a number, then it will lead to an article on time.com
		if href_str[1].isdigit(): 
			links_list.add(href_str)

links_list = set() # making list into a set ensures no duplicates

# find the URLs to 600+ Time articles
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
	print('length of links list:', len(links_list), flush=True)

# from those URLs, scrape the text
text_list = set()
for link in links_list:
	soup = get_soup_from_URL('https://time.com' + link)
	article_string = ""
	for paragraph in soup.find_all('p')[:-1]: # omit the last paragraph, which is an email address
		article_string += paragraph.get_text() + "\n"
	text_list.add(article_string)
	print('text of links list:', article_string, flush = True)

# put the text in a text file
with open('scraped.txt', 'w') as file:
	for text in text_list:
		file.write(text+'|||||') # makes it easier to identify separate articles later on
	file.close()






