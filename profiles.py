# Used for listing files in directory
import os

# Used for handling relative paths
from pathlib import Path

import json

# Function for reading all profile files and returning the content in a list if profileName is left empty, returning the contents of one profile if it isn't or simply just return the names of the available profile if profileName is left empty and justNames is set to true
def getProfiles(profileName="", justNames=False):

    profilePath = "./profiles/profiles/"

    if profileName == "":
        # Listing all the profiles by getting the OS indepentent path to profiles folder and listing files in it, and then only choosing those files that end in a .profile
        profileFiles = [
            x for x in os.listdir(path=Path(profilePath)) if ".profile" in x
        ]

        if justNames and profileName == "":
            # Remember to remove the .profile extension
            return [x[:-8] for x in profileFiles]

        # List for holding the information from all the files, so they only have to be read one
        profiles = list()

        # Reading all the different profile files and storing the contents in just created list
        for profile in profileFiles:

            # Stripping any potential trailing or leading newlines
            profiles.append(json.loads(Path(profilePath + profile).read_text().strip()))

        return profiles
    else:
        return json.loads(
            Path(profilePath + profileName + ".profile").read_text().strip()
        )


def collectWebsiteDetails(esClient):
    DBStoredProfiles = esClient.requestSourceCategoryListFromDB()

    profiles = getProfiles()

    # The final list of all the website information
    details = {}

    for profile in profiles:

        if profile["source"]["profileName"] in DBStoredProfiles:
            imageURL = profile["source"]["imageURL"]

            details[profile["source"]["profileName"]] = {
                "name": profile["source"]["name"],
                "image": imageURL,
                "url": profile["source"]["address"],
            }

    return {source: details[source] for source in sorted(details)}
