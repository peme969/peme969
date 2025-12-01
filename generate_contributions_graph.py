"""
GitHub-style contribution SVG with a one-time intro animation:

1. On load: ALL contribution cells fly into place to form TEXT_WORD
   (e.g. "PEME") in a bright color.
2. They pause there for a bit so you can actually see it.
3. They fly back to their true GitHub positions and colors and stay put.

To customize the word, change TEXT_WORD below.
"""
import datetime as dt,sys,os,textwrap,requests
GITHUB_GRAPHQL_ENDPOINT = "https://api.github.com/graphql"
TEXT_WORD = "PEME"
DARK_PALETTE = {
    "NONE": "#151B23",
    "FIRST_QUARTILE": "#0e4429",
    "SECOND_QUARTILE": "#006d32",
    "THIRD_QUARTILE": "#26a641",
    "FOURTH_QUARTILE": "#39d353",
}
LETTER_FILL = "#f59e0b"
def _day_suffix(day: int) -> str:
    if 11 <= day <= 13:
        return "th"
    last = day % 10
    if last == 1:
        return "st"
    if last == 2:
        return "nd"
    if last == 3:
        return "rd"
    return "th"
def format_tooltip(count: int, date_str: str) -> str:
    d = dt.date.fromisoformat(date_str)
    month_name = d.strftime("%B")
    day = d.day
    suffix = _day_suffix(day)
    year = d.year
    if count == 0:
        prefix = "No contributions"
    elif count == 1:
        prefix = "1 contribution"
    else:
        prefix = f"{count} contributions"

    return f"{prefix} on {month_name} {day}{suffix}, {year}"
