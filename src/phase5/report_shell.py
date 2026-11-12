"""Consistent navigation frame shared by Workforce Intelligence report pages.

The fixed UI shell — rather than the chart arrangement — is the report's
visual identity. Do not prescribe identical analytics visuals to all pages.
"""

from src.phase5.build_executive_report import PALETTE, shape, textbox, slicer, lid


def shared_filter(unique_label, display_label, table, field, x, width):
    """Stable per-page visual ID with the same visible filter label on all pages."""
    visual = slicer(unique_label, table, field, x, 12, width)
    visual["visual"]["objects"]["header"][0]["properties"]["text"] = lid(
        f"'{display_label}'"
    )
    return visual


def shared_frame(page_number, view_label, title_lines, subtitle, main_title,
                 main_subtitle, prefix):
    """Navy sidebar, page identity, top-right common filters and main heading.

    Positions and typography intentionally match the planning cockpit.
    `prefix` avoids colliding with existing pages' stable visual identifiers.
    """
    if len(title_lines) != 2:
        raise ValueError("Sidebar title must contain exactly two lines")
    return [
        shape(f"{prefix}_sidebar", 0, 0, 276, 720, PALETTE["navy"], z=10),
        shape(f"{prefix}_sidebar_accent", 273, 0, 3, 720,
              PALETTE["teal"], z=20),
        textbox(f"{prefix}_brand", "WORKFORCE INTELLIGENCE", 20, 17, 240,
                24, 11, "#9FB3C8", bold=True),
        textbox(f"{prefix}_page_index", f"{page_number:02d} / 06  -  {view_label}",
                20, 54, 238, 27, 13, "#52CBD1", bold=True),
        textbox(f"{prefix}_title_top", title_lines[0], 20, 91, 245, 42,
                25, PALETTE["white"], bold=True),
        textbox(f"{prefix}_title_bottom", title_lines[1], 20, 126, 245, 42,
                25, PALETTE["white"], bold=True),
        textbox(f"{prefix}_sidebar_subtitle", subtitle, 20, 180, 238, 25,
                12, "#C3D5E2"),
        textbox(f"{prefix}_main_title", main_title, 294, 25, 558, 38, 24,
                PALETTE["navy"], bold=True),
        textbox(f"{prefix}_main_subtitle", main_subtitle, 296, 65, 551, 25,
                12, PALETTE["subtle"]),
        shared_filter(f"{prefix} Year", "Year", "Dim Month", "year", 857, 145),
        shared_filter(f"{prefix} Department", "Department", "Dim Department",
                      "department", 1010, 251),
    ]
