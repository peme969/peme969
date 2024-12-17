import requests
from svgwrite import Drawing
from datetime import datetime
import os
GITHUB_API_KEY = os.environ['graphql'] 
USERNAME = "peme969"

COLORS = {
    "base03": "#002b36",
    "base02": "#073642",
    "blue": "#268bd2",
    "cyan": "#2aa198",
    "green": "#859900",
    "title_color":"#4b88a5",
    "title_bg":"#d5dbde"
}

def fetch_yearly_contributions(username, token):
    url = "https://api.github.com/graphql"
    headers = {"Authorization": f"Bearer {token}"}
    query = """
    query($username: String!) {
      user(login: $username) {
        contributionsCollection {
          contributionCalendar {
            weeks {
              contributionDays {
                date
                contributionCount
              }
            }
          }
        }
      }
    }
    """
    variables = {"username": username}
    response = requests.post(url, json={"query": query, "variables": variables}, headers=headers)
    response_json = response.json()

    if "errors" in response_json:
        raise Exception(f"GraphQL query error: {response_json['errors']}")

    if "data" not in response_json:
        raise Exception("Response does not contain 'data' field.")

    data = response_json["data"]
    contributions = []
    weeks = data["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    for week in weeks:
        for day in week["contributionDays"]:
            contributions.append({"date": day["date"], "count": day["contributionCount"]})

    return contributions

def format_date(date_str):
    date = datetime.strptime(date_str, "%Y-%m-%d")
    return date.strftime("%b. %d")

def generate_svg(data, filename="github_contributions_enhanced.svg"):
    width, height = 1020, 250  
    cell_size = 15
    padding = 3
    border_radius = 3  
    legend_height = 70
    dwg = Drawing(filename, size=(width, height), profile="full", debug=True)

    title_font = "Verdana"
    text_font = "Verdana"

    dwg.add(
    dwg.rect(
        insert=(0, 0),
        size=(width, height),
        fill=COLORS["base03"],
        fill_opacity=0.0,
    )
)

    title_y = 30
    dwg.add(
        dwg.rect(
            insert=(200, 6),
            size=(600, 30),
            fill=COLORS['title_bg'],
            rx=border_radius,
            ry=border_radius
        )
    )
    dwg.add(
        dwg.text(
            "GitHub Contributions - 2024",
            insert=(width / 2, title_y),
            fill=COLORS["title_color"],
            font_size="24px",
            font_family=title_font,
            font_weight="bold",
            text_anchor="middle",
        )
    )

    x_start, y_start = 50, 80
    x, y = x_start, y_start

    for i, day in enumerate(data):
        count = day["count"]

        if count == 0:
            color = COLORS["base02"]
        elif count == 1:
            color = COLORS["blue"]
        elif count == 2:
            color = COLORS["cyan"]
        elif count >= 3:
            color = COLORS["green"]

        rect = dwg.rect(
            insert=(x, y),
            size=(cell_size, cell_size),
            fill=color,
            rx=border_radius,
            ry=border_radius,
            style="opacity: 0; animation: fadeIn 1s ease-in-out forwards; animation-delay: {}s".format(i * 0.02)
        )
        dwg.add(rect)

        y += cell_size + padding
        if (i + 1) % 7 == 0:  
            y = y_start
            x += cell_size + padding

    legend_x = x_start
    legend_y = y_start + (7 * (cell_size + padding)) + 20
    legend_items = [
        {"label": "Less", "color": COLORS["base02"]},
        {"label": "1", "color": COLORS["blue"]},
        {"label": "2", "color": COLORS["cyan"]},
        {"label": "3+", "color": COLORS["green"]},
        {'label':'More','color':'nerd'}
    ]

    for i, item in enumerate(legend_items):
        legend_rect_x = legend_x + (i * (cell_size + 60))
        legend_text_x = legend_rect_x + cell_size + 5
        label = item['label']
        if label =='Less':
                    dwg.add(
                dwg.text(
                    item["label"],
                    insert=(legend_text_x, legend_y + cell_size / 2 + 4),
                    fill=COLORS["title_color"],
                    font_size="14px",
                    font_family=text_font,
                    text_anchor="start",
                )
            )
        if item['color'] == 'nerd':
            dwg.add(
                dwg.rect(
                    insert=(legend_rect_x, legend_y),
                    size=(cell_size, cell_size),
                    fill=COLORS['title_color'],
                    rx=border_radius,
                    ry=border_radius,
                )
            )
        else:
            dwg.add(
                dwg.rect(
                    insert=(legend_rect_x, legend_y),
                    size=(cell_size, cell_size),
                    fill=item["color"],
                    rx=border_radius,
                    ry=border_radius,
                )
            )
        dwg.add(
                dwg.text(
                    item["label"],
                    insert=(legend_text_x, legend_y + cell_size / 2 + 4),
                    fill=COLORS["title_color"],
                    font_size="14px",
                    font_family=text_font,
                    text_anchor="start",
                )
            )

    dwg.defs.add(
        dwg.style("""
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        """)
    )

    dwg.save()

contributions = fetch_yearly_contributions(USERNAME, GITHUB_API_KEY)
svg_filename = "github_contributions_enhanced.svg"
generate_svg(contributions, filename=svg_filename)

print(f"Enhanced SVG with legend and animation generated: {svg_filename}")
print("Generated with Python \033[1;33m⟡\033[0m \033[1;32m𓆗\033[0m \033[1;33m⟡\033[0m by \033[1;34mPeme969\033[0m")
