# SSched.py
# Skeletorfw
# 16/05/17
# Version 0.0.1
#
# Python 3.4.1
#
# Bot to post regularly to a particular subreddit

import logging
import time
import praw
import csv
from pprint import pprint
import textwrap

# Set up logging
# logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Create logfile handler
handler = logging.FileHandler('log/SSCHED.out')
handler.setLevel(logging.DEBUG)  # File logging level

# Create formatter and add to handler
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(funcName)s - %(message)s')
handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(handler)

# CONFIG
reddit = praw.Reddit('bot1')
default_sub = "getmetosleep"


class EmptyQueueError(Exception):
    pass


class MalformedPostEntry(Exception):
    pass


class RedditSubmission:
    # Class to hold active reddit submission
    def __init__(self, url, description, subreddit):
        self.url = url
        self.description = description
        self.subreddit = subreddit


def read_subqueue():
    """Read the current submission queue and return as a list"""
    logger.debug("Reading submission queue.")

    subqueue = []
    try:
        with open("data/subqueue.csv") as queuefile:
            queuereader = csv.reader(queuefile, delimiter='|')
            for entry in queuereader:
                # Split entry into ['url', 'description', 'subreddit']
                subqueue.append([x for x in entry])
                logger.debug("Loaded {0}.".format(entry[0]))
    except FileNotFoundError:
        logger.warning("No submission queue present. Using empty queue.")

    logger.info("Entries in submission queue: {0}.".format(len(subqueue)))

    return subqueue


def validate_post(post_entry, fallback_sub):
    logger.debug("Validating popped submission from queue.")

    try:
        using_default = False
        post_entry_working = post_entry

        # Process entry properly, removing whitespace and checking values.
        if len(post_entry_working) == 2:
            post_entry_working.append(fallback_sub)     # Use default subreddit if not defined in entry.
            using_default = True
            logger.debug("No subreddit defined, using default of {0}.".format(fallback_sub))
        if len(post_entry_working) > 3:     # Should catch many malformed entries.
            raise MalformedPostEntry
        post_entry_working = [x.strip() for x in post_entry_working]  # Cut whitespace from each string.
        # Should possibly try to validate URLs here.
        # Elegantly shorten descriptions over 300 chars.
        post_entry_working[1] = textwrap.shorten(post_entry_working[1], width=300, placeholder="...")

        # Create RedditSubmission obj
        post = RedditSubmission(post_entry_working[0], post_entry_working[1], post_entry_working[2])

        logger.info("Post successfully validated.")
        logger.debug("--------------- METADATA ----------------")
        logger.debug("{0:>9}: {1.description:}".format("Title", post))
        logger.debug("{0:>9}: {1.url}".format("Url", post))
        if using_default:
            logger.debug("{0:>9}: {1.subreddit}(default)".format("Subreddit", post))
        else:
            logger.debug("{0:>9}: {1.subreddit}".format("Subreddit", post))
        logger.debug("-----------------------------------------")

    except MalformedPostEntry:
        err_string = "".join(["{0}|".format(x) for x in post_entry]).rstrip("|")
        logger.error("Malformed post entry: {0}".format(err_string))
        with open("data/subqueue_errored.csv", "a", newline='') as errorfile:   # Write errored line to errorfile.
            errorwriter = csv.writer(errorfile, delimiter='|')
            errorwriter.writerow(post_entry)
        raise MalformedPostEntry

    return post


def main():
    starttime = time.perf_counter()
    logger.info("-----------------------------------------")
    logger.info("Started execution at {0}".format(time.strftime("%H:%M:%S, %d/%m/%Y", time.localtime())))
    logger.info("-----------------------------------------")
    queue = read_subqueue()
    popped = queue.pop(0)
    try:
        validated = validate_post(popped, default_sub)
    except MalformedPostEntry:
        logger.critical("Exiting due to malformed post.")
    endtime = time.perf_counter()
    runtime = time.strftime("%H:%M:%S", time.gmtime(endtime - starttime))
    logger.info("-----------------------------------------")
    logger.info("Ended execution at {0}".format(time.strftime("%H:%M:%S, %d/%m/%Y", time.localtime())))
    logger.info("Executed in {0}.".format(runtime))
    logger.info("-----------------------------------------")
main()
