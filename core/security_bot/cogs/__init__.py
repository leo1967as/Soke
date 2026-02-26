"""Cogs package for Security Bot."""
from .verification import VerificationCog, setup_verification_cog
from .security import SecurityLoggingCog, setup_security_cog
from .member_sync import MemberSyncCog, setup_member_sync_cog

__all__ = [
    "VerificationCog", "setup_verification_cog",
    "SecurityLoggingCog", "setup_security_cog",
    "MemberSyncCog", "setup_member_sync_cog"
]
