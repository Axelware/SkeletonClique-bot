import discord
import pendulum
from discord.ext import commands

import config
from bot import SemiBotomatic
from utilities import context, converters, exceptions, utils


class Time(commands.Cog):

    def __init__(self, bot: SemiBotomatic) -> None:
        self.bot = bot

    @commands.command(name='time')
    async def time(self, ctx: context.Context, *, timezone: str = None) -> None:
        """
        Displays the time of the member or timezone provided.

        `timezone`: The timezone or members Name, Nickname, ID, or @Mention that you want to get.
        """

        if not timezone:
            member = ctx.author
            timezone = ctx.user_config.timezone

        else:

            try:
                member = None
                timezone = await converters.TimezoneConverter().convert(ctx=ctx, argument=timezone)
            except exceptions.ArgumentError as error:
                try:
                    member = await commands.MemberConverter().convert(ctx=ctx, argument=timezone)
                    user_config = self.bot.user_manager.get_config(user_id=member.id)
                    if user_config.timezone_private is True and member.id != ctx.author.id:
                        raise exceptions.ArgumentError('That users timezone is private.')
                    timezone = user_config.timezone
                except commands.BadArgument:
                    raise exceptions.ArgumentError(str(error))

        datetime = utils.format_datetime(datetime=pendulum.now(tz=timezone))

        embed = discord.Embed(colour=ctx.colour, title=f'Time in {timezone.name}{f" ({member})" if member else ""}:', description=f'```py\n{datetime}\n```')
        await ctx.send(embed=embed)

    @commands.command(name='times')
    async def times(self, ctx: context.Context) -> None:

        configs = sorted(self.bot.user_manager.configs.items(), key=lambda kv: kv[1].time.offset_hours)
        timezone_users = {}

        for user_id, user_config in configs:

            member = ctx.guild.get_member(user_id)
            if not member:
                continue

            if user_config.timezone_private or user_config.timezone == pendulum.timezone('UTC'):
                continue

            if timezone_users.get(user_config.time.format('HH:mm (ZZ)')) is None:
                timezone_users[user_config.time.format('HH:mm (ZZ)')] = [f'{member} - {user_config.timezone.name}']
            else:
                timezone_users[user_config.time.format('HH:mm (ZZ)')].append(f'{member} - {user_config.timezone.name}')

        if not timezone_users:
            raise exceptions.ArgumentError('There are no users with timezones set.')

        entries = [f'`{timezone}:`\n{config.NL.join(members)}\n' for timezone, members in timezone_users.items()]
        await ctx.paginate_embed(entries=entries, per_page=5, header='**User timezones:**\n\n')

    @commands.command(name='timecard')
    async def timecard(self, ctx: context.Context) -> None:
        """
        Creates an image with the timezones of all the servers members.
        """

        async with ctx.typing():
            buffer = await self.bot.user_manager.create_timecard(guild_id=ctx.guild.id)
            await ctx.send(file=discord.File(fp=buffer, filename='timecard.png'))

    #

    @commands.group(name='timezone', aliases=['timezones', 'tzs', 'tz'], invoke_without_command=True)
    async def _timezone(self, ctx: context.Context) -> None:
        """
        Displays a list of timezones that can be used with the bot.
        """

        await ctx.paginate_embed(entries=pendulum.timezones, per_page=20,
                                 header='**Available timezones:**\nClick [here](https://skeletonclique.mrrandom.xyz/timezones) to view a list of timezones.\n\n')

    @_timezone.command(name='set')
    async def _timezone_set(self, ctx: context.Context, *, timezone: converters.TimezoneConverter) -> None:
        """
        Sets your timezone to the one specified.

        `timezone`: The timezone to use. See `!timezones` for a list of timezones.
        """

        await self.bot.user_manager.set_timezone(user_id=ctx.author.id, timezone=timezone.name)
        await ctx.send(f'Your timezone has been set to `{ctx.user_config.timezone.name}`.')

    @_timezone.command(name='reset', aliases=['default'])
    async def _timezone_reset(self, ctx: context.Context) -> None:
        """
        Sets your timezone back to the default (UTC).
        """

        await self.bot.user_manager.set_timezone(user_id=ctx.author.id)
        await ctx.send(f'Your timezone has been set to `{ctx.user_config.timezone.name}`.')

    @_timezone.command(name='private')
    async def _timezone_private(self, ctx: context.Context) -> None:
        """
        Sets your timezone to be private.
        """

        if ctx.user_config.timezone_private is True:
            raise exceptions.ArgumentError('Your timezone is already private.')

        await self.bot.user_manager.set_timezone(user_id=ctx.author.id, timezone=ctx.user_config.timezone.name, private=True)
        await ctx.send('Your timezone is now private.')

    @_timezone.command(name='public')
    async def _timezone_public(self, ctx: context.Context) -> None:
        """
        Sets your timezone to be public.
        """

        if ctx.user_config.timezone_private is False:
            raise exceptions.ArgumentError('Your timezone is already public.')

        await self.bot.user_manager.set_timezone(user_id=ctx.author.id, timezone=ctx.user_config.timezone.name)
        await ctx.send('Your timezone is now public.')

    #

    @commands.group(name='reminders', aliases=['remind', 'reminder', 'remindme'], invoke_without_command=True)
    async def reminders(self, ctx: context.Context, *, reminder: converters.DatetimeConverter) -> None:
        """
        Schedule a reminder for the given time.

        `reminder`: The content of reminder, should include some form of date or time such as `tomorrow`, `in 12h` or `1st january 2020`.
        """

        entries = {index: (datetime_phrase, datetime) for index, (datetime_phrase, datetime) in enumerate(reminder['found'].items())}
        if len(entries) != 1:
            choice = await ctx.paginate_choice(
                     entries=[f'`{index + 1}.` **{phrase}**\n`{utils.format_datetime(datetime=datetime)}`' for index, (phrase, datetime) in entries.items()],
                     per_page=10, header=f'**Multiple times/dates were detected within your query, please select the one you would like to be reminded at:**\n\n'
            )
            result = entries[choice]
        else:
            result = entries[0]

        datetime = utils.format_datetime(datetime=result[1], seconds=True)
        datetime_difference = utils.format_difference(datetime=result[1], suppress=[])
        content = await utils.safe_text(mystbin_client=self.bot.mystbin, text=reminder['argument'], max_characters=1800)

        reminder = await self.bot.reminder_manager.create_reminder(user_id=ctx.author.id, datetime=result[1], content=content, jump_url=ctx.message.jump_url)
        await ctx.send(f'Created a reminder with ID `{reminder.id}` for `{datetime}`, `{datetime_difference}` from now.')

    @reminders.command(name='list')
    async def reminders_list(self, ctx: context.Context) -> None:
        """
        Display a list of your active reminders.
        """

        reminders = [reminder for reminder in ctx.user_config.reminders.values() if not reminder.done]
        if not reminders:
            raise exceptions.ArgumentError('You do not have any active reminders.')

        entries = [
            f'`{reminder.id}:` **In {utils.format_difference(datetime=reminder.datetime, suppress=[])}**\n'
            f'`When:` {utils.format_datetime(datetime=reminder.datetime, seconds=True)}\n'
            f'`Content:` {await utils.safe_text(mystbin_client=self.bot.mystbin, text=reminder.content, max_characters=100)}\n'
            for reminder in sorted(reminders, key=lambda reminder: reminder.datetime)
        ]

        await ctx.paginate_embed(entries=entries, per_page=5, header=f'**Active reminders for** `{ctx.author}:`\n\n')

    @reminders.command(name='all')
    async def reminders_all(self, ctx: context.Context) -> None:
        """
        Display a list of all your reminders.
        """

        if not ctx.user_config.reminders:
            raise exceptions.ArgumentError('You do not have any reminders.')

        entries = [
            f'`{reminder.id}:` **{"In " if reminder.done is False else ""}{utils.format_difference(datetime=reminder.datetime, suppress=[])}{" ago" if reminder.done else ""}**\n'
            f'`When:` {utils.format_datetime(datetime=reminder.datetime, seconds=True)}\n'
            f'`Content:` {await utils.safe_text(mystbin_client=self.bot.mystbin, text=reminder.content, max_characters=100)}\n'
            f'`Done:` {reminder.done}\n'
            for reminder in sorted(ctx.user_config.reminders.values(), key=lambda reminder: reminder.datetime)
        ]

        await ctx.paginate_embed(entries=entries, per_page=5, header=f'**All reminders for** `{ctx.author}:`\n\n')

    @reminders.command(name='delete')
    async def reminders_delete(self, ctx: context.Context, *, reminder_ids: str) -> None:
        """
        Delete reminders with the given id's.

        `reminder_ids`: A list of reminders id's to delete, separated by spaces.
        """

        reminder_ids_to_remove = []

        for reminder_id in reminder_ids.split(' '):

            try:
                reminder_id = int(reminder_id)
            except ValueError:
                raise exceptions.ArgumentError(f'`{reminder_id}` is not a valid reminder id.')

            if reminder_id in reminder_ids_to_remove:
                raise exceptions.ArgumentError(f'You provided the reminder id `{reminder_id}` more than once.')

            reminder = await self.bot.reminder_manager.get_reminder(user_id=ctx.author.id, reminder_id=reminder_id)
            if not reminder:
                raise exceptions.ArgumentError(f'You do not have a reminder with the id `{reminder_id}`.')

            reminder_ids_to_remove.append(reminder.id)

        for reminder_id in reminder_ids_to_remove:
            await self.bot.reminder_manager.delete_reminder(user_id=ctx.author.id, reminder_id=reminder_id)

        s = 's' if len(reminder_ids_to_remove) > 1 else ''
        await ctx.send(f'Deleted `{len(reminder_ids_to_remove)}` reminder{s} with id{s} {", ".join(f"`{reminder_id}`" for reminder_id in reminder_ids_to_remove)}.')

    @reminders.command(name='edit')
    async def reminders_edit(self, ctx: context.Context, reminder_id: int, *, content: str) -> None:
        """
        Edit a reminders content.

        `reminder_id`: The id of the reminder to edit.
        `content`: The content to edit the reminder with.
        """

        reminder = await self.bot.reminder_manager.get_reminder(user_id=ctx.author.id, reminder_id=reminder_id)
        if not reminder:
            raise exceptions.ArgumentError('You do not have a reminder with that id.')

        content = await utils.safe_text(mystbin_client=self.bot.mystbin, text=content, max_characters=1800)
        await self.bot.reminder_manager.edit_reminder_content(user_id=ctx.author.id, reminder_id=reminder.id, content=content, jump_url=ctx.message.jump_url)

        await ctx.send(f'Edited reminder id `{reminder.id}`\'s content.')

    @reminders.command(name='info')
    async def reminders_info(self, ctx: context.Context, reminder_id: int) -> None:
        """
        Display information about the reminder with the given id.
        """

        reminder = await self.bot.reminder_manager.get_reminder(user_id=ctx.author.id, reminder_id=reminder_id)
        if not reminder:
            raise exceptions.ArgumentError('You do not have a reminder with that id.')

        embed = discord.Embed(colour=ctx.colour)
        embed.description = f'**Reminder `{reminder.id}`:**\n\n' \
                            f'**{"In " if reminder.done is False else ""}{utils.format_difference(datetime=reminder.datetime, suppress=[])}{" ago" if reminder.done else ""}**\n' \
                            f'`When:` {utils.format_datetime(datetime=reminder.datetime, seconds=True)}\n' \
                            f'`Created:` {utils.format_datetime(datetime=reminder.created_at, seconds=True)}\n' \
                            f'`Done:` {reminder.done}\n\n' \
                            f'`Content:`\n {await utils.safe_text(mystbin_client=self.bot.mystbin, text=reminder.content, max_characters=1800)}\n'

        await ctx.send(embed=embed)


def setup(bot: SemiBotomatic) -> None:
    bot.add_cog(Time(bot=bot))
