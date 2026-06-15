from dataclasses import dataclass, field


@dataclass
class Bookmark:
    title: str
    url: str
    add_date: str = ""
    last_visit: str = ""
    last_modified: str = ""


@dataclass
class Folder:
    title: str
    children: list = field(default_factory=list)  # List of Bookmark or Folder
    add_date: str = ""
    folded: bool = True
