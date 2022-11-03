import disnake
import os
import random
import re
import json
from disnake.ext import commands
from enum import Enum

TOKEN = os.environ['BOT_TOKEN']

intents = disnake.Intents.all()
intents.members = True

muzzled = {}
muzzlers = {}
muzzled_by = {}

bot = commands.InteractionBot(
	command_prefix='',
	intents=intents
)

class ApologyView(disnake.ui.View):
	def __init__(self):
		super().__init__(timeout=None)

	@disnake.ui.button(label="I'm sorry. 🥺", style=disnake.ButtonStyle.primary)
	async def a_button(
        self, button: disnake.ui.Button, interaction: disnake.MessageInteraction
    ):
		if interaction.author.mention in interaction.message.content:
			if not has_emoji(interaction.message,'⭐'):
				apology_accepted = flavor('accepted',interaction.author,'apology')
				await star_emoji(interaction.message)
				await interaction.response.send_message(content=apology_accepted)
			else:
				con = flavor('alreadyapologized',interaction.author,'apology')
				await interaction.response.send_message(content=con,ephemeral=True)	
		else:
			con = flavor('notyourswear',interaction.author,'apology', interaction.author.mention)
			await interaction.response.send_message(content=con,ephemeral=True)

intro_channels = {}
guild_role_colors = {}

@bot.user_command(description="Display this user's introduction.")
async def Introduction(inter):
	print(intro_channels)
	#Locate this server's introduction channel if we don't have it cached.
	guild_id = inter.guild.id
	if guild_id in intro_channels:
		channel_id = intro_channels[guild_id]
	else:
		channel_id = -1
		for channel in inter.guild.channels:
			if channel.name == 'introduction':
				channel_id = channel.id
				break
		if channel_id == -1:
			await inter.response.send_message(content="Server's introduction channel could not be found.",ephemeral=True)
			return
		else:
			intro_channels[guild_id] = channel_id

	user = inter.target
	guild = inter.guild
	channel = guild.get_channel_or_thread(channel_id)
	
	role_colors = {}
	if guild_id in guild_role_colors:
		role_colors = guild_role_colors[guild_id]
	else:
		for role in guild.roles:
			role_colors[role.name] = role.color
		guild_role_colors[guild_id] = role_colors

	history = channel.history(limit=500)
	last_message = -1
	extra = False
	found = False

	async for message in history:
		if found:
			if message.author.id == user.id:
				last_message = message
				extra = True
			else:
				break
		elif message.author.id == user.id:
			last_message = message
			found = True

	e = disnake.Embed()	
	if last_message == -1:
		con=""
		e.description=f"No introduction found for {user.mention}."
	else:
		con=""
		e.description = user.mention+"\n"+last_message.content
		if extra:			
			e.description += f"\r\r*This introduction is composed of multiple messages.* [View the first message]({last_message.jump_url})."
		if hasRole(user,'Sub'):
			e.color=role_colors['Sub']
		elif hasRole(user,'Switch'):
			e.color=role_colors['Switch']
		elif hasRole(user,'Dom'):
			e.color=role_colors['Dom']

	await inter.response.send_message(embed=e,content=con,ephemeral=True)

muzzle_flavor_text = json.load(open('flavor.json', encoding='utf-8'))
kink_list = json.load(open('bumps.json', encoding='utf-8'))

muzzle_options = list(muzzle_flavor_text.keys())
muzzle_options.remove("swearing")
muzzle_options.remove("apology")
MuzzleType = commands.option_enum(muzzle_options)

@bot.slash_command(description="Release ALL users in ALL chats.")
async def release_all(inter):
	await start_release(inter.author,inter=inter,release_all=True)

@bot.slash_command(description="Release a user")
async def release(inter,
	target:disnake.User = commands.Param(default="",description="Who are you releasing from their muzzle?")
	):
		override = False
		if hasRole(inter.author,'Staff'):
			override = True
		if target == "":
			await start_release(inter.author,inter=inter,override=override)
		else:
			await start_release(inter.author,target=target.mention,inter=inter,override=override)
