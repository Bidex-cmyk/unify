from pathlib import Path

from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory=str(Path(__file__).parent.parent / "templates"))


def money(amount_minor: int) -> str:
    """Render integer minor units as a two-decimal string (1299 -> "12.99")."""
    units, cents = divmod(amount_minor, 100)
    return f"{units}.{cents:02d}"


templates.env.filters["money"] = money
