import disnake
import os
import random
import re
import json
from disnake.ext.commands import Bot

TOKEN = os.environ['BOT_TOKEN']

intents = disnake.Intents.all()
intents.members = True
client = Bot(intents=intents, command_prefix="/")

muzzled = {}
muzzlers = {}
muzzled_by = {}

muzzle_flavor_text = json.load(open('flavor.json'))
kink_list = json.load(open('bumps.json', encoding='utf-8'))

swears = [
	r"\ba+ss+(?:hole)?\b",
	r"\ba+ss+e+s\b",
	r"\ba+r+s+e+s?(?:hole)?\b",
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
	"s+l+u+t+"
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

	#Special thing for Liz
	if (user.mention == "<@547728057264242688>" or user.mention == "<@!547728057264242688>"):
		s = "Hey everyone, @ li- oh, gosh, it's you, I'm so sorry, have a nice day, Miss. 😱"		

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

async def soap_emoji(msg):
	await msg.add_reaction('🧼')

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


def flavor(t,user,f):
	print('flavor',t,user,f)	

	flav = muzzle_flavor_text[f]
	if t == "subtry":
		s = flav[t]
	else:
		s = random.choice(flav[t])
	s=s.replace('@',user.mention)
	return replacePronouns(s,user)

async def release(user,channel, silent=False):
	global muzzlers
	print(muzzlers)
	muzzler = muzzled_by[user.mention]
	if not silent:
		await speak(flavor('end',user,muzzled[user.mention]['flavor']), channel)	
	muzzlers[muzzler].remove(user.mention)
	del muzzled[user.mention]
	del muzzled_by[user.mention]
	if len(muzzlers[muzzler]) == 0:	
		del muzzlers[muzzler]
	print(muzzlers)

def get_allowed_words(mention):
	if mention in muzzled:
		muzzled_person = muzzled[mention]
		s = 'Allowed words:\n> '
		return s + ', '.join(muzzled_person['allowed'])
	else:
		return "You are not restricted!"

async def muzzlemain(message):
	global muzzled
	global muzzlers
	global muzzled_by

	if message.author == client.user or message.author.bot:
		return

	allowed_channels = ['blush-chat','blush-chat-2','blush-chat-3','extreme-blush-chat','extreme-blush-chat-2','bot', 'rp-chat']	

	channel = message.channel
	author = message.author

	#Check for swearing
	if hasRole(author,'Soap Bar'):
		msg = message.content.lower()		
		if check_swear(msg):
			#They SWORE. O: Naughty.
			await soap_emoji(message)
			if str(channel) in allowed_channels:		
				await speak(flavor('swear',author,'swearing'),channel)

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
				print("Fail: " + msg, len(msg))
				#They spoke! How dare they!
				cnt = message.content
				await message.delete()				
				await speak(flavor('talk',author,flav), channel)				
	elif message.content.startswith("!release") or message.content.startswith("!unmuzzle"):
		command = message.content.split(' ')[0]
		arg = message.content[len(command)+1:]
		args = arg.split(' ')
		if hasRole(author, 'Privileges Revoked'):
			await speak('Sorry, '+message.author.mention + '. You\'ve had muzzling privileges revoked.', channel)
		elif hasRole(author,'Sub'):
			if not str(channel) in allowed_channels:
				await deny_emoji(message)
			else:
				await speak("Nope. Be a good subby and leave that to the Doms and Switches.", channel)
		elif hasRole(author,'Dom') or hasRole(author,'Switch'):
			if len(arg) == 0:				
				# Check if anyone is muzzled under this user's name.
				if author.mention in muzzlers:					
					muzzled_persons = muzzlers[author.mention]					
					last_muzzled = muzzlers[author.mention][len(muzzled_persons)-1]
					await release(getUser(last_muzzled,channel.members),channel)
				else:
					#Nope. We don't know who they mean.
					await speak('You need to choose a user to unmuzzle!', channel)
			elif args[0] == "all":
				await speak("Releasing all muzzled users.",channel)
				muzzled = {}
				muzzlers = {}
				muzzled_by = {}
			else:
				first = args[0]
				members = channel.members				
				user = getUser(first,members)
				if user != False:
					if user.mention in muzzled:
						await release(user,channel)
					else:
						await speak("That person isn't restricted!", channel)
				else:
					await speak("Could not find user: "+first, channel)
		else:
			if not str(channel) in allowed_channels:
				await deny_emoji(message)
			else:
				await speak('You need a Switch or Dom role to use this command.', channel)
	else:		
		flav_commands = muzzle_flavor_text.keys()

		for command in flav_commands:			
			if message.content.startswith('!'+command):
				if not str(channel) in allowed_channels:
					await deny_emoji(message)
				else:
					if hasRole(author, 'Privileges Revoked'):
						await speak('Sorry, '+message.author.mention + '. You\'ve had muzzling privileges revoked.', channel)
					else:
						#Fix any accidental doublespacing in the command.
						message.content = re.sub(r'\s+',' ',message.content)
						arg = message.content[len(command)+2:]					
						
						args = arg.split(' ')
						if hasRole(author,'Sub'):
							await speak(flavor('subtry',message.author,command), channel)
						elif hasRole(author,'Dom') or hasRole(author,'Switch'):
							if len(arg) == 0:
								await speak('You need to choose a target for this command!', channel)
							else:
								first = args[0]
								members = channel.members
								user = getUser(first,members)
								if user != False:
									if hasRole(user,'Dom'):
										await speak("You can't use this command on a Dom!", channel)
									else:
										#Muzzle the user!
										if user.mention in muzzled:
											#Hotswap, silently unmuzzle first.
											await release(user,channel,True)
										
										allowed = args[1:]					
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
												allowed = ' '.join(allowed)
												allowed = re.sub(escape_regex,'',allowed)
												allowed = allowed.lower().split('/')
												
												allowed_list = ' '.join(args[1:])
												allowed_list = allowed_list.split('/')
												#Muzzle the user!
												muzzled[user.mention] = {
													'allowed':allowed,
													'flavor':command
												}
										#Remember who muzzled them.
										remember_muzzle(user,author)
										
										await speak(flavor('start',user,command), channel)
										await speak('Allowed words:\n> ' + ', '.join(allowed_list), channel)
								else:
									await speak("Could not find user: "+first, channel)
						else:
							await speak('You need a Switch or Dom role to use this command.', channel)

@client.slash_command(description="List the words you are restricted to. Only you will see the result.")
async def listwords(inter):
	cont = get_allowed_words(inter.author.mention)
	await inter.response.send_message(content=cont,ephemeral=True)

@client.event
async def on_message_edit(before,after):
	if str(before.author) == 'DISBOARD#2760':
		return
	else:
		await muzzlemain(after)

@client.event
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
	print(user)
	valid_pronouns = {
		'masc':hasRole(user,'He/Him'),
		'fem':hasRole(user,'She/Her'),
		'amb':hasRole(user,'They/Them'),
		'obj':hasRole(user,'It/Its')
	}

	#Choose masc/fem terms based on available roles
	options = list(filter(lambda typ: valid_pronouns[typ], valid_pronouns.keys()))
	print(options)

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

async def speak(m, channel):
    await channel.send(m)

print("Starting...")
client.run(TOKEN)
