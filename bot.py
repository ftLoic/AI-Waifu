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
from glob import glob

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
translations = {}
for trf in glob("translation/*.json"):
    f = open(trf, "r", encoding="utf-8")
    name = trf.split(".json")[0][-5:]
    translations[name] = json.loads(f.read())
    f.close()

bot = commands.Bot(command_prefix=[','])

async def chan(ctx):
    if ctx.channel.topic:
        return ctx.channel.topic.lower().find('ia waifu') >= 0
    return False
def tr(message, guild):
    guild = check_setup_guild(guild)
    if "lang" not in bdd[guild]:
        bdd[guild]['lang'] = "en-us"
    lang = bdd[guild]['lang']
    if lang not in translations:
        bdd[guild]['lang'] = lang = "en-us"
    return translations[lang][message]
def check_setup_guild(guild):
    guild = str(guild)
    if guild not in bdd:
        bdd[guild] = {'waifus':[],'users':{},'lang':'en-us'}
    return guild
def check_setup(guild, user):
    guild = check_setup_guild(guild)
    user  = str(user)
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
async def show_list(ctx, title, waifu_list):
    my_harem = []
    i = 0
    pos = ""
    for wid in waifu_list:
        page = i//10
        waifu = Waifu(wid, guild=str(ctx.guild.id), bdd=bdd)
        if i == 0:
            first = wid
        if title == "Top Waifu":
            if i == 0:
                best = waifu_list[wid]+1
            pos = f"#{best-waifu_list[wid]} - "
        if len(my_harem) == page:
            my_harem.append(f"➡️ {pos}**{waifu.name} (N°{waifu.id})**\n")
        else:
            my_harem[page] += f"{pos}{waifu.name} (N°{waifu.id})\n".format(i, pos)
        i += 1
    page = 0
    embed = discord.Embed(title=title, description=f"Page {page+1}/{len(my_harem)}\n\n{my_harem[0]}", colour=discord.Colour(0x844BC2))
    if i > 0:
        embed.set_thumbnail(url=f"https://www.thiswaifudoesnotexist.net/example-{first}.jpg")
    embed.set_footer(text="Powered by: thiswaifudoesnotexist.net")
    msg = await ctx.send(embed=embed)

    pages = ["👈","👉"]
    emotes = ["⬆️","⬇️"]
    for p in pages:
        await msg.add_reaction(p)
        if p == "👈":
            for e in emotes:
                await msg.add_reaction(e)
    timeout = False
    n = 0
    while timeout == False:
        def check(reaction, user):
            return reaction.message.id == msg.id and user != bot.user and (reaction.emoji in emotes or reaction.emoji in pages)
        try:
            reaction, reacter = await bot.wait_for('reaction_add', timeout=120.0, check=check)
        except asyncio.TimeoutError:
            timeout = True
            await msg.clear_reactions()
        else:
            if reaction.emoji in pages: # Page
                if reaction.emoji == pages[0]:
                    np = page - 1
                else:
                    np = page + 1
                page = np % len(my_harem)
                n = 0
            else: # Haut/bas
                if reaction.emoji == emotes[0]:
                    n -= 1
                else:
                    n += 1
            h = my_harem[page].replace("➡️ ", "").replace("**", "").split("\n")
            n = n % (len(h)-1)
            h[n] = "➡️ **"+h[n]+"**"
            waifu_n = h[n].split("°")[1][:-3]
            h = "\n".join(h)

            embed = discord.Embed(title=title, description=f"Page {page+1}/{len(my_harem)}\n\n{h}", colour=discord.Colour(0x844BC2))
            embed.set_thumbnail(url=f"https://www.thiswaifudoesnotexist.net/example-{waifu_n}.jpg")
            embed.set_footer(text="Powered by: thiswaifudoesnotexist.net")
            await msg.edit(embed=embed)

# ==================================== IMAGE ====================================
@commands.check(chan)
@bot.command(aliases=['i','im'])
async def img(ctx, *, name):
    try:
        waifu = Waifu(name, guild=ctx.guild.id, bdd=bdd)
    except:
        await ctx.send(tr("waifu_404", ctx.guild.id))
    else:
        embed = discord.Embed(title=f"{waifu.name}", description=f"Waifu générée N°{waifu.id}", colour=discord.Colour(0x844BC2))
        embed.set_image(url=f"https://www.thiswaifudoesnotexist.net/example-{waifu.id}.jpg")
        if waifu.owned:
            m = ctx.guild.get_member(waifu.owner)
            embed.set_footer(icon_url=m.avatar_url, text=f"Appartient à {m.display_name}\nPowered by: thiswaifudoesnotexist.net")
        else:
            embed.set_footer(text=f"Powered by: thiswaifudoesnotexist.net")
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
    msg = f"vous avez encore {bdd[guild]['users'][user]['rolls']} roll(s).\n"
    claim = can_claim(guild, user)
    if claim['claim']:
        msg += "Vous pouvez encore claim cette heure."
    else:
        msg += "Vous ne pouvez plus claim cette heure."
    await ctx.send(f"{m.mention}, {msg}")

