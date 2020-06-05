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

os.chdir(os.path.dirname(os.path.abspath(__file__)))
# Database
if not os.path.exists("db"):
    os.mkdir("db")
if not os.path.exists("db/data.json"):
    bdd = {}
else:
    f = open("db/data.json", "r")
    bdd = json.loads(f.read())
    f.close()
# Translation
translations = {}
for trf in glob("translation/*.json"):
    f = open(trf, "r", encoding="utf-8")
    name = trf.split(".json")[0][-5:]
    translations[name] = json.loads(f.read())
    f.close()
# In procedure check
in_procedure = {}

bot = commands.Bot(command_prefix=[','])

async def chan(ctx):
    if ctx.channel.topic:
        return ctx.channel.topic.lower().find('ai waifu') >= 0
    return False
async def is_admin(ctx):
    return ctx.author.guild_permissions.administrator
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
def start_procedure(user):
    user = str(user)
    if user not in in_procedure:
        in_procedure[user] = False
    if in_procedure[user] == True:
        return False
    in_procedure[user] = True
    return True
def stop_procedure(user):
    in_procedure[str(user)] = False
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
async def show_list(ctx, title, waifu_list, message=""):
    my_harem = []
    i = 0
    pos = ""
    if len(waifu_list) == 0:
        embed = discord.Embed(title=title, description=f"Page 0/0\n\n... Célibataire et libre comme l'air.", colour=discord.Colour(0x844BC2))
        embed.set_footer(text=tr("footer", ctx.guild.id))
        msg = await ctx.send(message, embed=embed)
        return False
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
    embed.set_footer(text=tr("footer", ctx.guild.id))
    msg = await ctx.send(message, embed=embed)

    pages = ["👈","👉"]
    emotes = ["⬆️","⬇️"]
    for p in pages:
        if i > 9:
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
            embed.set_footer(text=tr("footer", ctx.guild.id))
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
            embed.set_footer(icon_url=m.avatar_url, text=f"Appartient à {m.display_name}\n"+tr("footer", ctx.guild.id))
        else:
            embed.set_footer(text=tr("footer", ctx.guild.id))
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
        embed.set_footer(text=tr("footer", ctx.guild.id))
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
                    embed.set_footer(icon_url=user.avatar_url, text=f"Appartient à {user.display_name}\n"+tr("footer", ctx.guild.id))
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
            if start_procedure(user):
                msg = await ctx.send(f"{ctx.author.mention}, vous voulez donner {waifu.name} à {m.mention}, hmm ? Réagissez dans les 20 secondes avec ✅ pour valider.")
                await msg.add_reaction("✅")
                def check(reaction, author):
                    return reaction.message.id == msg.id and author.id == ctx.author.id and reaction.emoji == "✅"
                try:
                    await bot.wait_for('reaction_add', timeout=20.0, check=check)
                except asyncio.TimeoutError:
                    await msg.clear_reactions()
                    stop_procedure(user)
                else:
                    bdd[guild]['users'][user]['waifus'].remove(waifu.id)
                    bdd[guild]['users'][str(m.id)]['waifus'].append(waifu.id)
                    await ctx.send("Hop-là ! \\o/")
                    stop_procedure(user)
            else:
                await ctx.send("Veuillez confirmer ou attendre la fin de tous vos dons/échanges/divorces en cours pour continuer.")
    else:
        await ctx.send("Syntaxe :\n,give @Utilisateur Ma_Waifu")

