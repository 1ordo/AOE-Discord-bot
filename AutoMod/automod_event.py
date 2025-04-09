import discord
from discord.ext import commands
import datetime
from typing import Optional
import json
import logging
from client import client
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

AUTOMOD_CONFIG = {
    "log_channel_id": None,  # Set your log channel ID
    "timeout_duration": {
        "spam": 5,          # minutes
        "mention_spam": 10,  # minutes
        "keyword": 3        # minutes
    },
    "warning_messages": {
        "spam": "Please slow down! You're sending messages too quickly.",
        "mention_spam": "Stop mentioning too many users at once!",
        "keyword": "Your message contained inappropriate content."
    }
}

async def log_automod_action(
    guild: discord.Guild,
    channel: discord.TextChannel,
    user: discord.Member,
    action_type: str,
    content: Optional[str] = None,
    duration: Optional[int] = None
) -> None:
    """Helper function to log AutoMod actions"""
    if not AUTOMOD_CONFIG["log_channel_id"]:
        return

    log_channel = guild.get_channel(AUTOMOD_CONFIG["log_channel_id"])
    if not log_channel:
        return

    embed = discord.Embed(
        title="🛡️ AutoMod Action",
        color=discord.Color.red(),
        timestamp=datetime.datetime.utcnow()
    )
    embed.add_field(name="User", value=f"{user.mention} ({user.id})", inline=True)
    embed.add_field(name="Channel", value=channel.mention, inline=True)
    embed.add_field(name="Action Type", value=action_type, inline=True)
    
    if content:
        embed.add_field(name="Filtered Content", value=content, inline=False)
    if duration:
        embed.add_field(name="Timeout Duration", value=f"{duration} minutes", inline=False)

    await log_channel.send(embed=embed)

async def handle_timeout(
    member: discord.Member,
    duration: int,
    reason: str
) -> None:
    """Helper function to timeout users"""
    try:
        await member.timeout(
            datetime.timedelta(minutes=duration),
            reason=reason
        )
    except discord.Forbidden:
        logger.error(f"Failed to timeout {member.name}: Missing permissions")
    except Exception as e:
        logger.error(f"Error timing out {member.name}: {str(e)}")


@client.event
async def on_auto_moderation_action(action: discord.AutoModAction):
    """Main AutoMod event handler"""
    # Extract info from action
    guild = action.guild
    channel = action.channel
    user = action.member
    content = action.matched_content
    rule = action.rule_id

    match action.rule_trigger_type:
        case discord.AutoModRuleTriggerType.spam:
            # Handle spam
            await handle_timeout(
                user,
                AUTOMOD_CONFIG["timeout_duration"]["spam"],
                "AutoMod: Spam Detection"
            )
            await channel.send(
                f"{user.mention} {AUTOMOD_CONFIG['warning_messages']['spam']}",
                delete_after=10
            )
            await log_automod_action(
                guild, channel, user, "Spam Detection",
                duration=AUTOMOD_CONFIG["timeout_duration"]["spam"]
            )

        case discord.AutoModRuleTriggerType.mention_spam:
            # Handle mention spam
            await handle_timeout(
                user,
                AUTOMOD_CONFIG["timeout_duration"]["mention_spam"],
                "AutoMod: Mention Spam"
            )
            await channel.send(
                f"{user.mention} {AUTOMOD_CONFIG['warning_messages']['mention_spam']}",
                delete_after=10
            )
            await log_automod_action(
                guild, channel, user, "Mention Spam",
                content=content,
                duration=AUTOMOD_CONFIG["timeout_duration"]["mention_spam"]
            )

        case discord.AutoModRuleTriggerType.keyword:
            # Handle keyword filter
            await handle_timeout(
                user,
                AUTOMOD_CONFIG["timeout_duration"]["keyword"],
                "AutoMod: Blocked Keywords"
            )
            await channel.send(
                f"{user.mention} {AUTOMOD_CONFIG['warning_messages']['keyword']}",
                delete_after=10
            )
            await log_automod_action(
                guild, channel, user, "Keyword Filter",
                content=content,
                duration=AUTOMOD_CONFIG["timeout_duration"]["keyword"]
            )

@client.event
async def on_auto_moderation_rule_create(rule: discord.AutoModRule):
    logger.info(f"AutoMod rule created: {rule.name}")

@client.event
async def on_auto_moderation_rule_update(rule: discord.AutoModRule):
    logger.info(f"AutoMod rule updated: {rule.name}")

@client.event
async def on_auto_moderation_rule_delete(rule: discord.AutoModRule):
    logger.info(f"AutoMod rule deleted: {rule.name}")
    