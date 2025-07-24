import logging
import discord
from discord.ext import commands

import config
from user_db import get_db

logger: logging.Logger
bot: commands.Bot


def setup(v_bot: commands.Bot, v_logger: logging.Logger):
    """
    Set globals.
    """
    global bot, logger
    bot = v_bot
    logger = v_logger


def get_guild() -> discord.Guild:
    """
    Gets the guild associated with this bot.
    """
    guild = bot.get_guild(config.get("guild"))
    if guild is None:
        logger.error("Could not find guild.")
        raise discord.ClientException

    return guild


async def welcome(member: discord.User | discord.Member):
    """
    Send verification instructions to new server member.
    """
    form_url = config.get("form_url") + str(member.id)
    try:
        await member.send(
            f"## Welcome to the Gunn Server!\n"
            f"Please fill out [this form]({form_url}) to verify as PAUSD.\n"
            f"If you are unable to do so, please reply to this message."
        )

    except discord.errors.Forbidden:
        channel = bot.get_channel(config.get("user_contact_channel"))

        if not isinstance(channel, discord.TextChannel):
            raise TypeError

        await channel.send(
            f"{member.mention} "
            "Please enable DMs from this server and reply with `verifyme`."
        )


async def verify(form_data: list[str]):
    """
    Begin verification process using received data.
    """
    logger.info(f"New verification form response:\n{form_data}")

    [email, timestamp, name, school, year, user_id] = form_data
    user_id = int(user_id)
    name = name.title()
    school = school.title()
    timestamp = int(timestamp)

    guild = get_guild()
    member = guild.get_member(user_id)
    if member is None:
        await notify_mods(
            f"Issue with submission:\nUser ID `{user_id}` is invalid.",
        )
        return

    if not email.endswith("@pausd.us"):
        await notify_mods(
            f"Issue with submission from {member.mention}:\nEmail address `{email}` may be invalid. I have told the user to re-submit.",
        )
        await notify_user(
            member,
            "You verified with a non-PAUSD email. Please re-submit the form from your PAUSD Google account.",
        )
        return

    if year not in [role.name for role in guild.roles]:
        await notify_mods(
            f"Issue with submission from {member.mention}:\nNo role exists for year `{year}`.",
        )
        await notify_user(
            member,
            "Your verification form submission contains unexpected data and requires manual"
            " verification. A mod will be in contact shortly.",
        )
        return

    if school not in ["Gunn", "Paly"]:
        await notify_mods(
            f"Issue with submission from {member.mention}:\nSchool `{school}` may be invalid.",
        )
        await notify_user(
            member,
            "Your verification form submission contains unexpected data and requires manual "
            "verification. A mod will be in contact shortly.",
        )
        return

    get_db().add_user(user_id, name, school, int(year), email, timestamp)

    await add_roles(member, year)


async def notify_mods(message: str, urgent: bool = True):
    if urgent:
        logger.warning(message)
    else:
        logger.info(message)

    channel = await bot.fetch_channel(config.get("mod_contact_channel"))
    if not isinstance(channel, discord.TextChannel):
        logger.error("Invalid mod_contact_channel.")
        raise discord.ClientException

    role = get_guild().get_role(config.get("mod_role"))
    if role is None:
        logger.error("Invalid mod_role.")
        raise discord.ClientException

    await channel.send(
        f"{role.mention if urgent else ''} {message}",
        allowed_mentions=discord.AllowedMentions.all(),
    )


async def notify_user(user: discord.User | discord.Member, message: str):
    """
    Attempts to DM a user.
    Returns whether or not the DM was sent successfully.
    """
    try:
        await user.send(message)
        return True
    except discord.Forbidden:
        await notify_mods(
            f"User {user.name} with id {user.id} has DMs disabled.", urgent=False
        )
        return False


async def add_roles(member: discord.Member, year: str | int):
    """
    Gives a member verification roles, granting access to server.
    """
    verified_role = member.guild.get_role(config.get("verified_role"))
    if verified_role is None:
        logger.error("Verification role not found.")
        raise discord.ClientException

    # add_roles may be called with int or str year, but role.name is always str
    year = str(year)
    year_role = next((role for role in member.guild.roles if role.name == year), None)
    if year_role is None:
        logger.error(f"No role for year {year}.")
        raise discord.ClientException

    await member.add_roles(verified_role, year_role, reason="Verified user")
    await notify_mods(f"Verified {member.mention} with year {year}.", urgent=False)
    await notify_user(member, "You have been successfully verified.")
