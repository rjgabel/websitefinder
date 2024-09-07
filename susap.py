import json
import requests
import time
from urllib.parse import urlparse

# For Google Sheets API
import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

import asyncio

import email_extractor

def get_lines(path):
    with open(path, 'r', encoding='utf-8') as f:
        keywords = f.readlines()
        # Strip trailing newlines
        keywords = [k.strip() for k in keywords]
        return keywords

# Returns the cached result, or False if there isn't one
def get_cache(path, is_json=True):
    path = path.replace('site:','site/')
    try:
        with open('cache/' + path, 'r', encoding='utf-8') as f:
            data = f.read()
            if is_json:
                return json.loads(data)
            else:
                return data
    except FileNotFoundError:
        return False

# Writes the result to the cache file
def set_cache(path, data):
    path = path.replace('site:','site/')
    with open('cache/' + path, 'x', encoding='utf-8') as f:
        f.write(data)
        print('Cached file: ' + path)

# Calls the Serper API to get results
def get_serp(keyword, max_results):
    if USE_CACHEING:
        results = get_cache('serper/' + keyword.replace('/',''))
        if results:
            return results
    
    url = 'https://google.serper.dev/search'
    payload = json.dumps({
        'q': keyword,
        'gl': 'us',
        'num': max_results
    })
    headers = {
        'X-API-KEY': SERPER_KEY,
        'Content-Type': 'application/json'
    }
    response = requests.request('POST', url, headers=headers, data=payload)

    if USE_CACHEING:
        set_cache('serper/' + keyword.replace('/',''), response.text)

    return json.loads(response.text)

def extract_sites(serp):
    urls = [x['link'] for x in serp['organic']]
    domains = [urlparse(x).netloc for x in urls]
    return domains

# Gets a result from the ahrefs API
def get_ahrefs(operation, query):
    if USE_CACHEING:
        results = get_cache('ahrefs/' + operation + '/' + query['target'])
        if results:
            return results

    url = 'https://api.ahrefs.com/v3/site-explorer/' + operation

    headers = {
        'Accept': 'application/json',
        'Authorization': 'Bearer ' + AHREFS_KEY
    }
    #print(url)
    #print(headers)
    #print(query)
    response = requests.get(url, headers=headers, params=query)

    if USE_CACHEING:
        set_cache('ahrefs/' + operation + '/' + query['target'], response.text)

    return json.loads(response.text)

def get_dr(target):
    query = {'target':target,'date':time.strftime('%Y-%m-%d')}
    data = get_ahrefs('domain-rating', query)
    return data['domain_rating']['domain_rating']

def get_refdomains(target):
    query = {'target':target,'date':time.strftime('%Y-%m-%d')}
    data = get_ahrefs('backlinks-stats', query)
    return data['metrics']['live_refdomains']

def get_backlinks(target):
    where = {
        'and': [
            { 'field': 'is_dofollow', 'is': ['eq', True] },
            { 'field': 'domain_rating_source', 'is': ['gte', 90] }
        ]
    }

    query = {
        'where': json.dumps(where),
        'select': 'domain_rating_source,url_from',
        'target': target,
        'aggregation': '1_per_domain',
        'history': 'live'
    }

    backlinks = get_ahrefs('all-backlinks', query)['backlinks']

    for x in backlinks:
        # Change urls to domain name
        x['url_from'] = urlparse(x['url_from']).netloc
        x['url_from'] = x['url_from'].removeprefix('www.')

    # Filter out urls already in bdev_links
    backlinks = [x for x in backlinks if x['url_from'] not in bdev_links]

    return backlinks

# From https://developers.google.com/sheets/api/quickstart/python
def get_sheets_creds():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds

def sheet_get_values(sheet_id, range_name):
    service = build('sheets', 'v4', credentials=creds)
    result = (
        service.spreadsheets().values()
        .get(spreadsheetId=sheet_id, range=range_name)
        .execute()
    )
    return result['values']

def sheet_append_values(range_name, values):
    service = build('sheets', 'v4', credentials=creds)
    result = (
        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=range_name,
            valueInputOption='RAW',
            body={'values': values}
        ).execute()
    )
    return result

def sheet_add_sites(sites):
    if len(sites) == 0:
        print('No new sites to add to spreadsheet.')
        return
    values = []
    for s in sites:
        site = sites[s]

        backlinks = site['backlinks']
        b_urls = ''
        b_drs = ''
        for b in backlinks:
            b_urls += b['url_from'] + '\n'
            b_drs += str(b['domain_rating_source']) + '\n'
        contacts = ''
        for e in site['contacts']:
            contacts += e + '\n'
        row = [s, site['dr'], site['refdomains'], b_urls.strip(), b_drs.strip(), contacts.strip()]
        values.append(row)
    sheet_append_values('A2', values)
    print('Sites added to spreadsheet: ' + str(len(sites)))

def get_contacts(domain):
    if USE_CACHEING:
        results = get_cache('emails/' + domain)
        if results or type(results)!=bool:
            return results
    
    results = list(asyncio.run(email_extractor.crawl(domain)))

    if USE_CACHEING:
        set_cache('emails/' + domain, json.dumps(results))

    return results

keywords = get_lines('keywords.txt')

creds = get_sheets_creds()

bdev_links = sheet_get_values(BDEV_LINKS_SHEET_ID,'A2:A')
# Flatten
bdev_links = [x[0] for x in bdev_links if len(x)==1]

old_sites = sheet_get_values(SPREADSHEET_ID,'A2:A') + sheet_get_values(SPREADSHEET_ID,'Black list!A2:A')
# Flatten old_sites
# if len(x)==1 prevents exception on empty rows
old_sites = [x[0] for x in old_sites if len(x)==1]
sites = dict()

for k in keywords:
    serp = get_serp(k,50)
    results = extract_sites(serp)
    for r in results:
        # remove initial www.
        r = r.removeprefix('www.')
        if r in old_sites:
            pass
        elif r in sites:
            sites[r]['keywords'].add(k)
        else:
            sites[r] = {'keywords': {k}}

# Filter out sites with more than MAX_INDEXED_PAGES
sites = {x:sites[x] for x in sites if len(get_serp('site:'+x,51)['organic']) <= MAX_INDEXED_PAGES}

for s in sites.keys():
    sites[s]['dr'] = get_dr(s)

# Filter out sites where DR < 35 or DR > 79
sites = {x:sites[x] for x in sites if sites[x]['dr'] >= 35 and sites[x]['dr'] <= 79}

for s in sites.keys():
    sites[s]['refdomains'] = get_refdomains(s)
    sites[s]['backlinks'] = get_backlinks(s)
    sites[s]['contacts'] = get_contacts(s)

sheet_add_sites(sites)
