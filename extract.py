# For parsing html
from bs4 import BeautifulSoup

# For parsing application/ld+json
import json

import re

from dateutil.parser import parse
from datetime import timezone, datetime


# Used for matching the relevant information from LD+JSON
JSONPatterns = {
    "publish_date": re.compile(r'("datePublished": ")(.*?)(?=")'),
    "author": re.compile(r'("@type": "Person",.*?"name": ")(.*?)(?=")'),
}

# Function for using the class of a container along with the element type and class of desired html tag (stored in the contentDetails variable) to extract that specific tag. Data is found under the "scraping" class in the profiles.
def locateContent(CSSSelector, soup, recursive=True):
    try:
        return soup.select(CSSSelector, recursive=recursive)
    except:
        return BeautifulSoup("Unknown", "html.parser")


# Function used for removing certain tags with or without class from a soup. Takes in a list of element tag and class in the format: "tag,class;tag,class;..."
def cleanSoup(soup, removeSelectors):
    for CSSSelector in removeSelectors.split(";"):
        for tag in soup.select(CSSSelector):
            tag.decompose()

    return soup


def extractArticleContent(selectors, soup, delimiter="\n"):

    # Clean the textlist for unwanted html elements
    if selectors["remove"] != "":
        cleanedSoup = cleanSoup(soup, selectors["remove"])
        textList = locateContent(selectors["container"], cleanedSoup, recursive=True)
    else:
        textList = locateContent(selectors["container"], soup, recursive=True)

    if textList == "Unknown":
        raise Exception(
            "Wasn't able to fetch the text for the following soup:" + str(soup)
        )

    assembledText = ""
    assembledClearText = ""
    textTagTypes = ["p", "span"] + [f"h{i}" for i in range(1, 7)]

    for textSoup in textList:

        for textTag in textSoup.find_all(textTagTypes):
            if textTag.string:
                textTag.string.replace_with(textTag.string.strip())

        assembledClearText = assembledClearText + textSoup.get_text() + delimiter
        assembledText = assembledText + str(textSoup) + delimiter

    return assembledText, assembledClearText


# Function for scraping meta information (like title, author and publish date) from articles. This both utilizes the OG tags and LD+JSON data, and while the proccess for extracting the OG tags is fairly simply as those is (nearly) always following the same standard, the LD+JSON data is a little more complicated. Here the data isn't parsed as JSON, but rather as a string where the relevant pieces of information is extracted using regex. It's probably ugly and definitly not the officially "right" way of doing this, but different placement of the information in the JSON object on different websites using different attributes made parsing the information from a python JSON object near impossible. As such, be warned that this function is not for the faint of heart
def extractMetaInformation(pageSoup, scrapingTargets, siteURL):
    OGTags = {}

    for tagKind in scrapingTargets:
        OGTags[tagKind] = None
        for selector in scrapingTargets[tagKind].split(";"):
            if selector:
                try:
                    if "meta" in selector:
                        OGTags[tagKind] = pageSoup.select(selector)[0].get("content")
                    elif "time" in selector:
                        OGTags[tagKind] = pageSoup.select(selector)[0].get("datetime")
                    else:
                        OGTags[tagKind] = pageSoup.select(selector)[0].text
                except IndexError:
                    pass

    if OGTags["author"] == None or OGTags["publish_date"] == None:

        # Use ld+json to extract extra information not found in the meta OG tags like author and publish date
        JSONScriptTags = pageSoup.find_all("script", {"type": "application/ld+json"})

        for scriptTag in JSONScriptTags:
            # Converting to and from JSON to standardize the format to avoid things like line breaks and excesive spaces at the end and start of line. Will also make sure there spaces in the right places between the keys and values so it isn't like "key" :"value" and "key  : "value" but rather "key": "value" and "key": "value".
            try:
                scriptTagString = json.dumps(json.loads("".join(scriptTag.contents)))
            except json.decoder.JSONDecodeError:
                pass

            for pattern in JSONPatterns:
                if OGTags[pattern] == None:
                    articleDetailPatternMatch = JSONPatterns[pattern].search(
                        scriptTagString
                    )
                    if articleDetailPatternMatch != None:
                        # Selecting the second group, since the first one is used to located the relevant information. The reason for not using lookaheads is because python doesn't allow non-fixed lengths of those, which is needed when trying to select pieces of text that doesn't always conform to a standard.
                        OGTags[pattern] = articleDetailPatternMatch.group(2)

    if OGTags["image_url"] == None:
        OGTags["image_url"] = f"{siteURL}/favicon.ico"

    if OGTags["publish_date"]:
        OGTags["publish_date"] = parse(OGTags["publish_date"]).astimezone(timezone.utc)
    else:
        OGTags["publish_date"] = datetime.now(timezone.utc)

    return OGTags
