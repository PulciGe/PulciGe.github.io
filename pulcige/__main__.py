from os import makedirs, remove, stat, listdir
from os.path import join, isdir
from shutil import rmtree
from time import sleep
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pulcige.ctftime import USER_PAGE, TeamInfo, get_team, TEAM_PAGE
from argparse import ArgumentParser
from urllib.parse import urlparse

env = Environment(loader=FileSystemLoader("src"), autoescape=select_autoescape())


PAGES = ["index.html", "members.html", "history.html"]
WATCH = PAGES + ["base.html", "divider.html"]

LOGOS = {
    "github.com": "fa-github",
    "linkedin.com": "fa-linkedin",
    "ctftime.org": "fa-flag",
}

DEFAULT_LOGO = "fa-link"

OUT_DIR = ".out"
SRC_DIR = "src"


def render(team: TeamInfo):
    for page in PAGES:
        with open(join(OUT_DIR, page), "w") as f:
            template = env.get_template(page)
            f.write(
                template.render(
                    team=team,
                    ctf_time=TEAM_PAGE,
                    favicon=team.logo,
                    logos=LOGOS,
                    page=page,
                )
            )


def get_logo(url: str) -> str:
    return LOGOS.get(urlparse(url).netloc.replace("www.", ""), DEFAULT_LOGO)


env.filters["get_logo"] = get_logo  # type: ignore


def setup() -> TeamInfo:
    makedirs(OUT_DIR, exist_ok=True)
    for file in [join(OUT_DIR, f) for f in listdir(OUT_DIR)]:
        if isdir(file):
            rmtree(file)
        else:
            remove(file)
    team = get_team()
    for member in team.members:
        if member.image is None:
            member.image = team.logo
        member.websites.insert(0, USER_PAGE.format(member.id))
    return team


def dev():
    team = setup()
    mtimes = {page: 0.0 for page in WATCH}
    print("Starting debug mode")
    while True:
        should_render = False
        for page in WATCH:
            mtime = stat(join(SRC_DIR, page)).st_mtime
            if mtime > mtimes[page]:
                should_render = True
                print("Update", page)
                mtimes[page] = mtime
        if should_render:
            render(team)
        sleep(1)


def build():
    team = setup()
    render(team)


def main():
    parser = ArgumentParser()
    parser.add_argument("command", choices=["dev", "build"])
    args = parser.parse_args()
    command: str = args.command
    if command == "dev":
        dev()
    else:
        build()


if __name__ == "__main__":
    main()
