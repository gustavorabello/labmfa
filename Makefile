PYTHON ?= /Users/gustavo/miniforge3/envs/pelican/bin/python
PELICAN ?= /Users/gustavo/miniforge3/envs/pelican/bin/pelican
PELICANOPTS =

BASEDIR = $(CURDIR)
INPUTDIR = $(BASEDIR)/content
OUTPUTDIR = $(BASEDIR)/output.nosync
CONFFILE = $(BASEDIR)/pelicanconf.py
PUBLISHCONF = $(BASEDIR)/publishconf.py

GITHUB_PAGES_BRANCH = gh-pages

.DEFAULT_GOAL := all

DEBUG ?= 0
ifeq ($(DEBUG), 1)
	PELICANOPTS += -D
endif

RELATIVE ?= 0
ifeq ($(RELATIVE), 1)
	PELICANOPTS += --relative-urls
endif

SERVER ?= 0.0.0.0

PORT ?= 0
ifneq ($(PORT), 0)
	PELICANOPTS += -p $(PORT)
endif

help:
	@echo 'Makefile for the LabMFA Pelican site'
	@echo
	@echo 'Usage:'
	@echo '   make                                update data and fully build the site'
	@echo '   make publish                        fully build and upload via SFTP'
	@echo '   make html                           generate Pelican content only'
	@echo '   make production                     generate with production settings'
	@echo '   make clean                          remove the generated files'
	@echo '   make regenerate                     regenerate files upon modification'
	@echo '   make serve [PORT=8000]              serve site at http://localhost:8000'
	@echo '   make serve-global [SERVER=0.0.0.0]  serve on the selected interface'
	@echo '   make devserver [PORT=8000]          serve and regenerate together'
	@echo '   make devserver-global               serve and regenerate on all interfaces'
	@echo '   make github                         upload the site via gh-pages'
	@echo
	@echo 'Set DEBUG=1 to enable Pelican debug mode.'
	@echo 'Set RELATIVE=1 to enable relative URLs.'

all:
	LABMFA_PELICAN_BIN="$(PELICAN)" "$(PYTHON)" build.py --build-only

html:
	"$(PELICAN)" "$(INPUTDIR)" -o "$(OUTPUTDIR)" -s "$(CONFFILE)" $(PELICANOPTS)

production:
	"$(PELICAN)" "$(INPUTDIR)" -o "$(OUTPUTDIR)" -s "$(PUBLISHCONF)" $(PELICANOPTS)

publish:
	LABMFA_PELICAN_BIN="$(PELICAN)" "$(PYTHON)" build.py

clean:
	[ ! -d "$(OUTPUTDIR)" ] || rm -rf "$(OUTPUTDIR)"

regenerate:
	"$(PELICAN)" -r "$(INPUTDIR)" -o "$(OUTPUTDIR)" -s "$(CONFFILE)" $(PELICANOPTS)

serve:
	"$(PELICAN)" -l "$(INPUTDIR)" -o "$(OUTPUTDIR)" -s "$(CONFFILE)" $(PELICANOPTS)

serve-global:
	"$(PELICAN)" -l "$(INPUTDIR)" -o "$(OUTPUTDIR)" -s "$(CONFFILE)" $(PELICANOPTS) -b $(SERVER)

devserver:
	"$(PELICAN)" -lr "$(INPUTDIR)" -o "$(OUTPUTDIR)" -s "$(CONFFILE)" $(PELICANOPTS)

devserver-global:
	"$(PELICAN)" -lr "$(INPUTDIR)" -o "$(OUTPUTDIR)" -s "$(CONFFILE)" $(PELICANOPTS) -b 0.0.0.0

github: production
	ghp-import -m "Generate Pelican site" -b $(GITHUB_PAGES_BRANCH) "$(OUTPUTDIR)"
	git push origin $(GITHUB_PAGES_BRANCH)

.PHONY: all help html production publish clean regenerate serve serve-global devserver devserver-global github
