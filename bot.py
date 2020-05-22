"""
AI-Waifu bot
Written in Python with discordpy
"""

# Discord-related libraries
import discord
from discord.ext import commands
from utils.waifu import Waifu
import asyncio
# Other libraries
import json
import random
import time
import datetime
import os

try:
    os.chdir('/root/bot_discord/ia/') # Replace with the bot directory
except:
    pass

if not os.path.exists("db"):
    os.mkdir("db")
if not os.path.exists("db/data.json"):
    bdd = {}
else:
    f = open("db/data.json", "r")
    bdd = json.loads(f.read())
    f.close()

bot = commands.Bot(command_prefix=[',','$'])

async def chan(ctx):
    if ctx.channel.topic:
        return ctx.channel.topic.lower().find('ia waifu') >= 0
    return False
def check_setup(guild, user):
    guild = str(guild)
    user = str(user)
    if guild not in bdd:
        bdd[guild] = {'waifus':[],'users':{}}
    if user not in bdd[guild]['users']:
        bdd[guild]['users'][user] = {'waifus':[],'rolls':10,'last_roll':0,'last_claim':0}
    return guild, user
def get_roll_time():
    return round(time.time()//(60*60))
def can_roll(guild: str, user: str):
    if bdd[guild]['users'][user]['last_roll'] < get_roll_time():
        bdd[guild]['users'][user]['rolls'] = 10
    if bdd[guild]['users'][user]['rolls'] > 0:
        return {'roll': True, 'wait': 0}
    return {'roll': False, 'wait': 60-datetime.datetime.now().minute}
def can_claim(guild: str, user: str):
    if bdd[guild]['users'][user]['last_claim'] < get_roll_time():
        return {'claim': True, 'wait': 0}
    return {'claim': False, 'wait': 60-datetime.datetime.now().minute}
def add_waifu(wid: int, guild: str, user: str): # Remplacer par waifu.claim()
    claim = can_claim(guild, user)
    if claim['claim']:
        bdd[guild]['waifus'].append(wid)
        bdd[guild]['users'][user]['waifus'].append(wid)
        bdd[guild]['users'][user]['last_claim'] = get_roll_time()
    return claim

# ==================================== IMAGE ====================================
@commands.check(chan)
@bot.command(aliases=['i','im'])
async def img(ctx, *, name):
    try:
        waifu = Waifu(name, guild=ctx.guild.id, bdd=bdd)
    except:
        await ctx.send("Cette waifu n'existe pas... Ou est tombée dans les profondeurs des abysses 🤔")
    else:
        embed = discord.Embed(title=f"{waifu.name}", description=f"Generated waifu N°{waifu.id}", colour=discord.Colour(0x844BC2))
        embed.set_image(url=f"https://www.thiswaifudoesnotexist.net/example-{waifu.id}.jpg")
        embed.set_footer(text="Powered by: thiswaifudoesnotexist.net")
        await ctx.send(embed=embed)

# ==================================== ROLLS ====================================
@commands.check(chan)
@bot.command(aliases=['r','mu'])
async def rolls(ctx, m: discord.Member = None):
    if m == None:
        m = ctx.author
    guild, user = check_setup(ctx.guild.id, m.id)

    if bdd[guild]['users'][user]['last_roll'] < get_roll_time():
        bdd[guild]['users'][user]['rolls'] = 10
    message = f"vous avez encore {bdd[guild]['users'][user]['rolls']} roll(s).\n"
    claim = can_claim(guild, user)
    if claim['claim']:
        message += "Vous pouvez encore claim cette heure."
    else:
        message += "Vous ne pouvez plus claim cette heure."
    await ctx.send(f"{m.mention}, {message}")

# ==================================== HAREM ====================================
@commands.check(chan)
@bot.command(aliases=['h','mm','mmr','mms'])
async def harem(ctx, m: discord.Member = None):
    if m == None:
        m = ctx.author
    guild, user = check_setup(ctx.guild.id, m.id)
    
    my_harem = ""
    for wid in bdd[guild]['users'][user]['waifus']:
        waifu = Waifu(wid, guild=guild, bdd=bdd)
        if my_harem == "":
            my_harem += f"➡️ **{waifu.name} (N°{waifu.id})**\n"
        else:
            my_harem += f"{waifu.name} (N°{waifu.id})\n"
    embed = discord.Embed(title=f"Harem de {m.display_name}", description=my_harem, colour=discord.Colour(0x844BC2))
    if my_harem != "":
        embed.set_thumbnail(url=f"https://www.thiswaifudoesnotexist.net/example-{bdd[guild]['users'][user]['waifus'][0]}.jpg")
    embed.set_footer(text="Powered by: thiswaifudoesnotexist.net")
    msg = await ctx.send(embed=embed)

    emotes = ["👈","👉"]
    for e in emotes:
        await msg.add_reaction(e)
    timeout = False
    n = 0
    while timeout == False:
        def check(reaction, user):
            return reaction.message.id == msg.id and user != bot.user and reaction.emoji in emotes
        try:
            reaction, reacter = await bot.wait_for('reaction_add', timeout=60.0, check=check)
        except asyncio.TimeoutError:
            timeout = True
            await msg.clear_reactions()
        else:
            if reaction.emoji == emotes[0]:
                n -= 1
            else:
                n += 1
            n = n % len(bdd[guild]['users'][user]['waifus'])
            my_harem = my_harem.replace("➡️ ", "").replace("**", "").split("\n")
            my_harem[n] = "➡️ **"+my_harem[n]+"**"
            my_harem = "\n".join(my_harem)
            embed = discord.Embed(title=f"Harem de {m.display_name}", description=my_harem, colour=discord.Colour(0x844BC2))
            embed.set_thumbnail(url=f"https://www.thiswaifudoesnotexist.net/example-{bdd[guild]['users'][user]['waifus'][n]}.jpg")
            embed.set_footer(text="Powered by: thiswaifudoesnotexist.net")
            await msg.edit(embed=embed)

# ==================================== ROLL ====================================
@commands.check(chan)
@bot.command(aliases=['w'])
async def waifu(ctx):
    guild, user = check_setup(ctx.guild.id, ctx.author.id)
    roll = can_roll(guild, user)
    if roll['roll']:
        bdd[guild]['users'][user]['last_roll'] = get_roll_time()
        bdd[guild]['users'][user]['rolls'] -= 1

        waifu = Waifu(random.randint(0, 100000), guild=guild, bdd=bdd)
        while waifu.owned == True:
            waifu = Waifu(random.randint(0, 100000), guild=guild, bdd=bdd)
        embed = discord.Embed(title=f"{waifu.name}", description=f"Generated waifu N°{waifu.id}", colour=discord.Colour(0x33DF33))
        embed.set_image(url=f"https://www.thiswaifudoesnotexist.net/example-{waifu.id}.jpg")
        embed.set_footer(text="Powered by: thiswaifudoesnotexist.net")
        msg = await ctx.send(embed=embed)
        hearts = ["❤️", "💓", "💗", "💘", "💝", "💞", "💖"]
        await msg.add_reaction(random.choice(hearts))

        def check(reaction, user):
            return reaction.message.id == msg.id and user != bot.user and reaction.emoji in hearts
        timeout = False
        while timeout == False:
            try:
                reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)
            except asyncio.TimeoutError:
                timeout = True
                await msg.clear_reactions()
            else:
                claim = add_waifu(waifu.id, str(ctx.guild.id), str(user.id))
                if claim['claim']:
                    await ctx.send(f"{user.mention}, Vous avez claim {waifu.name} !")
                else:
                    await ctx.send(f"{user.mention}, Vous avez déjà claim cette heure !")
    else:
        await ctx.send(f"{ctx.author.mention}, Vous avez déjà roll 10 fois ! Veuillez attendre {roll['wait']} minute(s) pour roll à nouveau.")
    
