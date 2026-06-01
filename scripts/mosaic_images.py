#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Author: Gustavo R. Anjos
# Email: gustavo.rabello@coppe.ufrj.br
# Date: 2026-05-30
# File: mosaic_images.py

"""Generate the clickable LabMFA team mosaic shown on the homepage."""

from __future__ import annotations

import html
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))
CONTENT_DIR = PROJECT_DIR / "content"
PERSON_DIR = CONTENT_DIR / "pages" / "person"
FRAGMENT_PATH = CONTENT_DIR / "images" / "team-mosaic.html"
LOGO_PATH = "./images/logo-LabMFA.png"
FALLBACK_IMAGE = "images/person/generic.jpg"
PLACEHOLDER_IMAGES = {
    "images/person/generic.jpg",
    "images/person/generic.png",
    "images/person/unknown-male.jpg",
    "images/person/unknown-male.png",
}
TARGET_RATIO = 1.55
LOGO_SHAPES = (
    (1, 1),
    (2, 1),
    (1, 2),
    (2, 2),
)
MOSAIC_GAP = ".45rem"
MOSAIC_MAX_WIDTH = "56rem"


@dataclass(frozen=True)
class Member:
    slug: str
    name: str
    image_path: str
    profile_url: str


@dataclass(frozen=True)
class TilePlacement:
    col: int
    row: int
    col_span: int
    row_span: int


@dataclass(frozen=True)
class Layout:
    columns: int
    rows: int
    logo_col: int
    logo_row: int
    logo_col_span: int
    logo_row_span: int
    placements: tuple[TilePlacement, ...]


def first_heading(path: Path) -> str:
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return path.stem


def profile_image(path: Path) -> tuple[str, bool]:
    source = path.read_text(encoding="utf-8")
    match = re.search(
        r"^\.\. image:: \{static\}/(images/person/[^\s]+)\s*$",
        source,
        flags=re.MULTILINE,
    )
    relative = match.group(1) if match else FALLBACK_IMAGE
    return relative, relative in PLACEHOLDER_IMAGES


def normalize_name(value: str) -> str:
    simplified = unicodedata.normalize("NFKD", value)
    simplified = "".join(
        char for char in simplified if not unicodedata.combining(char)
    )
    simplified = simplified.casefold()
    simplified = re.sub(r"[^a-z0-9]+", " ", simplified)
    return " ".join(simplified.split())


def postdoc_slugs() -> set[str]:
    try:
        import build
    except ImportError:
        return set()

    current, alumni = build.load_student_records()
    records = current + alumni
    build.assign_profile_slugs(records)
    return {
        record["slug"]
        for record in records
        if record["category"] == "postdoc"
    }


def display_name(name: str, slug: str, postdocs: set[str]) -> str:
    if slug not in postdocs:
        return name
    if normalize_name(name).startswith("dr"):
        return name
    return f"Dr. {name}"


def load_members() -> list[Member]:
    members: list[Member] = []
    postdocs = postdoc_slugs()
    for path in sorted(PERSON_DIR.glob("*.rst")):
        name = display_name(first_heading(path), path.stem, postdocs)
        image_path, placeholder = profile_image(path)
        if placeholder:
            continue
        image_file = CONTENT_DIR / image_path
        if not image_file.exists():
            continue
        members.append(
            Member(
                slug=path.stem,
                name=name,
                image_path=f"./{image_path}",
                profile_url=f"./person/{path.stem}",
            )
        )
    members = sorted(members, key=lambda member: normalize_name(member.name))
    gustavo_index = next(
        (index for index, member in enumerate(members) if member.slug == "gustavoRabello"),
        None,
    )
    if gustavo_index is not None:
        members.insert(0, members.pop(gustavo_index))
    return members


def center_start(track_count: int, span: int) -> int:
    return (track_count - span) // 2


def mark(
    occupied: list[list[bool]],
    row: int,
    col: int,
    row_span: int,
    col_span: int,
    value: bool,
) -> None:
    for test_row in range(row, row + row_span):
        for test_col in range(col, col + col_span):
            occupied[test_row][test_col] = value


def first_empty_cell(occupied: list[list[bool]]) -> tuple[int, int] | None:
    for row, values in enumerate(occupied):
        for col, used in enumerate(values):
            if not used:
                return row, col
    return None


def build_photo_placements(
    columns: int,
    rows: int,
    logo_col: int,
    logo_row: int,
    logo_col_span: int,
    logo_row_span: int,
) -> tuple[TilePlacement, ...]:
    occupied = [[False] * columns for _ in range(rows)]
    mark(
        occupied,
        logo_row,
        logo_col,
        logo_row_span,
        logo_col_span,
        True,
    )

    placements: list[TilePlacement] = []
    while True:
        empty = first_empty_cell(occupied)
        if empty is None:
            break
        row, col = empty
        placements.append(
            TilePlacement(
                col=col,
                row=row,
                col_span=1,
                row_span=1,
            )
        )
        occupied[row][col] = True
    return tuple(placements)


