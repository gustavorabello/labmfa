#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: Gustavo R. Anjos
# Email: gustavo.rabello@gmail.com
# Date: 2026-05-31
# File: prepare_advising_topics.py

"""Generate the draft advising-topics page from local BibTeX sources."""

from __future__ import annotations

import re
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

import build

OUTPUT_PATH = PROJECT_DIR / "content/pages/advising-topics.rst"
UNDERGRAD_BIB = build.BIB_DIR / "undergrad.bib"
THESIS_CONCLUDED_BIB = build.BIB_DIR / "thesisConcluded.bib"

CATEGORY_ORDER = [
    "multiphase flows, interface dynamics, two-phase flows, particulate flows",
    "fluid-structure interaction and coupled systems",
    "heat transfer, porous media, and thermal systems",
    "experimental infrastructure",
    "stream-function/vorticity formulation",
    "potential flows",
    "scientific computing",
]

CATEGORY_MAP = {
    "emanuelSantos2025": CATEGORY_ORDER[0],
    "barbedo2024": CATEGORY_ORDER[0],
    "vidal2023thesis": CATEGORY_ORDER[0],
    "feres2023": CATEGORY_ORDER[0],
    "innocente2021": CATEGORY_ORDER[0],
    "gros2018thesis": CATEGORY_ORDER[0],
    "renatoRosa2026": CATEGORY_ORDER[0],
    "ferreira2023": CATEGORY_ORDER[0],
    "coimbra2023": CATEGORY_ORDER[0],
    "spesani2023": CATEGORY_ORDER[0],
    "kropf2022": CATEGORY_ORDER[0],
    "andrade2021": CATEGORY_ORDER[0],
    "fontenele2021": CATEGORY_ORDER[0],
    "sousa2019": CATEGORY_ORDER[0],
    "garden2025": CATEGORY_ORDER[1],
    "rosa2026": CATEGORY_ORDER[1],
    "eduardoSoares2026": CATEGORY_ORDER[1],
    "oliveira2023": CATEGORY_ORDER[1],
    "goncalves2022": CATEGORY_ORDER[1],
    "gomes2021": CATEGORY_ORDER[1],
    "hildebrandt2021": CATEGORY_ORDER[1],
    "amaral2020": CATEGORY_ORDER[1],
    "silva2020": CATEGORY_ORDER[1],
    "victorino2020": CATEGORY_ORDER[1],
    "marquessantos2018": CATEGORY_ORDER[1],
    "lima2026": CATEGORY_ORDER[2],
    "gomes2025": CATEGORY_ORDER[2],
    "oliveira2025": CATEGORY_ORDER[2],
    "waehneldt2023": CATEGORY_ORDER[2],
    "teixeira2023": CATEGORY_ORDER[2],
    "miranda2023": CATEGORY_ORDER[2],
    "mattos2023": CATEGORY_ORDER[2],
    "araujo2022": CATEGORY_ORDER[2],
    "mello2022": CATEGORY_ORDER[2],
    "florentino2022": CATEGORY_ORDER[2],
    "prado2022": CATEGORY_ORDER[2],
    "ramalho2022": CATEGORY_ORDER[2],
    "pinheiro2022": CATEGORY_ORDER[2],
    "alves2021": CATEGORY_ORDER[2],
    "aguiar2020": CATEGORY_ORDER[2],
    "mendes2020": CATEGORY_ORDER[2],
    "cunha2019": CATEGORY_ORDER[2],
    "cerqueirajr2018": CATEGORY_ORDER[2],
    "cunha2018": CATEGORY_ORDER[2],
    "lobo2017": CATEGORY_ORDER[2],
    "eloy2017": CATEGORY_ORDER[2],
    "quentin2026": CATEGORY_ORDER[3],
    "mota2026": CATEGORY_ORDER[3],
    "igor2025": CATEGORY_ORDER[3],
    "balmant2025": CATEGORY_ORDER[3],
    "borgessantos2022": CATEGORY_ORDER[3],
    "ferreira2020": CATEGORY_ORDER[3],
    "cunha2020": CATEGORY_ORDER[4],
    "marquessantos2020": CATEGORY_ORDER[4],
    "cerqueira2020": CATEGORY_ORDER[4],
    "carrasco2022": CATEGORY_ORDER[4],
    "lage2022": CATEGORY_ORDER[4],
    "oliveirasantos2022": CATEGORY_ORDER[4],
    "pires2023": CATEGORY_ORDER[5],
    "antao2024": CATEGORY_ORDER[6],
    "gottgtroy2025": CATEGORY_ORDER[6],
    "rodrigues2015thesis": CATEGORY_ORDER[6],
    "brenoMota2026_tcc": CATEGORY_ORDER[6],
    "lucasBorges2026": CATEGORY_ORDER[6],
    "heitor2025": CATEGORY_ORDER[6],
    "carvalho2025": CATEGORY_ORDER[6],
    "xavier2024": CATEGORY_ORDER[6],
    "rocha2023": CATEGORY_ORDER[6],
    "capitanio2023": CATEGORY_ORDER[6],
    "ferreira2019": CATEGORY_ORDER[6],
}

DOC_LINKS = {
    "emanuelSantos2025": "/documents/antonioEmanuel-msc.pdf",
    "gottgtroy2025": "/documents/higorOdilon-msc.pdf",
    "antao2024": "/documents/gabrielAntao-msc.pdf",
    "barbedo2024": "/documents/danielBarbedo-dsc.pdf",
    "vidal2023thesis": "/documents/rafaelVidal-msc.pdf",
    "feres2023": "/documents/felipeFeres-msc.pdf",
    "innocente2021": "/documents/joaoInnocente-msc.pdf",
    "balmant2025": "/documents/anaMariaBalmant-tcc-tunel-vento.pdf",
}