# ==================================== ECHANGE ====================================
@commands.check(chan)
@bot.command(aliases=['e'])
async def exchange(ctx, m: discord.Member, *, name=''):
    guild, user = check_setup(ctx.guild.id, ctx.author.id)
    check_setup(ctx.guild.id, m.id)

    if m != None and m.id != ctx.author.id:
        try:
            waifu = Waifu(name, guild=guild, bdd=bdd)
        except:
            await ctx.send(tr("waifu_404", guild))
        else:
            if waifu.owner == ctx.author.id:
                await ctx.send("Fonctionnalité en cours de développement")
                # # Il faut que les 2 soient prêts
                # u1 = start_procedure(user)
                # if u1:
                #     u2 = start_procedure(m.id)
                #     if not u2:
                #         stop_procedure(user) # Finalement, u1 n'a pas lancé de procédure
                # if u1 and u2:
                #     await show_list(ctx, f"Harem de {m.display_name}", bdd[guild]['users'][str(m.id)]['waifus'], f"{m.mention}, {ctx.author.display_name} vous propose d'échanger {waifu.name}, de son harem... Qu'avez-vous à proposer ?")
                #     def check(message):
                #         return message.content == "✅"
                #     try:
                #         await bot.wait_for('message', timeout=20.0, check=check)
                #     except asyncio.TimeoutError:
                #         stop_procedure(user)
                #         stop_procedure(m.id)
                #     else:
                #         stop_procedure(user)
                #         stop_procedure(m.id)
                # else:
                #     await ctx.send("Veuillez confirmer ou attendre la fin de tous vos dons/échanges/divorces en cours pour continuer.")
            else:
                await ctx.send(tr("waifu_notowned", guild))
    else:
        await ctx.send("Syntaxe :\n,exchange @Utilisateur Ma_Waifu")
@exchange.error
async def exchange_error(ctx, error):
    print(error)
    await ctx.send("Erreur. Syntaxe :\n,exchange @Utilisateur Ma_Waifu")

# ==================================== DIVORCE ====================================
@commands.check(chan)
@bot.command(aliases=['del','rem','remove'])
async def divorce(ctx, *, name=''):
    guild, user = check_setup(ctx.guild.id, ctx.author.id)
    try:
        waifu = Waifu(name, guild=guild, bdd=bdd)
    except:
        await ctx.send(tr("waifu_404", guild))
    else:
        if waifu.owner == ctx.author.id:
            if start_procedure(user):
                msg = await ctx.send(f"{ctx.author.mention}, vous voulez vraiment abandonner {waifu.name} sur le bord de la route ? Réagissez dans les 20 secondes avec ✅ pour valider.")
                await msg.add_reaction("✅")
                def check(reaction, author):
                    return reaction.message.id == msg.id and author.id == ctx.author.id and reaction.emoji == "✅"
                try:
                    await bot.wait_for('reaction_add', timeout=20.0, check=check)
                except asyncio.TimeoutError:
                    await msg.clear_reactions()
                    stop_procedure(user)
                else:
                    bdd[guild]['users'][user]['waifus'].remove(waifu.id)
                    bdd[guild]['waifus'].remove(waifu.id)
                    await ctx.send(random.choice([f"{ctx.author.mention} : Adieu {waifu.name} !", f"{ctx.author.mention} : Célibataire et libre comme l'air !", f"{waifu.name} : *Je ne t'ai jamais aimé de toute façon {ctx.author.mention}...*"]))
                    stop_procedure(user)
            else:
                await ctx.send("Veuillez confirmer ou attendre la fin de tous vos dons/échanges/divorces en cours pour continuer.")
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
bot.remove_command("help")
@commands.check(chan)
@bot.command()
async def help(ctx):
    embed = discord.Embed(title="Aide d'AI Waifu", colour=discord.Colour(0x844BC2))
    commands = ['w', 'r', 'divorce', 'give', 'im <waifu>', 'harem [<user>]', 'fw <waifu>', 'top', 'invite', 'lang <lang>']
    for c in commands:
        name = c.split(" ")[0]
        embed.add_field(name=f"`,{c}`", value=tr(f"help_{name}", ctx.guild.id), inline=False)
    embed.set_footer(text=tr("footer", ctx.guild.id))
    await ctx.send(embed=embed)
@commands.check(chan)
@commands.check(is_admin)
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

if os.path.exists("db/access.json"):
    try:
        f = open("db/access.json", "r")
        access = json.loads(f.read())
        f.close()
    except:
        print("Error reading db/access.json")
    else:
        if access['token'] != "":
            bot.loop.create_task(save_db())
            try:
                bot.run(access['token'])
                print("Launching bot...")
            except:
                print("Wrong token in db/access.json")
        else:
            print("Token in db/access.json is empty")
else:
    print("File db/access.json is missing")
