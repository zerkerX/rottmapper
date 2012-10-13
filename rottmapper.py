#!/usr/bin/python
# Copyright 2012 Ryan Armstrong
#
# This file is part of ROTT Isometric Mapper.
#
# ROTT Isometric Mapper is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ROTT Isometric Mapper is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with ROTT Isometric Mapper.  If not, see <http://www.gnu.org/licenses/>.

"""Isometric map generator for Rise of the Triad maps"""
import sys, os

from PIL import Image, ImageDraw

import rtl, wad, walldb, spritedb
from rottfont import rottfont

class isomapper:
    """ Isometric map generator """
    def __init__(self, level, WAD):
        """ Initialize the map generator with a given ROTT level and the
        ROTT wad file
        """
        print "Initializing Map {} '{}'".format(level.index+1, level.name)
        self.level = level
        self.WAD = WAD
        self.wallinfo = walldb.walldb(WAD, level.floor)
        self.spriteinfo = spritedb.spritedb(WAD)
        self.wallinfo.generate_isometric(level.height)
        self.spriteinfo.generate_isometric(level.height)
        self.mappicture = Image.new("RGBA", (128*64*2, 128*64+level.height), (32, 32, 32))
        self.pen = ImageDraw.Draw(self.mappicture)
        self.minx = self.mappicture.size[0]
        self.maxx = 0
        self.miny = self.mappicture.size[1]
        self.maxy = 0

        self.switchsrcfont  = rottfont(WAD.db["General"]["NEWFNT1"], (255, 255, 0))
        self.switchdstfont  = rottfont(WAD.db["General"]["NEWFNT1"], (0, 255, 255))
        self.textspritefont = rottfont(WAD.db["General"]["NEWFNT1"], (0, 255, 0))

    @staticmethod
    def drawwall(adj, adjinfo):
        """ Tests whether we should draw a wall between the current tile
        (assumed to be a solid wall) and the specified adjacent tile.

        adj -- tile object (or subclass) for adjaent wall tile
        adjinfo -- info number for adjacent wall tile
        """
        return ( type(adj) is walldb.floortile and adjinfo != 0xd
            or type(adj) is walldb.thintile and adj.isowall[rtl.LEFT] == None
            or type(adj) is walldb.variabletile and adjinfo != 0)

    @staticmethod
    def nonsoliddifference(current, adj, curinfo, adjinfo):
        """ Tests whether we have a difference between the current tile
        and the specified adjacent tile, and that the adjacent tile is
        not solid. Used to guess orientation for thin tiles.

        current -- tile object (or subclass) for current wall tile
        adj -- tile object (or subclass) for adjaent wall tile
        curinfo -- info number for current wall tile
        adjinfo -- info number for adjacent wall tile
        """
        return (not adj.issolid(adjinfo) and
            (type(current) != type(adj) or
                curinfo in walldb.tile.specialheights and
                adjinfo not in walldb.tile.specialheights))

    def obscured(self, index, height):
        """ Tests whether a sprite at the given index and height would
        be obscured from view.

        index -- the map index of the sprite to test.
        height -- the height above the floor of the sprite.

        This works by counting tiles in line with the current tile on the
        left and right sides. As the distance from the current tile
        increases, the effective overlap decreases. An item is only
        obscured if the overlap is greater than the height at which the
        item is drawn.
        """
        # Test tiles that are in line with the right side (move RIGHT=0 then DOWN=3)
        pos = index
        rightobscure = -1000
        foundsolid = False

        for count in range(self.level.height / 32):
            pos = self.level.move(pos, count%2*3)
            checkwall = self.wallinfo.tiles[self.level.walls[pos]]
            if not foundsolid and checkwall.issolid(self.level.info[pos]):
                foundsolid = True
            elif not foundsolid and checkwall.isthin(self.level.info[pos]) and count%2 == 1:
                # Thin walls can obscure, but only if they are directly in line with the sprite
                rightobscure=max(rightobscure, checkwall.viewheight(self.level.info[pos]) - (count+1)*32)
            elif self.level.info[pos] == 0xd:
                # Skies will not draw walls adjacent. We need to ighnore the previous solid wall:
                foundsolid = False
            elif foundsolid and not checkwall.issolid(self.level.info[pos]) and \
                    type(checkwall) is not walldb.emptytile:
                rightobscure = max(rightobscure, self.level.height - count*32)
                break

        # Test tiles that are in line with the left side (move DOWN=3 then RIGHT=0)
        pos = index
        leftobscure = -1000
        foundsolid = False
        for count in range(self.level.height / 32):
            pos = self.level.move(pos, (count+1)%2*3)
            checkwall = self.wallinfo.tiles[self.level.walls[pos]]
            if not foundsolid and checkwall.issolid(self.level.info[pos]):
                foundsolid = True
            elif not foundsolid and checkwall.isthin(self.level.info[pos]) and count%2 == 1:
                leftobscure=max(leftobscure, checkwall.viewheight(self.level.info[pos]) - (count+1)*32)
            elif self.level.info[pos] == 0xd:
                # Skies will not draw walls adjacent. We need to ignore the previous solid wall:
                foundsolid = False
            elif foundsolid and not checkwall.issolid(self.level.info[pos]) and \
                    type(checkwall) is not walldb.emptytile:
                leftobscure = max(leftobscure, self.level.height - count*32)
                break

        return max(rightobscure, leftobscure) > height

    def drawtile(self, index):
        """ Draws a the contents of a specified index on the map (floor,
        walls, sprites). This is the "meat" of the isometric map generator.

        index -- index in the map to draw """

        wallval = self.level.walls[index]
        infoval = self.level.info[index]
        spriteval = self.level.sprites[index]

        # Base coordinates in the map
        x = index % 128
        y = index / 128

        # Coordinates of the top point of the isometric tile in the output
        # Map is rotated clockwise for easier drawing
        isox = 128*64+(x-y)*64
        isoy = (x+y)*32
        floorindex = x%2 + y%2*2
        spriteheight = 0

        current = self.wallinfo.tiles[wallval]
        sprite = self.spriteinfo.sprites[spriteval]

        # Adjacent information
        adj = [None]*4
        adjsprite = [None]*4
        adjinfo = [None]*4
        for direction in range(4):
            adj[direction] = self.wallinfo.tiles[self.level.nextwall(index, direction)]
            adjsprite[direction] = self.spriteinfo.sprites[self.level.nextsprite(index, direction)]
            adjinfo[direction] = self.level.nextinfo(index, direction)


        # Floors and Walls
        # ---------------------------------------------------------
        drawn = False

        if type(current) is walldb.floortile and infoval not in walldb.tile.specialheights:
            if infoval == 0xd:
                # Sky processing:
                pass
            else:
                # Draw the floor
                self.mappicture.paste(current.floor[floorindex],
                    (isox-64, isoy+current.height), current.floor[floorindex])
                drawn = True

        elif current.issolid(infoval):
            if infoval == 0xd:
                # Sky processing:
                pass
            else:
                # Draw a wall

                # Offsets are in the order as in RTL direction enum (RIGHT, UP, LEFT, DOWN):
                walloffs = [(0,32), (0,0), (-64,0), (-64, 32)]
                lineoffs = [(0,63,63,31), (0,0,63,31), (-64,31,0,0), (-64,31,0,63)] #x1,y1,x2,y2

                # Draw the walls in the given order so the tiles don't overlap
                # strangely. Note that the order differs from RTL direction order.
                for direction in [rtl.UP, rtl.LEFT, rtl.DOWN, rtl.RIGHT]:
                    if self.drawwall(adj[direction], adjinfo[direction]):
                        # Draw a standard wall and line on top
                        self.mappicture.paste(current.isowall[direction],
                            (isox +walloffs[direction][0], isoy +walloffs[direction][1]),
                            current.isomask[direction])
                        self.pen.line([(isox +lineoffs[direction][0],isoy +lineoffs[direction][1]),
                            (isox +lineoffs[direction][2], isoy +lineoffs[direction][3])],
                            fill=(192,192,192))
                        drawn = True
                    elif type(adj[direction]) is walldb.thintile:
                        if type(adjsprite[direction]) is spritedb.keysprite:
                            # Draw the wall edge from a locked door stored in
                            # the key sprite instead of the original edge
                            self.mappicture.paste(adjsprite[direction].wall.isowall[direction],
                                (isox +walloffs[direction][0], isoy +walloffs[direction][1]),
                                adjsprite[direction].wall.isomask[direction])
                        else:
                            # Draw a wall edge from a thin sprite (window, door)
                            # instead of the current wall
                            self.mappicture.paste(adj[direction].isowall[direction],
                                (isox +walloffs[direction][0], isoy +walloffs[direction][1]),
                                adj[direction].isomask[direction])

                        # Draw the line on top
                        self.pen.line([(isox +lineoffs[direction][0],isoy +lineoffs[direction][1]),
                            (isox +lineoffs[direction][2], isoy +lineoffs[direction][3])],
                            fill=(192,192,192))
                        drawn = True


        elif current.isthin(infoval):
            # Thin walls are also on top of the floor
            self.mappicture.paste(current.floor[floorindex],
                (isox-64, isoy+current.height), current.floor[floorindex])

            orientation = rtl.RIGHT
            # Decide orientation. Look for a different type of non-solid tile
            if (adj[rtl.RIGHT].issolid(adjinfo[rtl.RIGHT]) and adj[rtl.LEFT].issolid(adjinfo[rtl.LEFT])) or \
                self.nonsoliddifference(current, adj[rtl.UP], infoval, adjinfo[rtl.UP]) or \
                self.nonsoliddifference(current, adj[rtl.DOWN], infoval, adjinfo[rtl.DOWN]):
                    orientation = rtl.UP

            # Draw the thin wall itself. Thin walls are in the middle of
            # their respective tile. Variable tiles and spacers
            # only take up part of the vertical space; the exact
            # image to display (and thus what areas they take up)
            # is based on the info value.
            if type(current) is walldb.thintile:
                self.mappicture.paste(current.faces[orientation],
                    (isox-32, isoy+16), current.masks[orientation])
            elif type(current) is walldb.variabletile:
                self.mappicture.paste(current.faces[orientation][infoval],
                    (isox-32, isoy+16), current.masks[orientation][infoval])
            else:
                self.mappicture.paste(self.wallinfo.spacer.faces[orientation][infoval],
                    (isox-32, isoy+16), self.wallinfo.spacer.masks[orientation][infoval])

            # Since Gas overlays are drawn over doors, we draw them
            # here to use the proper orientation
            if sprite != None and type(sprite) is spritedb.gassprite:
                self.mappicture.paste(sprite.wall.faces[orientation],
                    (isox-32, isoy+16), sprite.wall.masks[orientation])

            drawn = True

        # Update level extents:
        if (drawn):
            self.minx = min(self.minx, isox-64)
            self.maxx = max(self.maxx, isox+64)
            self.miny = min(self.miny, isoy)
            self.maxy = max(self.maxy, isoy+64+self.level.height)


        # Sprites
        # ---------------------------------------------------------
        if sprite != None:
            # Note; Alignment to 56 is a smallish hack for slightly better
            # positioning of sprites in isometric perspective

            if type(sprite) is spritedb.textsprite:
                # Text sprites are drawn with the given text and a line pointing to their
                # location
                self.textspritefont.writetext(self.mappicture, (isox-56, isoy), sprite.text)
                self.pen.line([(isox,isoy + 16),
                    (isox, isoy +self.level.height -current.spriteheight(infoval) +32)],
                    fill=(0,152,0))
                self.pen.line([(isox+1,isoy + 16),
                    (isox+1, isoy +self.level.height -current.spriteheight(infoval) +32)],
                    fill=(0,108,0))

            elif (type(sprite) is spritedb.keysprite or type(sprite) is spritedb.gassprite) \
                    and type(current) is walldb.thintile:
                # Don't draw key or gas sprites on top of doors
                pass
            elif type(sprite) is spritedb.ceilingsprite:
                # Ceiling sprites are naturally always drawn on the ceiling
                self.mappicture.paste(sprite.image, (isox-48+sprite.xoffset,
                    isoy +16 +sprite.heightoffset), sprite.getmask(infoval))
            else:
                # Draw all other sprite types that do not require additional handling
                self.mappicture.paste(sprite.getimage(infoval, index), (isox-48+sprite.xoffset,
                    isoy +self.level.height -56 +sprite.heightoffset
                    -current.spriteheight(infoval, allowfloat=sprite.allowfloat)),
                    sprite.getmask(infoval, index))

            # Re-draw obscured important sprites above their obscured location
            if sprite.important and self.obscured(index, current.spriteheight(infoval)):
                self.pen.line([(isox,isoy),
                    (isox, isoy +self.level.height -24 -current.spriteheight(infoval))],
                    fill=(240,240,240))
                self.pen.line([(isox+1,isoy),
                    (isox+1, isoy +self.level.height -24 -current.spriteheight(infoval))],
                    fill=(190,190,190))
                self.mappicture.paste(sprite.getimage(infoval, index), (isox-48+sprite.xoffset,
                    isoy -72), sprite.getmask(infoval, index))

            # Draw key indicators if needed:
            if type(sprite) is spritedb.keysprite and type(current) is not walldb.thintile:
                self.pen.line([(isox,isoy),
                    (isox, isoy +self.level.height -24 -current.spriteheight(infoval))],
                    fill=sprite.linecolours[0])
                self.pen.line([(isox+1,isoy),
                    (isox+1, isoy +self.level.height -24 -current.spriteheight(infoval))],
                    fill=sprite.linecolours[1])
                self.mappicture.paste(sprite.glyph, (isox-8, isoy -32))

        elif spriteval > 0:
            print "Unknown Sprite {} at index {}".format(spriteval, index)


        # Switch source identifiers
        # ---------------------------------------------------------
        # Draw indices in pre-identified switch data (see rtl.py for more info)
        if index in self.level.switchdata:
            switchstr = self.level.switchdata[index]
            if len(switchstr) > 2:
                # Longer strings are time strings and take up more space:
                xoffs = -32
                yoffs = 8
            else:
                xoffs = -len(switchstr)*4
                yoffs = 16
            self.switchsrcfont.writetext(self.mappicture, (isox+xoffs, isoy+yoffs), switchstr)
            if current.spriteheight(infoval) < self.level.height - 64:
                self.pen.line([(isox,isoy + 48),
                    (isox, isoy +self.level.height -24 -current.spriteheight(infoval))],
                    fill=(152,152,0))
                self.pen.line([(isox+1,isoy + 48),
                    (isox+1, isoy +self.level.height -24 -current.spriteheight(infoval))],
                    fill=(108,108,0))

        # For index values that look like switch references, print the
        # index of the switch they point to
        elif infoval > 0x100 and infoval < 0x8000:
            switchstr = self.level.switchlookup(infoval)
            self.switchdstfont.writetext(self.mappicture, (isox-len(switchstr)*4, isoy+16), switchstr)
            if current.spriteheight(infoval) < self.level.height - 64:
                self.pen.line([(isox,isoy + 48),
                    (isox, isoy +self.level.height -24 -current.spriteheight(infoval))],
                    fill=(0,152,152))
                self.pen.line([(isox+1,isoy + 48),
                    (isox+1, isoy +self.level.height -24 -current.spriteheight(infoval))],
                    fill=(0,108,108))

        if current.debugnum > 0:
            print "Unknown Wall {} at index {}".format(debugnum, index)


    def savemap(self, outpath):
        """ Generates and saves the map

        outpath -- the folder to save the map. The filename is always
                   determined by the map name
        """
        print "Generating Map {} '{}'".format(self.level.index+1, self.level.name)

        for index, wallval in enumerate(self.level.walls):
            self.drawtile(index)

        print "Saving Map {} '{}'".format(self.level.index+1, self.level.name)
        self.mappicture.crop((self.minx, self.miny, self.maxx, self.maxy)).save(
            os.path.join(outpath, "{:02}-{}.png".format(self.level.index+1, self.level.name)))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print """Usage: python rottmapper.py [RTL/RTC FILE] ([Level Num])

Generates PNG isometric map images based on the specified ROTT RTL or
RTC file. If [Level Num] is specified, this will only generate a map
for the indicated level. Otherwise, maps for every level in the RTL/RTC
will be generated.

This tool requires DARKWAR.WAD from the registered version of ROTT
to be present in the current directory. Note that on case-sensitive file
systems the file name must also be uppercase.
"""
    else:
        filename = sys.argv[1]
        print "Loading Map Data"
        RTL = rtl.RTLFile(filename)
        print "Loading Wad Data"
        WAD = wad.WadFile('DARKWAR.WAD')
        WAD.cacheimages()

        outpath = filename.replace('.', ' ')
        if not os.path.exists(outpath):
            os.mkdir(outpath)

        if len(sys.argv) < 3:
            # Map every level in the RTL/RTC
            for level in RTL.levels:
                if level.index > -1:
                    mapper = isomapper(level, WAD)
                    mapper.savemap(outpath)
        else:
            # Map the specified level
            mapper = isomapper(RTL.levels[int(sys.argv[2])-1], WAD)
            mapper.savemap(outpath)

        RTL.close()
        WAD.close()