@bot.slash_command(description="Muzzle a user.")
async def muzzle(inter, 
		muzzle_type: MuzzleType = commands.Param(description="Which muzzle is being used for this command?"), 
		target:disnake.User = commands.Param(description="Who are you targetting with this muzzle?"), 
		words:str = commands.Param(default="",description="List of words the target is allowed to say. Separate these with /'s.")
	):		
		words = words.split('/')
		await start_muzzle(muzzle_type,inter.channel,target, words,inter.author, inter=inter)

swears = [	
	r"b+a+s+t+a+r+d+",
	r"\ba+ss+(?:hole)?\b",
	r"\ba+ss+e+s\b",
	r"\ba+r+s+e+s?(?:hole)?\b",
	r"\bb+a+d+a+ss+",	
	"b+i+t+c+h+",
	"da+m+n+",
	"f+u+c+k+",
	r"^hell([^o]|\b)|[^s]h+el+l([^o]|\b)",
	"s+h+i+t+",
	"w+h+o+r+e",
	"c+u+n+t+",
	"p+i+s+s",
	"wtf+",
	"gdi+",
	"lmfa+o+",
	"fml+",
	"s+l+u+t+",
	r"([^slue]|\b)t+w+a+t+",
	r"\bff+s+"
]

channel = ''
emojis = '🥺😀😃🙂🙃😊😇☺😋😛😜🤭🤐😐😑😶😏😳😨😭😖😣😤😡😈❤😠🤤💖❤🧡💛💚💙💜🤎🖤🤍♥💘💝💗'
safewords = '🔴🟡🟢'
stop_sign = '🛑'

escape_regex = r'[\’\'\.\!\?\,\(\)\-\s\>\<\~\\\^\:3]'

simple_text = []

def loadSimpleText():
	with open('simple.txt','r') as f:
		text = f.read().lower()
		return text.split('\n')

simple_text = loadSimpleText()
simple_text.sort(key = len)
simple_text.reverse()

def replacePronouns(s,user):
	pronouns = pronoun(user)
	he = pronouns['he']
	heis = pronouns['he is']
	hes = pronouns['hes']
	his = pronouns['his']
	him = pronouns['him']
	
	syntax = {'#is':heis, '#s':hes, '%':his, '!!':him, '#':he}

	for code in syntax:
		text = syntax[code]
		s = s.replace('+'+code,text)
		s = s.replace(code,text.lower())
	
	#Remove s's conditionally because english grammar sucks.	
	if he == 'They':
		s = s.replace('/s/','')
	else:
		s = s.replace('/s/','s')

	return s

async def sendBumpMessage(user, channel):

	roles = []
	for role in user.roles:
		if str(role) in kink_list:
			roles.append(str(role))

	random.shuffle(roles)

	s = ''

	for role in roles:
		flav = kink_list[role]
		if len(flav) > 0:
			s = random.choice(flav)
			break

	if len(s) == 0 or hasRole(user,'Dom'):
		s = "Thank you for bumping the server, @!"
	print('Bump message for',user.mention)
		
	#Special thing for Liz
	if (user.mention == "<@547728057264242688>" or user.mention == "<@!547728057264242688>"):
		s = "Hey everyone, @ li- oh, gosh, it's you, I'm so sorry, have a nice day, Miss. 😱"		

	#Special thing for King
	if (user.mention == "<@504712293750145024>" or user.mention == "<@!504712293750145024>"):
		s = "Thank you for taking the time out of your busy day to bump us, Mister @!"		

	s = s.replace('@',user.mention)
	
	split = s.split('|')
	if len(split) > 1:
		msg = split[0]
		eurl = split[1]
		e = disnake.Embed()
		e.set_image(url=eurl)
		s = replacePronouns(s,user)
		await channel.send(msg,embed=e)
	else:
		s = replacePronouns(s,user)
		await channel.send(s)

async def deny_emoji(msg):
	await msg.add_reaction('🛑')

async def star_emoji(msg):
	await msg.add_reaction('⭐')

async def soap_emoji(msg):
	await msg.add_reaction('🧼')

def has_emoji(msg,emoji):
	msg = disnake.utils.get(bot.cached_messages, id=msg.id)

	for react in msg.reactions:
		print(react)
		if react.emoji == emoji:
			return True
	return False

def check_swear(txt):
	for swear in swears:
		if not re.search(swear, txt) == None:
			return True
	return False

