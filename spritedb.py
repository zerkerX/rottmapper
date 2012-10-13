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

""" Module containing a variety of ROTT sprite-type classes, including
the main sprite database class."""
import random

from PIL import Image, ImageDraw

import walldb, rtl
from rottfont import rottfont

# Glyph types
(RIGHTARR, UPARR, LEFTARR, DOWNARR, UPDOWNARR, ELLIPSE, TEXT) = range(7)

class sprite(object):
    """ Base sprite class. This is used by the majority of sprites in
    the game.

    Public member variables:
    heightoffset -- height offset to apply when drawing this sprite.
                    i.e. positive numbers draw the sprite further into
                    the floor.
    xoffset -- horizontal offset when drawing this sprite. Positive
               numbers shift this sprite to the right. Always 0.
    important -- flag to indicate whether this sprite should be marked
                 if it is not visible.
    allowfloat -- flag for whether this sprite is allowed to float above
                  the ground due to special info values
    """
    def __init__(self, lump, heightoffset=0, important=False,
            glyphtype = -1, glyphpos = (0,0), glyphcolour = (0,0,0),
            font=None, text=None, allowfloat=True):
        """ Initializes the current sprite based on the provided data:

        lump -- a wad lump instance, which should be a patch-type lump.
                The image and mask from this lump will be used for this
                sprite.
        heightoffset -- height offset to apply when drawing this sprite.
                        i.e. positive numbers draw the sprite further into
                        the floor.
        important -- flag to indicate whether this sprite should be marked
                     if it is not visible.
        glyphtype -- if specified, the corresponding glyph will be drawn
                     on top of this sprite. Glyph enumerations are
                     defined at the top of this file.
        glyphpos -- if drawing a glyph, this specifies the x,y coordinate
                    offset of the SCALED image to draw the top-left
                    corner of the glyph at
        glyphcolour -- a valid PIL-supported colour to use when drawing
                       the specified glyph. Not used by TEXT glyphs.
        font -- for TEXT glyphs only, the instance of the rottfont class
                to use for drawing the text,
        text -- for TEXT glyphs only, the actual text to write.
        allowfloat -- flag for whether this sprite is allowed to float above
                      the ground due to special info values
        """
        self.image = self.spritescale(lump.data.convert("RGB"))
        self.mask = self.spritescale(lump.mask)
        if glyphtype >= 0:
            self.drawglyph(glyphtype, glyphpos, glyphcolour, font, text)

        self.heightoffset = heightoffset
        self.xoffset = 0
        self.important = important
        self.allowfloat=allowfloat

    def getimage(self, infoval = 0, mappos=0):
        """ Obtains the correct sprite image as a PIL Image object
        for a given info value and map index. Base sprites only have
        one image which is always returned.
        """
        return self.image

    def getmask(self, infoval = 0, mappos=0):
        """ Obtains the correct sprite mask as a PIL Image object
        for a given info value and map index. Base sprites only have
        one image which is always returned.
        """
        return self.mask


    def drawglyph(self, glyphtype, glyphpos, glyphcolour, font, text):
        """ Draws a glyph onto the current sprite image.

        glyphtype -- if specified, the corresponding glyph will be drawn
                     on top of this sprite. Glyph enumerations are
                     defined at the top of this file.
        glyphpos -- if drawing a glyph, this specifies the x,y coordinate
                    offset of the SCALED image to draw the top-left
                    corner of the glyph at
        glyphcolour -- a valid PIL-supported colour to use when drawing
                       the specified glyph. Not used by TEXT glyphs.
        font -- for TEXT glyphs only, the instance of the rottfont class
                to use for drawing the text,
        text -- for TEXT glyphs only, the actual text to write.
        """
        imagepen = ImageDraw.Draw(self.image)
        maskpen = ImageDraw.Draw(self.mask)
        for pen, colour in [(imagepen, glyphcolour), (maskpen, 255)]:
            if glyphtype == TEXT:
                font.writetext(self.image, glyphpos, text, self.mask)
            elif glyphtype == RIGHTARR:
                pen.polygon([(glyphpos[0]+22, glyphpos[1]+11),
                (glyphpos[0]+5, glyphpos[1]+11),
                (glyphpos[0]+9, glyphpos[1]+9),
                (glyphpos[0], glyphpos[1]+5),
                (glyphpos[0]+8, glyphpos[1]),
                (glyphpos[0]+17,  glyphpos[1]+4),
                (glyphpos[0]+22,  glyphpos[1]+2)],
                fill=colour, outline=colour)
            elif glyphtype == UPARR:
                pen.polygon([(glyphpos[0]+22, glyphpos[1]),
                (glyphpos[0]+5, glyphpos[1]),
                (glyphpos[0]+9, glyphpos[1]+2),
                (glyphpos[0], glyphpos[1]+6),
                (glyphpos[0]+8, glyphpos[1]+11),
                (glyphpos[0]+17,  glyphpos[1]+7),
                (glyphpos[0]+22,  glyphpos[1]+9)],
                fill=colour, outline=colour)
            elif glyphtype == LEFTARR:
                pen.polygon([glyphpos,
                (glyphpos[0]+17, glyphpos[1]),
                (glyphpos[0]+13, glyphpos[1]+2),
                (glyphpos[0]+22, glyphpos[1]+6),
                (glyphpos[0]+14, glyphpos[1]+11),
                (glyphpos[0]+5,  glyphpos[1]+7),
                (glyphpos[0],  glyphpos[1]+9)],
                fill=colour, outline=colour)
            elif glyphtype == DOWNARR:
                pen.polygon([(glyphpos[0], glyphpos[1]+11),
                (glyphpos[0]+17, glyphpos[1]+11),
                (glyphpos[0]+13, glyphpos[1]+9),
                (glyphpos[0]+22, glyphpos[1]+5),
                (glyphpos[0]+14, glyphpos[1]),
                (glyphpos[0]+5,  glyphpos[1]+4),
                (glyphpos[0],  glyphpos[1]+2)],
                fill=colour, outline=colour)
            elif glyphtype == UPDOWNARR:
                pen.polygon([(glyphpos[0], glyphpos[1]+6),
                (glyphpos[0]+7, glyphpos[1]),
                (glyphpos[0]+8, glyphpos[1]),
                (glyphpos[0]+15, glyphpos[1]+6),
                (glyphpos[0]+10, glyphpos[1]+6),
                (glyphpos[0]+10,  glyphpos[1]+9),
                (glyphpos[0]+15,  glyphpos[1]+9),
                (glyphpos[0]+8,  glyphpos[1]+15),
                (glyphpos[0]+7,  glyphpos[1]+15),
                (glyphpos[0],  glyphpos[1]+9),
                (glyphpos[0]+5,  glyphpos[1]+9),
                (glyphpos[0]+5,  glyphpos[1]+6)],
                fill=colour, outline=colour)
            elif glyphtype == ELLIPSE:
                pen.ellipse([glyphpos,
                (glyphpos[0]+22, glyphpos[1]+11)],
                fill=colour, outline=colour)

    @staticmethod
    def spritescale(image):
        """ Re-scales the specified image to make the size equivalent
        to wall sizing. A rough guess places sprites at about 1.5
        times larger than walls, so reduce size to 3/4 original size.
        """
        return image.transform((image.size[0]*3/4,image.size[1]*3/4),
            Image.AFFINE, (1.5, 0, 0, 0, 1.5, 0), Image.BICUBIC)

    @staticmethod
    def recolour_sprite(image, colourindex):
        """ Re-colours an image by replacing the colours in ROTT
        palette indicies 158 through 168 with the user-specified
        range.

        image -- the PIL Image to resize
        colourindex -- the index of the darkest colour in the desired
                       colour range. Colour index 168 will be replaced
                       with this colour and all ligher colours will be
                       lower index numbers. The re-colour algorithm
                       needs 11 colours in a range.
        """
        newimage = image.convert("P") # Use convert to duplicate image
        pixdata = list(image.getdata())

        for index, pixel in enumerate(pixdata):
            if pixel in range(158, 169):
                pixdata[index] = pixel - 168 + colourindex

        newimage.putdata(pixdata)
        return newimage


class ceilingsprite(sprite):
    """ Ceiling sprite class. This is identical to the parent sprite
    class and is only used to clue the parent mapper file that this
    sprite should be placed on the ceiling.
    """
    pass


class textsprite(sprite):
    """ Text sprite class. This sprite simply contains a text label
    with no other graphical information and needs to be drawn manually.

    Public member variables:
    text -- the text contents of this sprite
    heightoffset -- height offset to apply when drawing this sprite.
                    i.e. positive numbers draw the sprite further into
                    the floor. Always 0.
    xoffset -- horizontal offset when drawing this sprite. Positive
               numbers shift this sprite to the right. Always 0.
    important -- flag to indicate whether this sprite should be marked
                 if it is not visible. Always false.
    """
    def __init__(self, text):
        """ Initializes this text sprite with the text label specified."""
        self.text = text
        self.heightoffset = 0
        self.xoffset = 0
        self.important = False


