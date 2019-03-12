from mpl import player
import os, sys

if os.name != "nt": print("\033]2;Media player : idle\007")
#import stackimpact

#agent = stackimpact.start(
#    agent_key = '67c4e6bfd1363f7220f9e830fa7d6bd953132dfd',
#    app_name = 'Go')
#
#with agent.profile('span1'):
player.start()
