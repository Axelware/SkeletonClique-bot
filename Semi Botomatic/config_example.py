
# Bot
TOKEN = ''
PREFIX = ''
CLIENT_ID = ''
EXTENSIONS = [
    'cogs.information',
    'cogs.voice.music',
    'cogs.voice.radio',
    'cogs.background',
    'cogs.prometheus',
    'cogs.birthdays',
    'cogs.settings',
    'cogs.events',
    'cogs.images',
    'cogs.tags',
    'cogs.time',
    'cogs.todo',
    'cogs.fun',
    'cogs.dev',
    'jishaku',
]
OWNER_IDS = {
    709183570198921299, 434820920574738433, 406643416789942298, 411132793490374656, 360594708327825411, 405057609213673473, 238356301439041536, 494141434568376351,
    826593785617711134
}


# Tokens
AXEL_WEB_TOKEN = ''
KSOFT_TOKEN = ''
SPOTIFY_CLIENT_ID = ''
SPOTIFY_CLIENT_SECRET = ''


# Connection information
POSTGRESQL = {
    'host':     '',
    'user':     '',
    'database': '',
    'password': '',
}
REDIS = {
    'host':     '',
    'port':     00000,
    'password': '',
    'db':       0,
}
NODES = [
    {
        'host':       '',
        'port':       '',
        'identifier': '',
        'password':   '',
        'type':       '',
    },
    {
        'host':       '',
        'port':       '',
        'identifier': '',
        'password':   '',
        'type':       '',
    },
]
WEB_ADDRESS = '127.0.0.1'
WEB_PORT = 8080
WEB_URL = f'{WEB_ADDRESS}:{WEB_PORT}'
SPOTIFY_CALLBACK_URI = 'http://127.0.0.1'


# Custom values
COLOUR = 0x4E5122
ZWSP = '\u200b'
NL = '\n'


# ID's
SKELETON_CLIQUE_GUILD_ID = 470584033668104212
ALESS_LAND_GUILD_ID = 598911246087094272
NITRO_BOOSTER_ROLE_ID = 585552444969320454
FAIRY_LOCALS_ROLE_ID = 722086216228667402
STAFF_ROLE_ID = 687683937551777806
BOT_DEVELOPER_ROLE_ID = 781891316677345320
MODERATOR_ROLE_ID = 475649074037522434
ADMIN_ROLE_ID = 471044846635974656


# Webhooks
ERROR_WEBHOOK_URL = ''
DM_WEBHOOK_URL = ''
COMMON_LOG_WEBHOOK_URL = ''
IMPORTANT_LOG_WEBHOOK_URL = ''
STARBOARD_WEBHOOK_URL = ''


# Emoji mappings
CHANNEL_EMOJIS = {
    'text':         '<:text:739399497200697465>',
    'text_locked':  '<:text_locked:739399496953364511>',
    'text_nsfw':    '<:text_nsfw:739399497251160115>',
    'news':         '<:news:739399496936718337>',
    'news_locked':  '<:news_locked:739399497062416435>',
    'voice':        '<:voice:739399497221931058>',
    'voice_locked': '<:voice_locked:739399496924135476>',
    'category':     '<:category:738960756233601097>',
    'unknown':      '<:question:>',
}
BADGE_EMOJIS = {
    'staff':                  '<:staff:738961032109752441>',
    'partner':                '<:partner:738961058613559398>',
    'hypesquad':              '<:hypesquad:738960840375664691>',
    'bug_hunter':             '<:bug_hunter:738961014275571723>',
    'bug_hunter_level_2':     '<:bug_hunter_level_2:739390267949580290>',
    'hypesquad_bravery':      '<:hypesquad_bravery:738960831596855448>',
    'hypesquad_brilliance':   '<:hypesquad_brilliance:738960824327995483>',
    'hypesquad_balance':      '<:hypesquad_balance:738960813460684871>',
    'early_supporter':        '<:early_supporter:738961113219203102>',
    'system':                 '<:system_1:738960703284576378><:system_2:738960703288770650>',
    'verified_bot':           '<:verified_bot_1:738960728022581258><:verified_bot_2:738960728102273084>',
    'verified_bot_developer': '<:verified_bot_developer:738961212250914897>',
}


# Dateparser settings
DATEPARSER_SETTINGS = {
    'DATE_ORDER':               'DMY',
    'TIMEZONE':                 'UTC',
    'RETURN_AS_TIMEZONE_AWARE': False,
    'PREFER_DAY_OF_MONTH':      'current',
    'PREFER_DATES_FROM':        'future',
    'PARSERS':                  ['relative-time', 'absolute-time', 'timestamp', 'custom-formats']
}