class indexedsprite(sprite):
    """ Indexed sprite class. This sprite is used for sprites where
    the appearance changes based on the info value at the location of
    the sprite.

    Public member variables:
    heightoffset -- height offset to apply when drawing this sprite.
                    i.e. positive numbers draw the sprite further into
                    the floor.
    xoffset -- horizontal offset when drawing this sprite. Positive
               numbers shift this sprite to the right. Always 0.
    important -- flag to indicate whether this sprite should be marked
                 if it is not visible.
    allowfloat -- flag for whether this sprite is allowed to float above
                  the ground due to special info values
    """

    def __init__(self, lumps, heightoffset=0, important=False, allowfloat=True):
        """ Initializes the current sprite based on the provided data:

        lumps -- a dictionary of wad lump instances, which should be
                patch-type lumps. The images and masks from each lump
                will be used for this sprite. The dictionary should
                be keyed for the info value that will be used to select
                each variant of the sprite. Key value of 0 must be
                included as a fall-back when info values are present
                used in the map.
        heightoffset -- height offset to apply when drawing this sprite.
                        i.e. positive numbers draw the sprite further into
                        the floor.
        important -- flag to indicate whether this sprite should be marked
                     if it is not visible.
        allowfloat -- flag for whether this sprite is allowed to float above
                      the ground due to special info values
        """
        self.image = dict()
        self.mask = dict()

        for info, lump in lumps.iteritems():
            self.image[info] = self.spritescale(lump.data.convert("RGB"))
            self.mask[info] = self.spritescale(lump.mask)

        self.heightoffset = heightoffset
        self.xoffset = 0
        self.important = important
        self.allowfloat = allowfloat

    def getimage(self, infoval=0, mappos=0):
        """ Obtains the correct sprite image as a PIL Image object
        for a given info value and map index. Image will vary based
        on info value only for an indexed sprite.
        """
        if infoval not in self.image.keys():
            infoval = 0
        return self.image[infoval]

    def getmask(self, infoval=0, mappos=0):
        """ Obtains the correct sprite mask as a PIL Image object
        for a given info value and map index. Image will vary based
        on info value only for an indexed sprite.
        """
        if infoval not in self.image.keys():
            infoval = 0
        return self.mask[infoval]


class blanksprite(sprite):
    """ Simple sprite class which always contains a blank image. Used
    for sprites that have no visual component, but are known. Otherwise
    identical to the basic sprite class.
    """

    def __init__(self):
        """ Initializes the blank sprites with a default totally
        transparentimage
        """
        self.image = Image.new("RGB", (96,96), (0,0,0))
        self.mask = Image.new("L", (96,96), 0)
        self.heightoffset = 0
        self.xoffset = 0
        self.important = False
        self.allowfloat = False


class compositesprite(sprite):
    """ Composite sprite class. Functionally equivalent to the base
    sprite class, except the sprite image is actually a combination
    of a few source images.

    Public member variables:
    heightoffset -- height offset to apply when drawing this sprite.
                    i.e. positive numbers draw the sprite further into
                    the floor.
    xoffset -- horizontal offset when drawing this sprite. Positive
               numbers shift this sprite to the right. Always 0.
    important -- flag to indicate whether this sprite should be marked
                 if it is not visible.
    allowfloat -- flag for whether this sprite is allowed to float above
                  the ground due to special info values
    """

    def __init__(self, lumps, offsets, heightoffset=0, important=False,
            glyphtype = -1, glyphpos = (0,0), glyphcolour = (0,0,0),
            font=None, text=None, allowfloat=True):
        """ Initializes the current sprite based on the provided data:

        lumps -- a list of wad lump instances, which should be a
                patch-type lumps. The images and masks from each lump
                will be combined together and used for this sprite.
        offsets -- a list of two-tuple offsets (x,y) indicating where
                   to draw each subsequent lump in the overall composite
                   sprite.
        heightoffset -- height offset to apply when drawing this sprite.
                        i.e. positive numbers draw the sprite further into
                        the floor.
        important -- flag to indicate whether this sprite should be marked
                     if it is not visible.
        glyphtype -- if specified, the corresponding glyph will be drawn
                     on top of this sprite. Glyph enumerations are
                     defined at the top of this file.
        glyphpos -- if drawing a glyph, this specifies the x,y coordinate
                    offset of the SCALED image to draw the top-left
                    corner of the glyph at
        glyphcolour -- a valid PIL-supported colour to use when drawing
                       the specified glyph. Not used by TEXT glyphs.
        font -- for TEXT glyphs only, the instance of the rottfont class
                to use for drawing the text,
        text -- for TEXT glyphs only, the actual text to write.
        allowfloat -- flag for whether this sprite is allowed to float above
                      the ground due to special info values
        """
        tempimage = Image.new("RGB", lumps[0].data.size, (0,0,0))
        tempmask = Image.new("L", lumps[0].mask.size, (0))
        for index, lump in enumerate(lumps):
            tempimage.paste(lump.data, offsets[index], lump.mask)
            tempmask.paste(lump.mask, offsets[index], lump.mask)

        self.image = self.spritescale(tempimage)
        self.mask = self.spritescale(tempmask)
        if glyphtype >= 0:
            self.drawglyph(glyphtype, glyphpos, glyphcolour, font, text)

        self.heightoffset = heightoffset
        self.xoffset = 0
        self.important = important
        self.allowfloat = allowfloat

class flatsprite(sprite):
    """ Flat sprite class. This sprite is composed of a source image
    flattened into a floor-like tile which can then be placed on
    the floor or on top of walls.

    Public member variables:
    heightoffset -- height offset to apply when drawing this sprite.
                    i.e. positive numbers draw the sprite further into
                    the floor. Always 56 for proper alignment.
    xoffset -- horizontal offset when drawing this sprite. Positive
               numbers shift this sprite to the right. Always -16 for
               proper alignment.
    important -- flag to indicate whether this sprite should be marked
                 if it is not visible. Always false.
    allowfloat -- flag for whether this sprite is allowed to float above
                  the ground due to special info values. Always true,
                  although this feature is not expected to be used.
    """

    def __init__(self, glyphlump, colour, glyphpos, angle):
        """ Initializes the current sprite based on the provided data:

        glyphlump -- a wad lump instance which should be a patch-type
                lump. The image and mask from this lump will be
                flattened and used for this sprite.
        colour -- a valid PIL colour which will be used as the background
                  for this flat sprite.
        glyphpos -- the (x, y) coordinate tuple specifying where the
                    sprite should be pasted in the 64 x 64 working image
                    before it is flattened.
        angle -- the angle that this flat sprite will eventually face.
                 This assumes that the sprite was originally facing
                 RIGHT (i.e. +x)
        """
        tempimage = Image.new("RGB", (64, 64), colour)
        tempimage.paste(glyphlump.data, glyphpos, glyphlump.mask)
        self.image = walldb.tile.floorskew(tempimage.rotate(angle))

        tempimage = Image.new("L", (64, 64), 128)
        self.mask = walldb.tile.floorskew(tempimage)
        self.heightoffset = 56
        self.xoffset = -16
        self.important = False
        self.allowfloat = True

class flatdirsprite(sprite):
    """ Flat directional sprite class. This sprite is composed of
    arrow or circle indicating a specific direction  flattened into a
    floor-like tile which can then be placed on the floor or on top of walls.

    Public member variables:
    heightoffset -- height offset to apply when drawing this sprite.
                    i.e. positive numbers draw the sprite further into
                    the floor. Always 56 for proper alignment.
    xoffset -- horizontal offset when drawing this sprite. Positive
               numbers shift this sprite to the right. Always -16 for
               proper alignment.
    important -- flag to indicate whether this sprite should be marked
                 if it is not visible. Always false.
    allowfloat -- flag for whether this sprite is allowed to float above
                  the ground due to special info values. Always true,
                  although this feature is not expected to be used.
    """

    def __init__(self, colour, direction, dircolour, diagonal=False):
        """ Initializes the current sprite based on the provided data:

        colour -- a valid PIL colour which will be used as the
                  background for this flat sprite.
        direction -- the direction that this flat sprite is facing
                     per the constants in the rtl module. If NODIR
                     is specified, a circle is drawn instead of an arrow.
        dircolour -- a valid PIL colour which will be used to draw the
                     arrow/circle for this sprite.
        diagonal -- if true, this sprite is actually pointing in a
                    diagonal direction 45 degrees counter-clockwise
                    from the direction constant. (e.g. RIGHT points
                    to up-right instead)
        """
        tempimage = Image.new("RGB", (64, 64), colour)

        pen = ImageDraw.Draw(tempimage)
        if direction == rtl.NODIR:
            # Circle for no direction
            pen.ellipse([(8,8), (56,56)], fill=dircolour, outline=dircolour)
            self.image = walldb.tile.floorskew(tempimage)
        else:
            # Arrows for directions
            if not diagonal:
                # Points right without rotation
                pen.polygon([(8,20), (32, 20), (32, 8), (56,32),
                    (32, 56), (32, 44), (8,44)], fill=dircolour, outline=dircolour)
            else:
                # Points up-right without rotation
                pen.polygon([(16, 12), (52, 12), (52, 46), (42, 38), (26, 54),
                    (8, 36), (24, 20)], fill=dircolour, outline=dircolour)

            self.image = walldb.tile.floorskew(tempimage.rotate(direction * 90))

        tempimage = Image.new("L", (64, 64), 128)
        self.mask = walldb.tile.floorskew(tempimage)
        self.heightoffset = 56
        self.xoffset = -16
        self.important = False
        self.allowfloat = True

