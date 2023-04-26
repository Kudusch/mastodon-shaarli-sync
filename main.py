#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import base64
import hmac
import json
import time
import requests
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import time
import configparser
import getpass
from pathlib import Path
from datetime import datetime

def check_config():
    try:
        config = configparser.ConfigParser()
        config.read_file(open(Path(__file__).with_name("config.ini").absolute()))
        if not config["shaarli"]["server"].startswith("https:"):
            config["shaarli"]["server"] = f"https://{config['shaarli']['server']}"
        if not config["mastodon"]["server"].startswith("https:"):
            config["mastodon"]["server"] = f"https://{config['mastodon']['server']}"
        return(config)
    except:
        return(None)

def setup_config():
    config = configparser.ConfigParser()
    config["mastodon"] = {"server": "", "access_token":""}
    config["mastodon"]["server"] = input("Enter the mastodon instance address: ")
    config["mastodon"]["access_token"] = getpass.getpass("Enter the mastodon access token: ")
    config["shaarli"] = {"server": "", "tag_name":"", "api_secret":""}
    config["shaarli"]["server"] = input("Enter shaarli server address: ")
    config["shaarli"]["tag_name"] = input("Enter shaarli tag name (leave empty for 'mastodon-bookmark'): ") or "mastodon-bookmark"
    config["shaarli"]["api_secret"] = getpass.getpass("Enter shaarli api secret: ")
    if not config["shaarli"]["server"].startswith("https:"):
        config["shaarli"]["server"] = f"https://{config['shaarli']['server']}"
    if not config["mastodon"]["server"].startswith("https:"):
        config["mastodon"]["server"] = f"https://{config['mastodon']['server']}"
    try:
        config.write(open("config.ini", "w"))
        print("Written config.ini\n")
    except:
        return None
    return(config)

def make_shaarli_header():
    header = json.dumps({"typ":"JWT","alg":"HS512"}).encode("utf-8")
    payload = json.dumps({"iat": int(time.time())}).encode("utf-8")
    content = f"{base64.b64encode(header).decode().strip('=')}.{base64.b64encode(payload).decode().strip('=')}".encode("utf-8")
    signature = hmac.new(f"{config['shaarli']['api_secret']}".encode(), content, "sha512").digest()
    token = f"{base64.b64encode(header).decode().strip('=')}.{base64.b64encode(payload).decode().strip('=')}.{base64.urlsafe_b64encode(signature).decode().strip('=')}"
    return {"Authorization":f"Bearer {token}"}

def make_mastodon_header():
    return({"Authorization": f"Bearer {config['mastodon']['access_token']}"})

def title_from_url(u):
    try:
        r = requests.get(u, timeout=5)
        soup = BeautifulSoup(r.text, "html.parser")
        return(soup.find("title").get_text())
    except:
        return("")

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

def update_link(link):
    payload = {
        "url": link["url"],
        "title": link["title"],
        "description": link["description"],
        "tags": link["tags"] + [config["shaarli"]["tag_name"]],
        "private": False,
        "created": link["created"],
        "updated": datetime.now().isoformat()
    }
    r = requests.put(f"{shaarli_server}/api/v1/links/{link['id']}", json=payload, headers=make_shaarli_header())
    return(r)

def add_link(url, toot, link=None):
    payload = {
        "url": url,
        "title": title_from_url(url),
        "description": toot["uri"],
        "tags": [
            "unread",
            config["shaarli"]["tag_name"]
        ],
        "private": False,
        "created": datetime.now().isoformat(),
        "updated": datetime.now().isoformat()
    }
    r = requests.post(f"{config['shaarli']['server']}/api/v1/links", json=payload, headers=make_shaarli_header())
    if r.status_code == 201:
        print(f"{datetime.now():%Y-%m-%d %H:%M} | New url saved | {r.json()['id']}: {r.json()['title']}")
        return({"url":url,"shaarli_id":r.json()["id"], "toot_id":toot["id"], "created_at":datetime.now().isoformat()})
    elif r.status_code == 409:
        if not config["shaarli"]["tag_name"] in r.json()["tags"]:
            r = update_link(r.json())
            if r.status_code == 200:
                print("Existing url updated!")
                print(f"{datetime.now():%Y-%m-%d %H:%M} | Existing url updated | {r.json()['id']}: {r.json()['title']}")
                return({"url":url,"shaarli_id":r.json()["id"], "toot_id":toot["id"], "created_at":datetime.now().isoformat()})
            else:
                print(r.staus_code, r.json())
        else:
            return({
                "url":url,
                "shaarli_id":r.json()["id"],
                "shaarli_url":f"{config['shaarli']['server']}/shaare/{r.json()['shorturl']}",
                "toot_id":toot["id"],
                "toot_url":toot["uri"],
                "created_at":datetime.now().isoformat()
            })


def delete_bookmark(toot_id=None, shaarli_id=None):
    if toot_id:
        print(f"{datetime.now():%Y-%m-%d %H:%M} | Unbookmarking toot | id:{toot_id}")
        r = requests.post(f"{config['mastodon']['server']}/api/v1/statuses/{toot_id}/unbookmark", headers = make_mastodon_header())
    if shaarli_id:
        print(f"{datetime.now():%Y-%m-%d %H:%M} | Deleting Shaarli link | id:{shaarli_id}")
        r = requests.delete(f"{config['shaarli']['server']}/api/v1/links/{shaarli_id}", headers=make_shaarli_header())

def get_toots():
    toots = []
    r = requests.get(f"{config['mastodon']['server']}/api/v1/bookmarks", headers = make_mastodon_header())
    if r.status_code == 200:
        toots.extend(r.json())
    while "next" in r.links.keys():
        r = requests.get(r.links["next"]["url"], headers = headers)
        toots.extend(r.json())
    return toots

def get_links():
    r = requests.get(f"{config['shaarli']['server']}/api/v1/links?searchtags={config['shaarli']['tag_name']}", headers=make_shaarli_header())
    if (r.status_code == 200):
        return r.json()
    else:
        return []

def run():
    try:
        with open(Path(__file__).with_name("state.json").absolute(), "r") as f:
            old_state = json.load(f)
    except:
        old_state = []

    state = []
    bookmarked_toots = get_toots()
    bookmarked_links = get_links()
    for b in old_state:
        if not b["toot_id"] in [t["id"] for t in bookmarked_toots]:
            #print("Change in Mastodon detected, deleting bookmark")
            delete_bookmark(shaarli_id=b["shaarli_id"])
            bookmarked_links = get_links()
        elif not b["shaarli_id"] in [t["id"] for t in bookmarked_links]:
            #print("Change in Shaarli detected, unbookmarking toot")
            delete_bookmark(toot_id=b["toot_id"])
            bookmarked_toots = get_toots()
        else:
            state.append(b)

    for t in bookmarked_toots:
        if not t["id"] in [b["toot_id"] for b in state]:
            for u in urls_from_toot(t):
                state.append(add_link(u, t))

    with open(Path(__file__).with_name("state.json").absolute(), "w") as f:
        json.dump(state, f)

    #for b in state:
    #    print(f"{b['created_at']}\n{b['url']}\n{b['toot_url']}\n")

if __name__ == "__main__":
    config = check_config()
    if not config:
        config = setup_config()
    run()
