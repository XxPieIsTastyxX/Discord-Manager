# Discord Manager

Discord Manager is a project made to make it easier to invite friends to play games

## Installation

Use the package manager pip to install the necessary depenencies

```bash
pip install discord.py
```

## Setup

In order to use Discord Manager a gameslist.txt file must be present in the project directory. This is used to store the games persistently so that in the event that the bot stops running the data can be accessed on next launch.

There must also be a settings.ini file with the token and roles filled in, and optionally the command prefix and channel it should be using. A sample settings file is provided to demonstrate what the file should look like.

## Usage

### Any User can use the following commands:

**add** - Use the command ```add <game>``` in order to add a new game group for people to join

**help** - Use the command ```help``` to list all the available commands for users

**games** - Use the command ```games``` to list all the game groups that currently exist

**invite** - Use the command ```invite <game>``` to invite all the members of the group who are online to play

**join** - Use the command ```join``` to be join a group, if the gorup does not exist it will prompt to create it

**leave** - Use the command ```leave <game>``` to be removed from the specified game group

**players** - Use the command ```players <game>``` to list all of the memebers of that group

## TODO:

### Privileged Commands:

**channel** - Use the command

**clean** - Use the command

**reload** - Use the command

**remove** - Use the command ```remove <game>``` to delete a group and remove all of the players from it

**scrub** - Use the command

**verify** - Use the command
