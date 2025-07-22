import contextlib
import datetime
import io
import logging
import textwrap
import traceback

import discord
from discord.ext import commands

import config
import verification
from user_db import get_db

log_handler = logging.FileHandler(filename="bot.log", encoding="utf-8", mode="w")
log_handler.set_name("discord")
logger = logging.getLogger("discord")
intents = discord.Intents.all()

bot = commands.Bot(command_prefix="v", intents=intents)

verification.setup(bot, logger)


@bot.event
async def on_ready():
    logger.info(f"Logged in as {bot.user}")


@bot.event
async def on_member_join(member: discord.Member):
    info = get_db().get_user(member.id)
    if info is None:
        await verification.welcome(member)
        return

    await verification.add_roles(member, str(info["year"]))


@bot.event
async def on_message(message: discord.Message):
    assert bot.user is not None

    # New verification form submission
    if message.webhook_id == config.get("form_webhook"):
        form_data = message.content.splitlines()
        await verification.verify(form_data)
        return

    # Relay DMs to mod channel (does not work with non-text content)
    if isinstance(message.channel, discord.DMChannel) and message.author != bot.user:
        channel = await bot.fetch_channel(config.get("mod_contact_channel"))
        if not isinstance(channel, discord.TextChannel):
            logger.error("Invalid mod contact channel id.")
            raise discord.ClientException

        await channel.send(
            f"Message from {message.author.mention}:\n{message.content}",
            allowed_mentions=discord.AllowedMentions.none(),
        )
        await message.reply(
            "Thank you for your message. A mod will contact you shortly.",
            mention_author=False,
        )
        return

    # Necessary because we override the default on_message
    await bot.process_commands(message)


@bot.event
async def on_command_error(ctx, error):
    ignored_errors = (
        commands.CommandNotFound,
        commands.CheckFailure,
    )
    if isinstance(error, ignored_errors):
        return

    if isinstance(error, commands.UserInputError):
        await ctx.reply(error, mention_author=False)
        return

    return error


@bot.command(name="erifyme")  # Prefix is v, so command is invoked with "verifyme"
@commands.check(lambda ctx: ctx.channel.id == config.get("user_contact_channel"))
async def verifyme(ctx):
    """
    Begin the verification process.
    """
    await verification.welcome(ctx.author)


@bot.command()
@commands.is_owner()
async def test(ctx, *, data):
    """
    Test the verification system.
    Parameters should follow the same format as the webhook.
    """
    await verification.verify(data.splitlines())


@bot.command(name="exec")
@commands.is_owner()
async def execute(ctx, *, code):
    """
    Run python code.
    """
    if code.startswith("```") and code.endswith("```"):
        code = "\n".join(code.split("\n")[1:][:-1])

    local_variables = {"ctx": ctx}

    stdout = io.StringIO()

    global_variables = globals()
    global_variables["ctx"] = ctx
    local_variables = {}

    try:
        with contextlib.redirect_stdout(stdout):
            exec(
                f"async def func():\n{textwrap.indent(code, '    ')}",
                global_variables,
                local_variables,
            )

            await local_variables["func"]()
            result = f"py\n‌{stdout.getvalue()}\n"

    except Exception as _:
        result = "".join(traceback.format_exc())

    await ctx.send(f"```{result}```")


@bot.command()
@commands.has_role(config.get("mod_role"))
async def adduser(
    ctx,
    member: discord.Member,
    name: str,
    school: str,
    year: int,
    email: str | None = None,
):
    """
    Add verification info to the database for a user. This command bypasses checks.
    """
    try:
        get_db().add_user(
            member.id,
            name,
            school,
            year,
            email,
            int(datetime.datetime.now().timestamp()),
        )
    except Exception as e:
        await ctx.message.reply(e, mention_author=False)
    else:
        await verification.add_roles(member, str(year))
        await ctx.message.add_reaction("✅")


@bot.command()
@commands.has_role(config.get("mod_role"))
async def getuser(ctx, user: discord.User):
    """
    Get the verification info associated with a user.
    """
    info = get_db().get_user(user.id)

    if info is None:
        await ctx.message.reply(
            f"No info associated with user {user.mention}.", mention_author=False
        )
        return

    await ctx.message.reply(str(info), mention_author=False)


@bot.command()
@commands.has_role(config.get("mod_role"))
async def addalt(ctx, alt: discord.Member, owner: discord.User):
    """
    Verify an alt account for a user.
    """
    try:
        get_db().add_alt(alt.id, owner.id)
    except ValueError as e:
        await ctx.reply(e, mention_author=False)
        return

    info = get_db().get_user(alt.id)
    if info is None:
        await verification.notify_mods(
            f"No info associated with alt account {alt.mention}.", urgent=True
        )
        return

    await verification.add_roles(alt, str(info["year"]))
    await ctx.message.add_reaction("✅")

    await verification.notify_user(
        owner, f"{alt.mention} was successfully added as your alt."
    )


bot.run(config.get("token"), log_handler=log_handler)
