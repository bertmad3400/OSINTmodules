# Used for sleeping
import time

# Used for determining the path to the geckodriver
from pathlib import Path

# For manipulating lists in a way that's less memory intensive
import itertools

# Used to gather the urls from the articles, by reading a RSS feed
import feedparser

# Used for scraping static pages
import requests

# Used for dynamically scraping pages that aren't static
from selenium import webdriver

# Used for running the browser headlessly
from selenium.webdriver.firefox.options import Options

# For parsing html
from bs4 import BeautifulSoup

from modules.misc import catURL

# Used for selecting a random elemen from browserHeaders list
import random

# Used for simulating an actual browser when scraping for OGTags, stolen from here
browserHeadersList = [
    # Firefox 77 Mac
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:77.0) Gecko/20100101 Firefox/77.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.google.com/",
        "Connection": "keep-alive",
    },
    # Firefox 77 Windows
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:77.0) Gecko/20100101 Firefox/77.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Referer": "https://www.google.com/",
    },
    # Chrome 83 Mac
    {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Referer": "https://www.google.com/",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
    },
    # Chrome 83 Windows
    {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Referer": "https://www.google.com/",
        "Accept-Language": "en-US,en;q=0.9",
    },
]

# Simple function for scraping static page and converting it to a soup
def scrapeWebSoup(URL):
    currentHeaders = random.choice(browserHeadersList)
    pageSource = requests.get(URL, headers=currentHeaders)
    if pageSource.status_code != 200:
        print(
            "Error: Status code "
            + str(pageSource.status_code)
            + ", skipping URL: "
            + URL
        )
        return None
    return BeautifulSoup(pageSource.content, "html.parser")


# Scraping targets is element and class of element in which the target url is stored, and the profileName is prepended on the list, to be able to find the profile again when it's needed for scraping
def scrapeArticleURLs(rootURL, frontPageURL, scrapingTargets, profileName):

    # Getting a soup for the website
    frontPageSoup = (
        scrapeWebSoup(frontPageURL).select(scrapingTargets["containerList"])[0]
        if scrapingTargets["containerList"] != []
        else scrapeWebSoup(frontPageURL)
    )

    articleURLs = [
        catURL(
            rootURL,
            link.get("href")
            if scrapingTargets["linkContainers"] == ""
            else link.select(scrapingTargets["links"])[0].get("href"),
        )
        for link in itertools.islice(
            frontPageSoup.select(
                scrapingTargets["linkContainers"]
                if scrapingTargets["linkContainers"] != ""
                else scrapingTargets["links"]
            ),
            10,
        )
    ]

    return articleURLs


# Function for scraping a list of recent articles using the url to a RSS feed
def RSSArticleURLs(RSSURL, profileName):
    # Parse the whole RSS feed
    RSSFeed = feedparser.parse(RSSURL)

    # List for holding the urls from the RSS feed
    articleURLs = []

    # Extracting the urls only, as these are the only relevant information. Also only take the first 10, if more is given to only get the newest articles
    for entry in itertools.islice(RSSFeed.entries, 10):
        articleURLs.append(entry.id)

    return articleURLs


def scrapePageDynamic(pageURL, scrapingTypes, loadTime=3, headless=True):

    # Setting the options for running the browser driver headlessly so it doesn't pop up when running the script
    driverOptions = Options()
    driverOptions.headless = headless

    # Setup the webdriver with options
    driver = webdriver.Firefox(
        options=driverOptions,
        executable_path=Path("./tools/geckodriver").resolve(),
        log_path=Path("./logs/geckodriver.log").resolve(),
    )

    # Actually scraping the page
    driver.get(pageURL)

    # Sleeping a pre-specified time to let the driver actually render the page properly
    time.sleep(loadTime)

    for scrapingType in scrapingTypes:
        currentType = scrapingType.split(":")
        if currentType[0] == "JS":
            driver.execute_script(
                Path(f"./profiles/JSInjection/{currentType[1]}.js").read_text()
            )
            while driver.execute_script("return document.osinterReady") == False:
                time.sleep(1)

    # Getting the source code for the page
    pageSource = driver.page_source

    driver.quit()

    return pageSource
