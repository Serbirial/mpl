from mpl import player
import os, sys

if os.name != "nt": print("\033]2;Media player : idle\007")

player.start()
