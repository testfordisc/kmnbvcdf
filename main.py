import aiohttp
import discord
import yaml
import emoji
import os
from discord import utils
from discord.ext import commands
import discord.emoji

import docstoken

description = "Roblox API Server Documentation Bot"
bot = commands.Bot(command_prefix='?', description=description, help_command=None)
session = None


@bot.event
async def on_ready():
    global session
    session = aiohttp.ClientSession()
    print(f"Logged in as {bot.user.name}, id: {bot.user.id}")
    print("--")


# Message Logging
@bot.event
async def on_message_delete(message):
    channel = bot.get_channel(709176997233950790) # message-logs channel
    
    # Avoid duplicate channel; i.e message delete from log channel
    if message.channel == channel:
        return
    
    # Check Audit logs to find out who deleted the message
    entries = await message.guild.audit_logs(limit=None, action=discord.AuditLogAction.message_delete).flatten()
    base_entry = entries[0]

    emb = discord.Embed()
    emb.set_author(name="Message (Delete)", icon_url="https://cdn.discordapp.com/attachments/336577284322623499/683028692133216300/ac6e275e1f638f4e19af408d8440e1d1.png")
    emb.set_footer(text=f'{message.author}\t\t\t\t\t\tTimestamp: {message.created_at}', icon_url=message.author.avatar_url)
    emb.add_field(name="Message", value=message.content)
    #emb.add_field(name="Deleted By", value=f'{base_entry.user.name}#{base_entry.user.discriminator} ({base_entry.user.id})')
    await channel.send(embed=emb)
    

@bot.event
async def on_message_edit(before, after):
    channel = bot.get_channel(709176997233950790) # message-logs channel
   
    # If message data is malformed or blank, return
    if (before.content == "") or (after.content == ""):
        return
    
    emb = discord.Embed()
    emb.set_author(name="Message (Edit)", icon_url="https://cdn.discordapp.com/attachments/336577284322623499/683028692133216300/ac6e275e1f638f4e19af408d8440e1d1.png")
    emb.set_footer(text=f'{before.author}\t\t\t\t\t\tTimestamp: {after.created_at}', icon_url=before.author.avatar_url)
    emb.add_field(name="Before", value=(before.content), inline=False)
    emb.add_field(name="After", value=(after.content), inline=False)
    await channel.send(embed=emb)


@bot.command(aliases=["libs", "libraries", "librarylist"])
async def list(ctx):
    """Generate server library list"""
    embed, yml = await fetch_embed('libs')
    embed.set_author(name="Libraries", icon_url="https://cdn.discordapp.com/attachments/336577284322623499/683028692133216300/ac6e275e1f638f4e19af408d8440e1d1.png")
    for lang in yml["list"]:
        for lib in lang['libs']:
            user = bot.get_user(lib["uid"])
            embed.add_field(name=f'{lib["name"]}({lang["lang"]})', value=f'{lib["author"]}(@{user}) - {lib["url"]}')
    await ctx.send(embed=embed)


@bot.command()
async def ping(ctx):
    resp = await ctx.send('Pong! Loading...', delete_after=1.0)
    diff = resp.created_at - ctx.message.created_at
    totalms = 1000 * diff.total_seconds()
    emb = discord.Embed()
    emb.set_author(name="Pong!", icon_url="https://cdn.discordapp.com/attachments/336577284322623499/683028692133216300/ac6e275e1f638f4e19af408d8440e1d1.png")
    emb.add_field(name="Message time", value=f"{totalms}ms")
    emb.add_field(name="API latency", value=f"{(1000 * bot.latency):.1f}ms")
    await ctx.send(embed=emb)


@bot.command(aliases=["codeblocks"])
async def codeblock(ctx):
    emb, _ = await fetch_embed('codeblock')
    emb.set_author(name="Codeblocks", icon_url="https://cdn.discordapp.com/attachments/336577284322623499/683028692133216300/ac6e275e1f638f4e19af408d8440e1d1.png")
    await ctx.send(embed=emb)


@bot.command(aliases=["cookies"])
async def cookie(ctx):
    emb, _ = await fetch_embed('cookie')
    emb.set_author(name="Cookies", icon_url="https://cdn.discordapp.com/attachments/336577284322623499/683028692133216300/ac6e275e1f638f4e19af408d8440e1d1.png")
    await ctx.send(embed=emb)


async def check_doc_exists(ctx, doc, version):
    base = f'https://{doc}.roblox.com'
    async with session.get(f'{base}/docs/json/{version}') as r:
        if r.status != 200:
            return await ctx.send("Sorry, those docs don't exist."), None
        else:
            data = await r.json()
            return data, discord.Embed(description=base) # title=data['info']['title']


@bot.command()
async def docs(ctx, doc: str, version: str):
    data, embed = await check_doc_exists(ctx, doc, version)
    if embed is None:
        return
    i = 0
    embed.set_author(name=f'{doc.capitalize()} {version}', icon_url="https://cdn.discordapp.com/attachments/336577284322623499/683028692133216300/ac6e275e1f638f4e19af408d8440e1d1.png")
    for path in data['paths']:
        for method in data['paths'][path]:
            docs = data['paths'][path][method]
            desc = f"""{docs['summary']}"""
            embed.add_field(name=f"{method.upper()} {path}", value=desc, inline=True)
            if i >= 25:
                await ctx.send(embed=embed)
                embed = discord.Embed(title=data['info']['title'])
                i = 0
            i += 1
    await ctx.send(embed=embed)


