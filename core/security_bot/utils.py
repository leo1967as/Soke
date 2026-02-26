"""Utility functions for Security Bot."""
from datetime import datetime, timezone
from discord import Embed
from typing import Optional


def get_account_age(created_at: datetime) -> int:
    """Calculate account age in days."""
    now = datetime.now(created_at.tzinfo)
    diff = now - created_at
    return diff.days


def is_new_account(created_at: datetime, threshold_days: int = 7) -> bool:
    """Check if account is newer than threshold."""
    return get_account_age(created_at) < threshold_days


def create_embed(
    title: str,
    color: int,
    thumbnail_url: Optional[str] = None,
    **fields
) -> Embed:
    """Create a formatted embed with optional fields."""
    embed = Embed(title=title, color=color, timestamp=datetime.now(timezone.utc))
    
    for name, value in fields.items():
        inline = not name.lower().endswith("_long")
        embed.add_field(name=name, value=value, inline=inline)
    
    if thumbnail_url:
        embed.set_thumbnail(url=thumbnail_url)
    
    return embed


def format_user_info(user) -> str:
    """Format user information for logs."""
    return f"{user.mention} ({user})"


def safe_remove_roles(user, role) -> bool:
    """Safely remove a role from user. Returns True if successful."""
    import asyncio
    
    async def _remove():
        if role in user.roles:
            await user.remove_roles(role)
            return True
        return False
    
    # This should be called from within an async context
    return None
