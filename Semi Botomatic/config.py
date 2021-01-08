
# Bot stuff
TOKEN = 'Nzk2NDIxMDYyMTAyNjE0MDQ2.X_Xq6Q.mLuJ4gYW9OFRRwxznSxiTS4H044'
PREFIX = '!!'
COLOUR = 0x4e5122
ZWSP = '\u200b'
NL = '\n'

OWNER_IDS = {
    709183570198921299, 434820920574738433, 440113725970710528, 406643416789942298, 411132793490374656,
    360594708327825411, 516800955086536715, 405057609213673473, 238356301439041536, 494141434568376351
}

EXTENSIONS = [
    'cogs.information',
    'cogs.events',
    'cogs.fun',
    'cogs.dev',
    'jishaku',
]

# Webhooks
ERROR_WEBHOOK = 'https://canary.discord.com/api/webhooks/796488853619212299/0v0tNO86mxONGoVy29t3XbFukgs1CTW7NwwE4nNhUYKpzv8lh5J2aynuJvCfWm0Wc19E'
DM_WEBHOOK = 'https://canary.discord.com/api/webhooks/796488926009098290/-gJxnSLwLZrk8boeKikkQZCW5N-ADP-Od6zDl5LMK9fDUCeMLw8vKkyAdXyA4ysYWJ5i'
COMMON_LOG_WEBHOOK = 'https://canary.discord.com/api/webhooks/796488998666108979/aUHwE90s1gxNYiMtPr0-CR6yYe6WtcIchD8d54OD9WZvNZTCDQ9XYWZwRcDI68vaQ1bR'
IMPORTANT_LOG_WEBHOOK = 'https://canary.discord.com/api/webhooks/796489101279887411/pGTWOtWrKNVzFzWUEgbWcA4qABx2LEpO8MmOmyTxLFLn-VTCPZ865xmHzlrsBz0SziVr'

# Connection information
POSTGRESQL = {
    'host':     '144.172.70.212',
    'user':     'skeleton',
    'database': 'skeleton',
    'password': '2MNGd^GB,FP9G%aStTv:',
}

REDIS = {
    # TODO: Redis stuff
}


# Emoji mappings
CHANNEL_EMOJIS = {
    'text':         '<:text:739399497200697465>',
    'text_locked':  '<:text_locked:739399496953364511>',
    'text_nsfw':    '<:text_nsfw:739399497251160115>',
    'news':         '<:news:739399496936718337>',
    'news_locked':  '<:news_locked:739399497062416435>',
    'voice':        '<:voice:739399497221931058>',
    'voice_locked': '<:voice_locked:739399496924135476>',
    'category':     '<:category:738960756233601097>'
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