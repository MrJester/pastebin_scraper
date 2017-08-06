#!/usr/bin/env python3

import calendar
import datetime as dt
import json
import os
import socket
import time
import urllib.error
import urllib.parse
import urllib.request

old_data = []
new_data = []

new_pb_url = 'https://pastebin.com/api_scraping.php?limit=100'
pb_scrape_url = 'https://pastebin.com/api_scrape_item.php?i='
pb_dev_key = ''
out_dir = '/mnt/pastebin/'

parse_count = 0


def grab_data(pb_url):
    response_fail = False

    details = urllib.parse.urlencode({'api_dev_key': pb_dev_key})
    details = details.encode('UTF-8')
    try:
        url = urllib.request.Request(pb_url, details)
        url.add_header("User-Agent", "TBG PB Scraper")

        response_data = urllib.request.urlopen(url).read().decode('utf8', 'ignore')
    except urllib.error.HTTPError as e:
        response_data = e.read().decode('utf8', 'ignore')
        response_fail = False

    except urllib.error.URLError:
        response_fail = True

    except socket.error:
        response_fail = True

    except socket.timeout:
        response_fail = True

    except UnicodeEncodeError:
        print("[x]  Encoding Error")
        response_fail = True

    if response_fail:
        return 0
    else:
        return response_data


def find_file_old_data():
    now = dt.datetime.now()
    ago = now - dt.timedelta(minutes=30)
    file_list = []

    for root, dirs, files in os.walk(out_dir):
        for fname in files:
            path = os.path.join(root, fname)
            st = os.stat(path)
            mtime = dt.datetime.fromtimestamp(st.st_mtime)
            if mtime < ago:
                file_list.append(path)

    return file_list


if __name__ == '__main__':
    # build up old cache so we attempt to eliminate as many dups as possible
    print("[+] Parsing old records")
    for old_file in find_file_old_data():

        f_in = open(old_file, 'r')
        for line in f_in.readlines():
            try:
                data = json.loads(line.strip())
                old_data.append(data)
            except:
                pass

    print("[+] Loaded %s old entries into memory" % str(len(old_data)))
    print("[+] Entering scrape loop")

    while True:
        new_data = ""
        while new_data == "":
            try:
                new_data = json.loads(grab_data(new_pb_url))
                print("[+] Collected %s new entries" % str(len(new_data)))
            except:
                pass

        f_out = open(os.path.join(out_dir, "pb_data_" + str(calendar.timegm(time.gmtime())) + ".txt"), "w+")
        if len(new_data) > 0:
            print("[+] Parsing new entries")
            add_count = 0
            old_count = 0
            for pb_entry in new_data:
                new_key = pb_entry['key']
                key_found = False

                for old_entry in old_data:
                    if new_key == old_entry['key']:
                        print("[!] Key %s was already parsed" % str(new_key))
                        key_found = True
                        old_count += 1

                if not key_found:
                    add_count += 1
                    pb_entry['raw_text'] = grab_data(pb_scrape_url + pb_entry['key'])

                    json.dump(pb_entry, f_out, ensure_ascii=False)
                    f_out.write("\n")

            f_out.close()
            old_data = new_data
            print("[!] Discarded %s entries because we already parsed them" % str(old_count))
            print("[+] Added %s new entries" % str(add_count))
            print("[+] Sleeping for 1 minute")
            time.sleep(60)