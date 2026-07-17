# Production settings used by `make publish`, `make production`, or when this
# file is explicitly selected as the Pelican configuration.

import os
import sys
sys.path.append(os.curdir)
from pelicanconf import *

# If your site is available via HTTPS, make sure SITEURL begins with https://
SITEURL = 'https://labmfa.coppe.ufrj.br'
RELATIVE_URLS = False

# The SFTP account cannot create new top-level directories under /html.
# Keep every feed disabled so publishing never attempts to create /html/feeds.
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

DELETE_OUTPUT_DIRECTORY = True

# Following items are often useful when publishing

#DISQUS_SITENAME = ""
#GOOGLE_ANALYTICS = ""
