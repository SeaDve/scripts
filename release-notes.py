#!/usr/bin/env python3

import argparse
from xml.etree import ElementTree

from utils import log

parser = argparse.ArgumentParser()
parser.add_argument('appstream_file', help="The path to the appstream file", type=str)
args = parser.parse_args()

tree = ElementTree.parse(args.appstream_file)
root = tree.getroot()

releases = root.find('releases')
latest_release = releases[0]

latest_version = latest_release.get('version')
latest_release_description = latest_release.find('description')

header = latest_release_description.find('p')
body = latest_release_description.find('ul')

log(f"Printing release notes for version {latest_version}...")

print(header.text)
for line in body:
    print(f" * {line.text}")
