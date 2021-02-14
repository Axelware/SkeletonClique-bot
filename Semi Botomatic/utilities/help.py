from typing import List, Optional, Union

import discord
from discord.ext import commands

import config
from utilities import exceptions


class HelpCommand(commands.HelpCommand):

    def __init__(self) -> None:
        super().__init__(command_attrs={
            'help': 'Shows help for the bot, a category or a command.\n\n'
                    '**<argument>** means the argument is required.\n'
                    '**[argument]** means the argument is optional.\n'
                    '**[a|b]** means it can be "A" or "B".\n'
                    '**[argument...]** means you can have multiple arguments.'
        })

    def get_cog_commands(self, *, cog: commands.Cog) -> Optional[List[Union[commands.Command, commands.Group]]]:

        filtered_commands = []

        for command in cog.walk_commands():
            if (command.hidden or command.root_parent and command.root_parent.hidden) and self.context.author.id not in config.OWNER_IDS:
                continue
            filtered_commands.append(command)

        return filtered_commands

    @staticmethod
    def format_commands(*, unformatted_command: List[commands.Command]) -> List[str]:

        formatted_commands = []

        for command in unformatted_command:
            command_help = command.help.strip().split('\n')[0] if command.help else 'No help provided for this command.'
            space = f'{config.ZWSP} {config.ZWSP}  ' * (len(command.parents) - 1)
            indent = '`╚╡` ' if command.parents else ''
            formatted_commands.append(f'**{space}{indent}{command.name}** - {command_help}')

        return formatted_commands

    async def send_bot_help(self, mapping) -> None:

        entries = []

        if not self.context.bot.cogs:
            raise exceptions.ArgumentError('There are no loaded cogs.')

        for cog in sorted(self.context.bot.cogs.values(), key=lambda c: len(list(c.walk_commands())), reverse=True):

            if not (cog_commands := self.get_cog_commands(cog=cog)):
                continue

            entries.append(f'__**{cog.qualified_name}:**__\n{"".join(f"`{command.qualified_name}`{config.ZWSP} " for command in cog_commands)}')

        title = f'__{self.context.bot.user.name}\'s help page__'
        header = f'Use `{config.PREFIX}help [Command/Category]` for more help with a command or category.\n\n'
        await self.context.paginate_embed(entries=entries, per_page=5, title=title, header=header)

    async def send_cog_help(self, cog: commands.Cog) -> None:

        if (cog_commands := self.get_cog_commands(cog=cog)) is None:
            raise exceptions.ArgumentError('This cog has no commands. (Or you are not allowed to see them.')

        entries = self.format_commands(unformatted_command=cog_commands)
        title = f'__**{cog.qualified_name} help page:**__\n'
        header = f'{cog.description}\n\n' if cog.description else ''

        await self.context.paginate_embed(entries=entries, per_page=20, title=title, header=header)

    async def send_group_help(self, group: commands.Group) -> None:

        filtered_commands = []

        for command in group.walk_commands():
            if command.hidden and self.context.author.id not in config.OWNER_IDS:
                continue
            filtered_commands.append(command)

        if not filtered_commands:
            raise exceptions.ArgumentError('That command has no subcommands that you are able to see.')

        command_help = group.help if group.help else 'No help provided for this command.'
        aliases = f'**Aliases:** {"/".join(group.aliases)}\n\n' if group.aliases else ''

        entries = self.format_commands(unformatted_command=filtered_commands)
        title = f'{group.qualified_name} {group.signature if group.signature else ""}'
        header = f'{aliases}{command_help}\n\n__**Subcommands:**__\n'

        await self.context.paginate_embed(entries=entries, per_page=20, title=title, header=header)

    async def send_command_help(self, command: commands.Command) -> None:

        command_help = command.help.strip('\n') if command.help else 'No help provided for this command.'
        aliases = f'**Aliases:** {"/".join(command.aliases)}\n\n'

        title = f'{command.qualified_name} {command.signature if command.signature else ""}'
        description = f'{aliases if command.aliases else ""}{command_help}'
        embed = discord.Embed(colour=self.context.colour, title=title, description=description)

        await self.context.paginate_embeds(entries=[embed])

    def command_not_found(self, search: str) -> str:
        return f'There are no commands or categories with the name `{search}`. Be sure to capitalize the first letter if you are looking for the help of a category.'

    def subcommand_not_found(self, command: Union[commands.Command, commands.Group], search: str) -> str:

        if isinstance(command, commands.Group):
            return f'The command `{command.qualified_name}` has no sub-commands called `{search}`.'

        return f'The command `{command.qualified_name}` has no sub-commands.'
