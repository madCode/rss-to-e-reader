from typing import TypedDict, List, Optional, Any

class TtrssHeadline(TypedDict):
    id: int
    guid: str
    unread: bool
    marked: bool
    published: bool
    updated: int
    is_updated: bool
    title: str
    link: str
    feed_id: str
    tags: List[str]
    content: str
    labels: List[str]
    feed_title: str
    comments_count: int
    comments_link: str
    always_display_attachments: bool
    author: str
    score: int
    note: Optional[str]
    lang: str
    flavor_image: str
    flavor_stream: str

class TtrssResponse(TypedDict):
    seq: int
    status: int
    content: Any
