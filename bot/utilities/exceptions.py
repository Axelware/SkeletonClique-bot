# Future
from __future__ import annotations

# Packages
import discord
from discord.ext import commands

# My stuff
from core import colours
from utilities import utils


class SkeletonCliqueError(commands.CommandError):
    pass


class EmbedError(SkeletonCliqueError):

    def __init__(
        self,
        footer_url: str | None = None,
        footer: str | None = None,
        image: str | None = None,
        thumbnail: str | None = None,
        author: str | None = None,
        author_url: str | None = None,
        author_icon_url: str | None = None,
        title: str | None = None,
        description: str | None = None,
        url: str | None = None,
        colour: discord.Colour = colours.MAIN,
        emoji: str | None = None
    ) -> None:

        self.embed = utils.embed(
            footer_url=footer_url,
            footer=footer,
            image=image,
            thumbnail=thumbnail,
            author=author,
            author_url=author_url,
            author_icon_url=author_icon_url,
            title=title,
            description=description,
            url=url,
            colour=colour,
            emoji=emoji
        )
