# ===================================================================== #
#  LabMFA · Fluid Mechanics & Aerodynamics Laboratory — Pelican site
#  Colourful build helper.  Run `make help` for the full menu.
#  Colours are disabled automatically when NO_COLOR is set or TERM=dumb.
# ===================================================================== #

PYTHON ?= /Users/gustavo/miniforge3/envs/pelican/bin/python
PELICAN ?= /Users/gustavo/miniforge3/envs/pelican/bin/pelican
PELICANOPTS =

BASEDIR = $(CURDIR)
INPUTDIR = $(BASEDIR)/content
OUTPUTDIR = $(BASEDIR)/output.nosync
CONFFILE = $(BASEDIR)/pelicanconf.py
PUBLISHCONF = $(BASEDIR)/publishconf.py
DEDUPE = $(BASEDIR)/scripts/clean_icloud_duplicates.py

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

# --- Colours ---------------------------------------------------------- #
# Honour the NO_COLOR convention (any value) and dumb terminals.
ifeq ($(origin NO_COLOR), undefined)
ifeq ($(TERM), dumb)
COLOR := 0
else
COLOR := 1
endif
else
COLOR := 0
endif

ifeq ($(COLOR), 1)
C_RESET  := \033[0m
C_BOLD   := \033[1m
C_DIM    := \033[2m
C_RED    := \033[31m
C_GREEN  := \033[32m
C_YELLOW := \033[33m
C_BLUE   := \033[34m
C_MAGENTA:= \033[35m
C_CYAN   := \033[36m
C_WHITE  := \033[37m
B_NEW    := \033[30;42m
B_MOD    := \033[30;43m
B_STAGE  := \033[30;46m
else
C_RESET  :=
C_BOLD   :=
C_DIM    :=
C_RED    :=
C_GREEN  :=
C_YELLOW :=
C_BLUE   :=
C_MAGENTA:=
C_CYAN   :=
C_WHITE  :=
B_NEW    :=
B_MOD    :=
B_STAGE  :=
endif

# --- Banner (reused as a prerequisite) -------------------------------- #
_banner:
	@printf '$(C_CYAN)$(C_BOLD)\n'
	@printf '  ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓\n'
	@printf '  ┃  🌊  LabMFA — Fluid Mechanics & Aerodynamics Laboratory\n'
	@printf '  ┃  ⚙️   Pelican static-site builder  ·  make help for options\n'
	@printf '  ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛\n'
	@printf '$(C_RESET)'

help: _banner
	@printf '$(C_BOLD)$(C_WHITE)Usage:$(C_RESET) make $(C_CYAN)<target>$(C_RESET) [VAR=value]\n\n'
	@printf '$(C_BOLD)$(C_GREEN)  BUILD$(C_RESET)\n'
	@printf '    $(C_CYAN)make$(C_RESET)               update data + build the site, $(C_BOLD)highlighting what is new$(C_RESET)\n'
	@printf '    $(C_CYAN)html$(C_RESET)               generate Pelican content only (no data update)\n'
	@printf '    $(C_CYAN)production$(C_RESET)          generate with production settings\n'
	@printf '    $(C_CYAN)regenerate$(C_RESET)         rebuild automatically as content changes\n'
	@printf '    $(C_CYAN)clean$(C_RESET)              remove the generated site (output.nosync)\n\n'
	@printf '$(C_BOLD)$(C_BLUE)  PREVIEW$(C_RESET)\n'
	@printf '    $(C_CYAN)serve$(C_RESET) [PORT=8000]         serve at http://localhost:PORT\n'
	@printf '    $(C_CYAN)serve-global$(C_RESET) [SERVER=..]  serve on a chosen interface\n'
	@printf '    $(C_CYAN)devserver$(C_RESET) [PORT=8000]     serve + auto-regenerate\n'
	@printf '    $(C_CYAN)devserver-global$(C_RESET)          devserver on all interfaces\n\n'
	@printf '$(C_BOLD)$(C_MAGENTA)  PUBLISH$(C_RESET)\n'
	@printf '    $(C_CYAN)publish$(C_RESET)            build + deploy to the server via SFTP\n'
	@printf '    $(C_CYAN)github$(C_RESET)             publish to the gh-pages branch\n\n'
	@printf '$(C_BOLD)$(C_YELLOW)  MAINTENANCE$(C_RESET)\n'
	@printf '    $(C_CYAN)changes$(C_RESET)            show uncommitted content changes since last commit\n'
	@printf '    $(C_CYAN)dedupe$(C_RESET)             preview iCloud duplicate files $(C_DIM)(dry run, safe)$(C_RESET)\n'
	@printf '    $(C_CYAN)dedupe-apply$(C_RESET)       move iCloud duplicate files to the Trash\n\n'
	@printf '$(C_BOLD)$(C_WHITE)  FLAGS$(C_RESET)   $(C_DIM)DEBUG=1  RELATIVE=1  PORT=8000  NO_COLOR=1$(C_RESET)\n'

all: _banner
	@printf '$(C_BOLD)$(C_GREEN)▶  Updating data and building the LabMFA site...$(C_RESET)\n'
	LABMFA_PELICAN_BIN="$(PELICAN)" "$(PYTHON)" build.py --build-only

html:
	@printf '$(C_BOLD)$(C_GREEN)▶  Generating Pelican content (fast build)...$(C_RESET)\n'
	"$(PELICAN)" "$(INPUTDIR)" -o "$(OUTPUTDIR)" -s "$(CONFFILE)" $(PELICANOPTS)

production:
	@printf '$(C_BOLD)$(C_GREEN)▶  Generating with production settings...$(C_RESET)\n'
	"$(PELICAN)" "$(INPUTDIR)" -o "$(OUTPUTDIR)" -s "$(PUBLISHCONF)" $(PELICANOPTS)

publish:
	@printf '$(C_BOLD)$(C_MAGENTA)🚀  Building and deploying via SFTP...$(C_RESET)\n'
	LABMFA_PELICAN_BIN="$(PELICAN)" "$(PYTHON)" build.py

clean:
	@printf '$(C_BOLD)$(C_YELLOW)🧽  Removing generated site: $(OUTPUTDIR)$(C_RESET)\n'
	[ ! -d "$(OUTPUTDIR)" ] || rm -rf "$(OUTPUTDIR)"
	@printf '$(C_GREEN)✓  Clean.$(C_RESET)\n'

regenerate:
	@printf '$(C_BOLD)$(C_GREEN)♻️   Watching content and regenerating on change...$(C_RESET)\n'
	"$(PELICAN)" -r "$(INPUTDIR)" -o "$(OUTPUTDIR)" -s "$(CONFFILE)" $(PELICANOPTS)

serve:
	@printf '$(C_BOLD)$(C_BLUE)🌐  Serving at http://localhost:$(if $(filter 0,$(PORT)),8000,$(PORT))$(C_RESET)\n'
	"$(PELICAN)" -l "$(INPUTDIR)" -o "$(OUTPUTDIR)" -s "$(CONFFILE)" $(PELICANOPTS)

serve-global:
	@printf '$(C_BOLD)$(C_BLUE)🌐  Serving on $(SERVER)...$(C_RESET)\n'
	"$(PELICAN)" -l "$(INPUTDIR)" -o "$(OUTPUTDIR)" -s "$(CONFFILE)" $(PELICANOPTS) -b $(SERVER)

devserver:
	@printf '$(C_BOLD)$(C_BLUE)🌐  Dev server + auto-regeneration...$(C_RESET)\n'
	"$(PELICAN)" -lr "$(INPUTDIR)" -o "$(OUTPUTDIR)" -s "$(CONFFILE)" $(PELICANOPTS)

devserver-global:
	@printf '$(C_BOLD)$(C_BLUE)🌐  Dev server on all interfaces...$(C_RESET)\n'
	"$(PELICAN)" -lr "$(INPUTDIR)" -o "$(OUTPUTDIR)" -s "$(CONFFILE)" $(PELICANOPTS) -b 0.0.0.0

github: production
	@printf '$(C_BOLD)$(C_MAGENTA)🚀  Publishing to the $(GITHUB_PAGES_BRANCH) branch...$(C_RESET)\n'
	ghp-import -m "Generate Pelican site" -b $(GITHUB_PAGES_BRANCH) "$(OUTPUTDIR)"
	git push origin $(GITHUB_PAGES_BRANCH)

# --- Maintenance ------------------------------------------------------ #
# `changes` reports SOURCE edits since the last commit (a different
# "previous state" from the build diff, which reports the generated site).
changes:
	@printf '$(C_BOLD)$(C_MAGENTA)✨  Uncommitted content changes since the last commit$(C_RESET)\n'
	@printf '$(C_MAGENTA)──────────────────────────────────────────────────────$(C_RESET)\n'
	@git ls-files --others --exclude-standard | { first=1; while IFS= read -r f; do \
	   [ $$first -eq 1 ] && { printf '$(B_NEW) NEW $(C_RESET) $(C_BOLD)untracked files:$(C_RESET)\n'; first=0; }; \
	   printf '$(C_GREEN)  ✚ %s$(C_RESET)\n' "$$f"; done; }
	@git ls-files --modified | sort -u | { first=1; while IFS= read -r f; do \
	   [ $$first -eq 1 ] && { printf '$(B_MOD) MOD $(C_RESET) $(C_BOLD)modified files:$(C_RESET)\n'; first=0; }; \
	   printf '$(C_YELLOW)  ✎ %s$(C_RESET)\n' "$$f"; done; }
	@git diff --name-only --cached | { first=1; while IFS= read -r f; do \
	   [ $$first -eq 1 ] && { printf '$(B_STAGE) STG $(C_RESET) $(C_BOLD)staged for commit:$(C_RESET)\n'; first=0; }; \
	   printf '$(C_CYAN)  ● %s$(C_RESET)\n' "$$f"; done; }
	@if [ -z "`git status --porcelain`" ]; then \
	   printf '$(C_GREEN)  ✓  Working tree clean — nothing new since the last commit.$(C_RESET)\n'; fi

dedupe:
	@printf '$(C_BOLD)$(C_CYAN)🧹  Previewing iCloud duplicate files (dry run — nothing is deleted)...$(C_RESET)\n'
	"$(PYTHON)" "$(DEDUPE)"

dedupe-apply:
	@printf '$(C_BOLD)$(C_YELLOW)🧹  Moving iCloud duplicate files to the Trash...$(C_RESET)\n'
	"$(PYTHON)" "$(DEDUPE)" --apply

.PHONY: _banner all help html production publish clean regenerate serve \
        serve-global devserver devserver-global github changes dedupe dedupe-apply
