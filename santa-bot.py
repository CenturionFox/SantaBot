#IMPORTANT NOTE:
#This branch is the development branch, where i try to get major refactorings working, so i have a (mostly) stable branch in master.
#The current thing i'm refactoring is making it so that the bot can handle exchanges across multiple channels
#thing is, this is getting really messy, and i really want to try to get the master branch completely operational and debugged by 
#thanksgiving. 

#As such, this branch's development is suspended until i get master to a stable release stage.





import logging
import asyncio
import os.path
import random
import discord
from configobj import ConfigObj


#FIXME: make this entire program not a mess


class Participant(object):
    """class defining a participant and info associated with them"""
    def __init__(self, name, idstr, usrnum, address='', preferences='', partnerid=''):
        self.name = name                #string containing name of user
        self.idstr = idstr              #string containing id of user
        self.usrnum = usrnum            #int value referencing the instance's location in usr_list
        self.address = address          #string for user's address
        self.preferences = preferences  #string for user's gift preferences
        self.partnerid = partnerid      #string for id of partner
    
    def address_is_set(self):
        """returns whether the user has set an address"""
        if self.address == '':
            return False
        else:
            return True
    
    def pref_is_set(self):
        """returns whether the user has set gift preferences"""
        if self.preferences == '':
            return False
        else:
            return True


class Group(object):
    """class defining a group of participants
    based on server membership"""
    def __init__(self, name, idstr, totalUsers=0, participantList=[]):
        self.name = name                #server name
        self.idstr = idstr              #server ID
        self.totalUsers = totalUsers
        self.participantList = participantList  #participant list, populated as 
                                                #users join
    def asssign_partners(self):
        partners = self.participantList
        for user in self.participantList:
            candidates = partners
            candidates.remove(user)
            partner = candidates[random.randint(0, len(candidates) - 1)]
            #remove user's partner from list of possible partners
            partners.remove(partner)
            #save the partner id to the participant's class instance
            #if user.partnerid == ''
            user.partnerid = partner.idstr
            #else:
            #    user.partnerid = [user.partnerid, partner.idstr]
            config['users'][str(user.usrnum)][5] = user.partnerid
            config.write()
            #TODO: inform users of their partner
        #set hasStarted + assoc. cfg value to True
        self.hasStarted = True
        config['servers'][self.idstr][1] = True

    def add_participant(self, user):
        """appends a Participant object to this group's userlist"""
        self.participantList.append(get_participant_object(user))
        self.totalUsers = self.totalUsers + 1
        
#initialize client class instance
client = discord.Client()

#TODO: initialize config file

def user_is_participant(usrid, usrlist=usr_list):
    """Takes a discord user ID string and returns whether
    a user with that ID is in usr_list"""
    result = False
    for person in usrlist:
        if person.idstr == usrid:
            result = True
            break
    return result

def get_participant_object(usrid, usrlist=usr_list):
    """takes a discord user ID string and list of
    participant objects, and returns the first
    participant object with matching id."""
    for person in usrlist:
        if person.idstr == usrid:
            return person

def get_group_object(serverid, serverlist=svr_list):
    """takes discord server id string and list of server objects,
    and returns first server object with matching id"""
    for group in serverlist:
        if group.idstr == serverid:
            return group

#set up discord connection debug logging
client_log = logging.getLogger('discord')
client_log.setLevel(logging.DEBUG)
client_handler = logging.FileHandler(filename='./files/debug.log', encoding='utf-8', mode='w')
client_handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
client_log.addHandler(client_handler)


usr_list = []
svr_list = []


@client.event
async def on_ready():
    """print message when client is connected and perform
    some initialization"""
    
    #TODO:
    #-initialize list containing Group classes for each server that the client is connected to 
    #-initialize list containing Participant classes for each person who sends '$$join' and make sure to keep track of who is in which servers
    #-ensure all values contained in those classes can be reconstructed from a config file      
    
    
    global usr_list
    global svr_list
    
    #this is the default, no reading config for saved value yet
    for server in client.servers:
        server_list.append(Group(server.name, server.id))

    print('Logged in as')
    print(client.user.name)
    print(client.user.discriminator)
    print('------')


