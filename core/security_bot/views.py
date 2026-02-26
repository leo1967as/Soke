"""Discord UI Views for Security Bot."""
import discord
from discord.ui import View, button
from discord import Embed
from datetime import datetime, timezone
from typing import Optional
import logging
import asyncio

from .constants import CustomID, ErrorMessages, EmbedColor, LogMessages
from .member_tracker import MemberTracker

logger = logging.getLogger(__name__)


class VerifyView(View):
    """Persistent verification view with a single verify button."""
    
    def __init__(self, member_role_id: int, unverified_role_id: int, log_channel_id: Optional[int] = None):
        super().__init__(timeout=None)
        self.member_role_id = member_role_id
        self.unverified_role_id = unverified_role_id
        self.log_channel_id = log_channel_id
        self.tracker = MemberTracker()
    
    @button(
        label="✅ ยืนยันตัวตน (Verify)",
        style=discord.ButtonStyle.green,
        custom_id=CustomID.VERIFY_BUTTON
    )
    async def verify(self, interaction: discord.Interaction, button: discord.Button):
        """Handle verification button click."""
        guild = interaction.guild
        member_role = guild.get_role(self.member_role_id)
        unverified_role = guild.get_role(self.unverified_role_id)
        
        if not member_role:
            await interaction.response.send_message(
                ErrorMessages.ROLE_NOT_FOUND,
                ephemeral=True
            )
            logger.error(f"Member role {self.member_role_id} not found")
            return
        
        if member_role in interaction.user.roles:
            await interaction.response.send_message(
                ErrorMessages.ALREADY_VERIFIED,
                ephemeral=True
            )
            return
        
        try:
            # Add Member role
            await interaction.user.add_roles(member_role)
            logger.info(LogMessages.ROLE_ASSIGNED.format(
                role_name="Member",
                user_name=interaction.user.name,
                user_id=interaction.user.id
            ))
            
            # Remove Unverified role if present
            if unverified_role and unverified_role in interaction.user.roles:
                await interaction.user.remove_roles(unverified_role)
                logger.info(f"Removed Unverified role from {interaction.user.name}")
            
            # Wait a moment for Discord to update roles
            await asyncio.sleep(0.5)
            
            # Verify role was actually assigned by fetching fresh member data
            await interaction.user._update(interaction.user._state, await interaction.user._state.http.get_member(guild.id, interaction.user.id))
            
            # Check if role assignment was successful
            if member_role in interaction.user.roles:
                # Track verified member
                self.tracker.add_member(
                    user_id=interaction.user.id,
                    username=str(interaction.user)
                )
                
                await interaction.response.send_message(
                    ErrorMessages.VERIFICATION_SUCCESS,
                    ephemeral=True
                )
                
                # Log to channel
                if self.log_channel_id:
                    log_channel = guild.get_channel(self.log_channel_id)
                    if log_channel:
                        embed = Embed(
                            title="✅ Member Verified",
                            color=EmbedColor.VERIFIED,
                            timestamp=datetime.now(timezone.utc)
                        )
                        embed.add_field(name="User", value=f"{interaction.user.mention} ({interaction.user})")
                        embed.add_field(name="ID", value=str(interaction.user.id))
                        embed.add_field(name="Status", value="✅ Role confirmed & tracked")
                        await log_channel.send(embed=embed)
            else:
                # Role assignment failed somehow
                await interaction.response.send_message(
                    "⚠️ การยืนยันตัวตนอาจไม่สำเร็จ กรุณาลองใหม่อีกครั้งหรือติดต่อ Admin",
                    ephemeral=True
                )
                logger.error(f"Role verification failed for {interaction.user.name} - role not found after assignment")
                    
        except discord.Forbidden:
            await interaction.response.send_message(
                ErrorMessages.VERIFICATION_FAILED,
                ephemeral=True
            )
            logger.error(f"Permission denied when assigning role to {interaction.user.name}")
        except Exception as e:
            await interaction.response.send_message(
                ErrorMessages.COMMAND_ERROR.format(error=str(e)),
                ephemeral=True
            )
            logger.exception(f"Error during verification for {interaction.user.name}: {e}")


class ConfirmView(View):
    """Confirmation view for admin actions."""
    
    def __init__(self, confirm_callback, cancel_message: str = "ยกเลิกแล้ว"):
        super().__init__(timeout=30)
        self.confirm_callback = confirm_callback
        self.cancel_message = cancel_message
        self.result = None
    
    @button(label="✅ ยืนยัน", style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.Button):
        self.result = True
        self.stop()
        await self.confirm_callback(interaction)
    
    @button(label="❌ ยกเลิก", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.Button):
        self.result = False
        self.stop()
        await interaction.response.edit_message(content=self.cancel_message, view=None)
