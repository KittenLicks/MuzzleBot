import discord
import random
import re

print("This is a test")

TOKEN = process.env.BOT_TOKEN

print(TOKEN)

client = discord.Client()

muzzled = {}

channel = ''
emojis = '😀😃🙂🙃😊😇☺😋😛😜🤭🤐😐😑😶😏😳😨😭😖😣😤😡😈❤😠🤤💖❤🧡💛💚💙💜🤎🖤🤍♥💘💝💗'


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
	he = pronoun(user,'he')	
	heis = pronoun(user,'he is')
	his = pronoun(user,'his')
	him = pronoun(user,'him')
	
	s = s.replace('#is',heis)	
	s = s.replace('%',his)
	s = s.replace('!!',him)
	s = s.replace('#',he)
	
	return s

async def sendBumpMessage(user, channel):

	kink_list = {
		"Bondage":[
			'Ah, there you are @. What\'s wrong, got tied up? 😏',
			'Good pet, @. I\'ll tighten your bindings as a reward.',
			"So eager to please, hm, @? Come this way, I've a rope harness with your name on it."
		],
		"Degradation":[
			"I'm surprised you typed that out well enough, @, you dumb little slut.",
			"Hey everyone, @ likes to be degraded and insulted! How pathetic! :laughing:",
			"It's okay, @, I'm sure someone will give you a bump soon. Pathetic needy fuckslave."
		],
		"Chastity/Denial":[
			"Ah, one more day locked up won't hurt, right @?",
			"Oops, I think I broke the key to your little cage, @! You might be locked up forever! ...Oh no, here it is~",
			"Click the lock, turn the key, being locked gets @ weak at the knees~"
		],
		"SPH":[
			"Don't worry, @, penises of all sizes are good. Yours just happens to be good for laughing at.",
			"It's okay, @, size doesn't matter. Not unless you wanted to have sex with that tiny thing, anyway.",
			"How do you even masturbate with that little thing, @? If I wrapped my hand around it, it'd get lost."
		],
		"Diapers":[
			"@ needs some padding between % legs. Can somebody change !!?",
			"@ needs to be put back in diapers. Act like a baby, get treated like a baby.",
			"Diaper check, @! I hope your cute little butt is padded."
		],
		"Tease & Denial":[],
		"Petplay":[
			'Sit. Stay. Roll over. Good pet, @!',
			"What was that, @? All I hear is barking.",
			"Here, @! You can follow me around on a leash. Good pet."
		],
		"Ageplay":[
			"Hush, @, the adults are talking.",
			"It's bedtime for you, @. Come along now, I'll tuck you in."			
		],
		"Obectification":[],
		"Forced Bi":[],
		"BDSM":[],
		"Sissification":[
			"Wait right here, @, while I find you a nice cock to suck~",
			"Oh @, put on these panties for me, would you?",
			"You're going to be a good little slut for me, aren't you, @?"
		],
		"Cuckolding":[],
		"Creampies":[],
		"Hypnosis":[
			"Back already, @? Seems like the conditioning is working~",
			"And for my next trick I will turn @ into an obedient toy!",
			"Can you tell me the time, @? I'd check my pocket watch but you'd probably drop at the sight of it."
		],
		"Dronification":[],
		"Plushification":[
			"Oh wow, @ is useful for more than just cuddling?",
			"@ is such a good little plush!",
			"If anyone needs a plush to cuddle tonight, @ is available!"
		],
		"Spanking":[
			"Over my lap, @, it's time for your maintenance spanking.",
			"Get over my lap right this instant, @! You're about to have a very sore bottom.",
			"Bring me my paddle, @, I think it's time we turned that butt a nice red, don't you?"
		],	
		"Discipline":[],
		"Deepthroating":[],
		"Edge Play":[],
		"Voyeurism":[],
		"Exhibitionism":[],
		"DDLG":[],
		"Footplay":[],
		"CNC":[],
		"CBT":[],
		"Kinkshaming":[]
	}
	roles = []
	for role in user.roles:
		if str(role) in kink_list:
			roles.append(str(role))

	random.shuffle(roles)

	print(roles)

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
		e = discord.Embed()
		e.set_image(url=eurl)
		s = replacePronouns(s,user)
		await channel.send(msg,embed=e)
	else:
		s = replacePronouns(s,user)
		await channel.send(s)