#handler for all on_message events
@client.event
async def on_message(message):
    #declare global vars
    global usr_list
    global total_users
    global exchange_started
    #set up some local vars for convenience sake
    group = get_group_object(message.author.server)
    if user_is_participant(message.author.id):
        author = get_participant_object(message.author.id)
    #write all messages to a chatlog
    with open('./files/chat.log', 'a+') as chat_log:
        chat_log.write('[' + message.author.name + ' in ' + message.channel.name + ' at ' + str(message.timestamp) + ']' + message.content + '\n')
    
    #ignore messages from the bot itself
    if message.author == client.user:
        return
    
    #event for a user joining the secret santa
    elif message.content.startswith('$$join'):
        #cant really have a gift exchange in a pm
        if message.channel.is_private:
            await client.send_message(message.channel, '`Error: You must join a gift exchange through a server.`')
        #check if message author has already joined
        elif user_is_participant(message.author.id, group.participantList):
            await client.send_message(message.channel, '`Error: You have already joined this exchange.`')
        #check if the exchange has already started
        elif group.hasStarted:
            await client.send_message(message.channel, '`Error: Too late, the gift exchange is already in progress.`')
        else:
            #initialize instance of participant class for the author
            usr_list.append(Participant(message.author.name, message.author.id, total_users, message.author.server))
            group.add_participant(message.author.id)
            #write details of the class instance to config and increment total_users
            total_users = total_users + 1
            config['members'][str(total_users)] = [message.author.name, message.author.id, total_users]
            config.write()
            #prompt user about inputting info
            await client.send_message(message.channel, message.author.mention + ' Has been added to the OfficialFam Secret Santa exchange!')
            await client.send_message(message.author, 'Please input your mailing address so your secret Santa can send you something!')
            await client.send_message(message.author, 'Use `$$setaddress` to set your mailing adress')
            await client.send_message(message.author, 'Use `$$setpreference` to set gift preferences for your secret santa')
    
    #accept address of participants
    elif message.content.startswith('$$setaddress'):
        #check if author has joined the exchange yet
        if user_is_participant(message.author.id):
            #add the input to the value in the user's class instance
            user = get_participant_object(message.author.id)
            user.address = message.content.replace('$$setaddress', '', 1)
            #save to config file
            config['members'][str(user.usrnum)][3] = user.address
            config.write()
        else:
            await client.send_message(message.channel, 'Error: you have not yet joined the secret santa exchange. Use `$$join` to join the exchange.')
    
    #accept gift preferences of participants
    elif message.content.startswith('$$setprefs'):
        #check if author has joined the exchange yet
        if user_is_participant(message.author.id):
            #add the input to the value in the user's class instance
            author.preferences = message.content.replace('$$setpref', '', 1)
            #save to config file
            config['members'][str(user.usrnum)][4] = author.preferences
            config.write()
        else:
            await client.send_message(message.channel, 'Error: you have not yet joined the secret santa exchange. Use `$$join` to join the exchange.')
    
    #command for admin to begin the secret santa partner assignmenet
    elif message.content.startswith('$$start'):
        #only allow people with admin permissions to run
        if message.author.top_role == message.server.role_heirarchy[0]:
            #first ensure all users have all info submitted
            all_fields_complete = True
            for user in usr_list:
                if user.address_is_set() and user.pref_is_set():
                    pass
                else:
                    all_fields_complete = False
                    await client.send_message(message.author, '`Error: ' + user.name + ' has not submitted either a mailing address or gift preferences.`')
                    await client.send_message(message.author, '`Partner assignment canceled: participant info incomplete.`')
            #select a random partner for each participant if above loop found no empty values
            if all_fields_complete:
                group.asssign_partners()
        else:
            await client.send_message(message.channel, '`Error: you do not have permission to do this.`')
    
    #allows a way to exit the bot
    elif message.content.startswith('$$shutdown') and not message.channel.is_private:
        #Fonly allow ppl with admin permissions to run
        if message.author.top_role == message.server.role_heirarchy[0]:
            await client.send_message(message.channel, 'Curse your sudden but inevitable betrayal!')
            raise KeyboardInterrupt
        else:
            await client.send_message(message.channel, '`Error: you do not have permission to do this.`')
    
    #lists off all participant names and id's
    elif message.content.startswith('$$listparticipants'):
        if group.totalUsers == 0:
            await client.send_message(message.channel, 'Nobody has signed up for the secret santa exchange yet. Use `$$join` to enter the exchange.')
        else:
            msg = '```The following people are signed up for the secret santa exchange:\n'
            for user in group.participantList:
                msg = msg + user.name + '\n'
            msg = msg + 'Use `$$join` to enter the exchange.```'
            await client.send_message(message.channel, msg)
    
    #lists total number of participants
    elif message.content.startswith('$$totalparticipants'):
        if group.totalUsers == 0:
            await client.send_message(message.channel, 'Nobody has signed up for the secret santa exchange yet. Use `$$join` to enter the exchange.')
        elif group.totalUsers == 1:
            await client.send_message(message.channel, '1 person has signed up for the secret santa exchange. Use `$$join` to enter the exchange.')
        else:
            await client.send_message(message.channel, 'A total of ' + group.totalUsers + ' users have joined the secret santa exchange so far. Use `$$join` to enter the exchange.')
    
    #allows a user to have the details of their partner restated
    elif message.content.startswith('$$partnerinfo'):
        if group.hasStarted and user_is_participant(message.author.id):
            partnerobj = get_participant_object(author.partnerid)
            msg = 'Your partner is ' + partnerobj.name + '\n'
            msg = msg + 'Their mailing address is ' + partnerobj.address + '\n'
            msg = msg + 'their gift preference is as follows:\n'
            msg = msg + partnerobj.preferences
            await client.send_message(message.author, msg)
        elif not group.hasStarted:
            await client.send_message(message.channel, '`Error: partners have not been assigned yet.`')
        else:
            await client.send_message(message.author, '`Error: You are not participating in the gift exchange.`')

#event loop and discord initiation
client.run(config['programData']['discord_token'])
