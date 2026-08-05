def generate_post_text(title: str, summary: str) -> str:
    return (
        f"📰 {title}\n\n"
        f"{summary}\n\n"
        "👉 Follow the channel for more updates."
    )