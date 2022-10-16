from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime
from httpx import get
from bs4 import BeautifulSoup, Tag

TEAM_ID = 202484

JSON_API = f"https://ctftime.org/api/v1/teams/{TEAM_ID}/"
TEAM_PAGE = f"https://ctftime.org/team/{TEAM_ID}"
USER_PAGE = "https://ctftime.org/user/{}"
MEDIA_BASE = "https://ctftime.org{}"
START_YEAR = 2022
EVENT_API = "https://ctftime.org/api/v1/events/{}/"
EVENT_SITE = "https://ctftime.org/event/{}"


def get_logo_url() -> str:
    api = get(JSON_API).json()
    return api["logo"]


Member = int


def get_soup(url: str) -> BeautifulSoup:
    content = get(url)
    return BeautifulSoup(content.content, features="html.parser")


def get_members() -> list[Member]:
    soup = get_soup(TEAM_PAGE)
    div: Tag = soup.find("div", {"id": "recent_members"}).table  # type: ignore
    trs = div.find_all("tr")
    return [int(tr.td.a["href"].split("/")[2]) for tr in trs]


@dataclass(frozen=True, slots=True, kw_only=True)
class Event:
    name: str
    id: int
    rank: int
    date: date
    logo: str


@dataclass(slots=True, kw_only=True)
class UserInfo:
    username: str
    image: str | None
    websites: list[str]
    id: int


def extract_image_url(tag: Tag) -> str:
    text = tag.text
    text = text[text.index("https://") :]
    return text


def get_user(id: int) -> UserInfo:
    soup = get_soup(USER_PAGE.format(id))
    div = soup.find("div", {"class": "span10"})
    username: str = soup.find("div", {"class": "page-header"}).h2.text  # type: ignore
    image_div: Tag = soup.find("div", {"class": "span2"})  # type: ignore
    image: str = MEDIA_BASE.format(image_div.img["src"]) if image_div.img is not None else None  # type: ignore
    ps: list[Tag] = div.find_all("p")[2:]  # type: ignore
    websites: list[str] = [extract_image_url(p) for p in ps]  # type: ignore
    print(username, websites)
    return UserInfo(username=username, image=image, websites=websites, id=id)


def get_history() -> dict[int, list[Event]]:
    soup = get_soup(TEAM_PAGE)
    current_year = date.today().year
    result: dict[int, list[Event]] = {}
    for year in range(START_YEAR, current_year + 1):
        result[year] = []
        trs: list[Tag] = soup.find("div", {"id": f"rating_{year}"}).find_all("tr")[1:]  # type: ignore
        for tr in trs:
            place = int(tr.find("td", {"class": "place"}).text)  # type: ignore
            a = tr.find_all("td")[2].a  # type: ignore
            name: str = a.text  # type: ignore
            id = int(a["href"].split("/")[2])  # type: ignore
            d = get_event_date(id)
            result[year].append(
                Event(name=name, id=id, rank=place, date=d, logo=get_event_logo(id))
            )
    return result


def get_event_date(id: int) -> date:
    api = get(EVENT_API.format(id)).json()
    return datetime.fromisoformat(api["start"]).date()


def get_event_logo(id: int) -> str:
    api = get(EVENT_API.format(id)).json()
    return api["logo"]


@dataclass(frozen=True, slots=True, kw_only=True)
class TeamInfo:
    logo: str
    members: list[UserInfo]
    history: dict[int, list[Event]]


def get_team() -> TeamInfo:
    return TeamInfo(
        logo=get_logo_url(),
        members=[get_user(id) for id in get_members()],
        history=get_history(),
    )


if __name__ == "__main__":
    # print(get_user(145700))
    # print(get_event_date(1525))
    print(get_history())
    # print(get_team())
