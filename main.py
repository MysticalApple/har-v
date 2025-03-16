import logging

import discord

import config
import verification

log_handler = logging.FileHandler(
    filename='bot.log', encoding='utf-8', mode='w')

discord.utils.setup_logging(handler=log_handler)

intents = discord.Intents.all()

client = discord.Client(intents=intents)
verification.set_client(client)


@client.event
async def on_ready():
    print(f'Logged in as {client.user}')


@client.event
async def on_member_join(member: discord.Member):
    await verification.welcome(member)


@client.event
async def on_message(message: discord.Message):
    if message.content == "verifyme":
        await verification.welcome(message.author)

client.run(config.get("token"), log_handler=None)
