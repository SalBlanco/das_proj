import os
from datetime import datetime
import time
import feedparser
import json
import urllib, urllib.request
import re
from langchain_core.tools import tool

from scholarly import scholarly
from scholarly import ProxyGenerator

# @tool
# # adapted from https://info.arxiv.org/help/api/examples/python_arXiv_paging_example.txt
# def search(results_per_iteration, start):
#   """Search for DAS papers"""

#   obj = []
  
#   # Get current date + time
#   now = datetime.now()
#   today = now.strftime("%Y%m%d%H%M")

#   # Base API query url
#   base_url = 'http://export.arxiv.org/api/query?'

#   # API search parameters for DAS papers from 1/01/2010 to today.
#   search_query = f'all:DAS+AND+all:distributed+AND+all:acoustic+AND+all:sensing+submittedDate:201001010000+TO+{today}'

#   # Number of seconds to wait beetween calls; recommended by arXiv documentation
#   wait_time = 3 

#   print(f'Searching arXiv for {search_query}')

#   while True:

#     print(f"Results {start} - {start+results_per_iteration}")

#     query = f'search_query={search_query}&start={start}&max_results={start+results_per_iteration}'

#     # GET request using the base_url and query
#     response = urllib.request.urlopen(base_url+query).read()

#     if not response or len(response) == 0:
#       print("No more results. Please try again.")
#       break

#     # Parse the response using feedparser
#     feed = feedparser.parse(response)

#     # Run through each entry, and print out information
#     for entry in feed.entries:
#       paper_id = entry.id.split('/abs/')[-1]
#       title = entry.title
#       author = entry.author
#       summary = entry.summary if hasattr(entry, 'summary') else ""

#       # Format as a search result
#       content = f"Paper ID: {paper_id}\nTitle: {title}\nAuthor: {author}\nSummary: {summary}"

#       # Add to results
#       obj.append({
#           'url': entry.id,  # Use arXiv URL
#           'content': content
#       })

#       print("arxiv-id: ", paper_id)
#       print("Title: ", title)
#       # feedparser v4.1 only grabs the first author
#       print("First Author: ", author)

#     # Break loop after extracting relevant information
#     break

#   # Sleep before calling API again
#   print(f"Sleeping for {wait_time} seconds")
#   time.sleep(wait_time)
  
#   return obj

@tool
def search(papers_per_call, index, search_query='distributed acoustic sensing'):
    """Search for DAS papers"""

    # Create object to store paper information
    obj = []

    # Counter for pagination
    cnt = 0

    print(f'Searching arXiv for {search_query}')

    # Currently not working
    # pg = ProxyGenerator()
    # pg.FreeProxies()
    # scholarly.use_proxy(pg, pg)

    # Need to call this once at the start of the session so Google Scholar does not block IP
    search_query = scholarly.search_pubs('distributed acoustic sensing', year_low=2010, sort_by='date', start_index=index)
    
    while cnt < papers_per_call:
        try:
            # Extract publication data
            authors = pub_data['bib']['author']
            title = pub_data['bib']['title']
            pub_url = pub_data['pub_url']

            obj.append([{
            'title': title,
            'authors': authors,
            'pub_url': pub_url,
            }])
            
            cnt += 1
            pub_data = next(search_query)
        except StopIteration as e:
            # Handle the exception
            print(f"An error occurred: {e}")
            break

    return obj

@tool
def paginate(papers_per_call, index, success=True):
    """Increment counter for pagination."""
    # Update index if successfully returned new papers; else, keep index the same
    new_index = index + papers_per_call if success else index
    print(f"Paginating: index {index} → {new_index} (success={success})")
    return new_index

# @tool
def check_history(obj, filename='gs_records.json'):
    """Write DAS paper information to output file if not already in history."""
    # Create history set for efficient lookup
    history = set()
    # Read through pre-existing json file
    if os.path.exists(filename) and os.path.getsize(filename) > 0:
        with open(filename, 'r') as file:
            for line in file:
                try:
                    # Read each line, add to history set (unique values)
                    existing_entry = json.loads(line.strip())
                    history.add(json.dumps(existing_entry, sort_keys=True))
                except json.JSONDecodeError:
                        continue  # Skip invalid lines

    # Extract entries that have not been added already
    new_entries = [entry for entry in obj if json.dumps(entry, sort_keys=True) not in history]

    # If there are new entries to add, open correponding file and dump JSON objects
    if new_entries:
        with open(filename, 'a') as file:
            for entry in new_entries:
                file.write(json.dumps(entry, sort_keys=True) + '\n')

@tool
def write(obj, filename='gs_records.json'):
    """Write DAS paper information to output file for records."""
    # Filepath where we will store found papers' information.
    path = '../'

    # If corresponding output folder does not exist, create it
    os.listdir(path)
    if 'out' not in os.listdir(path):
        os.mkdir(path+'out')
        os.chdir(path+'out')
    else:
        os.chdir(path+'out')
        
    # Create and/or append to output.json file to handle dictionary format
    f = open('gs_records.json', 'a')
    # Write each entry on its own line
    check_history(obj, filename)