#!/usr/bin/python3
# Copyright 2012,2021 Ryan Armstrong
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

""" Module to handle processing of the ROTT RTL/RTC file format and the
levels contained therein.

Also generates a simple black and white map of each level in an RTL/RTC
file if called directly.
"""
import struct, sys, os.path, csv, math
from PIL import Image, ImagePalette, ImageOps, ImageDraw

# Directional constants
(RIGHT, UP, LEFT, DOWN) = list(range(4)) # (aka: +x, -y, -x, +y, respectively)
NODIR = -1

class RTLFile:
    """ Class for the overall RTL/RTC file. Handles the file header
    and main file structure.

    Public member variables:
    levels -- array of level objects inside this RTL/RTC file
    """

    # Version Info
    #  Offset   Size    Description
    #-------------------------------------------------------------
        #0        4     Format signature
        #4        4     Version number
    versioninfo = '<4sl'

    def __init__(self, filename, noprocess=False):
        """ Initializes the RTL/RTC file by loading the file header and
        populating the levels array with the data for each level.

        filename -- name of RTL/RTC to load

        Optional named parameters:
        noprocess -- if true, the individual levels are not
                     post-processed for item archs and to erase the
                     top-left corner data.  Used by rottdebugmapper.
        """
        self.filedata = open(filename, 'rb')
        (self.signature, self.version) = struct.unpack(self.versioninfo,
            self.filedata.read(struct.calcsize(self.versioninfo)))

        self.levels = []
        for i in range(100):
            templevel = Level(self.filedata, i, noprocess)
            if templevel.used == 1:
                self.levels.append(templevel)

    def close(self):
        self.filedata.close()

