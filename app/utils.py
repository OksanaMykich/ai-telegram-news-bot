def is_news_relevant(news_item: dict, keywords: list[str]) -> bool:
    if not keywords:
        return True

    text = " ".join(
        [
            news_item.get("title") or "",
            news_item.get("summary") or "",
            news_item.get("raw_text") or "",
        ]
    ).lower()

    for keyword in keywords:
        if keyword.lower() in text:
            return True

    return False