def find_layout(member_count: int) -> Layout:
    if member_count <= 0:
        raise RuntimeError("No team members available for the homepage mosaic.")

    best_layout: Layout | None = None
    best_score: float | None = None

    for logo_col_span, logo_row_span in LOGO_SHAPES:
        total_area = member_count + logo_col_span * logo_row_span
        for columns in range(max(logo_col_span, 3), total_area + 1):
            if total_area % columns != 0:
                continue
            rows = total_area // columns
            if rows < logo_row_span:
                continue

            logo_col = center_start(columns, logo_col_span)
            logo_row = center_start(rows, logo_row_span)
            placements = build_photo_placements(
                columns,
                rows,
                logo_col,
                logo_row,
                logo_col_span,
                logo_row_span,
            )
            if len(placements) != member_count:
                continue

            ratio = columns / rows
            center_offset = abs((columns / 2) - (logo_col + logo_col_span / 2))
            center_offset += abs((rows / 2) - (logo_row + logo_row_span / 2))
            logo_penalty = 0.0 if (logo_col_span, logo_row_span) == (1, 1) else 0.08
            score = abs(ratio - TARGET_RATIO) + center_offset * 0.05 + logo_penalty
            if best_score is None or score < best_score:
                best_score = score
                best_layout = Layout(
                    columns=columns,
                    rows=rows,
                    logo_col=logo_col,
                    logo_row=logo_row,
                    logo_col_span=logo_col_span,
                    logo_row_span=logo_row_span,
                    placements=placements,
                )

    if best_layout is None:
        raise RuntimeError("Could not compute a gap-free team mosaic layout.")
    return best_layout


def render_member_tile(member: Member, placement: TilePlacement) -> str:
    title = html.escape(member.name, quote=True)
    href = html.escape(member.profile_url, quote=True)
    image_path = html.escape(member.image_path, quote=True)
    return """    <a class="labmfa-team-mosaic__person" href="{href}" title="{title}" aria-label="{title}" style="background: #dfe7ee; border-radius: 14px; box-shadow: 0 10px 24px rgba(15, 35, 55, .12); display: block; grid-column: {col_start} / span {col_span}; grid-row: {row_start} / span {row_span}; min-height: 0; min-width: 0; overflow: hidden; position: relative; text-decoration: none;">
      <img src="{image_path}" alt="{title}" loading="lazy" style="display: block; width: 100%; height: 100%; object-fit: cover;">
      <span class="labmfa-team-mosaic__name" style="bottom: .55rem; color: #fff; font-size: .78rem; font-weight: 600; left: .65rem; line-height: 1.2; opacity: 0; position: absolute; right: .65rem; transform: translateY(6px); transition: opacity .2s ease, transform .2s ease; z-index: 2;">{title}</span>
    </a>""".format(
        href=href,
        title=title,
        image_path=image_path,
        col_start=placement.col + 1,
        col_span=placement.col_span,
        row_start=placement.row + 1,
        row_span=placement.row_span,
    )


def render_logo_tile(layout: Layout) -> str:
    return """    <div class="labmfa-team-mosaic__logo" aria-hidden="true" style="align-items: center; background: rgba(255, 255, 255, .96); border: 1px solid rgba(0, 64, 133, .14); border-radius: 50%; box-shadow: 0 22px 44px rgba(15, 35, 55, .2); display: flex; grid-column: {col_start} / span {col_span}; grid-row: {row_start} / span {row_span}; justify-content: center; min-height: 0; min-width: 0; overflow: hidden; padding: 1rem; pointer-events: none;">
      <img src="{logo_path}" alt="LabMFA logo" style="display: block; width: 100%; height: 100%; object-fit: contain;">
    </div>""".format(
        col_start=layout.logo_col + 1,
        col_span=layout.logo_col_span,
        row_start=layout.logo_row + 1,
        row_span=layout.logo_row_span,
        logo_path=html.escape(LOGO_PATH, quote=True),
    )


def render_fragment(members: list[Member]) -> str:
    layout = find_layout(len(members))

    tiles = [
        render_member_tile(member, placement)
        for member, placement in zip(members, layout.placements)
    ]

    return """<style>
.labmfa-team-mosaic__person::after {{
  background: linear-gradient(180deg, rgba(10, 20, 30, 0) 42%, rgba(10, 20, 30, .72) 100%);
  content: "";
  inset: 0;
  opacity: 0;
  position: absolute;
  transition: opacity .2s ease;
}}
.labmfa-team-mosaic__person:hover::after,
.labmfa-team-mosaic__person:focus::after {{
  opacity: 1;
}}
.labmfa-team-mosaic__person:hover .labmfa-team-mosaic__name,
.labmfa-team-mosaic__person:focus .labmfa-team-mosaic__name {{
  opacity: 1 !important;
  transform: translateY(0) !important;
}}
</style>
<div class="labmfa-team-mosaic" aria-label="LabMFA team mosaic" style="margin: 0 auto 1.5rem; max-width: {max_width}; width: 100%;">
  <div class="labmfa-team-mosaic__grid" style="display: grid; width: 100%; aspect-ratio: {columns} / {rows}; gap: {gap}; grid-template-columns: repeat({columns}, minmax(0, 1fr)); grid-template-rows: repeat({rows}, minmax(0, 1fr));">
{tiles}
{logo}
  </div>
</div>""".format(
        gap=MOSAIC_GAP,
        max_width=MOSAIC_MAX_WIDTH,
        columns=layout.columns,
        rows=layout.rows,
        tiles="\n".join(tiles),
        logo=render_logo_tile(layout),
    )


def main() -> None:
    members = load_members()
    fragment = render_fragment(members)
    FRAGMENT_PATH.parent.mkdir(parents=True, exist_ok=True)
    FRAGMENT_PATH.write_text(fragment + "\n", encoding="utf-8")
    print(f"Team mosaic fragment updated: {FRAGMENT_PATH}")
    print(f"Members included: {len(members)}")


if __name__ == "__main__":
    main()
