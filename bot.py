import discord
import asyncio
import configparser
import inspect
import os
from datetime import datetime
from time import strftime

def lister(array, _and=False):
    compiled = array[0]
    if len(array)==1:
        return compiled
    if len(array)>2:
        for n in array[1:-1]:
            compiled += ", " + n
        compiled += "," #Oxford comma
    if len(array) == 2 or _and == True:
        compiled += " and"
    compiled += " " + array[-1]
    return compiled

def capital(text):
    words = text.split(' ')
    text = ''
    for w in words:
        w = w[0].upper() + w[1:]
        text += w + ' '
    return text[:-1]

def file_read(name):
    items = []
    file = open(name)
    while True:
        line = file.readline()
        if line == '':
            break
        if line == '\n':
            continue
        if line[-1] == '\n':
            items.append(line[:-1])
        else:
            items.append(line)
    file.close()
    return items

def file_write(name, items):
    file = open(name, 'w')
    while len(items) > 0:
        file.write(items.pop(0)+'\n')
    file.close()
    
def file_append(name, item):
    file = open(name, 'a')
    file.write(item+'\n')
    file.close()
    
def file_create(name):
    file = open(name, 'w+')
    file.close()
    
def file_clean(name):
    items = file_read(name)
    file_write(name, items)
    


class MemberError(Exception):
    pass
class ChannelError(Exception):
    pass
class GameError(Exception):
    pass
class PlayerError(Exception):
    pass

class Config:
    def __init__(self, cfg):
        self.file = cfg
        config = configparser.ConfigParser(interpolation=None)
        config.read(cfg, encoding='utf-8')
        self.token = config.get('Essential','Token')
        self.roles = config.get('Essential','Roles').split(' ')
        self.prefix = config.get('Optional','Prefix',fallback='!')
        self.channel = config.get('Essential','MainChannel',fallback=None)
        self.invites = config.get('Optional','GameChannel',fallback=self.channel)
        self.banned_strings = config.get('Optional','Strings',fallback='')
        self.games = file_read('gameslist.txt')
        
        self.banned_strings = self.banned_strings.split(' ')
        

