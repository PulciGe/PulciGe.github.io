from __future__ import annotations
from dataclasses import dataclass
from datetime import date, datetime
from typing import TypeVar
from httpx import get
from bs4 import BeautifulSoup, Tag

TEAM_ID = 202484

BASE_URL = "https://ctftime.org"
JSON_API = f"{BASE_URL}/api/v1/teams/{TEAM_ID}/"
TEAM_PAGE = f"{BASE_URL}/team/{TEAM_ID}"
USER_PAGE = "https://ctftime.org/user/{}"
MEDIA_BASE = "https://ctftime.org{}"
START_YEAR = 2022
EVENT_API = "https://ctftime.org/api/v1/events/{}/"
EVENT_SITE = "https://ctftime.org/event/{}"


def get_logo_url() -> str:
    api = get(JSON_API).json()
    assert isinstance(api, dict)
    result = api["logo"]
    assert isinstance(result, str)
    return result


Member = int


def get_soup(url: str) -> BeautifulSoup:
    content = get(url)
    return BeautifulSoup(content.content, features="html.parser")


T = TypeVar("T")


def get_members() -> list[Member]:
    soup = get_soup(TEAM_PAGE)
    div: Tag = soup("div", {"id": "recent_members"})[0]("table")[0]
    trs = div("tr")
    return [int(tr("td")[0]("a")[0]["href"].split("/")[2]) for tr in trs]


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
    div = soup("div", {"class": "span10"})[0]
    username: str = soup("div", {"class": "page-header"})[0]("h2")[0].text
    image_div: Tag = soup("div", {"class": "span2"})[0]
    image: str | None = (
        MEDIA_BASE.format(image_div("img")[0]["src"]) if image_div("img") else None
    )
    ps: list[Tag] = div("p")[2:]
    websites: list[str] = [extract_image_url(p) for p in ps]
    print(username, websites)
    return UserInfo(username=username, image=image, websites=websites, id=id)


def get_history() -> dict[int, list[Event]]:
    soup = get_soup(TEAM_PAGE)
    current_year = date.today().year
    result: dict[int, list[Event]] = {}
    for year in range(START_YEAR, current_year + 1):
        result[year] = []
        trs: list[Tag] = soup("div", {"id": f"rating_{year}"})[0]("tr")[1:]
        for tr in trs:
            place = int(tr("td", {"class": "place"})[0].text)
            a = tr("td")[2]("a")[0]
            name: str = a.text
            id = int(a["href"].split("/")[2])
            d = get_event_date(id)
            result[year].append(
                Event(name=name, id=id, rank=place, date=d, logo=get_event_logo(id))
            )
    return result


def get_event_date(id: int) -> date:
    api = get(EVENT_API.format(id)).json()
    assert isinstance(api, dict)
    assert isinstance(api["start"], str)
    return datetime.fromisoformat(api["start"]).date()


def get_event_logo(id: int) -> str:
    soup = get_soup(EVENT_SITE.format(id))
    img = soup("img")[3]
    assert img is not None
    return BASE_URL + img["src"]


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