def remember_muzzle(user, author):
	global muzzled_by
	global muzzlers

	muzzled_by[user.mention] = author.mention															
	if author.mention in muzzlers:												
		muzzlers[author.mention].append(user.mention)													
	else:
		muzzlers[author.mention] = [user.mention]

def flavor(t,user,f, muzzler=-1, msg="", failed=""):
	if muzzler == -1:
		muzzler = user.mention
	print('flavor',t,user,f)

	flav = muzzle_flavor_text[f]
	if t == "subtry":
		s = flav[t]
	else:
		s = random.choice(flav[t])
	s=s.replace('@',user.mention)
	s=s.replace('[muzzler]',muzzler)
	s=s.replace("[message]",msg)
	s=s.replace("[disallowed]",failed)

	return replacePronouns(s,user)

async def do_release(user,channel, silent=False, inter=None):
	global muzzlers	
	muzzler = muzzled_by[user.mention]
	if not silent:
		await speak(flavor('end',user,muzzled[user.mention]['flavor'], muzzler), channel,inter=inter)	
	muzzlers[muzzler].remove(user.mention)
	del muzzled[user.mention]
	del muzzled_by[user.mention]
	if len(muzzlers[muzzler]) == 0:	
		del muzzlers[muzzler]
	print(muzzlers)

async def start_release(author,target=None,message=None,inter=None,override=False, release_all=False):
	global allowed_channels
	global muzzlers
	global muzzled

	channel = message.channel if message != None else inter.channel

	if hasRole(author, 'Privileges Revoked'):
		await speak('Sorry, '+author.mention + '. You\'ve had muzzling privileges revoked.', channel, inter)
	elif hasRole(author,'Sub') and not override:
		if not str(channel) in allowed_channels:
			await deny_emoji(message)
		else:
			await speak("Nope. Be a good subby and leave that to the Doms and Switches.", channel,inter)
	elif author.mention in muzzled: #No jailbreaks!		
		flav = muzzled[author.mention]['flavor']
		verbed = muzzle_flavor_text[flav]['verbed']
		if author.mention in muzzlers and author.mention in muzzlers[author.mention]: # Are they stuck in their own muzzle?
			await speak(f"Nope! If you're silly enough to be {verbed} by yourself, you'll have to find someone else to rescue you.",inter)
		else:
			await speak(f"Nope! Ask the person that {verbed} you to release you.",inter)
	elif hasRole(author,'Dom') or hasRole(author,'Switch') or override:
		if release_all:
			await speak("Releasing all muzzled users.",channel,inter)
			muzzled = {}
			muzzlers = {}
			muzzled_by = {}
		elif target == None:
			# Check if anyone is muzzled under this user's name.
			if author.mention in muzzlers:			
				muzzled_persons = muzzlers[author.mention]				
				last_muzzled = muzzlers[author.mention][len(muzzled_persons)-1]
				# If this is a testrelease, make sure it's being used on a test muzzle.					
				if override and not (muzzled[last_muzzled]['flavor'] == 'testmuzzle') and not (hasRole(author,'Dom') or hasRole(author,'Switch')):
					await speak("This command can only be used to release a user in a test-muzzle.", channel, inter)
				else:
					await do_release(getUser(last_muzzled,channel.members),channel,inter=inter)
			else:
				#Nope. We don't know who they mean.				
				await speak('You need to choose a user to unmuzzle!', channel,inter)		
		else:
			members = channel.members				
			user = getUser(target,members)
			if user != False:
				if user.mention in muzzled:
					if override and not (muzzled[user.mention]['flavor'] == 'testmuzzle'):
						await speak("This command can only be used to release a user in a test-muzzle.", channel,inter)
					else:
						await do_release(user,channel,inter=inter)
				else:
					await speak("That person isn't restricted!", channel,inter)					
			else:
				await speak("Could not find user.", channel,inter)
	else:
		if not str(channel) in allowed_channels:
			await deny_emoji(message)
		else:
			await speak('You need a Switch or Dom role to use this command.', channel,inter)

