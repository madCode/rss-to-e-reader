from ArticleMetadata import ArticleMetadata
from TtrssCollector_mocks import MOCK_HEADLINE

MOCK_ARTICLE_METADATA_DO_NOT_FETCH: ArticleMetadata = ArticleMetadata(
    MOCK_HEADLINE['title'], MOCK_HEADLINE['link'],
    MOCK_HEADLINE['feed_id'], MOCK_HEADLINE['content'],
    MOCK_HEADLINE['feed_title'], str(MOCK_HEADLINE['id']),
    fetch_content_from_url=False)

MOCK_ARTICLE_METADATA_FETCH: ArticleMetadata = ArticleMetadata(
    MOCK_HEADLINE['title'], MOCK_HEADLINE['link'],
    MOCK_HEADLINE['feed_id'], MOCK_HEADLINE['content'],
    MOCK_HEADLINE['feed_title'], str(MOCK_HEADLINE['id']),
    fetch_content_from_url=True)