def flavor(t,user,f):
	print('flavor',t,user,f)
	flavs = {
		'muzzle':{
			'start':[
				'has been muzzled! Behave yourself.',
				'has been muzzled! Be good.',
				'has been muzzled! Maybe that\'ll quiet !! down.',
				'has been muzzled! Was that a complaint? Sorry, can\'t hear you.',
				'has been muzzled! Where\'s the leash and collar?',
				'has been muzzled! That\'ll teach !! to behave.'			
			],
			'talk':[
				'had something to say, but nobody could hear it through the muzzle.',
				'tried to say a disallowed word. Bad pet!',
				'tried to speak through % muzzle. It thinks it\'s people, cute!'		
			],
			'end':[
				'has had % muzzle removed. I hope you learned a lesson.',
				'is free from % muzzle now. I\'m keeping my eye on you.',
				'has been released from % muzzle. Maybe #\'ll behave this time.'
			],
			'subtry':"Sorry, subby, if you want to be muzzled you'll have to ask a Switch or Dom to do it for you."
		},
		'gag':{
			'start':[
				'has been gagged! Hush, dear, the doms are talking.',
				'has been gagged! We\'ll come up with a use for that mouth in a minute.',
				'has been gagged! Don\'t make me chain you up too.',
				'has been gagged! Hard to brat with your mouth full, isn\'t it?',
				'has been gagged! Look at you drool.',
				'has been gagged! Slaves should be seen, not heard.'
			],
			'talk':[
				'makes some noises through the gag. Mrph hmf mfff!',
				'is trying to be sassy, but forgot #is not allowed to right now.',
				'forgot that % mouth is for pleasing doms, not talking.'
			],
			'end':[
				'has had % gag removed. For now.',
				'is no longer gagged. Maybe you\'ll think twice next time you mouth off.',
				'is ungagged. Respect the doms, or it goes right back in.'
			],
			'subtry':"Sorry, subby, if you want to be gagged you'll have to ask a Switch or Dom to do it for you."
		},
		'pantygag':{
			'start':[
				'has been panty-gagged! How do you taste, slut?',
				'has been panty-gagged! Look at !! choking on % own bottom!',
				'has been panty-gagged! Get a good whiff.'
			],
			'talk':[
				'tries to talk through % panties. Mrph hmf mfff!',
				'tried to say something, but only succeeded in getting a good taste of % panties.',
				'tried to talk, but % smell is making !! lightheaded!'],
			'end':[
				'is no longer panty-gagged. But the taste still lingers in % mouth.',
				'had % panties taken out of % mouth. Say thank you!'
			],
			'subtry':"Sorry, subby, if you want to be gagged you'll have to ask a Switch or Dom to do it for you."
		},
		'pacify':{
			'start':[
				'is now pacified! Act like a baby, get treated like a baby.',
				'is now pacified! Aww... is the baby cranky?',
				'is now pacified! Hush, little baby, don\'t say a word...',
				'is now pacified! Even pretty babies need to know when to hush.'
			],
			'talk':[
				'forgot babies can\'t talk. Wa na de nuh!',
				'tried to talk. Little baby thinks #is smart! So cute!',
				'is trying to say something. Don\'t worry, baby, it\'s almost naptime.'
			],
			'end':[
				'is no longer pacified. Are you ready to behave now?',
				'had % pacifier removed, but is still a pretty baby.' 
			],
			'subtry':"Sorry, subby, if you want to be pacified you'll have to ask a Switch or Dom to do it for you."
		},
		'plushify':{
			'start':[
				'has been turned into a plushy by a magic spell! :sparkles:',
				'has been plushified! What a pretty little toy!',
				'suddenly turns into a huggable little plushy!'
			],
			'talk':[
				'squeaks! Did someone squeeze !!?',
				'squeaks for attention! I think # needs a hug.',
				'is just a dumb little plush that needs others to tell !! what to say.'
			],
			'end':[
				'turns back to normal, but we all know #is still a plushy at heart.',
				'has been released from the plushy curse.',
				'returns to human form! Don\'t worry, you\'ll get to be a plushy again soon.'
			],
			'subtry':"Sorry, subby, if you want to be plushified you'll have to ask a Switch or Dom to do it for you."
		},
		'hypnotize':{
			'start':[
				'has been caught by a pretty pattern of lights!',
				'gets enraptured by a powerful spiral. Pretty..',
				'is a plaything, and playthings don\'t have smarts. Let\'s take those away.',
				'is going to obey and sink.'
			],
			'talk':[
				'tried to disobey. Shh... don\'t think. Just sink.',
				'tried to speak, but only a compliant moan came out.',
				'is trying to be smart, but something\'s just not working right now.',
				'lets out a compliant moan as all % brains go down the drain.',
				'needs some help wiping drool from % chin.'
			],
			'end':[
				'has been released from control! Be good and remember who owns you.',
				'has been released from hypnosis! It\'s okay, we all know you\'ll obey anyway.',
				'has been brought back to lucidity! Good thing #is still such a dumb toy.'
			],
			'subtry':"Sorry, subby, if you want to be hypnotized you'll have to ask a Switch or Dom to do it for you."
		}
	}
	flav = flavs[f]
	if t == "subtry":
		s = flav[t]
	else:
		s = random.choice(flav[t])
	return replacePronouns(s,user)


