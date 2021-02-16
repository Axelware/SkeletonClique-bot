from __future__ import annotations

import logging
from typing import Optional, TYPE_CHECKING, List

from utilities import objects, exceptions

if TYPE_CHECKING:
    from bot import SemiBotomatic

__log__ = logging.getLogger(__name__)


class TodoManager:

    def __init__(self, bot: SemiBotomatic) -> None:
        self.bot = bot

    async def load(self) -> None:

        todos = await self.bot.db.fetch('SELECT * FROM todos')
        for todo_data in todos:

            todo = objects.Todo(data=todo_data)

            user_config = await self.bot.user_manager.get_or_create_user_config(user_id=todo_data['user_id'])
            user_config.todos[todo.id] = todo

        __log__.info(f'[TODO MANAGER] Loaded reminders. [{len(todos)} todos]')
        print(f'[TODO MANAGER] Loaded reminders. [{len(todos)} todos]')

    #

    async def create_todo(self, *, user_id: int, content: str, jump_url: str = None) -> objects.Todo:

        user_config = await self.bot.user_manager.get_or_create_user_config(user_id=user_id)

        data = await self.bot.db.fetchrow('INSERT INTO todos (user_id, content, jump_url) VALUES ($1, $2, $3) RETURNING *', user_id, content, jump_url)
        todo = objects.Todo(data=data)

        __log__.info(f'[TODO MANAGER] Created todo with id \'{todo.id}\'for user with id \'{todo.user_id}\'')

        user_config.todos[todo.id] = todo
        return todo

    def get_todo(self, *, user_id: int, todo_id: int) -> Optional[objects.Todo]:

        user_config = self.bot.user_manager.get_user_config(user_id=user_id)
        return user_config.todos.get(todo_id)

    async def delete_todo(self, user_id: int, todo_id: int) -> None:

        user_config = await self.bot.user_manager.get_or_create_user_config(user_id=user_id)

        if not user_config.todos.get(todo_id):
            raise exceptions.GeneralError(f'Todo with id `{todo_id}` was not found.')

        await self.bot.db.execute('DELETE FROM todos WHERE id = $1', todo_id)
        del user_config.todos[todo_id]

    async def delete_todos(self, user_id: int, todo_ids: List[int]) -> None:

        user_config = await self.bot.user_manager.get_or_create_user_config(user_id=user_id)

        for todo_id in todo_ids:
            if not user_config.todos.get(todo_id):
                raise exceptions.GeneralError(f'Todo with id `{todo_id}` was not found.')

        await self.bot.db.executemany('DELETE FROM todos WHERE id = $1', [[todo_id] for todo_id in todo_ids])
        for todo_id in todo_ids:
            del user_config.todos[todo_id]

    async def edit_todo_content(self, user_id: int, todo_id: int, content: str, jump_url: str = None) -> None:

        user_config = await self.bot.user_manager.get_or_create_user_config(user_id=user_id)

        todo = user_config.todos.get(todo_id)
        if not todo:
            raise exceptions.GeneralError(f'Todo with id `{todo_id}` was not found.')

        await self.bot.db.execute('UPDATE todos SET content = $1, jump_url = $2 WHERE id = $3', content, jump_url, todo.id)
        todo.content = content
        if jump_url:
            todo.jump_url = jump_url