# ==================================== FIRST WAIFU ====================================
@commands.check(chan)
@bot.command(aliases=['fm','fw','firstwaifu'])
async def firstmarry(ctx, name):
    guild, user = check_setup(ctx.guild.id, ctx.author.id)
    try:
        waifu = Waifu(name, guild=guild, bdd=bdd)
    except:
        await ctx.send("Cette waifu n'existe pas... Ou est tombée dans les profondeurs des abysses 🤔")
    else:
        if waifu.owner == ctx.author.id:
            index = bdd[guild]['users'][user]['waifus'].index(waifu.id)
            bdd[guild]['users'][user]['waifus'].insert(0, bdd[guild]['users'][user]['waifus'].pop(index))
            await ctx.send(f"{waifu.name} a été déplacée en haut de votre liste !")
        else:
            await ctx.send("Cette waifu ne t'appartient pas... 🤔")
        
# ==================================== GIVE ====================================
@commands.check(chan)
@bot.command(aliases=['g'])
async def give(ctx, m: discord.Member=None, *, name=''):
    guild, user = check_setup(ctx.guild.id, ctx.author.id)
    check_setup(ctx.guild.id, m.id)

    if m != None and m.id != ctx.author.id:
        try:
            waifu = Waifu(name, guild=guild, bdd=bdd)
        except:
            await ctx.send("Cette waifu n'existe pas... Ou est tombée dans les profondeurs des abysses 🤔")
        else:
            msg = await ctx.send(f"{ctx.author.mention}, vous voulez donner {waifu.name} à {m.mention}, hmm ? Réagissez dans les 20 secondes avec ✅ pour valider.")
            await msg.add_reaction("✅")
            def check(reaction, author):
                return reaction.message.id == msg.id and author.id == ctx.author.id and reaction.emoji == "✅"
            try:
                await bot.wait_for('reaction_add', timeout=20.0, check=check)
            except asyncio.TimeoutError:
                await msg.clear_reactions()
            else:
                if waifu.id in bdd[guild]['users'][user]['waifus']:
                    bdd[guild]['users'][user]['waifus'].remove(waifu.id)
                    bdd[guild]['users'][str(m.id)]['waifus'].append(waifu.id)
                    await ctx.send("Hop-là ! \\o/")
                else:
                    await ctx.send("Hé... Tu tenterais pas de dupliquer ta waifu par hasard ? 🤔 Je peux te la retirer définitivement si tu veux jouer !")
    else:
        await ctx.send("Syntaxe :\n,give @Utilisateur Waifu")

