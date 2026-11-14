from coingecko_mobile_api.infrastructure.coingecko_api.schemas import NewsArticle, NewsFeed


def articles_about_coin(articles: list[NewsArticle], *, coin_id: str, feed: NewsFeed) -> list[NewsArticle]:
    feed_coin_ids_by_url = {article.url: {coin.id for coin in article.coins or []} for article in feed.data}
    return [
        article
        for article in articles
        if article.url not in feed_coin_ids_by_url or coin_id in feed_coin_ids_by_url[article.url]
    ]
