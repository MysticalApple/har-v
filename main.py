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
    if message.content == "verifyme" and message.channel.id == config.get(
        "user_contact_channel"
    ):
        await verification.welcome(message.author)

    if message.webhook_id == config.get("form_webhook"):
        form_data = message.content.splitlines()
        await verification.verify(form_data)

    if message.content.startswith("verifytest"):
        await verification.verify(message.content.splitlines()[1:])


client.run(config.get("token"), log_handler=log_handler)