class keysprite(sprite):
    """ Key sprite class. This is used for complicated key objects,
    which are present on their own, as well as used to "lock" doors.
    Additionally, the key should be properly coloured and indicated
    with a very clear key marker.

    Public member variables:
    wall -- the walldb.walltile instance representing the wall data
            to draw on the edge of any given locked door.
    glyph -- the key marker image to draw over the key's location
    linecolours -- a 2-element collection containing the two
                   PIL-compatible colours to draw the line between
                   the key indicator and the key sprite.
    heightoffset -- height offset to apply when drawing this sprite.
                    i.e. positive numbers draw the sprite further into
                    the floor. Always 0
    xoffset -- horizontal offset when drawing this sprite. Positive
               numbers shift this sprite to the right. Always 0.
    important -- flag to indicate whether this sprite should be marked
                 if it is not visible. Always false, since key markers
                  are drawn specially.
    allowfloat -- flag for whether this sprite is allowed to float above
                  the ground due to special info values. Always false.
    """

    def __init__(self, spritelump, walllump, guilump, colourindex, linecolours):
        """ Initializes the current sprite based on the provided data:

        spritelump -- a wad lump instance, which should be a patch-type
                      lump. The image and mask from this lump will be
                      used when drawing the key sprite into the world.
        walllump -- a wad lump instance, which should be a wall-type
                    lump. This should be the wall instance corresponding
                    to this key's lock texture. This will be used
                    whenever the key sprite is drawn over a doorway to
                    replace the door's native edge texture.
        guilump -- a wad lump instance, which should be a pic-type lump.
                   This should be the GUI indication of the specified
                   key which will be double-scaled and drawn above the
                   key location itself.
        colourindex -- the index in the ROTT palette to recolour this
                       key using. See the recolour_sprite method for
                       more details.
        linecolours -- a 2-element collection containing the two
                       PIL-compatible colours to draw the line between
                       the key indicator and the key sprite.
        """
        self.image = self.spritescale(self.recolour_sprite(spritelump.data, colourindex))
        self.mask = self.spritescale(spritelump.mask)

        self.wall = walldb.walltile([walllump.data])
        self.glyph = self.double_scale(guilump.data)

        self.linecolours = linecolours

        # All keys have no offsets
        self.heightoffset = 0
        self.xoffset = 0

        # Keys ARE important, but indicators are explicitly drawn.
        # We don't want to trigger the normal obscured sprite logic
        self.important = False

        self.allowfloat = True

    @staticmethod
    def double_scale(image):
        """ Simply doubles the size of the specified PIL Image"""
        return image.transform((image.size[0]*2,image.size[1]*2),
            Image.AFFINE, (0.5, 0, 0, 0, 0.5, 0), Image.NEAREST)

class gassprite(sprite):
    """ Gas sprite class. This is used for gas-grates and for gas-locked
    doors. Gas locked doors need to be marked by a green overlay for
    identification.

    Public member variables:
    wall -- a walldb.thintile instance representing the green overlay
            for any locked doors.
    heightoffset -- height offset to apply when drawing this sprite.
                    i.e. positive numbers draw the sprite further into
                    the floor.
    xoffset -- horizontal offset when drawing this sprite. Positive
               numbers shift this sprite to the right. Always 0.
    important -- flag to indicate whether this sprite should be marked
                 if it is not visible.
    allowfloat -- flag for whether this sprite is allowed to float above
                  the ground due to special info values
    """

    def __init__(self, lump, heightoffset=0, important=False,
            glyphtype = -1, glyphpos = (0,0), glyphcolour = (0,0,0),
            font=None, text=None, allowfloat=True):
        """ Initializes the current sprite based on the provided data:

        lump -- a wad lump instance, which should be a patch-type lump.
                The image and mask from this lump will be used for this
                sprite.
        heightoffset -- height offset to apply when drawing this sprite.
                        i.e. positive numbers draw the sprite further into
                        the floor.
        important -- flag to indicate whether this sprite should be marked
                     if it is not visible.
        glyphtype -- if specified, the corresponding glyph will be drawn
                     on top of this sprite. Glyph enumerations are
                     defined at the top of this file.
        glyphpos -- if drawing a glyph, this specifies the x,y coordinate
                    offset of the SCALED image to draw the top-left
                    corner of the glyph at
        glyphcolour -- a valid PIL-supported colour to use when drawing
                       the specified glyph. Not used by TEXT glyphs.
        font -- for TEXT glyphs only, the instance of the rottfont class
                to use for drawing the text,
        text -- for TEXT glyphs only, the actual text to write.
        allowfloat -- flag for whether this sprite is allowed to float above
                      the ground due to special info values
        """
        super(gassprite, self).__init__(lump, heightoffset, important,
            glyphtype, glyphpos, glyphcolour, font, text, allowfloat)

        self.wall = walldb.thintile(
            [Image.new("RGB", (64, 64), (4, 96, 4))],
            [Image.new("L", (64, 64), 128)],
            None)

class randomcoloursprite(sprite):
    """ A sprite that is randomly re-coloured whenever it is drawn in
    the map. Used for sprites that can come in a variety of colours,
    such as player sprites and Comm-bat collectables.

    Public member variables:
    heightoffset -- height offset to apply when drawing this sprite.
                    i.e. positive numbers draw the sprite further into
                    the floor.
    xoffset -- horizontal offset when drawing this sprite. Positive
               numbers shift this sprite to the right. Always 0.
    important -- flag to indicate whether this sprite should be marked
                 if it is not visible.
    allowfloat -- flag for whether this sprite is allowed to float above
                  the ground due to special info values
    """

    def __init__(self, lump, heightoffset=0, important=False,
            allowfloat=True):
        """ Initializes the current sprite based on the provided data:

        lump -- a wad lump instance, which should be a patch-type lump.
                The image and mask from this lump will be used for this
                sprite.
        heightoffset -- height offset to apply when drawing this sprite.
                        i.e. positive numbers draw the sprite further into
                        the floor.
        important -- flag to indicate whether this sprite should be marked
                     if it is not visible.
        allowfloat -- flag for whether this sprite is allowed to float above
                      the ground due to special info values
        """
        self.image = self.spritescale(lump.data)
        self.mask = self.spritescale(lump.mask)

        self.heightoffset = heightoffset
        self.xoffset = 0
        self.important = important
        self.allowfloat=allowfloat
        self.lastpos = -1
        self.colour = 220

    def getimage(self, infoval=0, mappos=0):
        if self.lastpos != mappos:
            self.colour = random.choice(
                [220, 60, 13, 168, 27, 95, 139, 118, 33, 231, 36])

        self.lastpos = mappos

        return self.recolour_sprite(self.image, self.colour)

