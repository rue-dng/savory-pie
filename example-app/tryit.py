#!/usr/bin/python

"""
When we are doing runserver, we can test against the full stack.
"""

import urllib
import urllib2
import json
import pprint
import time
import os
import sys
import subprocess

opener = urllib2.build_opener(urllib2.HTTPHandler)

USE_SUBPROCESS = (len(sys.argv) == 1)

if USE_SUBPROCESS:
    subprocess.Popen('./helper.sh')
    time.sleep(5)

def get(uri):
    request = urllib2.Request(uri)
    request.add_header('Book-Type', 'application/json')
    request.get_method = lambda: 'GET'
    data = json.load(opener.open(request))
    return data

def put(uri, data):
    request = urllib2.Request(uri, data=json.dumps(data))
    request.add_header('Book-Type', 'application/json')
    request.get_method = lambda: 'PUT'
    opener.open(request)

def post(uri, data):
    request = urllib2.Request(uri, data=json.dumps(data))
    request.add_header('Book-Type', 'application/json')
    request.get_method = lambda: 'POST'
    opener.open(request)

def delete(uri):
    request = urllib2.Request(uri)
    request.add_header('Book-Type', 'application/json')
    request.get_method = lambda: 'DELETE'
    opener.open(request)

REDIRECT_JSON = False
if REDIRECT_JSON:
    os.system('rm -f /tmp/junk.txt')
    outf = open('/tmp/junk.txt', 'w')

def show_all():
    data = {
        'book': get('http://localhost:8000/api/book'),
        'author': get('http://localhost:8000/api/author'),
        'authorbook': get('http://localhost:8000/api/authorbook'),
    }
    if REDIRECT_JSON:
        pprint.pprint(data, stream=outf)
        outf.write('\n' + (50 * '-') + '\n\n')
    else:
        pprint.pprint(data)
    return data


try:
    # Update then delete
    uri = 'http://localhost:8000/api/book/1'
    data = {
        'resourceUri': uri,
        'title': 'Harry Potter and the Endless Sequels',
        'authors': [{'name': 'abcd',
                   'resourceUri': 'http://localhost:8000/api/author/1'}]
    }

    x = show_all()
    assert x['book']['meta']['count'] == 2
    assert x['author']['meta']['count'] == 2
    assert x['authorbook']['meta']['count'] == 2

    put(uri, data)
    x = show_all()
    assert x['book']['meta']['count'] == 2
    assert x['author']['meta']['count'] == 2
    assert x['authorbook']['meta']['count'] == 3

    delete(uri)
    x = show_all()
    assert x['book']['meta']['count'] == 1
    assert x['author']['meta']['count'] == 2
    assert x['authorbook']['meta']['count'] == 1

    # Create a new one then delete
    uri = 'http://localhost:8000/api/book'
    data = {
        'resourceUri': uri,
        'title': 'Another Dumb Title',
        'authors': [{'name': 'ijkl',
                   'resourceUri': 'http://localhost:8000/api/author/1'}]
    }

    post(uri, data)
    x = show_all()
    assert x['book']['meta']['count'] == 2
    assert x['author']['meta']['count'] == 2
    assert x['authorbook']['meta']['count'] == 2

    delete('http://localhost:8000/api/book/3')
    x = show_all()
    assert x['book']['meta']['count'] == 1
    assert x['author']['meta']['count'] == 2
    assert x['authorbook']['meta']['count'] == 1

finally:
    if REDIRECT_JSON:
        outf.close()
    if USE_SUBPROCESS:
        for pid in os.popen('lsof -i:8000 | grep LISTEN | cut -c 8-12').read().strip().split('\n') + \
                   os.popen('ps ax | grep helper.sh | cut -c 1-5').read().strip().split('\n'):
            if pid:
                try:
                    os.kill(int(pid), 9)
                except OSError:
                    pass
