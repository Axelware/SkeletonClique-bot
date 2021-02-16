import discord
from discord.ext import commands

from bot import SemiBotomatic
from utilities import context, exceptions


class Todo(commands.Cog):

    def __init__(self, bot: SemiBotomatic):
        self.bot = bot

    @commands.group(name='todo', aliases=['todos'], invoke_without_command=True)
    async def todo(self, ctx: context.Context, *, content: str = None) -> None:
        """
        Display a list of your todos.
        """

        if content is not None:
            await ctx.invoke(self.todo_add, content=content)
            return

        if not ctx.user_config.todos:
            raise exceptions.GeneralError('You do not have any todos.')

        entries = [f'[`{todo.id}`]({todo.jump_url}) {todo.content}' for todo in ctx.user_config.todos.values()]
        await ctx.paginate_embed(entries=entries, per_page=10, title=f'`{ctx.author.name}\'s` todo list:')

    @todo.command(name='list')
    async def todo_list(self, ctx: context.Context) -> None:
        """
        View a list of your todos.
        """
        await ctx.invoke(self.todo, content=None)

    @todo.command(name='add', aliases=['make', 'create'])
    async def todo_add(self, ctx: context.Context, *, content: commands.clean_content) -> None:
        """
        Create a todo.

        `content`: The content of your todo. Can not be more than 180 characters.
        """

        if len(ctx.user_config.todos) > 100:
            raise exceptions.GeneralError('You have too many todos. Try doing some of them before adding more.')

        content = str(content)
        if len(content) > 180:
            raise exceptions.ArgumentError('Your todo can not be more than 180 characters long.')

        todo = await self.bot.todo_manager.create_todo(user_id=ctx.author.id, content=content, jump_url=ctx.message.jump_url)
        await ctx.send(f'Todo with id `{todo.id}` was created.')

    @todo.command(name='delete', aliases=['remove'])
    async def todo_delete(self, ctx: context.Context, *, todo_ids: str) -> None:
        """
        Delete todos with the given ids.

        `todo_ids`: The ids of the todos to delete. You can provide a list of ids separated by spaces to delete multiple.
        """

        if not ctx.user_config.todos:
            raise exceptions.GeneralError('You do not have any todos.')

        todo_ids_to_delete = []
        for todo_id in todo_ids.split(' '):

            try:
                todo_id = int(todo_id)
            except ValueError:
                raise exceptions.ArgumentError(f'`{todo_id}` is not a valid todo id.')

            if todo_id not in ctx.user_config.todos.keys():
                raise exceptions.ArgumentError(f'You do not have a todo with the id `{todo_id}`.')
            if todo_id in todo_ids_to_delete:
                raise exceptions.ArgumentError(f'You provided the todo id `{todo_id}` more than once.')

            todo_ids_to_delete.append(todo_id)

        embed = discord.Embed(colour=ctx.colour, title=f'Deleted `{len(todo_ids_to_delete)}` todo{"s" if len(todo_ids_to_delete) > 1 else ""}:')
        embed.add_field(name='Contents: ', value='\n'.join(f'[`{ctx.user_config.todos[todo_id].id}`]({ctx.user_config.todos[todo_id].jump_url}) '
                                                           f'{ctx.user_config.todos[todo_id].content}' for todo_id in todo_ids_to_delete))

        await self.bot.todo_manager.delete_todos(user_id=ctx.author.id, todo_ids=todo_ids_to_delete)
        await ctx.send(embed=embed)

    @todo.command(name='clear')
    async def todo_clear(self, ctx: context.Context) -> None:
        """
        Clear your todo list.
        """

        if not ctx.user_config.todos:
            raise exceptions.GeneralError('You do not have any todos.')

        todo_ids = list(ctx.user_config.todos.keys())
        await self.bot.todo_manager.delete_todos(user_id=ctx.author.id, todo_ids=todo_ids)
        await ctx.send(f'Cleared your todo list of `{len(todo_ids)}` todo{"s" if len(todo_ids) > 1 else ""}.')

    @todo.command(name='edit', aliases=['update'])
    async def todo_edit(self, ctx: context.Context, todo_id: str, *, content: commands.clean_content) -> None:
        """
        Edit the todo with the given id.

        `todo_id`: The id of the todo to edit.
        `content`: The content of the new todo.
        """

        if not ctx.user_config.todos:
            raise exceptions.GeneralError('You do not have any todos.')

        content = str(content)
        if len(content) > 180:
            raise exceptions.ArgumentError('Your todo can not be more than 180 characters long.')

        try:
            todo_id = int(todo_id)
        except ValueError:
            raise exceptions.ArgumentError(f'`{todo_id}` is not a valid todo id.')

        todo = ctx.user_config.todos.get(todo_id)
        if not todo:
            raise exceptions.ArgumentError(f'You do not have a todo with the id `{todo_id}`.')

        await self.bot.todo_manager.edit_todo_content(user_id=ctx.author.id, todo_id=todo.id, content=content, jump_url=ctx.message.jump_url)
        await ctx.send(f'Edited todo with id `{todo_id}`.')


def setup(bot: SemiBotomatic):
    bot.add_cog(Todo(bot))
