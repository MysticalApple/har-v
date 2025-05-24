import logging

import discord

import config
import verification

log_handler = logging.FileHandler(filename="bot.log", encoding="utf-8", mode="w")
log_handler.set_name("discord")
logger = logging.getLogger("discord")
intents = discord.Intents.all()

client = discord.Client(intents=intents)

verification.setup(client, logger)


@client.event
async def on_ready():
    logger.info(f"Logged in as {client.user}")


@client.event
async def on_member_join(member: discord.Member):
    # TODO: Check if already verified

    await verification.welcome(member)


@client.event
async def on_message(message: discord.Message):
    assert client.user is not None

    if message.content == "verifyme" and message.channel.id == config.get(
        "user_contact_channel"
    ):
        await verification.welcome(message.author)
        return

    if message.webhook_id == config.get("form_webhook"):
        form_data = message.content.splitlines()
        await verification.verify(form_data)
        return

    if message.content.startswith("verifytest"):
        await verification.verify(message.content.splitlines()[1:])
        return

    # Relay DMs to mod channel (does not work with non-text content)
    if (
        isinstance(message.channel, discord.DMChannel)
        and message.author.id != client.user.id
    ):
        channel = await client.fetch_channel(config.get("mod_contact_channel"))
        if not isinstance(channel, discord.TextChannel):
            logger.error("Invalid mod contact channel id.")
            raise discord.ClientException

        await channel.send(
            f"Message from {message.author.mention}:\n{message.content}",
            allowed_mentions=discord.AllowedMentions.none(),
        )
        await message.reply(
            "Thank you for your message. A mod will contact you shortly."
        )
        return


client.run(config.get("token"), log_handler=log_handler)