def fetch_contributions(login: str, year: int, token: str):
    start = dt.datetime(year, 1, 1, 0, 0, 0)
    end = dt.datetime(year, 12, 31, 23, 59, 59)
    query = """
    query($login: String!, $from: DateTime!, $to: DateTime!) {
      user(login: $login) {
        contributionsCollection(from: $from, to: $to) {
          contributionCalendar {
            totalContributions
            weeks {
              contributionDays {
                date
                weekday
                contributionCount
                contributionLevel
              }
            }
          }
        }
      }
    }
    """
    variables = {
        "login": login,
        "from": start.isoformat() + "Z",
        "to": end.isoformat() + "Z",
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    resp = requests.post(
        GITHUB_GRAPHQL_ENDPOINT,
        headers=headers,
        json={"query": query, "variables": variables},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if "errors" in data:
        raise RuntimeError(f"GitHub GraphQL error: {data['errors']}")
    try:
        calendar = data["data"]["user"]["contributionsCollection"][
            "contributionCalendar"
        ]
    except TypeError:
        raise RuntimeError("User not found or contributions unavailable")
    return calendar

# ----------------- 5x7 ASCII FONT + TEXT → PIXELS -----------------

# Minimal 5x7 font for A–Z and space. You can extend this if you want.
FONT_5x7 = {
    "A": [
        ".###.",
        "#...#",
        "#...#",
        "#####",
        "#...#",
        "#...#",
        ".....",
    ],
    "B": [
        "####.",
        "#...#",
        "####.",
        "#...#",
        "#...#",
        "####.",
        ".....",
    ],
    "E": [
        "#####",
        "#....",
        "###..",
        "#....",
        "#....",
        "#####",
        ".....",
    ],
    "M": [
        "#...#",
        "##.##",
        "#.#.#",
        "#.#.#",
        "#...#",
        "#...#",
        ".....",
    ],
    "P": [
        "####.",
        "#...#",
        "####.",
        "#....",
        "#....",
        "#....",
        ".....",
    ],
    "F": [
        "#####",
        "#....",
        "###..",
        "#....",
        "#....",
        "#....",
        ".....",
    ],
    " ": [
        ".....",
        ".....",
        ".....",
        ".....",
        ".....",
        ".....",
        ".....",
    ],
}
def build_text_pixels(text: str, scale: int = 2, spacing: int = 1):
    """
    Convert TEXT_WORD into a list of "on" pixel positions using the 5x7 font.

    Returns:
      pixels: list[(col, row)]
      num_cols: total columns in the scaled grid
      num_rows: total rows in the scaled grid
    """
    text = text.upper()
    # Build the base 5x7 grid row by row
    base_rows = [""] * 7
    first = True
    for ch in text:
        pattern = FONT_5x7.get(ch, FONT_5x7[" "])  # unknown → space
        for r in range(7):
            if not first:
                base_rows[r] += "." * spacing
            base_rows[r] += pattern[r]
        first = False
    base_cols = len(base_rows[0])
    base_rows_count = len(base_rows)
    pixels = []
    for row_idx, row in enumerate(base_rows):
        for col_idx, ch in enumerate(row):
            if ch == "#":
                # scale each "on" pixel into a block of size scale x scale
                for sy in range(scale):
                    for sx in range(scale):
                        pixels.append((col_idx * scale + sx, row_idx * scale + sy))
    num_cols = base_cols * scale
    num_rows = base_rows_count * scale
    return pixels, num_cols, num_rows
# ----------------- SVG & ANIMATION -----------------
def build_svg(calendar: dict, year: int, username: str) -> str:
    weeks = calendar["weeks"]
    CELL_SIZE = 11
    CELL_GAP = 3
    CARD_PADDING_LEFT = 46
    CARD_PADDING_TOP = 38
    CARD_PADDING_RIGHT = 22
    CARD_PADDING_BOTTOM = 36
    TITLE_X = 24
    TITLE_Y = 30
    NUM_WEEKS = len(weeks)
    NUM_DAYS = 7

    card_width = (
        CARD_PADDING_LEFT
        + CARD_PADDING_RIGHT
        + NUM_WEEKS * (CELL_SIZE + CELL_GAP)
        - CELL_GAP
    )
    card_height = (
        CARD_PADDING_TOP
        + CARD_PADDING_BOTTOM
        + NUM_DAYS * (CELL_SIZE + CELL_GAP)
        - CELL_GAP
    )

    SVG_PADDING = 20
    width = card_width + SVG_PADDING * 2
    height = card_height + SVG_PADDING * 2 + 20

    CARD_X = SVG_PADDING
    CARD_Y = TITLE_Y + 18

    background_color = "#00000000"
    card_color = "#0d1117"
    border_color = "#30363d"

    FONT_FAMILY = "system-ui,-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif"
    # Build pixels for TEXT_WORD (e.g. "PEME")
    text_pixels, letter_cols, letter_rows = build_text_pixels(TEXT_WORD, scale=2)
    # Place the word roughly centered in the card
    letter_block_width = letter_cols * (CELL_SIZE + CELL_GAP) - CELL_GAP
    letter_block_height = letter_rows * (CELL_SIZE + CELL_GAP) - CELL_GAP
    letter_origin_x = CARD_X + (card_width - letter_block_width) / 2
    letter_origin_y = CARD_Y + (card_height - letter_block_height) / 2
    svg_parts = []
    # Background
    svg_parts.append(
        f'<rect width="{width}" height="{height}" fill="{background_color}" />'
    )
    # Title
    svg_parts.append(
        f'<text x="{TITLE_X}" y="{TITLE_Y}" '
        f'font-family="{FONT_FAMILY}" font-size="18" '
        f'fill="#8b949e">{calendar["totalContributions"]} '
        f"contributions in {year}</text>"
    )
    # Card
    svg_parts.append(
        f'<rect x="{CARD_X}" y="{CARD_Y}" '
        f'width="{card_width}" height="{card_height}" '
        f'rx="10" ry="10" fill="{card_color}" '
        f'stroke="{border_color}" stroke-width="1" />'
    )
    inner_left = CARD_X + CARD_PADDING_LEFT
    inner_top = CARD_Y + CARD_PADDING_TOP
    # Weekday labels
    weekday_labels = {1: "Mon", 3: "Wed", 5: "Fri"}
    for weekday, label in weekday_labels.items():
        y = inner_top + weekday * (CELL_SIZE + CELL_GAP) + CELL_SIZE - 1
        svg_parts.append(
            f'<text x="{CARD_X + 6}" y="{y}" '
            f'font-family="{FONT_FAMILY}" font-size="12" '
            f'fill="#8b949e">{label}</text>'
        )
    # Month labels
    last_month = None
    for week_index, week in enumerate(weeks):
        if not week["contributionDays"]:
            continue
        first_date_str = week["contributionDays"][0]["date"]
        first_date = dt.date.fromisoformat(first_date_str)
        month_name = first_date.strftime("%b")
        if month_name != last_month:
            last_month = month_name
            x = inner_left + week_index * (CELL_SIZE + CELL_GAP)
            svg_parts.append(
                f'<text x="{x}" y="{CARD_Y + 20}" '
                f'font-family="{FONT_FAMILY}" font-size="14" '
                f'fill="#e6edf3">{month_name}</text>'
            )
    # Animation timing – with a hold in the text shape
    ANIM_DURATION = "6s"
    # 0: start grid, 0.25: in text, 0.75: still text, 1: back to grid
    ANIM_KEYTIMES = "0;0.25;0.75;1"
    # Flatten all cells for easy mapping
    all_cells = []
    for week_index, week in enumerate(weeks):
        for day in week["contributionDays"]:
            all_cells.append((week_index, day))
    total_cells = len(all_cells)
    total_text_pixels = len(text_pixels)
    # Contribution cells – ALL animate into the text then back
    for cell_index, (week_index, day) in enumerate(all_cells):
        weekday = day["weekday"]
        level = day["contributionLevel"]
        count = day["contributionCount"]
        date_str = day["date"]
        # Final (graph) color
        if count == 0:
            final_color = DARK_PALETTE["NONE"]
        else:
            if level == "FIRST_QUARTILE":
                final_color = DARK_PALETTE["FIRST_QUARTILE"]
            elif level == "SECOND_QUARTILE":
                final_color = DARK_PALETTE["SECOND_QUARTILE"]
            elif level == "THIRD_QUARTILE":
                final_color = DARK_PALETTE["THIRD_QUARTILE"]
            elif level == "FOURTH_QUARTILE":
                final_color = DARK_PALETTE["FOURTH_QUARTILE"]
            else:
                final_color = DARK_PALETTE["FIRST_QUARTILE"]
        # Grid position
        x = inner_left + week_index * (CELL_SIZE + CELL_GAP)
        y = inner_top + weekday * (CELL_SIZE + CELL_GAP)
        tooltip = format_tooltip(count, date_str)
        # Pick target text pixel (wrap index so ALL cells land on some letter pixel).
        # This makes extra cells stack on existing letter pixels, so there are
        # NO stray dots outside the text shape.
        px, py = text_pixels[cell_index % total_text_pixels]
        target_x = letter_origin_x + px * (CELL_SIZE + CELL_GAP)
        target_y = letter_origin_y + py * (CELL_SIZE + CELL_GAP)
        svg_parts.append(
            "<g>"
            f'<rect x="{x}" y="{y}" width="{CELL_SIZE}" height="{CELL_SIZE}" '
            f'rx="3" ry="3" fill="{final_color}">'
            f"<title>{tooltip}</title>"
            # X animation: grid → text → text → grid
            f'<animate attributeName="x" '
            f'values="{x};{target_x};{target_x};{x}" '
            f'keyTimes="{ANIM_KEYTIMES}" dur="{ANIM_DURATION}" '
            f'begin="0s" fill="freeze" />'
            # Y animation
            f'<animate attributeName="y" '
            f'values="{y};{target_y};{target_y};{y}" '
            f'keyTimes="{ANIM_KEYTIMES}" dur="{ANIM_DURATION}" '
            f'begin="0s" fill="freeze" />'
            # Fill animation: final → bright → bright → final
            f'<animate attributeName="fill" '
            f'values="{final_color};{LETTER_FILL};{LETTER_FILL};{final_color}" '
            f'keyTimes="{ANIM_KEYTIMES}" dur="{ANIM_DURATION}" '
            f'begin="0s" fill="freeze" />'
            "</rect>"
            "</g>"
        )
    # Legend
    legend_y = CARD_Y + card_height - 10
    legend_x = inner_left - 6
    svg_parts.append(
        f'<text x="{legend_x}" y="{legend_y}" '
        f'font-family="{FONT_FAMILY}" font-size="14" '
        f'fill="#8b949e">Less</text>'
    )
    legend_colors = [
        DARK_PALETTE["NONE"],
        DARK_PALETTE["FIRST_QUARTILE"],
        DARK_PALETTE["SECOND_QUARTILE"],
        DARK_PALETTE["THIRD_QUARTILE"],
        DARK_PALETTE["FOURTH_QUARTILE"],
    ]
    square_x = legend_x + 40
    for c in legend_colors:
        svg_parts.append(
            f'<rect x="{square_x}" y="{legend_y - 11}" '
            f'width="14" height="14" rx="3" ry="3" fill="{c}" />'
        )
        square_x += 18
    svg_parts.append(
        f'<text x="{square_x + 6}" y="{legend_y}" '
        f'font-family="{FONT_FAMILY}" font-size="14" '
        f'fill="#8b949e">More</text>'
    )
    svg = textwrap.dedent(
        f"""\
        <svg xmlns="http://www.w3.org/2000/svg"
             width="{width}" height="{height}"
             viewBox="0 0 {width} {height}">
          {" ".join(svg_parts)}
        </svg>
        """
    )
    return svg

def main():
    login = "peme969"
    year = dt.datetime.now().year
    # get os environment variable called GTHUB_TOKEN
    token = os.environ.get("GTHUB_TOKEN")
    if not token:
        print("Error: please set the GITHUB_TOKEN environment variable.")
        sys.exit(1)
    print(f"Fetching contributions for {login} in {year}...")
    calendar = fetch_contributions(login, year, token)
    print("Building SVG...")
    svg = build_svg(calendar, year, login)
    filename = f"{login}_contributions.svg"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Done. Wrote SVG to {filename}")
if __name__ == "__main__":
    main()
