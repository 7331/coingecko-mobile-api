import re

from coingecko_mobile_api.infrastructure.coingecko_api.schemas import NewsArticle, NewsFeed

_SHORTEST_SYMBOL_MATCHED_IN_TITLES = 3


def articles_about_coin(
    articles: list[NewsArticle], *, coin_id: str, coin_name: str, coin_symbol: str, feed: NewsFeed
) -> list[NewsArticle]:
    urls_tagged_with_coin = {
        article.url for article in feed.data if any(coin.id == coin_id for coin in article.coins or [])
    }
    return [
        article
        for article in articles
        if article.url in urls_tagged_with_coin
        or _title_names_coin(article.title, coin_name=coin_name, coin_symbol=coin_symbol)
    ]


def _title_names_coin(title: str, *, coin_name: str, coin_symbol: str) -> bool:
    if re.search(rf"\b{re.escape(coin_name)}\b", title, flags=re.IGNORECASE):
        return True
    return (
        len(coin_symbol) >= _SHORTEST_SYMBOL_MATCHED_IN_TITLES
        and re.search(rf"\b{re.escape(coin_symbol.upper())}\b", title) is not None
    )
