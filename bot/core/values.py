# Future
from __future__ import annotations

# Packages
import discord

# My stuff
from core import config


ZWSP = "\u200b"
NL = "\n"

PERMISSIONS = discord.Permissions(
    read_messages=True,
    send_messages=True,
    embed_links=True,
    attach_files=True,
    read_message_history=True,
    add_reactions=True,
    external_emojis=True,
)

INVITE_LINK = discord.utils.oauth_url(client_id=config.BOT_ID, permissions=PERMISSIONS, scopes=["bot"])
INVITE_LINK_NO_PERMISSIONS = discord.utils.oauth_url(client_id=config.BOT_ID)

SUPPORT_LINK = "https://discord.gg/w9f6NkQbde"
GITHUB_LINK = "https://github.com/SkeletonCliqueDiscord/SkeletonClique-bot"