# ==================================== DIVORCE ====================================
@commands.check(chan)
@bot.command(aliases=['kick','del','remove'])
async def divorce(ctx, *, name=''):
    guild, user = check_setup(ctx.guild.id, ctx.author.id)
    try:
        waifu = Waifu(name, guild=guild, bdd=bdd)
    except:
        await ctx.send("Cette waifu n'existe pas... Ou est tombée dans les profondeurs des abysses 🤔")
    else:
        if waifu.owner == ctx.author.id:
            msg = await ctx.send(f"{ctx.author.mention}, vous voulez vraiment abandonner {waifu.name} sur le bord de la route ? Réagissez dans les 20 secondes avec ✅ pour valider.")
            await msg.add_reaction("✅")
            def check(reaction, author):
                return reaction.message.id == msg.id and author.id == ctx.author.id and reaction.emoji == "✅"
            try:
                await bot.wait_for('reaction_add', timeout=20.0, check=check)
            except asyncio.TimeoutError:
                await msg.clear_reactions()
            else:
                if waifu.id in bdd[guild]['users'][user]['waifus']:
                    bdd[guild]['users'][user]['waifus'].remove(waifu.id)
                    bdd[guild]['waifus'].remove(waifu.id)
                    await ctx.send(random.choice([f"{ctx.author.mention} : Adieu {waifu.name} !", f"{ctx.author.mention} : Célibataire et libre comme l'air !", f"{waifu.name} : *Je ne t'ai jamais aimé de toute façon {ctx.author.mention}...*"]))
                else:
                    await ctx.send("Hein ? 🤔 Tu l'as déjà abandonnée sur le bord de la route, en fait ?")
        else:
            await ctx.send("Hein ? 🤔 Tu es déjà célibataire et libre comme l'air !")
async def save_db():
    await bot.wait_until_ready()
    while True:
        f = open('db/data.json', 'w', encoding='utf-8')
        f.write(json.dumps(bdd, indent=4, separators=(',', ': ')))
        f.close()
        await asyncio.sleep(5)

if os.path.exists("access.json"):
    try:
        f = open("access.json", "r")
        access = json.loads(f.read())
        f.close()
    except:
        print("Error reading access.json")
    else:
        if access['token'] != "":
            bot.loop.create_task(save_db())
            try:
                bot.run(access['token'])
                print("Launching bot...")
            except:
                print("Wrong token in access?hsin")
        else:
            print("Token in access.json is empty")
else:
    print("File access.json is missing")
