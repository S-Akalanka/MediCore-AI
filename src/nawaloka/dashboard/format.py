def plain(text: str) -> str:
    """Escape dollar signs so Streamlit does not render them as math."""
    return text.replace("$", "\$")
