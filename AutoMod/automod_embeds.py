# This file contains all the embeds used in the automod
import discord
from database import database
class automod_embeds:
    @staticmethod
    def start_auto_mod_config():
        embed_start = discord.Embed(
            title="AutoMod Configuration",
            description="Configure AutoMod settings",
            color=discord.Color.blurple()
        )
        embed_start.add_field(
            name="How It Works",
            value="This allows you to configure AutoMod settings for your server.\n",
            inline=False
        )
        embed_start.add_field(
            name="How to use",
            value=(
                "In the next pages you will be asked to provide the following settings:\n"
                "1. anti-spam protection\n"
                "2. mention spam protection\n"
                "3. suspicious link detection\n"
                "4. suspicious account monitoring\n"
                "5. new account restrictions\n"
                "6. raid protection\n"
                "7. anti-nuke protection\n"
                "8. mass-ban/kick protection\n"
                "9. suspicious keyword detection\n"
            ),
            inline=False
        )
        embed_start.add_field(name="Select an option", value="Choose an option to get started, channel log is the channel that the bot will log any suspicious activity in.", inline=False)
        return embed_start
    
    @staticmethod
    def Anti_spam_embed(is_enabled: bool):
        embed_anti_spam = discord.Embed(
            title="Anti-Spam Protection",
            description="Configure Anti-Spam settings",
            color=discord.Color.green() if is_enabled else discord.Color.orange()
        )
        embed_anti_spam.add_field(
            name="How It Works",
            value="This allows you to configure Anti-Spam settings for your server.\n",
            inline=False
        )
        # todo add the needed tables for each, this is just design
        embed_anti_spam.add_field(
            name="How does it work?",
            value=(
                "This feature allows you to configure Anti-Spam settings for your server.\n"
                "You can enable/disable Anti-Spam settings, set a threshold for spam detection, exceptions and the action taken for spamming.\n"
            ),)
        embed_anti_spam.add_field(name="Select an option", value="Choose an option to get started", inline=False)
        return embed_anti_spam
    
    
    @staticmethod
    def Mention_spam_embed(is_enabled: bool):
        embed_mention_spam = discord.Embed(
            title="Mention Spam Protection",
            description="Configure Mention Spam settings",
            color=discord.Color.green() if is_enabled else discord.Color.orange()
        )
        embed_mention_spam.add_field(
            name="How It Works",
            value="This allows you to configure Mention Spam settings for your server.\n",
            inline=False
        )
        # todo add the needed tables for each, this is just design
        embed_mention_spam.add_field(
            name="How does it work?",
            value=(
                "This feature allows you to configure Mention Spam settings for your server.\n"
                "You can enable/disable Mention Spam settings, set a threshold for spam detection, exceptions and the action taken for spamming.\n"
            ),)
        embed_mention_spam.add_field(name="Select an option", value="Choose an option to get started", inline=False)
        return embed_mention_spam
    
    
    @staticmethod
    def Suspicious_link_embed(is_enabled: bool):
        embed_suspicious_link = discord.Embed(
            title="Suspicious Link Detection",
            description="Configure Suspicious Link settings",
            color=discord.Color.green() if is_enabled else discord.Color.orange()
        )
        embed_suspicious_link.add_field(
            name="How It Works",
            value="This allows you to configure Suspicious Link settings for your server.\n",
            inline=False
        )
        # todo add the needed tables for each, this is just design
        embed_suspicious_link.add_field(
            name="How does it work?",
            value=(
                "This feature allows you to configure Suspicious Link settings for your server.\n"
                "You can enable/disable Suspicious Link settings and the action taken for it.\n"
            ),
            )
        embed_suspicious_link.add_field(name="Select an option", value="Choose an option to get started", inline=False)
        return embed_suspicious_link
    
    @staticmethod
    def Suspicious_account_embed(is_enabled: bool):
        embed_suspicious_account = discord.Embed(
            title="Suspicious Account Monitoring",
            description="Configure Suspicious Account settings",
            color=discord.Color.green() if is_enabled else discord.Color.orange()
        )
        embed_suspicious_account.add_field(
            name="How It Works",
            value="This allows you to configure Suspicious Account settings for your server.\n",
            inline=False
        )
        # todo add the needed tables for each, this is just design
        embed_suspicious_account.add_field(
            name="How does it work?",
            value=(
                "This feature allows you to configure Suspicious Account settings for your server.\n"
                "You can enable/disable Suspicious Account settings, choose the action taken for suspicious accounts.\n"
            ),)
        embed_suspicious_account.add_field(name="Select an option", value="Choose an option to get started", inline=False)
        return embed_suspicious_account
    
    
    @staticmethod
    def New_account_restrictions_embed(is_enabled: bool):
        embed_new_account_restrictions = discord.Embed(
            title="New Account Restrictions",
            description="Configure New Account settings",
            color=discord.Color.green() if is_enabled else discord.Color.orange()
        )
        embed_new_account_restrictions.add_field(
            name="How It Works",
            value="This allows you to configure New Account settings for your server.\n",
            inline=False
        )
        # todo add the needed tables for each, this is just design
        embed_new_account_restrictions.add_field(
            name="How does it work?",
            value=(
                "This feature allows you to configure New Account settings for your server.\n"
                "You can enable/disable New Account settings, choose the action taken for new accounts.\n"
            ),)
        embed_new_account_restrictions.add_field(name="Select an option", value="Choose an option to get started", inline=False)
        return embed_new_account_restrictions
    
    
    @staticmethod
    def Raid_protection_embed(is_enabled: bool):
        embed_raid_protection = discord.Embed(
            title="Raid Protection",
            description="Configure Raid settings",
            color=discord.Color.green() if is_enabled else discord.Color.orange()
        )
        embed_raid_protection.add_field(
            name="How It Works",
            value="This allows you to configure Raid settings for your server.\n",
            inline=False
        )
        
        # todo add the needed tables for each, this is just design , invite exceptions
        embed_raid_protection.add_field(
            name="what is raids?",
            value=("raids are when a server is flooded with bots or users to cause chaos and spam\n",
                   "This feature protects your server from that by setting a threshold for raid detection, invites exceptions and the action taken for raiding.\n")
        )
        embed_raid_protection.add_field(name="Select an option", value="Choose an option to get started", inline=False)
        return embed_raid_protection
    
    
    @staticmethod
    def Anti_nuke_protection_embed(is_enabled: bool):
        embed_anti_nuke_protection = discord.Embed(
            title="Anti-Nuke Protection",
            description="Configure Anti-Nuke settings",
            color=discord.Color.green() if is_enabled else discord.Color.orange()
        )
        embed_anti_nuke_protection.add_field(
            name="How It Works",
            value="This allows you to configure Anti-Nuke settings for your server.\n",
            inline=False
        )
        # todo add the needed tables for each
        embed_anti_nuke_protection.add_field(
            name="what is server nuking?",
            value=("server nuking is when a server is deleted or spammed with channels and roles\n",
                   "This feature protects your server from that by setting a threshold for nuke detection and prevent it with the ability to lock the server.\n"))
        
        embed_anti_nuke_protection.add_field(name="Select an option", value="Choose an option to get started", inline=False)
        return embed_anti_nuke_protection
    
    @staticmethod
    def Mass_ban_kick_protection_embed(is_enabled: bool):
        embed_mass_ban_kick_protection = discord.Embed(
            title="Mass Ban/Kick Protection",
            description="Configure Mass Ban/Kick settings",
            color=discord.Color.green() if is_enabled else discord.Color.orange()
        )
        embed_mass_ban_kick_protection.add_field(
            name="How It Works",
            value="This allows you to configure Mass Ban/Kick settings for your server.\n",
            inline=False
        )
        # todo add the needed tables for each
        embed_mass_ban_kick_protection.add_field(
            name="what is mass ban/kick?",
            value=("mass ban/kick is when a bot or a user tries to kick alot of users in the same time\n",
                   "This feature protects your server from that by setting a threshold for mass ban/kick detection for mods and bots, invites exceptions and the action taken for mass ban/kick.\n"))
        
        embed_mass_ban_kick_protection.add_field(name="Select an option", value="Choose an option to get started", inline=False)        
        return embed_mass_ban_kick_protection
    
    @staticmethod
    def Suspicious_keyword_detection_embed(is_enabled: bool):
        embed_suspicious_keyword_detection = discord.Embed(
            title="Suspicious Keyword Detection",
            description="Configure Suspicious Keyword settings",
            color=discord.Color.green() if is_enabled else discord.Color.orange()
        )
        embed_suspicious_keyword_detection.add_field(
            name="How It Works",
            value="This allows you to configure Suspicious Keyword settings for your server.\n",
            inline=False
        )
        # todo add the needed tables for each
        embed_suspicious_keyword_detection.add_field(
            name="what is suspicious keyword detection?",
            value=("this feature detects suspicious keywords (mainly scams or fake links) in messages and tries to block them or flag them to moderators of the server!\n",
                   "Note: this feature is not 100% preventive, it's just a tool to help moderators to detect suspicious messages.\n"))
        
        embed_suspicious_keyword_detection.add_field(name="Select an option", value="Choose an option to get started", inline=False)
        return embed_suspicious_keyword_detection
    
        
automod_embed = automod_embeds()