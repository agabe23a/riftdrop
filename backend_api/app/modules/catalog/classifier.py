from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.models import Category


async def suggest_categories(db: AsyncSession, product_name: str, limit: int = 3) -> list[dict]:
    """Explainable local keyword matching; admins retain the final category decision."""
    terms = {term.lower() for term in product_name.split() if len(term) > 2}
    categories = (await db.execute(select(Category))).scalars().all()
    scored = []
    for category in categories:
        category_terms = set(category.name.lower().replace("&", " ").split())
        score = len(terms & category_terms)
        if score:
            scored.append((score, category))
    return [{"category_id": item.id, "name": item.name, "confidence": round(score / max(len(terms), 1), 2)} for score, item in sorted(scored, key=lambda row: (-row[0], row[1].name))[:limit]]
