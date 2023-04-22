#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import base64
import hmac
import json
import time
import requests
import config
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import time
from datetime import datetime

#api_base = "https://www.{0}".format((urlparse(config.SERVER)).netloc)
if not config.SERVER.startswith("https"):
    if config.SERVER.startswith("http:"):
        exit()
    api_base = f"https://{config.SERVER}"
headers = {"Authorization": f"Bearer {config.TOKEN}"}

def make_header():
    header = json.dumps({"typ":"JWT","alg":"HS512"}).encode("utf-8")
    payload = json.dumps({"iat": int(time.time())}).encode("utf-8")
    content = f"{base64.b64encode(header).decode().strip('=')}.{base64.b64encode(payload).decode().strip('=')}".encode("utf-8")
    signature = hmac.new("e7263694bd85".encode(), content, "sha512").digest()
    token = f"{base64.b64encode(header).decode().strip('=')}.{base64.b64encode(payload).decode().strip('=')}.{base64.urlsafe_b64encode(signature).decode().strip('=')}"
    return {"Authorization":f"Bearer {token}"}

def urls_from_toot(toot):
    content = BeautifulSoup(toot["content"], "html.parser")
    urls = []
    for a in content.find_all("a"):
        if a.text.startswith("http"):
            urls.append(a.text)
    if len(urls) > 0:
        return urls
    else:
        return [toot["url"]]

def title_from_url(u):
    try:
        r = requests.get(u)
        soup = BeautifulSoup(r.text, "html.parser")
        return(soup.find("title").get_text())
    except:
        return("")

def save_url(url, toot_url):
    payload = {
        "url": url,
        "title": title_from_url(u),
        "description": toot_url,
        "tags": [
            "unread",
            "mastodon-bookmark"
        ],
        "private": False,
        "created": datetime.now().isoformat(),
        "updated": datetime.now().isoformat()
    }
    r = requests.post('https://kudusch.de/apps/Shaarli/api/v1/links', json=payload, headers=make_header())
    if r.status_code == 201:
        print("New url saved!")
    elif r.status_code == 409:
        print("url already saved!")
    

def print_link(link_id):
    r = requests.get(f"https://kudusch.de/apps/Shaarli/api/v1/links{link_id}", headers=make_header())
    if (r.status_code == 200):
        link = r.json()
        print(f"{link['title']} ({link['url']})")
    else:
        return False

def get_links():
    r = requests.get('https://kudusch.de/apps/Shaarli/api/v1/links', headers=make_header())
    if (r.status_code == 200):
        return r.json()
    else:
        return False

def read_headers(headers):
    try:
        links = headers["Link"].split(", ")
    except:
        pass

def get_bookmarks():
    bookmarks = []
    r = requests.get(f"{api_base}/api/v1/bookmarks", headers = headers)
    if r.status_code == 200:
        bookmarks.extend(r.json())
    while "next" in r.links.keys():
        r = requests.get(r.links["next"]["url"], headers = headers)
        bookmarks.extend(r.json())
    return bookmarks

if __name__ == "__main__":
    try:
        with open("state.json", "r") as f:
            state = json.load(f)
    except:
        state = {}
        state = {"links": get_links(), "toots": get_bookmarks()}
    
    bookmarked_urls = state["bookmarked_urls"]
    n_bookmarked_urls = len(bookmarked_urls)
    bookmarked_toots = get_bookmarks()
    bookmarked_urls = {k: v for k, v in bookmarked_urls.items() if k in [t["id"] for t in bookmarked_toots]}
    if len(bookmarked_urls) != n_bookmarked_urls:
        print(f"Removed {n_bookmarked_urls-len(bookmarked_urls)} bookmarked toot")
    for m in bookmarked_toots:
        if not m["id"] in bookmarked_urls:
            urls = urls_from_toot(m)
            if len(urls) > 0:
                bookmarked_urls[m["id"]] = {"saved_at":int(time.time()), "urls":urls, "uri":m["uri"]}
                print(f"Found new bookmarked toot with id {m['id']} and {len(urls)} urls")
                for u in urls:
                    save_url(u, m["uri"])
    with open("state.json", "w") as f:
        print(f"Bookmarked urls form {len(bookmarked_urls)} toots.")
        json.dump(bookmarked_urls, f)
