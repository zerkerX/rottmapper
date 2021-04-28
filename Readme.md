# About and Dependencies #

This is a series of Python scripts to generate Isometric views of Rise 
of the Triad maps, as well as extract the complete contents of 
DARKWAR.WAD. These scripts require [the Python Imaging Library 
(PIL)][pil] and [Python 2.x][py] (tested with Python 2.7.3). PIL 
unfortunately does not yet support Python 3, which prevents these 
scripts from being forward-compatible at this time.

Windows users should be able to download Python and PIL from the above 
links. Most Linux/Unix varients should be able to install Python and 
PIL via your package manager of choice; Ubuntu users can install the 
**python** and **python-imaging** libraries. OSX users should already 
have Python, but you may need to compile PIL yourself via the source 
download at the PIL website.

The scripts also obviously require **Rise of the Triad: Dark War**, 
which can be purchased from either [3D Realms][3dr] or [GOG.com][gog]. 
For the mapping scripts, **DARKWAR.WAD** must be in the current 
directory.

[pil]: http://www.pythonware.com/products/pil/index.htm
[py]:  http://python.org/
[3dr]: http://www.3drealms.com/rott/
[gog]: http://www.gog.com/en/gamecard/rise_of_the_triad__dark_war

# Usage #

There are three scripts included in the package that are intended to be 
executed directly. **rottmapper.py** is the main isometric mapper 
script, **rottdebugmapper.py** is a script to generate debug maps 
containing all the original wall/sprite/info values, and **wad.py** is 
a script to extract the complete contents of a ROTT wad file. In 
addition to the three scripts above, **rtl.py** can also be run 
directly to generate a simple black and white pixel image of a level, 
but this is not its primary purpose.

## rottmapper.py ##

**python rottmapper.py [RTL/RTC FILE] ([Level Num])**

Generates PNG isometric map images based on the specified ROTT RTL or
RTC file. If [Level Num] is specified, this will only generate a map
for the indicated level. Otherwise, maps for every level in the RTL/RTC
will be generated.

This tool requires DARKWAR.WAD from the registered version of ROTT
to be present in the current directory. Note that on case-sensitive file
systems the file name must also be uppercase.

## rottdebugmapper.py ##

**python rottdebugmapper.py [RTL/RTC FILE]...**

Generates a debug HTML file for each level in the specified ROTT RTL or
RTC file. Each index in the map is output into a cell in an HTML table
containing the following information:

 * The map index
 * The data in the walls layer, if present, as W###
 * The data in the info layer, if present, as I###
 * The data in the sprite layer, if present, as S###

## wad.py ##

**python wad.py [WAD FILE]**

Extracts the complete contents of a give ROTT wad file. Currently only
supports DARKWAR.WAD. All images will be written as PNG files,
other data will remain in its original format (e.g. .mid for music,
.voc for SFX). Unidentified data will be written with no extension.

# Notes #

I am not much of a pixel artist, so any tiles/icons that are not in the 
Rise of Triad wad file are rendered as solid colour shapes using PIL's 
drawing capabilities. If anyone wants to contribute some additional 
artwork to the project, it would be appreciated. However, the existing 
images do their job fairly well and don't look too much out of place.

Since isometric perspective can obscure certain items from view, I 
implemented an algorithm to detect this and draw important items above 
their space with a line pointing downwards. The algorithm is a bit 
sensitive for items that are partially obscured (i.e. wall over left 
half of area), but I considered this more important than having a 
difficult-to-find item. If I get enough feedback about this, I may 
consider introducing some sort of threshold and sizing metrics to 
decide when something isn't really obscured. Important items consist 
of:

 * Player Start
 * All Weapons
 * All Power-Ups, including the Random Powerup, but not Power-Downs
 * More Potent health pickups (Priest Porrage, Large Monk Crystals, 
   Healing Basins) and 50 point pickups
 * All Bosses and Secret Items (excluding Scott Miller's head, as
   that only shows up one in the standard levels and is only partially
   obscured in that case)
 * The collectable triads in Comm-bat levels

Keys are always marked with the key icon and a line pointing to their 
location, whether they are obscured or not.

Switch links are also indicated on the map. Switches are marked yellow 
letter and activate any items indicated by the same letter in teal. 
Timed objects are marked instead with the time interval in mm:ss that 
they are active (e.g.: 03:00 to 05:00). Elevators are represented in a 
similar fashion, in green text. Any elevators with the same number are 
linked to each other.

The cluster of guards that appears on most maps represents a random 
enemy spawn point. These are used all over. In the shareware and 
episode 1, the guards in that group represent the most commonly spawned 
results. In Episodes 2 and 3, the Strike Guard and Triad Enforcer can 
also show up. In Episode 4, this will spawn mostly Monks.

Enemies can also have a few characters denoting with particular 
characteristics. Enemies marked with a <b>^</b> will only show up in 
the hardest difficulty. Enemies marked with <b>!</b> are set to ambush 
the player. Patrolling enemies will be shown in their walking 
animation. Robots have no walking animation, but they are always 
patrolling.

The main single player start to a level is marked with the sprite for 
Taradino Cassatt. Any Comm-bat spawns in a level will be marked with 
the sprite for Thi Barrett. She will show up all over the place, even 
in single player maps.

Flat Arrow sprites in ROTT are a bit special. If they are placed on a 
wall, that wall is a pushwall and can be pushed (or triggered) in that 
direction. If they are on the floor, they redirect other objects, such 
as moving walls, patrolling guards, GADs, traps, etc. Circles on a wall 
indicate a non-directional pushwall.

Some algorithms are not exactly the same as the original game. Most 
notably, the algorithms to decide the orientation of thin walls, and 
the algorithm to loft sprites in an arch. The result is fairly good, 
but there is room for improvement.