class Bot(discord.Client):
    def __init__(self):
        super().__init__(max_messages=500)
        self.config = Config('settings.ini')
        self.restricted_commands = {'channel': -1,'close': -1, 'verify': 1, 'clean': -1, 'add': -2, 'remove': -1, 'join': 0, 'leave': 0, 'players': 1, 'invite': 1, 'scrub': -1}
        self.channel = None
        self.invite_channel = None
        self.server = None
        self.num_roles = len(self.config.roles)
        self.numerical_reactions = ['\u0031\u20E3', '\u0032\u20E3', '\u0033\u20E3', '\u0034\u20E3', '\u0035\u20E3', '\u0036\u20E3', '\u0037\u20E3', '\u0038\u20E3', '\u0039\u20E3']
        self.gameslists = dict()
        for g in self.config.games:
            self.gameslists[g] = file_read('games/%s.txt' % g)
        
        
    async def on_ready(self):
        print('------')
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        self.channel = self.get_channel(self.config.channel)
        self.invite_channel = self.get_channel(self.config.invites)
        for s in self.servers:
            self.server = s
            break
        print('Listening on')
        print(self.server.name)
        print(self.channel.name)
        print(self.channel.id)
        print('Broadcasting on')
        print(self.server.name)
        print(self.invite_channel.name)
        print(self.invite_channel.id)
        print('------')
        
        
    def list_clean(self):
        file_clean('gameslist.txt')
        for g in self.config.games:
            file_clean('games/%s.txt' % g)

    def find(self, name):
        for m in self.server.members:
            if m.name.lower() == name.lower():
                return m
        raise MemberError()
    
    def find_channel(self, name):
        for c in self.server.channels:
            if c.name.lower() == name.lower():
                return c
        raise ChannelError()
    
    def game_check(self, game):
        if not game.lower() in self.config.games:
            raise GameError
    
    def level(self, user):
        highest = 0;
        for r in user.roles:
            try:
                temp = self.config.roles.index(r.id) + 1
            except:
                continue
            else:
                highest = temp
        return highest
    
    def list_roles(self, levels=range(0)):
        text = ''
        if levels == range(0):
            levels = range(self.num_roles)
        
        for l in levels:
            for r in self.server.roles:
                if r.id == self.config.roles[l]:
                    name = r.name
                    break
            text += '%d: %s\n' % (l+1, name)
        return text
    
    def list_players(self, game):
        players = []
        
        for u in self.gameslists[game.lower()]:
            players.append(self.server.get_member(u))
        while None in players:
            players.remove(None)
        
        return players
    
    def log(self, message):
        file_append('log.txt', '<Command Detected>\n[%s] [%s] [%s]\n%s' % (strftime('%D %T'), message.channel.name, message.author.name, message.content))
    
    def allowed(self, user, command):
        return not (command in list(self.restricted_commands.keys())) or \
            self.level(user) > ( self.num_roles + self.restricted_commands[command] ) % self.num_roles
    
    async def query(self, user, mess):
        reactions = ['\u2705','\u274c']
        for r in reactions:
            await self.add_reaction(mess, r)
            
        answer = await self.wait_for_reaction(reactions, user=user, timeout=30, message=mess)
        
        if not answer:
            await self.send_message(self.channel, 'Request timed out.')
            await self.delete_message(mess)
            raise TimeoutError
        
        return answer.reaction.emoji == reactions[0]
    
    async def screen(self, mess):
        text = mess.content.translate(' ')
        
        bad = False
        for s in self.config.banned_strings:
            if s in text:
                bad = True
                break
        
        if bad:
            await self.send_message(mess.channel, 'Message from %s was removed because it contained a banned character combination.' % mess.author.mention)
            await self.delete_message(mess)
        
        return bad
    
    async def cmd_add(self, user, game):
        if game.lower() in self.config.games:
            await self.send_message(self.channel, 'This game group already exists.')
            return
        
        self.config.games.append(game.lower())
        self.gameslists[game.lower()] = []
        file_append('gameslist.txt', game.lower())
        file_create('games/%s.txt' % game.lower())
        print('Game added by %s - %s' % (user.name, game))
        await self.send_message(self.channel, '%s game invite group added by %s' % (game, user.name))
    
    async def cmd_channel(self, chan):
        self.channel = chan
        print('Channel changed to %s.' % chan.name)
        await self.send_message(chan, 'Channel changed to %s.' % chan.name)
    
    async def cmd_clean(self):
        self.list_clean()
        
    async def cmd_close(self):
        await self.send_message(self.channel, 'Clocking out...')
        self.logout()
        exit()
        
    async def cmd_help(self, user):
        functions = inspect.getmembers(self, predicate=inspect.ismethod)
        commands = []
        for t in functions:
            if t[0][0:4] == 'cmd_' and self.allowed(user, t[0][4:]):
                commands.append(self.config.prefix + t[0][4:])
        await self.send_message(self.channel, "Command list: \n```%s```" % lister(commands))
        
    async def cmd_join(self, user, game):
        self.game_check(game)
        
        if user.id in self.gameslists[game.lower()]:
            await self.send_message(self.channel, 'You are already part of the %s group.' % game)
            return
        
        self.gameslists[game.lower()].append(user.id)
        file_append('games/%s.txt' % game.lower(), user.id)
        await self.send_message(self.channel, 'You are now part of the %s group, %s.' % (game, user.name))
     
    async def cmd_games(self):
        if len(self.config.games) == 0:
            await self.send_message(self.channel, 'There are no game invite groups. Hopefully someone will add one!')
            return
        
        games = []
        for g in self.config.games:
            games.append(capital(g))
        await self.send_message(self.channel, 'Here is the list of game invite groups:\n*(Capitalization is not important)*\n```%s```' % lister(games, _and=True))
        
    async def cmd_invite(self, user, game):
        self.game_check(game)
        chan = self.channel
        
        players = self.list_players(game)
        try:
            players.remove(user)
        except:
            pass
        
        selected = []
        if await self.query(user, await self.send_message(chan, 'Do you want to invite everyone from the %s group?' % game)):
            for p in players:
                if str(p.status) == 'online':
                    selected.append(p)
            
        else:
            nreact = self.numerical_reactions
            
            selected = []
            for i in range(0, len(players), 9):
                remaining = len(players) - i
                if remaining <= 9:
                    amount = remaining
                else:
                    amount = 9
                    
                options = ''
                for j in range(1, amount+1):
                    options += '%d: %s\n' % (j, players[i+j-1])
                    
                request = await self.send_message(chan, 'Select players to invite from the list below by clicking on the corresponding reactions. Then click the check button to continue.\n```%s```' % options)
                for j in range(0, amount):
                    await self.add_reaction(request, nreact[j])
                await self.add_reaction(request, '\u2705')
                
                done = await self.wait_for_reaction('\u2705', user=user, timeout=40, message=request)
                
                if not done:
                    await self.send_message(chan, 'Request timed out.')
                    await self.delete_message(request)
                    raise TimeoutError
                
                request = discord.utils.get(self.messages, id=request.id)
                reactions = request.reactions[:amount]
                await self.delete_message(request)
                
                for r in reactions:
                    if r.count > 1:
                        selected.append(players[i + nreact.index(r.emoji)])
        
        if not len(selected):
            if await self.query(user, await self.send_message(chan, 'You appear to have not selected any players to invite. (Or they might just be offline)\nTry again?')):
                await self.cmd_invite(user, game)
            return
        
        mentions = []
        for u in selected:
            mentions.append(u.mention)
                        
        if chan != self.invite_channel:
            await self.send_message(chan, 'Broadcasting invites on text channel #%s...' % self.invite_channel.name)
        await self.send_message(self.invite_channel, 'The following players have been invited by %s to play %s:\n%s.' % (user.name, game, lister(mentions, True))) 
    
    
    async def cmd_leave(self, user, game):
        self.game_check(game)
        
        if not user.id in self.gameslists[game.lower()]:
            await self.send_message(self.channel, 'You are not part of the %s group.' % game)
            return
        
        self.gameslists[game.lower()].remove(user.id)
        file_write('games/%s.txt' % game.lower(), self.gameslists[game.lower()])
        await self.send_message(self.channel, 'You are no longer part of the %s group, %s.' % (game, user.name))
    
    async def cmd_players(self, user, game):
        self.game_check(game)
        
        if len(self.gameslists[game.lower()]) == 0:
            await self.send_message(self.channel, 'There are no players in the %s group. Perhaps you should join.' % game)
            return
        
        players = self.list_players(game)
        namelist = []
        for p in players:
            namelist.append(p.name)
        
        await self.send_message(self.channel, 'The following users play %s: \n```%s```' % (game, lister(namelist, _and=True)))
    
    async def cmd_roles(self):
        await self.send_message(self.channel, 'Managed Roles:\n```%s```' % self.list_roles())

    async def cmd_reload(self):
        self.config = Config('settings.ini')
        self.num_roles = len(self.config.roles)
        self.gameslists = dict()
        for g in self.config.games:
            self.gameslists[g] = file_read('games/%s.txt' % g)
        
    async def cmd_remove(self, user, game):
        self.game_check(game)
        
        self.config.games.remove(game.lower())
        self.gameslists[game.lower()] = []
        file_write('gameslist.txt', self.config.games)
        os.remove('games/%s.txt' % game.lower())
        print('Game removed by %s - %s' % (user.name, game))
        await self.send_message(self.channel, '%s game invite group removed by %s' % (game, user.name))
        
        await self.cmd_reload() # don't want to do this but it works
    
    async def cmd_scrub(self, channel, time):
        now = datetime.utcnow()
        time = time.split(':')
        for i in range(len(time)):
            time[i] = int(time[i])
        minute = time[0]
        if len(time) > 1:
            hour = time[1]
            if len(time) > 2:
                day = time[2]
                if len(time) > 3:
                    month = time[3]
                else:
                    month = now.month
            else:
                day = now.day
                month = now.month
        else:
            hour = now.hour
            day = now.day
            month = now.month
            
        date = datetime(now.year, month, day, hour, minute)
        async for message in self.logs_from(channel, limit=200, after=date):
            await self.delete_message(message)
    
    async def cmd_verify(self, sponsor, name):
        chan = self.channel
        
        endorsed = self.find(name)
        
        level = self.level(sponsor) - 1
        elevel = self.level(endorsed)
        levels = range(elevel, level)
        
        if elevel >= level:
            await self.send_message(chan, "You don't have permission to grant that user a role higher than they currently have.")
            return
        
        request = await self.send_message(chan, 'Please select a role to assign to %s:\n```%s```' % (endorsed.name, self.list_roles(levels)))
        
        reactions = self.numerical_reactions
        for i in levels:
            await self.add_reaction(request, reactions[i])
        answer = await self.wait_for_reaction(reactions[elevel:level], user=sponsor, timeout=30, message=request)
        
        if not answer:
            await self.send_message(chan, 'Request timed out.')
            await self.delete_message(request)
            raise TimeoutError
        
        for i in levels:
            if answer.reaction.emoji == reactions[i]:
                for r in self.server.roles:
                    if r.id == self.config.roles[i]:
                        await self.add_roles(endorsed, r)
                        await self.send_message(chan, '%s successfully given %s role by %s.' % (endorsed.name, r.name, sponsor.name))
                        await self.delete_message(request)
                        return
            
    
    async def on_message(self, mess):
        await self.wait_until_ready()
        
        if await self.screen(mess):
            return
        if not mess.content.startswith(self.config.prefix):
            return        
        if not ( mess.channel == self.channel or mess.content[1:8] == 'channel' or mess.content[1:6] == 'scrub' ):
            return        
        if mess.author == self.user:
            return
        
        try:
            space = mess.content.index(' ')
        except ValueError:
            space = None
        command = mess.content[1:space]
        print('Command detected - %s' % command)
        self.log(mess)
        
        if command == 'channel' or command == 'scrub':
            parameter1 = mess.channel
        else:
            parameter1 = mess.author
            
        if space == None:
            parameter2 = None    
        else:
            parameter2 = mess.content[space+1:]
        
            
        try:
            function = getattr(self, 'cmd_%s' % command)
        except:
            print('Command invalid.')
        else:
            if self.allowed(mess.author, command):
                params = len(inspect.signature(function).parameters)
                
                try:
                    if params == 0:
                        await function()
                    elif params == 1:
                        await function(parameter1)
                    elif params == 2:
                        await function(parameter1, parameter2)
                        
                except MemberError:
                    await self.send_message(mess.channel, 'Could not find a user by the name of %s' % parameter2)

                except GameError:
                    await self.send_message(mess.channel, 'Could not find a game group by the name of %s' % parameter2)
                    if self.allowed(mess.author, getattr(self, 'cmd_add')) and await self.query(mess.author, await self.send_message(mess.channel, 'Would you like to add it?')):
                        await self.cmd_add(parameter1, parameter2)
                
                except PlayerError:
                    await self.send_message(self.channel, 'There are no players in the %s group. Perhaps you should join.' % parameter2)
                    
                except TimeoutError:
                    pass
                
                    
                    
            else:
                await self.send_message(mess.channel, 'You do not have permission to use that command.')
    
    
    
    
    
if __name__ == '__main__':
    t=Bot()
    t.run(t.config.token)
    
    
    