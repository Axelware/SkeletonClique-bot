import aiohttp.web
import aiohttp_jinja2

import config


# noinspection PyUnusedLocal
@aiohttp_jinja2.template('index.html')
async def index_get(request: aiohttp.web.Request):
    return None


# noinspection PyUnusedLocal
@aiohttp_jinja2.template('staff.html')
async def staff_get(request: aiohttp.web.Request):

    staff = {'admins': [], 'moderators': [], 'bot_developers': []}
    guild = request.app.bot.get_guild(config.SKELETON_CLIQUE_GUILD_ID)

    for owner_id in config.OWNER_IDS:

        person = guild.get_member(owner_id)
        avatar = person.avatar_url_as(format='gif' if person.is_avatar_animated() else 'png')
        data = {'name': str(person), 'image': avatar}

        if person.top_role.id == config.ADMIN_ROLE_ID:
            staff['admins'].append(data)
        elif person.top_role.id == config.MODERATOR_ROLE_ID:
            staff['moderators'].append(data)
        elif person.top_role.id == config.BOT_DEVELOPER_ROLE_ID:
            staff['bot_developers'].append(data)

    return staff


def setup(app: aiohttp.web.Application) -> None:

    app.add_routes([
        aiohttp.web.get(r'/', index_get),
        aiohttp.web.get(r'/staff', staff_get)
    ])
