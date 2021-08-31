from discord.ext import commands


class SemiBotomaticError(commands.CommandError):
    pass


class ArgumentError(SemiBotomaticError):
    pass


class ImageError(SemiBotomaticError):
    pass


class VoiceError(SemiBotomaticError):
    pass


class GeneralError(SemiBotomaticError):
    pass


class NotFound(SemiBotomaticError):
    pass
