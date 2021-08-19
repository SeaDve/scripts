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

lines = [f"* {line.text}" for line in body]
lines.insert(0, header.text)
output = "\n".join(lines)

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, Gdk

    # FIXME Not working, so raise ImportError for now
    raise ImportError

    clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
    clipboard.set_text(output, -1)
    clipboard.store()

    log(f"Copied release notes for version {latest_version} to clipboard")
except ImportError:
    log("Failed to import `Gtk` and `Gdk`")
    log(f"Printing the release notes for version {latest_version} instead...")

    print(output)
