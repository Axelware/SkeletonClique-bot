import discord
from discord.ext import commands

import config
from bot import SemiBotomatic
from utilities import context, converters, exceptions, utils


class Tags(commands.Cog):

    def __init__(self, bot: SemiBotomatic) -> None:
        self.bot = bot

    #

    @staticmethod
    def get_tag_limit(member: discord.Member) -> int:

        limit = 5
        if discord.utils.get(member.roles, id=config.NITRO_BOOSTER_ROLE_ID) is not None:
            limit = 10
        elif discord.utils.get(member.roles, id=config.FAIRY_LOCALS_ROLE_ID) is not None:
            limit = 20

        return limit

    #

    @commands.group(name='tag', aliases=['tags'], invoke_without_command=True)
    async def tag(self, ctx: context.Context, *, name: converters.TagNameConverter) -> None:
        """
        Get a tag using its name or alias.

        `name`: The name or alias of the tag that you want to find.
        """
        name = str(name)

        if not (tags := ctx.guild_config.get_tags_matching(name=name)):
            raise exceptions.ArgumentError(f'There are no tags with the name `{name}`.')
        tag = tags[0]

        if tag.name != name:
            msg = f'Maybe you meant one of these?\n{config.NL.join(f"- `{tag.name}`" for tag in tags[0:])}' if len(tags) > 1 else ''
            raise exceptions.ArgumentError(f'There are no tags with the name `{name}`. {msg}')

        if tag.alias:
            tag = ctx.guild_config.get_tag(tag_id=tag.alias)

        await ctx.send(tag.content)

    @tag.command(name='raw')
    async def tag_raw(self, ctx: context.Context, *, name: converters.TagNameConverter) -> None:
        """
        Get a tags raw content.

        `name`: The name or alias of the tag that you want to find.
        """
        name = str(name)

        if not (tags := ctx.guild_config.get_tags_matching(name=name)):
            raise exceptions.ArgumentError(f'There are no tags with the name `{name}`.')
        tag = tags[0]

        if tag.name != name:
            msg = f'Maybe you meant one of these?\n{config.NL.join(f"- `{tag.name}`" for tag in tags[0:])}' if len(tags) > 1 else ''
            raise exceptions.ArgumentError(f'There are no tags with the name `{name}`. {msg}')

        if tag.alias:
            tag = ctx.guild_config.get_tag(tag_id=tag.alias)

        await ctx.send(discord.utils.escape_markdown(tag.content))

    @tag.command(name='create', aliases=['make'])
    async def tag_create(self, ctx: context.Context, name: converters.TagNameConverter, *, content: converters.TagContentConverter) -> None:
        """
        Create a tag.

        `name`: The name of the tag.
        `content`: The content of the tag.
        """
        name = str(name)
        content = str(content)

        limit = self.get_tag_limit(member=ctx.author)
        if len(ctx.guild_config.get_user_tags(ctx.author.id)) >= limit and ctx.author.id not in config.OWNER_IDS:
            raise exceptions.ArgumentError(f'You already have the maximum of `{limit}` tags.')

        if tag_check := ctx.guild_config.get_tag(tag_name=name):
            raise exceptions.ArgumentError(f'There is already a tag with the name `{tag_check.name}`.')

        tag = await ctx.guild_config.create_tag(user_id=ctx.author.id, name=name, content=content, jump_url=ctx.message.jump_url)
        await ctx.send(f'Created tag with name `{tag.name}`.')

    @tag.command(name='alias')
    async def tag_alias(self, ctx: context.Context, alias: converters.TagNameConverter, original: converters.TagNameConverter) -> None:
        """
        Alias a new tag to a pre-existing tag.

        `alias`: The alias, the name of this new tag.
        `name`: The name of the tag to point the alias at.
        """
        alias = str(alias)
        original = str(original)

        limit = self.get_tag_limit(member=ctx.author)
        if len(ctx.guild_config.get_user_tags(ctx.author.id)) >= limit and ctx.author.id not in config.OWNER_IDS:
            raise exceptions.ArgumentError(f'You already have the maximum of `{limit}` tags.')

        if tag_check := ctx.guild_config.get_tag(tag_name=alias):
            raise exceptions.ArgumentError(f'There is already a tag with the name `{tag_check.name}`.')

        if not (original_tag := ctx.guild_config.get_tag(tag_name=original)):
            raise exceptions.ArgumentError(f'There are no tags with the name `{original}` to alias too.')

        if original_tag.alias is not None:
            original_tag = ctx.guild_config.get_tag(tag_id=original_tag.alias)

        tag = await ctx.guild_config.create_tag_alias(user_id=ctx.author.id, name=alias, original=original_tag.id, jump_url=ctx.message.jump_url)
        await ctx.send(f'Tag alias from `{tag.name}` to `{original}` was created.')

    @tag.command(name='claim')
    async def tag_claim(self, ctx: context.Context, *, name: converters.TagNameConverter) -> None:
        """
        Claim a tag if its owner has left the server.

        `name`: The name of the tag to claim.
        """
        name = str(name)

        limit = self.get_tag_limit(member=ctx.author)
        if len(ctx.guild_config.get_user_tags(ctx.author.id)) >= limit and ctx.author.id not in config.OWNER_IDS:
            raise exceptions.ArgumentError(f'You already have the maximum of `{limit}` tags.')

        if not (tag := ctx.guild_config.get_tag(tag_name=name)):
            raise exceptions.ArgumentError(f'There are no tags with the name `{name}`.')

        if ctx.guild.get_member(tag.user_id):
            raise exceptions.ArgumentError('The owner of that tag is still in this server.')

        await tag.change_owner(ctx.author.id)
        await ctx.send('Transferred tag to you.')

    @tag.command(name='transfer')
    async def tag_transfer(self, ctx: context.Context, name: converters.TagNameConverter, *, member: discord.Member) -> None:
        """
        Transfer a tag to another member.

        `name`: The name of the tag to transfer.
        `member`: The member to transfer the tag too. Can be their ID, Username, Nickname or @Mention.
        """
        name = str(name)

        if member.bot:
            raise exceptions.ArgumentError('You can not transfer tags to bots.')

        limit = self.get_tag_limit(member=member)
        if len(ctx.guild_config.get_user_tags(member.id)) >= limit and member.id not in config.OWNER_IDS:
            raise exceptions.ArgumentError(f'The person you are trying to transfer the tag too already has the maximum of `{limit}` tags.')

        if not (tag := ctx.guild_config.get_tag(tag_name=name)):
            raise exceptions.ArgumentError(f'There are no tags with the name `{name}`.')
        if tag.user_id != ctx.author.id:
            raise exceptions.ArgumentError('You do not own that tag.')
        if tag.user_id == member.id:
            raise exceptions.ArgumentError('You can not transfer tags to yourself.')

        await tag.change_owner(user_id=member.id)
        await ctx.send(f'Transferred tag from `{ctx.author}` to `{ctx.guild.get_member(tag.user_id)}`.')

    @tag.command(name='edit')
    async def tag_edit(self, ctx: context.Context, name: converters.TagNameConverter, *, content: converters.TagContentConverter) -> None:
        """
        Edit a tag's content.

        `name`: The name of the tag to edit the content of.
        `content:` The content to edit the tag with.
        """
        name = str(name)
        content = str(content)

        if not (tag := ctx.guild_config.get_tag(tag_name=name)):
            raise exceptions.ArgumentError(f'There are no tags with the name `{name}`.')
        if tag.user_id != ctx.author.id:
            raise exceptions.ArgumentError('You do not own that tag.')

        await tag.change_content(content)
        await ctx.send(f'Edited content of tag with name `{name}`.')

    @tag.command(name='delete', aliases=['remove'])
    async def tag_delete(self, ctx: context.Context, *, name: converters.TagNameConverter) -> None:
        """
        Delete a tag.

        `name`: The name of the tag to delete.
        """
        name = str(name)

        if not (tag := ctx.guild_config.get_tag(tag_name=name)):
            raise exceptions.ArgumentError(f'There are no tags with the name `{name}`.')
        if tag.user_id != ctx.author.id:
            raise exceptions.ArgumentError('You do not own that tag.')

        await tag.delete()
        await ctx.send(f'Deleted tag with name `{name}`.')

    @tag.command(name='search')
    async def tag_search(self, ctx: context.Context, *, name: converters.TagNameConverter) -> None:
        """
        Display a list of tags that are similar to the search.

        `name`: The search terms to look for tags with.
        """
        name = str(name)

        if not (tags := ctx.guild_config.get_tags_matching(name=name, limit=100)):
            raise exceptions.ArgumentError(f'There are no tags similar to the search `{name}`.')

        entries = [f'`{index + 1}.` {tag.name}' for index, tag in enumerate(tags)]
        await ctx.paginate_embed(entries=entries, per_page=25, title=f'Tags matching: `{name}`')

    @tag.command(name='list')
    async def tag_list(self, ctx: context.Context, *, member: discord.Member = None) -> None:
        """
        Get a list of yours or someone else's tags.

        `member`: The member to get a tag list for. Can be their ID, Username, Nickname or @Mention.
        """

        if not member:
            member = ctx.author

        if not (tags := ctx.guild_config.get_user_tags(member.id)):
            raise exceptions.ArgumentError(f'`{member}` does not have any tags.')

        entries = [f'`{index + 1}.` {tag.name}' for index, tag in enumerate(tags)]
        await ctx.paginate_embed(entries=entries, per_page=25, title=f'`{member}`\'s tags:')

    @tag.command(name='all')
    async def tag_all(self, ctx: context.Context) -> None:
        """
        Get a list of all tags in this server.
        """

        if not (tags := ctx.guild_config.get_all_tags()):
            raise exceptions.ArgumentError('There are no tags.')

        entries = [f'`{index + 1}.` {tag.name}' for index, tag in enumerate(tags)]
        await ctx.paginate_embed(entries=entries, per_page=25, title=f'`{ctx.guild}`\'s Tags:')

    @tag.command(name='info')
    async def tag_info(self, ctx: context.Context, *, name: converters.TagNameConverter) -> None:
        """
        Displays information about a tag.

        `name`: The name of the tag to get the information for.
        """
        name = str(name)

        if not (tag := ctx.guild_config.get_tag(tag_name=name)):
            raise exceptions.ArgumentError(f'There are no tags with the name `{name}`.')

        owner = ctx.guild.get_member(tag.user_id)

        embed = discord.Embed(
                colour=ctx.colour, title=f'{tag.name}',
                description=f'`Owner:` {owner.mention if owner else "*Not found*"} ({tag.user_id})\n'
                            f'`Claimable:` {owner is None}\n'
                            f'`Alias:` {ctx.guild_config.get_tag(tag_id=tag.alias).name if tag.alias else None}\n'
                            f'`Created on:` {utils.format_datetime(tag.created_at)}\n'
                            f'`Created:` {utils.format_difference(tag.created_at, suppress=[])} ago'
        )
        await ctx.send(embed=embed)


def setup(bot: SemiBotomatic) -> None:
    bot.add_cog(Tags(bot=bot))
