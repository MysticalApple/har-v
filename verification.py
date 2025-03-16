import discord
import config


async def welcome(member: discord.Member):
    form_url = config.get("form_url") + str(member.id)
    try:
        await member.send(
            f"## Welcome to the Gunn Server!\n"
            f"Please fill out [this form]({form_url}) to verify as PAUSD.\n"
            f"If you are unable to do so, please reply to this message."
        )

    except discord.errors.Forbidden:
        channel = member.guild.get_channel(
            config.get("user_contact_channel"))

        if not isinstance(channel, discord.TextChannel):
            raise config.InvalidValue

        await channel.send(
            f"{member.mention} "
            "Please enable DMs from this server and reply with `verifyme`.")