async def muzzlemain(message):
	global muzzled

	if message.author == client.user:
		return

	if str(message.author) == 'DISBOARD#2760':
		
		if len(message.embeds) == 1:
			embed = message.embeds[0]	
			text = embed.description
			
			text = text.split(', ')
			user = text[0]

			user = getUser(user, message.channel.members)

			await sendBumpMessage(user,message.channel)
		return

	allowed_channels = ['blush-chat','blush-chat-2','extreme-blush-chat','bot', 'rp-chat']

	channel = message.channel
	author = message.author
	if message.content == "!simpletext":
		await author.send("Here is a list of all the words you can say when restricted to simple language.\n>>> " + '\n'.join(simple_text))
		await speak('List sent to '+author.mention+'.',channel)
	elif author.mention in muzzled:
		if  "🔴" in message.content or (not str(channel) in allowed_channels):
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
				await speak(author.mention + ' ' +flavor('talk',author,flav), channel)				
	elif message.content.startswith("!release"):
		arg = message.content[9:]		
		args = arg.split(' ')
		if hasRole(author,'Sub'):
			await speak("Nope. Be a good subby and leave that to the Doms and Switches.", channel)
		elif hasRole(author,'Dom') or hasRole(author,'Switch'):
			if len(arg) == 0:
				await speak('You need to choose a user to unmuzzle!', channel)
			elif args[0] == "all":
				await speak("Releasing all muzzled users.",channel)
				muzzled = {}
			else:
				first = args[0]
				members = channel.members				
				user = getUser(first,members)
				if user != False:
					if user.mention in muzzled:
						await speak(user.mention + ' ' + flavor('end',user,muzzled[user.mention]['flavor']), channel)
						del muzzled[user.mention]
					else:
						await speak("That person isn't restricted!", channel)
				else:
					await speak("Could not find user: "+first, channel)
		else:
			await speak('You need a Switch or Dom role to use this command.', channel)
	else:
		flav_commands = ['muzzle','gag','pantygag','pacify','plushify','hypnotize']
		flavor_defaults = {
			'muzzle':["woof","bark","awoo","whine","arf"],
			'gag':['mmph'],
			'pantygag':['mmph'],
			'pacify':['wah'],
			'plushify':['squeak'],
			'hypnotize':['yes', 'no', 'miss', 'mistress', 'sir', 'master', 'owner', 'i obey', 'I understand', '😵', '🌀']
		}
		for command in flav_commands:
			if message.content.startswith('!'+command):
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
								allowed = args[1:]					
								if len(allowed) == 0:
									#Use defaults
									allowed = flavor_defaults[command]									
									allowed_list = flavor_defaults[command]
									#Muzzle the user!
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

								await speak(user.mention + ' ' + flavor('start',user,command), channel)
								await speak('Allowed words:\n> ' + ', '.join(allowed_list), channel)
						else:
							await speak("Could not find user: "+first, channel)
				else:
					await speak('You need a Switch or Dom role to use this command.', channel)

@client.event
async def on_message_edit(before,after):
	if str(before.author) == 'DISBOARD#2760':
		return
	else:
		await muzzlemain(after)

@client.event
async def on_message(message):	
	await muzzlemain(message)

def pronoun(user,t):	
	if hasRole(user,'Male') or hasRole(user,'FtM'):
		p =	{'he':'he','he is':'he is','his':'his','him':'him'}
		return p[t]
	elif hasRole(user,'Female') or hasRole(user,'MtF'):
		p = {'he':'she','he is':'she is','his':'her','him':'her'}
		return p[t]
	else:
		p = {'he':'they','he is':'they are','his':'their','him':'them'}
		return p[t]

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
