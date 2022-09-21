#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = 'LabMFA - Fluid Mechanics and Aerodynamics Laboratory'
COPYRIGHT_NAME = AUTHOR
COPYRIGHT_YEAR = str(__import__("datetime").date.today().year)
SITENAME = 'Fluid Mechanics and Aerodynamics Laboratory'
#SITETITLE = "LabMFA"
SITESUBTITLE = "Fluid Mechanics and Aerodynamics Laboratory"
SITEDESCRIPTION = "Laboratory Website"
FAVICON = "/images/favicon.ico"
SITEURL = "https://labfma.coppe.ufrj.br"

# Theme setup
THEME = "Flex"
BROWSER_COLOR = "#333"

# Static directories
STATIC_PATHS = (
    "images",
    "css",
)

# Extra CSS customization
EXTRA_PATH_METADATA = {
    "css/custom.css": {"path": "css/custom.css"},
}
CUSTOM_CSS = "css/custom.css"

ROBOTS = "index, follow"

PATH = "content"
DELETE_OUTPUT_DIRECTORY = True

TIMEZONE = 'America/Sao_Paulo'

DEFAULT_LANG = "en"

# Feed generation is usually not desired when developing
FEED_ALL_ATOM = None
CATEGORY_FEED_ATOM = None
TRANSLATION_FEED_ATOM = None
AUTHOR_FEED_ATOM = None
AUTHOR_FEED_RSS = None

# Links in the front page, aside from the static ``pages``
DIRECT_TEMPLATES = [
    "index",
    #"publications",
]

LINKS = (
    ('about the lab', '/about'),
    #('staff', '/staff'),
    ('students', '/students'),
    #('research', '/research'),
    ('education', '/education'),
    #('facilities', '/facilities'),
    ('contact us', '/contact'),
)

# Social widget
SOCIAL = (
    #("coppe", "https://www.coppe.ufrj.br"),
    #("github", "https://github.com/anjos"),
    #("orcid", "https://github.com/anjos"),
    #("orcid", "https://github.com/anjos"),
    # ('skype', 'skype:andrezito?call'),
)
#GOOGLE_ANALYTICS = "UA-22320747-1"

# Plugins
PLUGIN_PATHS = [
    "plugins",
]
#PLUGINS = [
#    "deadlinks",
#    "bibtex",
#    "bibcite",
#]

DEFAULT_PAGINATION = False
DISABLE_URL_HASH = True  # don't put hashes by the end of urls
DISPLAY_PAGES_ON_MENU = False
DISPLAY_CATEGORIES_ON_MENU = False
OUTPUT_RETENTION = [
    "CNAME",
]

# URL organization
ARTICLE_URL = "{category}/{slug}/"
ARTICLE_SAVE_AS = "{category}/{slug}/index.html"
CATEGORY_URL = "{slug}/"
CATEGORY_SAVE_AS = "{slug}/index.html"
PAGE_URL = "{slug}/.html"
PAGE_SAVE_AS = "{slug}/index.html"
PUBLICATIONS_SAVE_AS = "publications/index.html"

# Uncomment following line if you want document-relative URLs when developing
RELATIVE_URLS = True

# Set to ``True`` the following line to enable link-checking
DEADLINK_VALIDATION = False
DEADLINK_OPTS = {
    "timeout_duration_ms": 5000,
    "archive": False,
    "classes": ["disabled"],
}

# Where is the location of your BibTeX database
#PUBLICATIONS_SRC = "content/data/publications.bib"

# Theme configuration options
#USE_LESS = True #set to "True" to test theme changes
THEME_COLOR = "light"
THEME_COLOR_AUTO_DETECT_BROWSER_PREFERENCE = True
THEME_COLOR_ENABLE_USER_OVERRIDE = True
PYGMENTS_STYLE = "solarized-light"
PYGMENTS_STYLE_DARK = "solarized-dark"
