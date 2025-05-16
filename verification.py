import discord

import config


client = None


def set_client(bot_client: discord.Client):
    global client
    client = bot_client


async def welcome(member: discord.User | discord.Member):
    if not isinstance(client, discord.Client):
        raise discord.errors.ClientException

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
