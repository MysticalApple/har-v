import logging
import discord

import config

logger: logging.Logger
client: discord.Client


def setup(bot_client: discord.Client, bot_logger: logging.Logger):
    """
    Set globals.
    """
    global client, logger, guild
    client = bot_client
    logger = bot_logger


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
        channel = client.get_channel(config.get("user_contact_channel"))

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

    if not email.endswith("@pausd.us"):
        # TODO: Non-PAUSD
        logger.warning("Non-PAUSD email used.")
        return

    guild = client.get_guild(config.get("guild"))
    if guild is None:
        logger.error("Could not find guild.")
        raise discord.ClientException

    member = guild.get_member(user_id)
    if member is None:
        # TODO: NOT IN SERVER
        logger.warning("User ID invalid (user not in server or non-existent).")
        return

    if year not in [role.name for role in guild.roles]:
        # TODO: YEAR ROLE DOES NOT EXIST
        logger.warning(f"No role for year {year}.")
        return

    if school not in ["Gunn", "Paly"]:
        # TODO: UNKNOWN SCHOOL
        logger.warning("Unknown school.")
        return

    # TODO: Add user to verification db

    await add_roles(member, year)


async def add_roles(member: discord.Member, year: str):
    """
    Gives a member verification roles, granting access to server.
    """
    logger.info(f"Verifying {member.name} with year {year}.")
    verified_role = member.guild.get_role(config.get("verified_role"))
    if verified_role is None:
        logger.error("Verification role not found.")
        raise discord.ClientException

    year_role = next((role for role in member.guild.roles if role.name == year), None)
    if year_role is None:
        logger.error(f"No role for year {year}.")
        raise discord.ClientException

    await member.add_roles(verified_role, year_role, reason="Verified user")