class Level:
    """ Class for an individual level inside an RTL/RTC file.

    Public member variables:
    name -- map name as stored in map header
    walls -- array of wall data layer
    info -- array of info data layer
    sprites -- array of sprite data layer
    height -- wall height in pixels (i.e. 64 pixels = 1 block)
    switchdata -- dictionary of known switch letters, keyed by location
                  index
    """

    # Header
    # Offset   Size    Explanation
    #-------------------------------------------------------------
        #0        4     Used flag
        #4        4     CRC
        #8        4     RLEWtag
       #12        4     MapSpecials
       #12        4     Offset in file of Wall plane
       #16        4     Offset in file of Sprite plane
       #20        4     Offset in file of Info plane
       #24        4     Length of Wall plane
       #28        4     Length of Sprite plane
       #32        4     Length of Info plane
       #36       24     Name of level

    levelheader = '<LLLL3L3L24s'

    def __init__(self, filedata, index, noprocess):
        """ Loads the current level data out of the RTL/RTC file

        filedata -- the RTC/RTL file opened in binary mode with the
                    current cursor set to the start of the level data
        index -- the position in RTL/RTC that this level is located at
        noprocess -- if true, the individual levels are not
                     post-processed for item archs and to erase the
                     top-left corner data. Used by rottdebugmapper.
        """
        (self.used, self.crc, self.RLEWtag, self.specials,
            wall_offset, sprite_offset, info_offset,
            wall_length, sprite_length, info_length,
            tempname) = struct.unpack(self.levelheader,
                filedata.read(struct.calcsize(self.levelheader)))
        self.name = tempname.decode().rstrip('\0')
        self.index = index

        if self.used == 1:
            # Load the level contents. First memorize our current position.
            lastpos = filedata.tell()

            # Load the block data:
            self.walls = self.decode_block(filedata, wall_offset, wall_length)
            self.sprites = self.decode_block(filedata, sprite_offset, sprite_length)
            self.info = self.decode_block(filedata, info_offset, info_length)

            # Interpret (TODO) then zero out the special first four blocks:
            self.floor = self.walls[0] - 179
            # Ignore ceiling, brightness and fade out

            tempheight = self.sprites[0]
            if tempheight < 0x100:
                self.height = (tempheight - 0x59)*64
            else:
                self.height = (tempheight - 0x1B9)*64

            # Ignore skyheight, fog, lightsourcing, lightning

            self.song = self.info[0] # Just for reference

            # Return to last header position for next level
            filedata.seek(lastpos)

            if not noprocess:
                self.interpret_info()

                self.walls[:7] = [0]*7
                self.sprites[:7] = [0]*7
                self.info[:7] = [0]*7

    @staticmethod
    def switchindex(switchinfo):
        """ Converts a switch info value (format XXYY) into the correct
        map index
        """
        return (switchinfo // 256) + (switchinfo % 256)*128

    @staticmethod
    def timeval(infoval):
        """ Converts a timer info value (format MMSS) into a tuple of
        (minutes, seconds)
        """
        return ((infoval // 256), (infoval % 256))

    def switchlookup(self, switchinfo):
        """ Looks up the switch letter for a given switch info value
        (format XXYY)
        """
        return self.switchdata[self.switchindex(switchinfo)]

    def interpret_info(self):
        """ Re-interprets and pre-processes the following map data:

        Switches
        Switch-triggered objects are info values of the form XXYY
        (assumed between 0100 and 8000) and point to the location of
        the switch that triggers it. This function forms a catalog of
        known switches and assigns a letter to each.

        Timed Objects
        Timers are in the upper-left corner and are marked with
        sprite 121. The info value for the sprite points to the XXYY
        coordiante of the item to be timed. At THAT coordinate is the
        start time in the format MMSS, and immediately adjacent to that
        coordinate is the end time in the same format.

        Item Arches
        Info value of 11 indicates a line and info value 12 indicates
        a arch. This function groups items with the same value in the
        same region, orients according to the nearby trampoline
        placement, and re-writes the item height in the B### info value
        region for "normal" processing by the subsequent mapper.
        """
        self.switchdata = dict()
        switchnum = 0

        # Timed Objects
        # -------------------------------------------------------
        for index in range(15):
            # Refer to RT_TED.C, SetupClocks

            # Look for timers at the start of the level:
            if self.sprites[index] == 0x79:
                timedobjindex = self.switchindex(self.info[index])
                starttime = self.timeval(self.info[timedobjindex])
                self.info[index] = 0
                self.info[timedobjindex] = 0
                self.sprites[index] = 0

                # Find the end time. It should always be present
                endtime = None
                for direction in [UP, LEFT, DOWN, RIGHT]:
                    if self.nextinfo(timedobjindex, direction) > 0:
                        endtime = self.timeval(self.nextinfo(timedobjindex, direction))
                        self.info[self.move(timedobjindex, direction)] = 0
                        break

                self.switchdata[timedobjindex] = "{0[0]:02}:{0[1]:02}\n  to\n{1[0]:02}:{1[1]:02}".format(
                    starttime, endtime)

        for index, info in enumerate(self.info):
            # Skip the first few elements
            if index < 7:
                continue

            # Switches
            # -------------------------------------------------------
            if info > 0x100 and info < 0x8000:
                swindex = self.switchindex(info)
                if swindex not in self.switchdata:
                    # Prefer uppercase letters, then just number the rest
                    if switchnum < 26:
                        self.switchdata[swindex] = chr(switchnum+0x41)
                    else:
                        self.switchdata[swindex] = str(switchnum-25)

                    switchnum = switchnum + 1

            # Item Archs and Lines
            # -------------------------------------------------------
            if info == 11 or info == 12:
                # Find Dimensions. We always start from upper-left due to map processing order
                region = [0, 0]

                for checkdir in (RIGHT, DOWN):
                    pos = index
                    while self.info[pos] == info:
                        region[checkdir%2] = region[checkdir%2] + 1
                        pos = self.move(pos, checkdir)

                # Confirm orientation:
                orientation = -1
                if region[0] > region[1]:
                    checkorder = [LEFT, RIGHT, UP, DOWN]
                else:
                    checkorder = [UP, DOWN, LEFT, RIGHT]

                for checkdir in checkorder:
                    # Move to middle of perpendicular direction:
                    pos = self.move(index, (checkdir+1)%2*3, region[(checkdir+1)%2]//2)

                    # Move to edge of this side:
                    if checkdir in [RIGHT, DOWN]:
                        pos = self.move(pos, checkdir, region[checkdir%2]-1)

                    # Check suspected trampoline position:
                    if self.nextsprite(pos, checkdir) == 193:
                        # Actual arch/line orientation is facing away from trampoline
                        orientation = (checkdir+2)%4
                        break

                # Move to starting position
                if orientation in [LEFT, UP]:
                    pos = self.move(index, (orientation+2)%4, region[orientation%2]-1)
                else:
                    pos = index

                # Loft Sprites:
                for i in range(region[orientation%2]):
                    homepos = pos

                    # Adjust all heights in perpendicular direction:
                    for j in range(region[(orientation+1)%2]):
                        if info == 11:
                            self.info[pos] = 0xB000 + int(math.sin(i*math.pi/region[orientation%2])*(self.height-64)/4)
                        elif info == 12:
                            self.info[pos] = 0xB000 + i*(self.height-64) // (4 * (region[orientation%2]-1) )

                        # Perpendicular direction is always processed either RIGHT or DOWN
                        pos = self.move(pos, (orientation+1)%2*3)

                    pos = self.move(homepos, orientation)

    def decode_block(self, filedata, offset, length):
        """ Decodes a block of level data (walls, sprites or info) using
        the simple run-length compression algorithm of the rott level
        format. See HACKER.TXT included with the ROTT source code for
        more details.

        filedata -- file handle
        offset -- offset in the file for the current block
        length -- data length of this block
        """
        outdata = []
        filedata.seek(offset)
        while filedata.tell() < offset + length:
            (word,) = struct.unpack('<H', filedata.read(2))
            if (word == self.RLEWtag):
                (numwords,) = struct.unpack('<H', filedata.read(2))
                (value,)    = struct.unpack('<H', filedata.read(2))
                for count in range(numwords):
                    outdata.append(value)
            else:
                outdata.append(word)

        return outdata

    def move(self, index, direction, distance=1):
        """ Returns the index of the position in the given direction
        from a starting position. If there is no position in that
        direction, the index of 0 is used. Since index 0 is always
        erased by the processing algorithm, it is safe to use for almost
        any purpose.

        index -- starting position
        direction -- direction to move (per directional constants)

        Optional named parameters:
        distance -- number of blocks to move in that direction
        """
        result = 0
        if (direction == UP):
            result = index-128*distance
        elif (direction == DOWN):
            result = index+128*distance
        elif (direction == LEFT):
            if index%128 >= distance:
                result = index-distance
        elif (direction == RIGHT):
            if index%128 < 128-distance:
                result = index+distance

        if result < 0 or result >= 128*128:
            return 0
        else:
            return result

    def nextwall(self, index, direction, distance=1):
        """ Returns the contents of the wall layer in the given
        direction from a starting position. If there is no position in
        that direction, an empty wall (wall data of 0) should be
        returned.

        index -- starting position
        direction -- direction to look (per directional constants)

        Optional named parameters:
        distance -- number of blocks to look in that direction
        """
        return self.walls[self.move(index, direction, distance)]

    def nextinfo(self, index, direction, distance=1):
        """ Returns the contents of the info layer in the given
        direction from a starting position. If there is no position in
        that direction, info value of 0 should be returned.

        index -- starting position
        direction -- direction to look (per directional constants)

        Optional named parameters:
        distance -- number of blocks to look in that direction
        """
        return self.info[self.move(index, direction, distance)]

    def nextsprite(self, index, direction, distance=1):
        """ Returns the contents of the sprite layer in the given
        direction from a starting position. If there is no position in
        that direction, an empty sprite (sprite data of 0) should be
        returned.

        index -- starting position
        direction -- direction to look (per directional constants)

        Optional named parameters:
        distance -- number of blocks to look in that direction
        """
        return self.sprites[self.move(index, direction, distance)]

    def write_simple_map(self):
        """ Legacy function to write the map wall data to a simple
        grayscale image.
        """
        mappicture = Image.new("L", (128, 128))
        mappicture.putdata(self.walls)
        mappicture.save("{:02}-{}.png".format(self.index, self.name))

    @staticmethod
    def write_csv(block, filename):
        """ Legacy function to write a given block (info,sprite,wall)
        to CSV for debugging.

        block -- reference to array containing the desired data layer
        filename -- name of csv to write
        """
        outfile = open(filename, 'wb')
        output = csv.writer(outfile)
        for index in range(128):
            output.writerow(block[index*128:(index+1)*128])
        outfile.close()

    def write_csvs(self):
        """ Legacy function to write a all blocks (info, sprite, wall)
        to CSV for debugging. Rottdebugmapper writes a more usable
        debug file now and is preferred.
        """
        self.write_csv(self.walls, "{:02}-{}_walls.csv".format(self.index, self.name))
        self.write_csv(self.sprites, "{:02}-{}_sprites.csv".format(self.index, self.name))
        self.write_csv(self.info, "{:02}-{}_info.csv".format(self.index, self.name))

if __name__ == "__main__":
    # Default behaviour is to generate simple maps
    for filename in sys.argv[1:]:
        RTL = RTLFile(filename)

        for level in RTL.levels:
            level.write_simple_map()

        RTL.close()