class spritedb:
    """ Database of all known index to sprite mappings.

    Public member variables:
    sprites -- an array of sprites, indexed by the sprite id. Each
               position will contain a corresponding sprite object.
    """

    def __init__(self, WAD):
        """ Populates the index to sprite mappings in the sprite
        database using the sprites found in the provided WAD file
        instance.
        """
        self.sprites = [None] * 512

        # Ensure random sprites are random
        random.seed()

        # Player Start
        # NOTE: Player directions seem different
        self.sprites[19] = randomcoloursprite(WAD.db["SHAP"]["CASS6"], important=True) # -y (ur)
        self.sprites[20] = randomcoloursprite(WAD.db["SHAP"]["CASS8"], important=True) # +x (dr)
        self.sprites[21] = randomcoloursprite(WAD.db["SHAP"]["CASS2"], important=True) # +y (dl)
        self.sprites[22] = randomcoloursprite(WAD.db["SHAP"]["CASS4"], important=True) # -x (ul)
        # Deathmatch Spawn
        self.sprites[274] = randomcoloursprite(WAD.db["SHAP"]["BARS6"]) # +x (dr)
        self.sprites[275] = randomcoloursprite(WAD.db["SHAP"]["BARS8"]) # +x (dr)
        self.sprites[276] = randomcoloursprite(WAD.db["SHAP"]["BARS2"]) # +y (dl)
        self.sprites[277] = randomcoloursprite(WAD.db["SHAP"]["BARS4"]) # -x (ul)


        self.sprites[106] = blanksprite() # Secret Exit
        self.sprites[107] = blanksprite() # Exit
        self.sprites[460] = blanksprite() # Ambient wind sound

        # Elevators
        for i in range(8):
            self.sprites[90+i] = textsprite("Elevator {}".format(i+1))

        self.assign_enemies(WAD)
        self.assign_statics(WAD)
        self.assign_dynamics(WAD)


    def assign_enemies(self, WAD):
        """ Populates the index to sprite mappings for all enemy sprites."""

        enemyfont = rottfont(WAD.db["General"]["NEWFNT1"], (255, 64, 0))

        # Random Enemy!
        self.sprites[122] = compositesprite(
            [WAD.db["SHAP"]["LWGS8"], WAD.db["SHAP"]["LIGS8"], WAD.db["SHAP"]["HG2S8"],],
            [(-32, -16), (32, -16), (0, 0)], 16) # +x (dr)
        self.sprites[123] = compositesprite(
            [WAD.db["SHAP"]["LIGS6"], WAD.db["SHAP"]["HG2S6"], WAD.db["SHAP"]["LWGS6"]],
            [(0, -32), (32, -16), (0, 0)], 16) # -y (ur)
        self.sprites[124] = compositesprite(
            [WAD.db["SHAP"]["LIGS4"], WAD.db["SHAP"]["HG2S4"], WAD.db["SHAP"]["LWGS4"]],
            [(0, -32), (-32, -16), (0, 0)], 16) # -x (ul)
        self.sprites[125] = compositesprite(
            [WAD.db["SHAP"]["LIGS2"], WAD.db["SHAP"]["LWGS2"], WAD.db["SHAP"]["HG2S2"]],
            [(-32, -16), (32, -16), (0, 0)], 16) # +y (dl)


        # Light Guard
        # ----------------------------
        # Hard
        self.sprites[126] = sprite(WAD.db["SHAP"]["LWGS8"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # +x (dr)
        self.sprites[127] = sprite(WAD.db["SHAP"]["LWGS6"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # -y (ur)
        self.sprites[128] = sprite(WAD.db["SHAP"]["LWGS4"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # -x (ul)
        self.sprites[129] = sprite(WAD.db["SHAP"]["LWGS2"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # +y (dl)
        # Normal/Easy
        self.sprites[108] = sprite(WAD.db["SHAP"]["LWGS8"]) # +x (dr)
        self.sprites[109] = sprite(WAD.db["SHAP"]["LWGS6"]) # -y (ur)
        self.sprites[110] = sprite(WAD.db["SHAP"]["LWGS4"]) # -x (ul)
        self.sprites[111] = sprite(WAD.db["SHAP"]["LWGS2"]) # +y (dl)

        # Patrolling
        # Hard
        self.sprites[130] = sprite(WAD.db["SHAP"]["LWGW28"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # +x (dr)
        self.sprites[131] = sprite(WAD.db["SHAP"]["LWGW26"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # -y (ur)
        self.sprites[132] = sprite(WAD.db["SHAP"]["LWGW24"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # -x (ul)
        self.sprites[133] = sprite(WAD.db["SHAP"]["LWGW22"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # +y (dl)
        # Normal/Easy
        self.sprites[112] = sprite(WAD.db["SHAP"]["LWGW28"]) # +x (dr)
        self.sprites[113] = sprite(WAD.db["SHAP"]["LWGW26"]) # -y (ur)
        self.sprites[114] = sprite(WAD.db["SHAP"]["LWGW24"]) # -x (ul)
        self.sprites[115] = sprite(WAD.db["SHAP"]["LWGW22"]) # +y (dl)

        # Ambush?
        # Hard
        self.sprites[134] = sprite(WAD.db["SHAP"]["LWGS8"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^!") # +x (dr)
        self.sprites[135] = sprite(WAD.db["SHAP"]["LWGS6"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^!") # -y (ur)
        self.sprites[136] = sprite(WAD.db["SHAP"]["LWGS4"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^!") # -x (ul)
        self.sprites[137] = sprite(WAD.db["SHAP"]["LWGS2"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^!") # +y (dl)
        # Normal/Easy
        self.sprites[116] = sprite(WAD.db["SHAP"]["LWGS8"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="!") # +x (dr)
        self.sprites[117] = sprite(WAD.db["SHAP"]["LWGS6"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="!") # -y (ur)
        self.sprites[118] = sprite(WAD.db["SHAP"]["LWGS4"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="!") # -x (ul)
        self.sprites[119] = sprite(WAD.db["SHAP"]["LWGS2"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="!") # +y (dl)

        # Sneaky:
        # Hard
        self.sprites[138] = sprite(WAD.db["SHAP"]["SNGDEAD"])
        # Normal/Easy
        self.sprites[120] = sprite(WAD.db["SHAP"]["SNGDEAD"])

        # High Guard:
        # ----------------------------
        # Hard
        self.sprites[162] = sprite(WAD.db["SHAP"]["HG2S8"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # +x (dr)
        self.sprites[163] = sprite(WAD.db["SHAP"]["HG2S6"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # -y (ur)
        self.sprites[164] = sprite(WAD.db["SHAP"]["HG2S4"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # -x (ul)
        self.sprites[165] = sprite(WAD.db["SHAP"]["HG2S2"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # +y (dl)
        # Normal/Easy
        self.sprites[144] = sprite(WAD.db["SHAP"]["HG2S8"]) # +x (dr)
        self.sprites[145] = sprite(WAD.db["SHAP"]["HG2S6"]) # -y (ur)
        self.sprites[146] = sprite(WAD.db["SHAP"]["HG2S4"]) # -x (ul)
        self.sprites[147] = sprite(WAD.db["SHAP"]["HG2S2"]) # +y (dl)

        # Ambush?
        # Hard
        self.sprites[170] = sprite(WAD.db["SHAP"]["HG2S8"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^!") # +x (dr)
        self.sprites[171] = sprite(WAD.db["SHAP"]["HG2S6"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^!") # -y (ur)
        self.sprites[172] = sprite(WAD.db["SHAP"]["HG2S4"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^!") # -x (ul)
        self.sprites[173] = sprite(WAD.db["SHAP"]["HG2S2"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^!") # +y (dl)
        # Normal/Easy
        self.sprites[152] = sprite(WAD.db["SHAP"]["HG2S8"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="!") # +x (dr)
        self.sprites[153] = sprite(WAD.db["SHAP"]["HG2S6"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="!") # -y (ur)
        self.sprites[154] = sprite(WAD.db["SHAP"]["HG2S4"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="!") # -x (ul)
        self.sprites[155] = sprite(WAD.db["SHAP"]["HG2S2"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="!") # +y (dl)

        # Patrolling
        # Hard
        self.sprites[166] = sprite(WAD.db["SHAP"]["HG2W28"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # +x (dr)
        self.sprites[167] = sprite(WAD.db["SHAP"]["HG2W26"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # -y (ur)
        self.sprites[168] = sprite(WAD.db["SHAP"]["HG2W24"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # -x (ul)
        self.sprites[169] = sprite(WAD.db["SHAP"]["HG2W22"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # +y (dl)
        # Normal/Easy
        self.sprites[148] = sprite(WAD.db["SHAP"]["HG2W28"]) # +x (dr)
        self.sprites[149] = sprite(WAD.db["SHAP"]["HG2W26"]) # -y (ur)
        self.sprites[150] = sprite(WAD.db["SHAP"]["HG2W24"]) # -x (ul)
        self.sprites[151] = sprite(WAD.db["SHAP"]["HG2W22"]) # +y (dl)

        # Blitz Guard:
        # ----------------------------
        # Hard
        self.sprites[342] = sprite(WAD.db["SHAP"]["LIGS8"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # +x (dr)
        self.sprites[343] = sprite(WAD.db["SHAP"]["LIGS6"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # -y (ur)
        self.sprites[344] = sprite(WAD.db["SHAP"]["LIGS4"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # -x (ul)
        self.sprites[345] = sprite(WAD.db["SHAP"]["LIGS2"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # +y (dl)
        # Normal/Easy
        self.sprites[324] = sprite(WAD.db["SHAP"]["LIGS8"]) # +x (dr)
        self.sprites[325] = sprite(WAD.db["SHAP"]["LIGS6"]) # -y (ur)
        self.sprites[326] = sprite(WAD.db["SHAP"]["LIGS4"]) # -x (ul)
        self.sprites[327] = sprite(WAD.db["SHAP"]["LIGS2"]) # +y (dl)

        # Ambush?
        # Hard
        self.sprites[350] = sprite(WAD.db["SHAP"]["LIGS8"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^!") # +x (dr)
        self.sprites[351] = sprite(WAD.db["SHAP"]["LIGS6"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^!") # -y (ur)
        self.sprites[352] = sprite(WAD.db["SHAP"]["LIGS4"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^!") # -x (ul)
        self.sprites[353] = sprite(WAD.db["SHAP"]["LIGS2"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^!") # +y (dl)
        # Normal/Easy
        self.sprites[332] = sprite(WAD.db["SHAP"]["LIGS8"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="!") # +x (dr)
        self.sprites[333] = sprite(WAD.db["SHAP"]["LIGS6"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="!") # -y (ur)
        self.sprites[334] = sprite(WAD.db["SHAP"]["LIGS4"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="!") # -x (ul)
        self.sprites[335] = sprite(WAD.db["SHAP"]["LIGS2"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="!") # +y (dl)

        # Patrolling
        # Hard
        self.sprites[346] = sprite(WAD.db["SHAP"]["LIGW28"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # +x (dr)
        self.sprites[347] = sprite(WAD.db["SHAP"]["LIGW26"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # -y (ur)
        self.sprites[348] = sprite(WAD.db["SHAP"]["LIGW24"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # -x (ul)
        self.sprites[349] = sprite(WAD.db["SHAP"]["LIGW22"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # +y (dl)
        # Normal/Easy
        self.sprites[328] = sprite(WAD.db["SHAP"]["LIGW28"]) # +x (dr)
        self.sprites[329] = sprite(WAD.db["SHAP"]["LIGW26"]) # -y (ur)
        self.sprites[330] = sprite(WAD.db["SHAP"]["LIGW24"]) # -x (ul)
        self.sprites[331] = sprite(WAD.db["SHAP"]["LIGW22"]) # +y (dl)

        # Overpatrol:
        # ----------------------------
        # Hard
        self.sprites[234] = sprite(WAD.db["SHAP"]["OBPS8"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # +x (dr)
        self.sprites[235] = sprite(WAD.db["SHAP"]["OBPS6"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # -y (ur)
        self.sprites[236] = sprite(WAD.db["SHAP"]["OBPS4"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # -x (ul)
        self.sprites[237] = sprite(WAD.db["SHAP"]["OBPS2"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # +y (dl)
        # Normal/Easy
        self.sprites[216] = sprite(WAD.db["SHAP"]["OBPS8"]) # +x (dr)
        self.sprites[217] = sprite(WAD.db["SHAP"]["OBPS6"]) # -y (ur)
        self.sprites[218] = sprite(WAD.db["SHAP"]["OBPS4"]) # -x (ul)
        self.sprites[219] = sprite(WAD.db["SHAP"]["OBPS2"]) # +y (dl)

        # Ambush?
        # Hard
        self.sprites[242] = sprite(WAD.db["SHAP"]["OBPS8"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^!") # +x (dr)
        self.sprites[243] = sprite(WAD.db["SHAP"]["OBPS6"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^!") # -y (ur)
        self.sprites[244] = sprite(WAD.db["SHAP"]["OBPS4"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^!") # -x (ul)
        self.sprites[245] = sprite(WAD.db["SHAP"]["OBPS2"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^!") # +y (dl)
        # Normal/Easy
        self.sprites[224] = sprite(WAD.db["SHAP"]["OBPS8"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="!") # +x (dr)
        self.sprites[225] = sprite(WAD.db["SHAP"]["OBPS6"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="!") # -y (ur)
        self.sprites[226] = sprite(WAD.db["SHAP"]["OBPS4"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="!") # -x (ul)
        self.sprites[227] = sprite(WAD.db["SHAP"]["OBPS2"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="!") # +y (dl)

        # Patrolling
        # Hard
        self.sprites[238] = sprite(WAD.db["SHAP"]["OBPW28"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # +x (dr)
        self.sprites[239] = sprite(WAD.db["SHAP"]["OBPW26"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # -y (ur)
        self.sprites[240] = sprite(WAD.db["SHAP"]["OBPW24"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # -x (ul)
        self.sprites[241] = sprite(WAD.db["SHAP"]["OBPW22"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # +y (dl)
        # Normal/Easy
        self.sprites[220] = sprite(WAD.db["SHAP"]["OBPW28"]) # +x (dr)
        self.sprites[221] = sprite(WAD.db["SHAP"]["OBPW26"]) # -y (ur)
        self.sprites[222] = sprite(WAD.db["SHAP"]["OBPW24"]) # -x (ul)
        self.sprites[223] = sprite(WAD.db["SHAP"]["OBPW22"]) # +y (dl)

        # Strike Guard:
        # ----------------------------
        # Hard
        self.sprites[198] = sprite(WAD.db["SHAP"]["ANGS8"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # +x (dr)
        self.sprites[199] = sprite(WAD.db["SHAP"]["ANGS6"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # -y (ur)
        self.sprites[200] = sprite(WAD.db["SHAP"]["ANGS4"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # -x (ul)
        self.sprites[201] = sprite(WAD.db["SHAP"]["ANGS2"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # +y (dl)
        # Normal/Easy
        self.sprites[180] = sprite(WAD.db["SHAP"]["ANGS8"]) # +x (dr)
        self.sprites[181] = sprite(WAD.db["SHAP"]["ANGS6"]) # -y (ur)
        self.sprites[182] = sprite(WAD.db["SHAP"]["ANGS4"]) # -x (ul)
        self.sprites[183] = sprite(WAD.db["SHAP"]["ANGS2"]) # +y (dl)

        # Ambush?
        # Hard
        self.sprites[206] = sprite(WAD.db["SHAP"]["ANGS8"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^!") # +x (dr)
        self.sprites[207] = sprite(WAD.db["SHAP"]["ANGS6"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^!") # -y (ur)
        self.sprites[208] = sprite(WAD.db["SHAP"]["ANGS4"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^!") # -x (ul)
        self.sprites[209] = sprite(WAD.db["SHAP"]["ANGS2"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^!") # +y (dl)
        # Normal/Easy
        self.sprites[188] = sprite(WAD.db["SHAP"]["ANGS8"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="!") # +x (dr)
        self.sprites[189] = sprite(WAD.db["SHAP"]["ANGS6"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="!") # -y (ur)
        self.sprites[190] = sprite(WAD.db["SHAP"]["ANGS4"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="!") # -x (ul)
        self.sprites[191] = sprite(WAD.db["SHAP"]["ANGS2"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="!") # +y (dl)

        # Patrolling
        # Hard
        self.sprites[202] = sprite(WAD.db["SHAP"]["ANGW28"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # +x (dr)
        self.sprites[203] = sprite(WAD.db["SHAP"]["ANGW26"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # -y (ur)
        self.sprites[204] = sprite(WAD.db["SHAP"]["ANGW24"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # -x (ul)
        self.sprites[205] = sprite(WAD.db["SHAP"]["ANGW22"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # +y (dl)
        # Normal/Easy
        self.sprites[184] = sprite(WAD.db["SHAP"]["ANGW28"]) # +x (dr)
        self.sprites[185] = sprite(WAD.db["SHAP"]["ANGW26"]) # -y (ur)
        self.sprites[186] = sprite(WAD.db["SHAP"]["ANGW24"]) # -x (ul)
        self.sprites[187] = sprite(WAD.db["SHAP"]["ANGW22"]) # +y (dl)


        # Triad Enforcer
        # ----------------------------
        # Hard
        self.sprites[306] = sprite(WAD.db["SHAP"]["TRIS8"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # +x (dr)
        self.sprites[307] = sprite(WAD.db["SHAP"]["TRIS6"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # -y (ur)
        self.sprites[308] = sprite(WAD.db["SHAP"]["TRIS4"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # -x (ul)
        self.sprites[309] = sprite(WAD.db["SHAP"]["TRIS2"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # +y (dl)
        # Normal/Easy
        self.sprites[288] = sprite(WAD.db["SHAP"]["TRIS8"]) # +x (dr)
        self.sprites[289] = sprite(WAD.db["SHAP"]["TRIS6"]) # -y (ur)
        self.sprites[290] = sprite(WAD.db["SHAP"]["TRIS4"]) # -x (ul)
        self.sprites[291] = sprite(WAD.db["SHAP"]["TRIS2"]) # +y (dl)

        # Ambush?
        # Hard
        self.sprites[314] = sprite(WAD.db["SHAP"]["TRIS8"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^!") # +x (dr)
        self.sprites[315] = sprite(WAD.db["SHAP"]["TRIS6"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^!") # -y (ur)
        self.sprites[316] = sprite(WAD.db["SHAP"]["TRIS4"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^!") # -x (ul)
        self.sprites[317] = sprite(WAD.db["SHAP"]["TRIS2"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^!") # +y (dl)
        # Normal/Easy
        self.sprites[296] = sprite(WAD.db["SHAP"]["TRIS8"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="!") # +x (dr)
        self.sprites[297] = sprite(WAD.db["SHAP"]["TRIS6"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="!") # -y (ur)
        self.sprites[298] = sprite(WAD.db["SHAP"]["TRIS4"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="!") # -x (ul)
        self.sprites[299] = sprite(WAD.db["SHAP"]["TRIS2"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="!") # +y (dl)

        # Patrolling
        # Hard
        self.sprites[310] = sprite(WAD.db["SHAP"]["TRIW28"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # +x (dr)
        self.sprites[311] = sprite(WAD.db["SHAP"]["TRIW26"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # -y (ur)
        self.sprites[312] = sprite(WAD.db["SHAP"]["TRIW24"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # -x (ul)
        self.sprites[313] = sprite(WAD.db["SHAP"]["TRIW22"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # +y (dl)
        # Normal/Easy
        self.sprites[292] = sprite(WAD.db["SHAP"]["TRIW28"]) # +x (dr)
        self.sprites[293] = sprite(WAD.db["SHAP"]["TRIW26"]) # -y (ur)
        self.sprites[294] = sprite(WAD.db["SHAP"]["TRIW24"]) # -x (ul)
        self.sprites[295] = sprite(WAD.db["SHAP"]["TRIW22"]) # +y (dl)


        # Death Monk
        # ----------------------------
        # Hard
        self.sprites[378] = sprite(WAD.db["SHAP"]["MONS8"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # +x (dr)
        self.sprites[379] = sprite(WAD.db["SHAP"]["MONS6"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # -y (ur)
        self.sprites[380] = sprite(WAD.db["SHAP"]["MONS4"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # -x (ul)
        self.sprites[381] = sprite(WAD.db["SHAP"]["MONS2"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # +y (dl)
        # Normal/Easy
        self.sprites[360] = sprite(WAD.db["SHAP"]["MONS8"]) # +x (dr)
        self.sprites[361] = sprite(WAD.db["SHAP"]["MONS6"]) # -y (ur)
        self.sprites[362] = sprite(WAD.db["SHAP"]["MONS4"]) # -x (ul)
        self.sprites[363] = sprite(WAD.db["SHAP"]["MONS2"]) # +y (dl)

        # Ambush?
        # Hard
        self.sprites[386] = sprite(WAD.db["SHAP"]["MONS8"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^!") # +x (dr)
        self.sprites[387] = sprite(WAD.db["SHAP"]["MONS6"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^!") # -y (ur)
        self.sprites[388] = sprite(WAD.db["SHAP"]["MONS4"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^!") # -x (ul)
        self.sprites[389] = sprite(WAD.db["SHAP"]["MONS2"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^!") # +y (dl)
        # Normal/Easy
        self.sprites[368] = sprite(WAD.db["SHAP"]["MONS8"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="!") # +x (dr)
        self.sprites[369] = sprite(WAD.db["SHAP"]["MONS6"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="!") # -y (ur)
        self.sprites[370] = sprite(WAD.db["SHAP"]["MONS4"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="!") # -x (ul)
        self.sprites[371] = sprite(WAD.db["SHAP"]["MONS2"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="!") # +y (dl)

        # Patrolling
        # Hard
        self.sprites[382] = sprite(WAD.db["SHAP"]["MONW28"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # +x (dr)
        self.sprites[383] = sprite(WAD.db["SHAP"]["MONW26"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # -y (ur)
        self.sprites[384] = sprite(WAD.db["SHAP"]["MONW24"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # -x (ul)
        self.sprites[385] = sprite(WAD.db["SHAP"]["MONW22"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # +y (dl)
        # Normal/Easy
        self.sprites[364] = sprite(WAD.db["SHAP"]["MONW28"]) # +x (dr)
        self.sprites[365] = sprite(WAD.db["SHAP"]["MONW26"]) # -y (ur)
        self.sprites[366] = sprite(WAD.db["SHAP"]["MONW24"]) # -x (ul)
        self.sprites[367] = sprite(WAD.db["SHAP"]["MONW22"]) # +y (dl)




        # DeathFire Monk
        # ----------------------------
        # Hard
        self.sprites[414] = sprite(WAD.db["SHAP"]["ALLS8"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # +x (dr)
        self.sprites[415] = sprite(WAD.db["SHAP"]["ALLS6"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # -y (ur)
        self.sprites[416] = sprite(WAD.db["SHAP"]["ALLS4"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # -x (ul)
        self.sprites[417] = sprite(WAD.db["SHAP"]["ALLS2"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # +y (dl)
        # Normal/Easy
        self.sprites[396] = sprite(WAD.db["SHAP"]["ALLS8"]) # +x (dr)
        self.sprites[397] = sprite(WAD.db["SHAP"]["ALLS6"]) # -y (ur)
        self.sprites[398] = sprite(WAD.db["SHAP"]["ALLS4"]) # -x (ul)
        self.sprites[399] = sprite(WAD.db["SHAP"]["ALLS2"]) # +y (dl)

        # Ambush?
        # Hard
        self.sprites[422] = sprite(WAD.db["SHAP"]["ALLS8"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^!") # +x (dr)
        self.sprites[423] = sprite(WAD.db["SHAP"]["ALLS6"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^!") # -y (ur)
        self.sprites[424] = sprite(WAD.db["SHAP"]["ALLS4"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^!") # -x (ul)
        self.sprites[425] = sprite(WAD.db["SHAP"]["ALLS2"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^!") # +y (dl)
        # Normal/Easy
        self.sprites[404] = sprite(WAD.db["SHAP"]["ALLS8"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="!") # +x (dr)
        self.sprites[405] = sprite(WAD.db["SHAP"]["ALLS6"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="!") # -y (ur)
        self.sprites[406] = sprite(WAD.db["SHAP"]["ALLS4"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="!") # -x (ul)
        self.sprites[407] = sprite(WAD.db["SHAP"]["ALLS2"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="!") # +y (dl)

        # Patrolling
        # Hard
        self.sprites[418] = sprite(WAD.db["SHAP"]["ALLW28"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # +x (dr)
        self.sprites[419] = sprite(WAD.db["SHAP"]["ALLW26"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # -y (ur)
        self.sprites[420] = sprite(WAD.db["SHAP"]["ALLW24"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # -x (ul)
        self.sprites[421] = sprite(WAD.db["SHAP"]["ALLW22"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # +y (dl)
        # Normal/Easy
        self.sprites[400] = sprite(WAD.db["SHAP"]["ALLW28"]) # +x (dr)
        self.sprites[401] = sprite(WAD.db["SHAP"]["ALLW26"]) # -y (ur)
        self.sprites[402] = sprite(WAD.db["SHAP"]["ALLW24"]) # -x (ul)
        self.sprites[403] = sprite(WAD.db["SHAP"]["ALLW22"]) # +y (dl)


        # Patrol Robot
        # ----------------------------
        # Hard
        self.sprites[176] = sprite(WAD.db["SHAP"]["ROBGRD15"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # +x (dr)
        self.sprites[177] = sprite(WAD.db["SHAP"]["ROBGRD11"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # -y (ur)
        self.sprites[178] = sprite(WAD.db["SHAP"]["ROBOGRD7"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # -x (ul)
        self.sprites[179] = sprite(WAD.db["SHAP"]["ROBOGRD3"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # +y (dl)
        # Normal/Easy
        self.sprites[158] = sprite(WAD.db["SHAP"]["ROBGRD15"]) # +x (dr)
        self.sprites[159] = sprite(WAD.db["SHAP"]["ROBGRD11"]) # -y (ur)
        self.sprites[160] = sprite(WAD.db["SHAP"]["ROBOGRD7"]) # -x (ul)
        self.sprites[161] = sprite(WAD.db["SHAP"]["ROBOGRD3"]) # +y (dl)


        # Ballistikraft
        # ----------------------------
        # Hard
        self.sprites[426] = sprite(WAD.db["SHAP"]["BCRAFT15"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # +x (dr)
        self.sprites[427] = sprite(WAD.db["SHAP"]["BCRAFT11"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # -y (ur)
        self.sprites[428] = sprite(WAD.db["SHAP"]["BCRAFT7"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # -x (ul)
        self.sprites[429] = sprite(WAD.db["SHAP"]["BCRAFT3"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # +y (dl)
        # Normal/Easy
        self.sprites[408] = sprite(WAD.db["SHAP"]["BCRAFT15"]) # +x (dr)
        self.sprites[409] = sprite(WAD.db["SHAP"]["BCRAFT11"]) # -y (ur)
        self.sprites[410] = sprite(WAD.db["SHAP"]["BCRAFT7"]) # -x (ul)
        self.sprites[411] = sprite(WAD.db["SHAP"]["BCRAFT3"]) # +y (dl)


        # 4-Way Guns
        # ----------------------------
        self.sprites[89] = sprite(WAD.db["SHAP"]["GUNEMPF1"])
        self.sprites[211] = sprite(WAD.db["SHAP"]["GUNEMPF1"])


        # Rising Gun
        # ----------------------------
        # Hard
        self.sprites[212] = sprite(WAD.db["SHAP"]["GRISE58"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # +x (dr)
        self.sprites[213] = sprite(WAD.db["SHAP"]["GRISE56"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # -y (ur)
        self.sprites[214] = sprite(WAD.db["SHAP"]["GRISE54"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # -x (ul)
        self.sprites[215] = sprite(WAD.db["SHAP"]["GRISE52"],
            glyphtype = TEXT, glyphpos = (52,68), font = enemyfont, text="^") # +y (dl)
        # Normal/Easy
        self.sprites[194] = sprite(WAD.db["SHAP"]["GRISE58"]) # +x (dr)
        self.sprites[195] = sprite(WAD.db["SHAP"]["GRISE56"]) # -y (ur)
        self.sprites[196] = sprite(WAD.db["SHAP"]["GRISE54"]) # -x (ul)
        self.sprites[197] = sprite(WAD.db["SHAP"]["GRISE52"]) # +y (dl)


        # Bosses and related sprites:
        # ----------------------------
        self.sprites[98] = sprite(WAD.db["SHAP"]["ETOUCH1"]) # Darian's Pushbutton
        self.sprites[99] = sprite(WAD.db["SHAP"]["DARS8"], important=True) # General Darian
        self.sprites[100] = sprite(WAD.db["SHAP"]["HSIT8"], important=True) # Sebastian Krist
        self.sprites[101] = sprite(WAD.db["SHAP"]["THBALL5"], important=True) # El Obscuro
        self.sprites[102] = compositesprite(
            [WAD.db["SHAP"]["RSW15"], WAD.db["SHAP"]["RBODY115"], WAD.db["SHAP"]["RHEAD115"],],
            [(0, 0), (0, 0), (0, 0)], important=True) # NME
        self.sprites[103] = sprite(WAD.db["SHAP"]["TOMHEAD2"], important=True) # El Obscuro (Snake)

    def assign_dynamics(self, WAD):
        """ Populates the index to sprite mappings for all dynamic
        level sprites (e.g pushwalls, traps, trampolines, GADs, etc.).
        """

        # Floor/Wall Arrows. Pushwalls or redirectors
        self.sprites[72] = flatdirsprite((128, 128, 128), rtl.RIGHT,(0, 0, 255))
        self.sprites[73] = flatdirsprite((128, 128, 128), rtl.RIGHT,(0, 0, 255), diagonal=True)
        self.sprites[74] = flatdirsprite((128, 128, 128), rtl.UP,   (0, 0, 255))
        self.sprites[75] = flatdirsprite((128, 128, 128), rtl.UP,   (0, 0, 255), diagonal=True)
        self.sprites[76] = flatdirsprite((128, 128, 128), rtl.LEFT, (0, 0, 255))
        self.sprites[77] = flatdirsprite((128, 128, 128), rtl.LEFT, (0, 0, 255), diagonal=True)
        self.sprites[78] = flatdirsprite((128, 128, 128), rtl.DOWN, (0, 0, 255))
        self.sprites[79] = flatdirsprite((128, 128, 128), rtl.DOWN, (0, 0, 255), diagonal=True)

        # Non-directional pushwall
        self.sprites[80] = flatdirsprite((128, 128, 128), rtl.NODIR, (0, 0, 255))

        # Moving walls
        self.sprites[256] = flatdirsprite((128, 128, 128), rtl.RIGHT,(255, 0, 0))
        self.sprites[257] = flatdirsprite((128, 128, 128), rtl.UP,   (255, 0, 0))
        self.sprites[258] = flatdirsprite((128, 128, 128), rtl.LEFT, (255, 0, 0))
        self.sprites[259] = flatdirsprite((128, 128, 128), rtl.DOWN, (255, 0, 0))

        self.sprites[300] = flatdirsprite((128, 128, 128), rtl.RIGHT,(255, 0, 0))
        self.sprites[318] = flatdirsprite((128, 128, 128), rtl.UP,   (255, 0, 0))
        self.sprites[336] = flatdirsprite((128, 128, 128), rtl.LEFT, (255, 0, 0))
        self.sprites[354] = flatdirsprite((128, 128, 128), rtl.DOWN, (255, 0, 0))

        # GADs
        self.sprites[461] = sprite(WAD.db["SHAP"]["PLATFRM5"],8)
        self.sprites[462] = sprite(WAD.db["SHAP"]["PLATFRM5"],8,
            glyphtype = UPDOWNARR, glyphpos = (34,6), glyphcolour = (0,0,255))

        for i in range(463,467):
            self.sprites[i] = sprite(WAD.db["SHAP"]["PLATFRM5"],8,
                glyphtype = i-463, glyphpos = (34,6), glyphcolour = (0,0,255))

        # Springs.
        # Spring with Info 2 will break. Just show as already broken
        # Spring with info 3 is delayed. Show partially sprung
        self.sprites[193] = indexedsprite(
            {0: WAD.db["SHAP"]["SPRING1"],
            2: WAD.db["SHAP"]["SPRING10"],
            3: WAD.db["SHAP"]["SPRING2"]},
            allowfloat=False)

        # Pushable Columns
        # Non-Directional
        for i in range(285,288):
            self.sprites[i] = sprite(WAD.db["SHAP"]["PSHCOL1A"],16,
                glyphtype = ELLIPSE, glyphpos = (34,6), glyphcolour = (0,0,255))

        # Directional
        for i in range(303,306):
            self.sprites[i] = sprite(WAD.db["SHAP"]["PSHCOL1A"],16,
                glyphtype = RIGHTARR, glyphpos = (34,6), glyphcolour = (0,0,255))

        for i in range(321,324):
            self.sprites[i] = sprite(WAD.db["SHAP"]["PSHCOL1A"],16,
                glyphtype = UPARR, glyphpos = (34,6), glyphcolour = (0,0,255))

        for i in range(339,342):
            self.sprites[i] = sprite(WAD.db["SHAP"]["PSHCOL1A"],16,
                glyphtype = LEFTARR, glyphpos = (34,6), glyphcolour = (0,0,255))

        for i in range(357,360):
            self.sprites[i] = sprite(WAD.db["SHAP"]["PSHCOL1A"],16,
                glyphtype = DOWNARR, glyphpos = (34,6), glyphcolour = (0,0,255))

        # Crushing Columns
        self.sprites[413] = ceilingsprite(WAD.db["SHAP"]["CRDOWN1"])
        self.sprites[431] = sprite(WAD.db["SHAP"]["CRUP3"])

        # Gas Grate & Gas Door:
        self.sprites[192] = gassprite(WAD.db["SHAP"]["GRATE"])

        # Fire Jets
        self.sprites[372] = ceilingsprite(WAD.db["SHAP"]["FJDOWN9"])
        self.sprites[390] = sprite(WAD.db["SHAP"]["FJUP9"])

        for i in range(373,377):
            self.sprites[i] = ceilingsprite(WAD.db["SHAP"]["FJDOWN9"],
                glyphtype = i-373, glyphpos = (52,80), glyphcolour = (255,0,0))

        for i in range(391,395):
            self.sprites[i] = sprite(WAD.db["SHAP"]["FJUP9"],
                glyphtype = i-391, glyphpos = (52,80), glyphcolour = (255,0,0))

        # Pit
        self.sprites[284] = sprite(WAD.db["SHAP"]["POSTPIT"])

        # Spears
        self.sprites[412] = ceilingsprite(WAD.db["SHAP"]["SPEARDN1"])
        self.sprites[430] = sprite(WAD.db["SHAP"]["SPEARUP1"])

        # Boulder Start:
        for i in range(278,282):
            self.sprites[i] = ceilingsprite(WAD.db["SHAP"]["BDROP10"],
                glyphtype = i-278, glyphpos = (36,8), glyphcolour = (255,0,0))

        # Boulder End:
        self.sprites[395] = sprite(WAD.db["SHAP"]["BSINK5"])

        # Blade Pillars
        # UPDN: 1 = Floor, 0 = Ceiling
        # Moving: 1 = Popping up and Down, 0 = Static
        self.sprites[156] = ceilingsprite(WAD.db["SHAP"]["DBLADE3"]) # nodir, updn=0, moving=0
        self.sprites[157] = ceilingsprite(WAD.db["SHAP"]["SPSTDN11"]) # nodir, updn=0, moving=1
        self.sprites[174] = sprite(WAD.db["SHAP"]["UBLADE3"]) # nodir, updn=1, moving=0
        self.sprites[175] = sprite(WAD.db["SHAP"]["SPSTUP11"]) # nodir, updn=1, moving=1

        self.sprites[301] = ceilingsprite(WAD.db["SHAP"]["DBLADE3"],
                glyphtype = RIGHTARR, glyphpos = (52,80), glyphcolour = (255,0,0)) # east, updn=0, moving=0
        self.sprites[302] = sprite(WAD.db["SHAP"]["UBLADE3"],
                glyphtype = RIGHTARR, glyphpos = (52,80), glyphcolour = (255,0,0)) # east, updn=1, moving=0
        self.sprites[319] = ceilingsprite(WAD.db["SHAP"]["DBLADE3"],
                glyphtype = UPARR, glyphpos = (52,80), glyphcolour = (255,0,0)) # north, updn=0, moving=0
        self.sprites[320] = sprite(WAD.db["SHAP"]["UBLADE3"],
                glyphtype = UPARR, glyphpos = (52,80), glyphcolour = (255,0,0)) # north, updn=1, moving=0
        self.sprites[337] = ceilingsprite(WAD.db["SHAP"]["DBLADE3"],
                glyphtype = LEFTARR, glyphpos = (52,80), glyphcolour = (255,0,0)) # west, updn=0, moving=0
        self.sprites[338] = sprite(WAD.db["SHAP"]["UBLADE3"],
                glyphtype = LEFTARR, glyphpos = (52,80), glyphcolour = (255,0,0)) # west, updn=1, moving=0
        self.sprites[355] = ceilingsprite(WAD.db["SHAP"]["DBLADE3"],
                glyphtype = DOWNARR, glyphpos = (52,80), glyphcolour = (255,0,0)) # south, updn=0, moving=0
        self.sprites[356] = sprite(WAD.db["SHAP"]["UBLADE3"],
                glyphtype = DOWNARR, glyphpos = (52,80), glyphcolour = (255,0,0)) # south, updn=1, moving=0

        # Fire Shooters
        self.sprites[140] = flatsprite(WAD.db["SHAP"]["CRFIRE17"], (170, 30, 0), (-32,-32), 0 ) # +x (dr)
        self.sprites[141] = flatsprite(WAD.db["SHAP"]["CRFIRE17"], (170, 30, 0), (-32,-32), 90 ) # -y (ur)
        self.sprites[142] = flatsprite(WAD.db["SHAP"]["CRFIRE17"], (170, 30, 0), (-32,-32), 180 ) # -x (ul)
        self.sprites[143] = flatsprite(WAD.db["SHAP"]["CRFIRE17"], (170, 30, 0), (-32,-32), 270 ) # +y (dl)


    def assign_statics(self, WAD):
        """ Populates the index to sprite mappings for all static
        sprites (e.g. decorations, weapons, items, etc.)."""

        # Static list from RT_STAT
        # Ceiling Lights are distracting and don't add much value
        self.sprites[23] = blanksprite() #["YLIGHT"]
        self.sprites[24] = blanksprite() #["RLIGHT"]
        self.sprites[25] = blanksprite() #["GLIGHT"]
        self.sprites[26] = blanksprite() #["BLIGHT"]
        self.sprites[27] = blanksprite() #["CHAND"]

        self.sprites[28] = sprite(WAD.db["SHAP"]["LAMP"])

        # Keys
        self.sprites[29] = keysprite(WAD.db["SHAP"]["GKEY1"],
            WAD.db["SIDE"]["LOCK1"], WAD.db["General"]["KEY1"],
            121, [(255, 158, 48), (178, 93, 52)]) # Gold
        self.sprites[30] = keysprite(WAD.db["SHAP"]["GKEY1"],
            WAD.db["SIDE"]["LOCK2"], WAD.db["General"]["KEY2"],
            34, [(170, 170, 170), (101, 101, 101)]) # Silver
        self.sprites[31] = keysprite(WAD.db["SHAP"]["GKEY1"],
            WAD.db["SIDE"]["LOCK3"], WAD.db["General"]["KEY3"],
            15, [(105, 97, 73), (60, 56, 40)]) # Iron
        self.sprites[32] = keysprite(WAD.db["SHAP"]["GKEY1"],
            WAD.db["SIDE"]["LOCK4"], WAD.db["General"]["KEY4"],
            60, [(125, 0, 0), (77, 12, 16)]) # Obscuro

        self.sprites[33] = sprite(WAD.db["SHAP"]["GIBS1"])
        self.sprites[34] = sprite(WAD.db["SHAP"]["GIBS2"])
        self.sprites[35] = sprite(WAD.db["SHAP"]["GIBS3"])
        self.sprites[36] = sprite(WAD.db["SHAP"]["MONKMEAL"])
        self.sprites[37] = sprite(WAD.db["SHAP"]["PPOR1"], important=True)
        self.sprites[38] = sprite(WAD.db["SHAP"]["MONKC11"])
        self.sprites[39] = sprite(WAD.db["SHAP"]["MONKC21"], important=True)
        self.sprites[40] = sprite(WAD.db["SHAP"]["ONEUP3"], important=True)
        self.sprites[41] = sprite(WAD.db["SHAP"]["THREEUP3"], important=True)
        self.sprites[42] = sprite(WAD.db["SHAP"]["ABRAZ1"])
        self.sprites[43] = sprite(WAD.db["SHAP"]["ABRZO20"])
        self.sprites[44] = sprite(WAD.db["SHAP"]["FBASIN1"], important=True)
        self.sprites[45] = sprite(WAD.db["SHAP"]["EBASIN"])
        self.sprites[46] = sprite(WAD.db["SHAP"]["BATSPR1"], important=True)
        self.sprites[47] = sprite(WAD.db["SHAP"]["KSTATUE8"])
        self.sprites[48] = sprite(WAD.db["SHAP"]["TWOPIST"], important=True)
        self.sprites[49] = sprite(WAD.db["SHAP"]["MP40"], important=True)
        self.sprites[50] = sprite(WAD.db["SHAP"]["BAZOOKA"], important=True)
        self.sprites[51] = sprite(WAD.db["SHAP"]["FIREBOMB"], important=True)
        self.sprites[52] = sprite(WAD.db["SHAP"]["HEATSEEK"], important=True)
        self.sprites[53] = sprite(WAD.db["SHAP"]["DRUNK"], important=True)
        self.sprites[54] = sprite(WAD.db["SHAP"]["FIREWALL"], important=True)
        self.sprites[55] = sprite(WAD.db["SHAP"]["SPLITM"], important=True)
        self.sprites[56] = sprite(WAD.db["SHAP"]["KES"], important=True)

        self.sprites[57] = sprite(WAD.db["SHAP"]["LIFE_A7"],-32)
        self.sprites[58] = sprite(WAD.db["SHAP"]["LIFE_B7"],-32)
        self.sprites[59] = sprite(WAD.db["SHAP"]["LIFE_D7"],-32)
        self.sprites[60] = sprite(WAD.db["SHAP"]["LIFE_C7"],-32, important=True)
        self.sprites[61] = sprite(WAD.db["SHAP"]["EXPLOSI"])
        self.sprites[62] = sprite(WAD.db["SHAP"]["BBARREL"])
        self.sprites[63] = sprite(WAD.db["SHAP"]["ABRAZ1"])
        self.sprites[64] = sprite(WAD.db["SHAP"]["FFLAME1"])
        self.sprites[65] = sprite(WAD.db["SHAP"]["DIPBAL11"], important=True)
        self.sprites[66] = sprite(WAD.db["SHAP"]["DIPBAL21"], important=True)
        self.sprites[67] = sprite(WAD.db["SHAP"]["DIPBAL31"], important=True)
        self.sprites[68] = sprite(WAD.db["SHAP"]["TP1"])
        self.sprites[69] = sprite(WAD.db["SHAP"]["TP2"])
        self.sprites[70] = sprite(WAD.db["SHAP"]["TP3"])
        self.sprites[71] = sprite(WAD.db["SHAP"]["TP4"])
        self.sprites[210] = sprite(WAD.db["SHAP"]["SCTHEAD5"]) # Easter Egg Head
        self.sprites[228] = sprite(WAD.db["SHAP"]["GARBAG1"])
        self.sprites[229] = sprite(WAD.db["SHAP"]["GARBAG2"])
        self.sprites[230] = sprite(WAD.db["SHAP"]["GARBAG3"])
        self.sprites[231] = sprite(WAD.db["SHAP"]["SHITBUK"])
        self.sprites[232] = sprite(WAD.db["SHAP"]["GRATE"])
        self.sprites[233] = sprite(WAD.db["SHAP"]["MSHARDS"])
        self.sprites[246] = sprite(WAD.db["SHAP"]["PEDESTA"])
        self.sprites[247] = sprite(WAD.db["SHAP"]["ETABLE"])
        self.sprites[248] = sprite(WAD.db["SHAP"]["STOOL"])
        self.sprites[249] = sprite(WAD.db["SHAP"]["PSHCOL1A"],16) #stat_bcolumn
        self.sprites[250] = sprite(WAD.db["SHAP"]["PSHCOL1A"],16) #stat_gcolumn
        self.sprites[251] = sprite(WAD.db["SHAP"]["PSHCOL1A"],16) #stat_icolumn
        self.sprites[252] = sprite(WAD.db["SHAP"]["GODUP2"], important=True)
        self.sprites[253] = sprite(WAD.db["SHAP"]["DOGUP1"], important=True)
        self.sprites[254] = sprite(WAD.db["SHAP"]["FEETUP2"], important=True)
        self.sprites[255] = compositesprite(
            [WAD.db["SHAP"]["RNDOMUP4"], WAD.db["SHAP"]["RNDOMUP2"]],
            [(0, 0), (0, 0)], important=True)
        self.sprites[260] = sprite(WAD.db["SHAP"]["ELASTUP2"])
        self.sprites[261] = sprite(WAD.db["SHAP"]["MUSHUP2"])
        self.sprites[262] = sprite(WAD.db["SHAP"]["TOMLARV3"])
        self.sprites[263] = randomcoloursprite(WAD.db["SHAP"]["COLEC5"], important=True)
        self.sprites[264] = sprite(WAD.db["SHAP"]["TREE"])
        self.sprites[265] = sprite(WAD.db["SHAP"]["PLANT"])
        self.sprites[267] = sprite(WAD.db["SHAP"]["ESTATUE8"]) #stat_emptystatue,
        self.sprites[266] = sprite(WAD.db["SHAP"]["URN"])
        self.sprites[268] = sprite(WAD.db["SHAP"]["HAY"])
        self.sprites[269] = sprite(WAD.db["SHAP"]["IBARREL"])
        self.sprites[270] = sprite(WAD.db["SHAP"]["PROOFUP"], important=True)
        self.sprites[271] = sprite(WAD.db["SHAP"]["ASBESTOS"], important=True)
        self.sprites[272] = sprite(WAD.db["SHAP"]["GASUP"], important=True)
        self.sprites[282] = sprite(WAD.db["SHAP"]["HGRATE1"])
        self.sprites[283] = indexedsprite(
            {0: WAD.db["SHAP"]["STNPOLE8"], # Default
            0xE: WAD.db["SHAP"]["STNPOLE8"], # Right
            0xF: WAD.db["SHAP"]["STNPOLE6"], # Up
            0x10: WAD.db["SHAP"]["STNPOLE4"], # Left
            0x11: WAD.db["SHAP"]["STNPOLE2"]}) # Down


    def generate_isometric(self, height):
        """ Generates the isometric views for any sprites which contain
        a wall component. Isometric views are generated at the specified
        height.
        """
        for sprite in self.sprites:
            if type(sprite) is keysprite or type(sprite) is gassprite:
                sprite.wall.generate_isometric(height)