SECTION_INTROS = {
    CATEGORY_ORDER[0]: (
        "This section groups works centered on multiphase phenomena and related "
        "transport problems, including particle-laden and porous-flow applications."
    ),
    CATEGORY_ORDER[4]: (
        "This section isolates works explicitly organized around the "
        "stream-function/vorticity formulation."
    ),
    CATEGORY_ORDER[5]: (
        "This section isolates the potential-flow line used in aerodynamic studies."
    ),
    CATEGORY_ORDER[6]: (
        "This section groups works whose main contribution is computational "
        "methodology, code development, optimization, machine learning, or "
        "scientific-computing infrastructure."
    ),
}

TYPE_LABELS = {
    "phdthesis": "D.Sc.",
    "masterthesis": "M.Sc.",
    "bachelorsthesis": "TCC",
}

TYPE_PRIORITY = {
    "phdthesis": 0,
    "masterthesis": 1,
    "bachelorsthesis": 2,
}


def normalize_space(value: str) -> str:
    return " ".join(value.split())


def entry_text(entry: dict[str, str], field_name: str) -> str:
    return normalize_space(build.latex_to_text(entry.get(field_name, "")))


def has_anjos_advising(entry: dict[str, str]) -> bool:
    note = entry_text(entry, "note")
    return "Anjos" in note


def format_bib_author(author: str) -> str:
    author = normalize_space(build.latex_to_text(author))
    if "," not in author:
        return author
    last, first = [part.strip() for part in author.split(",", 1)]
    return f"{first} {last}".strip()


def format_authors(raw_authors: str) -> str:
    authors = [
        format_bib_author(author)
        for author in re.split(r"\s+and\s+", raw_authors)
        if author.strip()
    ]
    return "; ".join(authors)


def link_label(entry_key: str) -> str:
    return f"doc-{entry_key}"


def format_title(entry_key: str, title: str) -> str:
    if entry_key in DOC_LINKS:
        return f"`{title} <{link_label(entry_key)}_>`_"
    return f"*{title}*"


def load_entries() -> list[dict[str, str]]:
    combined = []
    for path in (THESIS_CONCLUDED_BIB, UNDERGRAD_BIB):
        for entry in build.parse_bibtex_entries(path, {"thesis"}):
            if not has_anjos_advising(entry):
                continue
            entry_type = entry.get("type", "").strip().lower()
            if entry_type not in TYPE_LABELS:
                continue
            key = entry["_entry_key"]
            if key not in CATEGORY_MAP:
                raise KeyError(f"Missing category mapping for {key}")
            combined.append(entry)
    return combined


def sort_key(entry: dict[str, str]) -> tuple[int, int, str]:
    year = int(entry_text(entry, "year") or 0)
    entry_type = entry.get("type", "").strip().lower()
    title = entry_text(entry, "title").casefold()
    return (-year, TYPE_PRIORITY[entry_type], title)


def render_section(entries: list[dict[str, str]], category: str) -> list[str]:
    lines = [category, "_" * len(category), ""]
    intro = SECTION_INTROS.get(category)
    if intro:
        lines.extend([intro, ""])

    for entry in sorted(entries, key=sort_key):
        key = entry["_entry_key"]
        entry_type = entry.get("type", "").strip().lower()
        year = entry_text(entry, "year")
        title = entry_text(entry, "title")
        authors = format_authors(entry.get("author", ""))
        lines.append(
            f"- `{TYPE_LABELS[entry_type]}` {year} - "
            f"{format_title(key, title)} ({authors})"
        )
    lines.append("")
    lines.append("")
    return lines


def render_references(entries: list[dict[str, str]]) -> list[str]:
    lines = [".. Place your references here"]
    for entry in sorted(entries, key=lambda item: item["_entry_key"]):
        key = entry["_entry_key"]
        if key not in DOC_LINKS:
            continue
        lines.append(f".. _{link_label(key)}: {DOC_LINKS[key]}")
    return lines


def render_page(entries: list[dict[str, str]]) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    by_category = {category: [] for category in CATEGORY_ORDER}
    for entry in entries:
        by_category[CATEGORY_MAP[entry["_entry_key"]]].append(entry)

    lines = [
        "Supervision Themes and Research Lines",
        "-------------------------------------",
        "",
        ":date: 2026-05-31 22:20",
        f":modified: {now}",
        ":status: draft",
        ":slug: advising-topics",
        "",
        "This draft page organizes completed undergraduate final projects, M.Sc.",
        "dissertations, and D.Sc. theses by research line.",
        "",
        "The taxonomy is generated from local ``.bib`` files through",
        "``python3 scripts/prepare_advising_topics.py``.",
        "",
        ".. AUTO-GENERATED ADVISING TOPICS START: run python3 scripts/prepare_advising_topics.py",
        "",
    ]

    for category in CATEGORY_ORDER:
        lines.extend(render_section(by_category[category], category))

    lines.extend(render_references(entries))
    lines.extend(
        [
            "",
            ".. AUTO-GENERATED ADVISING TOPICS END",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> None:
    entries = load_entries()
    OUTPUT_PATH.write_text(render_page(entries), encoding="utf-8")
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