@bot.command()
async def doc(ctx, doc: str, version: str, *, args):
    data, embed = await check_doc_exists(ctx, doc, version)
    if embed is None:
        return
    embed.set_author(name=f'{doc.capitalize()} {version}', icon_url="https://cdn.discordapp.com/attachments/336577284322623499/683028692133216300/ac6e275e1f638f4e19af408d8440e1d1.png")
    embed.set_footer(text=f'Keyword(s): {args}')
    for path in data['paths']:
        for method in data['paths'][path]:
            docs = data['paths'][path][method]
            if docs['summary'].find(args) != -1:
                desc = f"""{docs['summary']}"""
                embed.add_field(name=f"{method.upper()} {path}", value=desc, inline=True)
                await ctx.send(embed=embed)
                return
    await ctx.send("Sorry, that keyword was not found in docs specified")


async def fetch_embed(filename: str):
    with open(f'yaml/{filename}.yml') as file:
        j = file.read()
    d = yaml.load(j, Loader=yaml.FullLoader)
    return discord.Embed.from_dict(d), d


@bot.command()
async def leaderboard(ctx):
    roles = [(r.name, len(r.members)) for r in ctx.guild.roles if 'news' in r.name]
    roles.sort(key=lambda x: x[1], reverse=True)
    embed = discord.Embed()
    embed.set_author(name="Subscriber Leaderboards", icon_url="https://cdn.discordapp.com/attachments/336577284322623499/683028692133216300/ac6e275e1f638f4e19af408d8440e1d1.png")
    for i, r in enumerate(roles):
        embed.add_field(name=f"{i + 1}. {r[0]}", value=f"**Subscribers:** {r[1]}")
    await ctx.send(embed=embed)


@bot.command(aliases=["apisites", "robloxapi", "references", "reference"])
async def api(ctx):
    emb, _ = await fetch_embed('endpoints')
    emb.set_author(name="References", icon_url="https://cdn.discordapp.com/attachments/336577284322623499/683028692133216300/ac6e275e1f638f4e19af408d8440e1d1.png")
    await ctx.send(embed=emb)


@bot.command()
async def resources(ctx):
    emb, _ = await fetch_embed('resources')
    emb.set_author(name="Resources", icon_url="https://cdn.discordapp.com/attachments/336577284322623499/683028692133216300/ac6e275e1f638f4e19af408d8440e1d1.png")
    await ctx.send(embed=emb)


def get_news_role(ctx, channel: discord.TextChannel = None):
    ch = channel if channel else ctx.channel
    return utils.find(lambda r: r.name.startswith(ch.name.split('_')[1]), ctx.guild.roles)


@bot.command()
async def subscribe(ctx, channel: discord.TextChannel = None):

    # bot_commands channel
    if ctx.channel.id == 598564981989965854 and channel:
        role = get_news_role(ctx, channel)
    
    # Not bot_commands channel, but is a channel in "Libraries" or "Frameworks" categories
    elif (ctx.channel.id != 598564981989965854 or ctx.channel.category_id == 361587040749355018 or ctx.channel.category_id == 361587387538604054) and not channel:
        role = get_news_role(ctx)
    else:
        return

    if role in ctx.author.roles:
        await ctx.author.remove_roles(role)
        await ctx.message.add_reaction('👎')
    else:
        await ctx.author.add_roles(role)
        await ctx.message.add_reaction('👍')

@bot.command()
@commands.has_role("Library Developer")
async def poll(ctx, *, args):
    role = get_news_role(ctx)
    await role.edit(mentionable=True)
    await ctx.send(f'{role.mention}')
    await role.edit(mentionable=False)
    embed = discord.Embed(Title="Poll")
    embed.set_author(name="Poll", icon_url="https://cdn.discordapp.com/attachments/336577284322623499/683028692133216300/ac6e275e1f638f4e19af408d8440e1d1.png")
    hasEmojis = ((args.find('[') and args.find(']')) != -1) # Regex?

    if hasEmojis:
        emojis = (args[args.find('[')+1:args.find(']')-1]).split()
        args = args[args.find(']')+1:]
        embed.add_field(name="Question", value=f'{args}')
        embed.set_footer(text='React below to cast a vote')
        message = await ctx.send(embed=embed)
        for _emoji in emojis:
            await message.add_reaction(_emoji)
    else:
        embed.add_field(name="Question", value=f'{args}')
        embed.set_footer(text="👍 for upvote or 👎 for downvote")
        message = await ctx.send(embed=embed)
        await message.add_reaction('👍')
        await message.add_reaction('👎')


@bot.command()
@commands.has_role("Library Developer")
async def pingnews(ctx, version: str, *, args):
    role = get_news_role(ctx)
    await role.edit(mentionable=True)
    await ctx.send(f'{role.mention}\n**Release Notes {version}**\n{args}')
    await role.edit(mentionable=False)


@bot.command()
@commands.has_role("Moderator")
async def pinglibrarydevelopers(ctx, title, *, message):
    role = utils.get(ctx.guild.roles, name="Library Developer")
    await role.edit(mentionable=True)
    await ctx.send(f'{role.mention}\n**{title}**\n{message}')
    await role.edit(mentionable=False)


@bot.command()
@commands.has_role("Moderator")
async def restart(ctx):
    await bot.logout()


# Disabled for now    
# bot.load_extension('verify')

if __name__ == "__main__":
    bot.run(docstoken.discord)