async def start_muzzle(command, channel, target, words, muzzler, message=None,inter=None):
	author = message.author if message != None else inter.author
	if not str(channel) in allowed_channels:
		if not message == None:
			await deny_emoji(message)				
		elif not inter == None:
			await inter.response.send_message(content="Please move to an allowed chat to use muzzle features.",ephemeral=True)
		else:
			print("Muzzle failed in disallowed chat, but we can't react to the message or send an interaction.")
	else:
		if hasRole(muzzler, 'Privileges Revoked'):
			await speak('Sorry, '+muzzler.mention + '. You\'ve had muzzling privileges revoked.', channel, inter)
		elif author.mention in muzzled: #No jailbreaks!
			flav = muzzled[author.mention]['flavor']
			verbed = muzzle_flavor_text[flav]['verbed']		
			await speak(f"Nope! You can't do that while you are {verbed}.",inter)
		else:						
			if (command=="testmuzzle" and hasRole(muzzler,'Staff')) or ( (hasRole(muzzler,'Dom') or hasRole(muzzler,'Switch')) and not command=="testmuzzle" ):
				if target == False:
					await speak("Could not find user.", channel,inter)
				else:					
					members = channel.members
					user = getUser(target.mention,members)
					if user != False:
						if hasRole(user,'Dom'):
							he = replacePronouns("#",user)
							verbed = muzzle_flavor_text[command]['verbed']	
							await speak(f"{user.mention} is a dom! I don't think {he}'d appreciate being {verbed}.",channel,inter)						
						else:
							#Muzzle the user!
							if user.mention in muzzled:
								#Hotswap, silently unmuzzle first.
								await do_release(user,channel,True,inter)
							
							words = [i for i in words if i != ''] #Remove all blank entries
							print(words)

							allowed = words

							if len(allowed) == 0:
								#Use defaults
								allowed = muzzle_flavor_text[command]['defaults']							
								allowed_list = muzzle_flavor_text[command]['defaults']
								muzzled[user.mention] = {
									'allowed':allowed,
									'flavor':command
								}
							else:
								#Check for the simple list
								if '**simple**' in allowed:
									muzzled[user.mention] = {
										'allowed':simple_text,
										'flavor':command
									}
									allowed_list = ["Please see !simpletext for a complete list."]
								else:
									allowed = '///'.join(allowed)
									allowed = re.sub(escape_regex,'',allowed)
									allowed = allowed.lower().split('///')

									allowed_list = words
									#Muzzle the user!
									muzzled[user.mention] = {
										'allowed':allowed,
										'flavor':command
									}
							#Remember who muzzled them.
							remember_muzzle(user,muzzler)

							allowed_string = 'Allowed words:\n> ' + ', '.join(allowed_list)
							await speak(flavor('start',user,command, muzzler.mention), channel,inter)
							await speak(allowed_string, channel)
							#DM the person that was muzzled to inform them, provided they are a user and not a bot.
							if not user.bot:
								s = f"You were {muzzle_flavor_text[command]['verbed']} by {muzzler.mention} in `#{channel}`!"	
								await user.send(s+"\n"+allowed_string)						
					else:
						await speak("Could not find user.", channel)
			elif hasRole(muzzler,'Sub') or (command=="testmuzzle" and not hasRole(muzzler,'Staff')):			
				await speak(flavor('subtry',muzzler,command,muzzler.mention), channel, inter=inter)
			else:
				await speak('You need a Switch or Dom role to use this command.', channel)

allowed_channels = ['blush-chat','blush-chat-2','blush-chat-3','extreme-blush-chat','extreme-blush-chat-2','bot', 'rp-chat']	