# ==================================== HAREM ====================================
@commands.check(chan)
@bot.command(aliases=['h','mm','mmr','mms'])
async def harem(ctx, m: discord.Member = None):
    if m == None:
        m = ctx.author
    guild, user = check_setup(ctx.guild.id, m.id)
    await show_list(ctx, f"Harem de {m.display_name}", bdd[guild]['users'][user]['waifus'])

# ==================================== TOP ====================================
@commands.check(chan)
@bot.command(aliases=['best'])
async def top(ctx):
    guild, user = check_setup(ctx.guild.id, ctx.author.id)
    _top = {}
    for guild in bdd:
        for waifu in bdd[guild]['waifus']:
            if waifu not in _top:
                _top[waifu] = 0
            _top[waifu] += 1
    _top = {k: v for k, v in sorted(_top.items(), key=lambda item: item[1], reverse=True)}
    await show_list(ctx, "Top Waifu", _top)

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
        embed = discord.Embed(title=f"{waifu.name}", description=f"Waifu générée N°{waifu.id}", colour=discord.Colour(0x33DF33))
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
                    timeout = True
                    await ctx.send(f"{user.mention}, vous avez claim {waifu.name} !")

                    embed = discord.Embed(title=f"{waifu.name}", description=f"Waifu générée N°{waifu.id}", colour=discord.Colour(0xDF3333))
                    embed.set_image(url=f"https://www.thiswaifudoesnotexist.net/example-{waifu.id}.jpg")
                    embed.set_footer(icon_url=user.avatar_url, text=f"Appartient à {user.display_name}\nPowered by: thiswaifudoesnotexist.net")
                    await msg.edit(embed=embed)
                else:
                    await ctx.send(f"{user.mention}, vous avez déjà claim cette heure !")
    else:
        await ctx.send(f"{ctx.author.mention}, vous avez déjà roll 10 fois ! Veuillez attendre {roll['wait']} minute(s) pour roll à nouveau.")
    
# ==================================== FIRST WAIFU ====================================
@commands.check(chan)
@bot.command(aliases=['fm','fw','firstwaifu'])
async def firstmarry(ctx, name):
    guild, user = check_setup(ctx.guild.id, ctx.author.id)
    try:
        waifu = Waifu(name, guild=guild, bdd=bdd)
    except:
        await ctx.send(tr("waifu_404", guild))
    else:
        if waifu.owner == ctx.author.id:
            index = bdd[guild]['users'][user]['waifus'].index(waifu.id)
            bdd[guild]['users'][user]['waifus'].insert(0, bdd[guild]['users'][user]['waifus'].pop(index))
            await ctx.send(f"{waifu.name} a été déplacée en haut de votre liste !")
        else:
            await ctx.send(tr("waifu_notowned", guild))
        
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
            await ctx.send(tr("waifu_404", guild))
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
                    await ctx.send("Ben... Elle s'est volatilisée ? 🤔")
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
        await ctx.send(tr("waifu_404", guild))
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
            await ctx.send(tr("waifu_notowned", guild))

# ==================================== OTHER ====================================
@commands.check(chan)
@bot.command()
async def ping(ctx):
    await ctx.send(f"Pong! <:kanna_open:685809301201092652> {round(bot.latency*1000)}ms")
@commands.check(chan)
@bot.command()
async def invite(ctx):
    await ctx.send(f"Tu peux m'inviter sur ton serveur avec ce lien : \nhttps://discordapp.com/oauth2/authorize?client_id=712770357844508822&scope=bot&permissions=322624")
@commands.check(chan)
@commands.is_owner()
@bot.command(aliases=['lang','langage','lg'])
async def language(ctx, new_lang: str):
    new_lang = new_lang.lower().strip()
    if new_lang in translations:
        bdd[str(ctx.guild.id)]['lang'] = new_lang
        await ctx.send(tr("language_new", ctx.guild.id))
    else:
        await ctx.send(tr("language_404", ctx.guild.id))

# ================================================================================
# ==================================== SYSTEM ====================================
async def save_db():
    await bot.wait_until_ready()
    while True:
        f = open("db/data.json", "w", encoding="utf-8")
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
                print("Wrong token in access.json")
        else:
            print("Token in access.json is empty")
else:
    print("File access.json is missing")
