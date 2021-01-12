import discord
from discord.ext import commands

import config
from bot import SemiBotomatic
from utilities import context, converters, exceptions, utils


class Tags(commands.Cog):

    def __init__(self, bot: SemiBotomatic) -> None:
        self.bot = bot

    @commands.group(name='tag', aliases=['tags'], invoke_without_command=True)
    async def tag(self, ctx: context.Context, *, name: converters.TagNameConverter) -> None:
        """
        Get a tag by it's name or alias.

        `name`: The name or alias of the tag you want to find.
        """

        tags = self.bot.tag_manager.get_tags_matching(name=str(name))
        if not tags:
            raise exceptions.ArgumentError(f'There are no tags that match the name `{name}`')

        if tags[0].name != name:
            extra_msg = f'Maybe you meant one of these?\n{f"{config.NL}".join(f"`{index + 1}.` {tag.name}" for index, tag in enumerate(tags[0:]))}' if len(tags) > 1 else ''
            raise exceptions.ArgumentError(f'There are no tags with the name `{name}`. {extra_msg}')

        if tags[0].alias is not None:
            tags = self.bot.tag_manager.get_tags_matching(name=tags[0].alias)

        await ctx.send(tags[0].content)

    @tag.command(name='raw')
    async def tag_raw(self, ctx: context.Context, *, name: converters.TagNameConverter) -> None:
        """
        Get a tag's raw content.

        `name`: The name or alias of the tag you want to find.
        """

        tags = self.bot.tag_manager.get_tags_matching(name=str(name))
        if not tags:
            raise exceptions.ArgumentError(f'There are no tags that match the name `{name}`')

        if tags[0].name != name:
            extra_msg = f'Maybe you meant one of these?\n{f"{config.NL}".join(f"`{index + 1}.` {tag.name}" for index, tag in enumerate(tags[0:]))}' if len(tags) > 1 else ''
            raise exceptions.ArgumentError(f'There are no tags with the name `{name}`. {extra_msg}')

        if tags[0].alias is not None:
            tags = self.bot.tag_manager.get_tags_matching(name=tags[0].alias)

        await ctx.send(discord.utils.escape_markdown(tags[0].content))

    @tag.command(name='create', aliases=['make', 'add'])
    async def tag_create(self, ctx: context.Context, name: converters.TagNameConverter, *, content: converters.TagContentConverter) -> None:
        """
        Create a tag.

        `name`: The name of the tag.
        `content`: The content of the tag.
        """

        tag = self.bot.tag_manager.get_tag(name=str(name))
        if tag:
            raise exceptions.ArgumentError(f'There is already a tag with the name `{name}`.')

        await self.bot.tag_manager.create_tag(author=ctx.author, name=str(name), content=str(content))
        await ctx.send(f'Created tag with name `{name}`')

    @tag.command(name='alias')
    async def tag_alias(self, ctx: context.Context, alias: converters.TagNameConverter, original: converters.TagNameConverter) -> None:
        """
        Alias a name to a tag.

        `alias`: The alias to create.
        `name`: The name of the tag to point the alias at.
        """

        alias_tag = self.bot.tag_manager.get_tag(name=str(alias))
        if alias_tag:
            raise exceptions.ArgumentError(f'There is already a tag alias in this server with the name `{alias}`.')

        original_tag = self.bot.tag_manager.get_tag(name=str(original))
        if not original_tag:
            raise exceptions.ArgumentError(f'There are no tags in this server with the name `{original}`.')

        await self.bot.tag_manager.create_tag_alias(author=ctx.author, alias=str(alias), original=str(original))
        await ctx.send(f'Tag alias from `{alias}` to `{original}` was created.')

    @tag.command(name='claim')
    async def tag_claim(self, ctx: context.Context, *, name: converters.TagNameConverter) -> None:
        """
        Claim a tag if it's owner has left the server.

        `name`: The name of the tag to claim.
        """

        tag = self.bot.tag_manager.get_tag(name=str(name))
        if not tag:
            raise exceptions.ArgumentError(f'There are no tags with the name `{name}`.')

        owner = ctx.guild.get_member(tag.owner_id)
        if owner is not None:
            raise exceptions.ArgumentError(f'The owner of that tag is still in the server.')

        await self.bot.tag_manager.edit_tag_owner(name=str(name), new_owner=ctx.author)
        await ctx.send(f'You claimed the tag with name `{name}`.')

    @tag.command(name='transfer')
    async def tag_transfer(self, ctx: context.Context, name: converters.TagNameConverter, *, member: discord.Member) -> None:
        """
        Transfer a tag to another member.

        `name`: The name of the tag to transfer.
        `member`: The member to transfer the tag too. Can be their ID, Username, Nickname or @Mention.
        """

        if member.bot:
            raise exceptions.ArgumentError('You can not transfer tags to bots.')

        tag = self.bot.tag_manager.get_tag(name=str(name))
        if not tag:
            raise exceptions.ArgumentError(f'There are no tags with the name `{name}`.')

        if tag.owner_id != ctx.author.id:
            raise exceptions.ArgumentError(f'You do not own the tag with name `{name}`.')

        await self.bot.tag_manager.edit_tag_owner(name=str(name), new_owner=member)
        await ctx.send(f'Transferred tag from `{ctx.author}` to `{(await self.bot.fetch_user(tag.owner_id))}`.')

    @tag.command(name='edit')
    async def tag_edit(self, ctx: context.Context, name: converters.TagNameConverter, *, content: converters.TagContentConverter) -> None:
        """
        Edit a tag's content.

        `name`: The name of the tag to edit the content of.
        `content:` The content to edit the tag with.
        """

        tag = self.bot.tag_manager.get_tag(name=str(name))
        if not tag:
            raise exceptions.ArgumentError(f'There are no tags with the name `{name}`.')

        if tag.owner_id != ctx.author.id:
            raise exceptions.ArgumentError(f'You do not own the tag with the name `{name}`.')

        await self.bot.tag_manager.edit_tag_content(name=str(name), new_content=str(content))
        await ctx.send(f'Edited content of tag with name `{name}`.')

    @tag.command(name='delete', aliases=['remove'])
    async def tag_delete(self, ctx: context.Context, *, name: converters.TagNameConverter) -> None:
        """
        Delete a tag.

        `name`: The name of the tag to delete.
        """

        tag = self.bot.tag_manager.get_tag(name=str(name))
        if not tag:
            raise exceptions.ArgumentError(f'There are no tags with the name `{name}`.')
        if tag.owner_id != ctx.author.id and ctx.author.id not in config.OWNER_IDS:
            raise exceptions.ArgumentError(f'You do not own the tag with name `{name}`.')

        await self.bot.tag_manager.delete_tag(name=str(name))
        await ctx.send(f'Delete tag with name `{name}`.')

    @tag.command(name='search')
    async def tag_search(self, ctx: context.Context, *, name: converters.TagNameConverter) -> None:
        """
        Display a list of tags that are similar to the search.

        `name`: The search terms to look for tags with.
        """

        tags = self.bot.tag_manager.get_tags_matching(name=str(name), limit=100)
        if not tags:
            raise exceptions.ArgumentError(f'There are no tags similar to the search `{name}`.')

        entries = [f'`{index + 1}.` {tag.name}' for index, tag in enumerate(tags)]
        await ctx.paginate_embed(entries=entries, per_page=25, header=f'**Tags matching:** `{name}`\n\n')

    @tag.command(name='list')
    async def tag_list(self, ctx: context.Context, *, member: discord.Member = None) -> None:
        """
        Get a list of yours or someones else's tags.

        `member`: The member to get a tag list for. Can be their ID, Username, Nickname or @Mention.
        """

        if not member:
            member = ctx.author

        tags = self.bot.tag_manager.get_tags_owned_by(member=member)
        if not tags:
            raise exceptions.ArgumentError(f'`{member}` does not have any tags.')

        entries = [f'`{index + 1}.` {tag.name}' for index, tag in enumerate(tags)]
        await ctx.paginate_embed(entries=entries, per_page=25, header=f'**{member}\'s tags:**\n\n')

    @tag.command(name='all')
    async def tag_all(self, ctx: context.Context) -> None:
        """
        Get a list of all tags in this server.
        """

        tags = self.bot.tag_manager.get_tags()
        if not tags:
            raise exceptions.ArgumentError('There are no tags.')

        entries = [f'`{index + 1}.` {tag.name}' for index, tag in enumerate(tags)]
        await ctx.paginate_embed(entries=entries, per_page=25, header=f'**Semi Botomatic\'s Tags:**\n\n')

    @tag.command(name='info')
    async def tag_info(self, ctx: context.Context, *, name: converters.TagNameConverter) -> None:
        """
        Displays information about a tag.

        `name`: The name of the tag to get the information for.
        """

        tag = self.bot.tag_manager.get_tag(name=str(name))
        if not tag:
            raise exceptions.ArgumentError(f'There are no tags with the name `{name}`.')

        owner = ctx.guild.get_member(tag.owner_id)

        embed = discord.Embed(colour=ctx.colour, description=f'**{tag.name}**')
        embed.description = f'`Owner:` {owner.mention if owner else "None"} ({tag.owner_id})\n`Claimable:` {owner is None}\n`Alias:` {tag.alias}'
        embed.set_footer(text=f'Created on {utils.format_datetime(datetime=tag.created_at)}')
        await ctx.send(embed=embed)


def setup(bot: SemiBotomatic) -> None:
    bot.add_cog(Tags(bot=bot))