async def muzzlemain(message):
	global muzzled
	global muzzlers
	global muzzled_by
	global allowed_channels

	if message.author == bot.user or message.author.bot:
		return	

	channel = message.channel
	author = message.author	

	#Check for swearing
	if hasRole(author,'Soap Bar'):
		msg = message.content.lower()		
		if check_swear(msg):
			#They SWORE. O: Naughty.
			await soap_emoji(message)
			if str(channel) in allowed_channels:						
				await channel.send(content=flavor('swear',author,'swearing'),view=ApologyView())

	if message.content == "!simpletext":
		await author.send("Here is a list of all the words you can say when restricted to simple language.\n>>> " + '\n'.join(simple_text))
		await speak('List sent to '+author.mention+'.',channel)
	elif author.mention in muzzled:
		#If message contains a safeword, or if it's in a disallowed channel, we don't touch it.
		if safewords[0] in message.content or safewords[1] in message.content or safewords[2] in message.content or (not str(channel) in allowed_channels):
			return
		else:			
			#Ensure the message uses only allowed words and punctuation			
			msg = message.content.lower()
			msg = re.sub(escape_regex,'',msg)

			allowed_words = muzzled[author.mention]['allowed']			
			allowed_words.sort(key = len)
			allowed_words.reverse()
			flav = muzzled[author.mention]['flavor']
			for word in muzzled[author.mention]['allowed']:
				if (word == '*'): # roleplaying
					msg = re.sub(r'\*.+?\*','',msg)
				else:
					msg = msg.replace(word,'')
			for emoji in emojis:
				msg = msg.replace(emoji,'')
			if (len(msg) != 0):
				print(allowed_words)
				print("Fail: " + msg, len(msg))
				#They spoke! How dare they!
				cnt = message.content
				await message.delete()		
				await speak(flavor('talk',author,flav, muzzled_by[message.author.mention], message.content, msg), channel)				
	elif message.content.startswith("!release") or message.content.startswith("!unmuzzle") or message.content.startswith('!testrelease') or message.content.startswith('!testunmuzzle'):
		command = message.content.split(' ')[0]
		arg = message.content[len(command)+1:]
		args = arg.split(' ')
		first = args[0]
		release_all = False
		if first == '':
			user = None
		elif first == 'all':
			user = None
		else:
			user = first

		if command == '!testrelease':
			override = True
		else:
			override = False

		#async def start_release(author,target=None,message=None,inter=None,override=False, release_all=False):
		await start_release(message.author,target=user,override=override,message=message,release_all=release_all)
	else:		
		flav_commands = muzzle_flavor_text.keys()

		for command in flav_commands:			
			if message.content.startswith('!'+command):
				
				arg = message.content[len(command)+2:]					
			
				args = arg.split(' ')
				first = args[0]				
				user = getUser(first,channel.members)				
				words = ' '.join(args[1:]).split('/')
				await start_muzzle(command, channel, user, words, author, message) 

@bot.event
async def on_message_edit(before,after):
	if str(before.author) == 'DISBOARD#2760':
		return
	else:
		await muzzlemain(after)

@bot.event
async def on_message(message):
	if str(message.author) == 'DISBOARD#2760':
		if len(message.embeds) == 1:
			if 'Bump done!' in message.embeds[0].description:	
				user = message.interaction.author.mention
				user = getUser(user, message.channel.members)
				await sendBumpMessage(user,message.channel)
	else:		
		await muzzlemain(message)

def pronoun(user):
	valid_pronouns = {
		'masc':hasRole(user,'He/Him'),
		'fem':hasRole(user,'She/Her'),
		'amb':hasRole(user,'They/Them'),
		'obj':hasRole(user,'It/Its')
	}
	#Choose masc/fem terms based on available roles
	options = list(filter(lambda typ: valid_pronouns[typ], valid_pronouns.keys()))
	
	if len(options) == 0:
		option = 'amb'
	else:
		option = random.choice(options)
	terms = {
		'masc':{'he':'He',  "hes":"He's",    'he is':'He is',    'his':'His',   'him':'Him'},
		'fem':{'he':'She',  "hes":"She's",   'he is':'She is',   'his':'Her',   'him':'Her'},
		'amb':{'he':'They', "hes":"They're", 'he is':'They are', 'his':'Their', 'him':'Them'},
		'obj':{'he':'It',   "hes":"It's",     'he is':'It is',    'his':'Its',   'him':'It'}
	}	
	return terms[option]

def getUser(user,members):
	user = user.replace('<@!','<@')

	for member in members:
		mem = member.mention.replace('<@!','<@')
		if mem == user:
			return member
	return False

def hasRole(user,role):
	roles = user.roles
	for r in roles:
		if str(r) == role:
			return True
	return False

async def speak(m, channel, inter=None):
	if inter == None:
		await channel.send(m)
	else:
		await inter.response.send_message(m)

print("Starting...")
bot.run(TOKEN)
