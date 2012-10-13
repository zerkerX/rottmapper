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

""" Module containing a variety of ROTT wall and floor-type classes.
Also includes the wall database class.
"""

import sys

from PIL import Image, ImageOps, ImageDraw

import rtl, wad

class tile(object):
    """ Base tile class, which is expanded by all subsequent floor/wall
    tiles. This class has no meaning on its own, but it does define
    a number of common methods for handling height placement that are
    used by all tile subclasses.

    Public member variables:
    height -- the world height in pixels that this tile is generated for
    viewheightovr -- if >=0, this overrides the view height for this
                     tile. Only used for fence tiles, which do not
                     obscure anything behind them. Always -1.
    debugnum -- the wall number for a debug tile. 0 (unused) by default.
    """
    specialheights = [1]+range(4,10)
    debugnum = 0

    """ Base tile class"""
    def __init__(self, images):
        """ Initializes using the following information:

        images -- a list of images to be used by this tile. Specific use
                  depends on subclass.
        """
        if images != None:
            self.images = [image.convert("RGBA") for image in images]
        else:
            self.images = None

        self.viewheightovr = -1

    @staticmethod
    def categorizeimages(images):
        """ Sorts a given image list into bottom, middle and top. Used
        for walls and thin walls to decide what to draw at what height.

        The general scheme is:
        1 image:  image 0 is drawn for all positions
        2 images: image 0 is drawn for ground level, image 1 is for
                  everything else
        3 images: image 0 is drawn for ground level, image 2 is for the
                  highest position, and image 1 is for everything
                  inbetween.

        Return order is (ground level, middle image, top image)
        """
        if len(images)>2:
            topimg = images[2]
            midimg = images[1]
        elif len(images)>1:
            topimg = images[1]
            midimg = images[1]
        else:
            topimg = images[0]
            midimg = images[0]
        botimg = images[0]
        return (botimg, midimg, topimg)

    @staticmethod
    def leftskew(image):
        """ Skews the image to the left for isometric walls.
        For UP and DOWN (i.e. y axis) directions.
        """
        return image.transform((image.size[0],int(image.size[1]+image.size[0]/2)),
            Image.AFFINE, (1, 0, 0, -0.5, 1, 0), Image.BICUBIC)

    @staticmethod
    def rightskew(image):
        """ Skews the image to the right for isometric wals.
        For LEFT and RIGHT (i.e. x axis) directions.
        """
        return image.transform((image.size[0],int(image.size[1]+image.size[0]/2)),
            Image.AFFINE, (1, 0, 0, 0.5, 1, -image.size[0]/2), Image.BICUBIC)

    @staticmethod
    def floorskew(image):
        """ Skews an image to display on the floor """
        return image.transform((128,128), Image.AFFINE,
            (0.5, 0.5, -32, -0.5, 0.5, 32), Image.NEAREST).transform(
            (128,64), Image.AFFINE, (1, 0, 0, 0, 2, 0), Image.NEAREST)

    @staticmethod
    def floortrans(image):
        """ Transforms a base floor image into 4 tiles in isometric
        perspective, ready to place.

        Return order is: (upper left, upper right, lower left, lower right)
        """
        ul = image.crop((0, 0, 64, 64))
        ur = image.crop((64, 0, 128, 64))
        ll = image.crop((0, 64, 64, 128))
        lr = image.crop((64, 64, 128, 128))

        return (tile.floorskew(ul), tile.floorskew(ur),
            tile.floorskew(ll), tile.floorskew(lr))

    def generate_isometric(self, height):
        """ Generates isometric views for this tile. Does nothing for
        the basic tile class.
        """
        self.height = height

    def setdebug(self, number):
        """ Assigns the given wall ID as a debug number to this tile.
        Used for marking unknown tiles.
        """
        self.debugnum = number

    def issolid(self, infoval):
        """ Checks if this tile type is a solid wall according to the
        given info value. Returns False.
        """
        return False

    def isthin(self, infoval):
        """ Checks if this tile type is a thin wall according to the
        given info value. False by default, but special height info
        values will create a spacer wall which is considered thin.
        """
        return infoval in self.specialheights

    def spriteheight(self, infoval, allowfloat=True):
        """ Checks the height of a sprite placed at this tile with
        a given info value. Handles two main reasons for a higher
        sprite:
        1) Special height info values will place the sprite on top of
           the spacer thin wall.
        2) Info values >= 0xB000 will float the sprite in the air
           according to the value.

        infoval -- the value of the info layer at the current position
                   in the map.
        allowfloat -- whether the sprite at this position is actually
                      allowed to float in the air.
        """
        # Special hybrid walls and spacers for floors
        if infoval in self.specialheights:
            if infoval == 9 or infoval == 1:
                return self.height - 64
            elif infoval == 5 or infoval == 6:
                return 64;
            else:
                return 0
        elif self.issolid(infoval) or self.isthin(infoval):
            return self.height
        elif allowfloat:
            # Floating sprites
            if infoval >= 0xB0F0:
                return (infoval - 0xB100)*4
            elif infoval >= 0xB000:
                return (infoval - 0xB000)*4
            else:
                return 0
        else:
            return 0

    def viewheight(self, infoval):
        """ Checks how much vertical height this tile will obscure
        when drawn based on the provided info value. Used by obscured
        sprite indicator processing,
        """
        if self.viewheightovr > 0:
            return self.viewheightovr
        elif infoval in self.specialheights:
            if infoval == 8 or infoval == 9 or infoval == 1:
                return self.height - 64
            elif infoval == 5:
                return 64;
            else:
                return self.height
        elif self.issolid(infoval) or self.isthin(infoval):
            return self.height
        else:
            return 0

class emptytile(tile):
    """ Empty tile subclass to mark a blank spot on the map."""
    pass

class walltile(tile):
    """ Standard wall tile type to mark a solid wall on the map.

    Public member variables:
    height -- the world height in pixels that this tile is generated for
    viewheightovr -- if >=0, this overrides the view height for this
                     tile. Only used for fence tiles, which do not
                     obscure anything behind them. Always -1.
    debugnum -- the wall number for a debug tile. 0 (unused) by default.
    isowall -- a list of isometric wall images, indexed by directional
               facing and adjusted to the map height.
    isomask -- a list of isometric mask images, indexed by directional
               facing and adjusted to the map height.
    """
    def generate_isometric(self, height):
        """ Generates isometric views for this tile at the specified
        map height. Creates skewed wall images facing in each direction,
        populating the isowall and isomask member variables.
        """
        self.height = height
        self.isowall = [None]*4
        self.isomask = [None]*4

        if self.images != None:
            fullimage = Image.new("RGBA", (64, height))

            (botimg, midimg, topimg) = self.categorizeimages(self.images)

            numtiles = height/64
            for pos in range(numtiles):
                if pos==0 and numtiles > 1:
                    fullimage.paste(topimg, (0, pos*64))
                elif pos == numtiles - 1:
                    fullimage.paste(botimg, (0, pos*64))
                else:
                    fullimage.paste(midimg, (0, pos*64))

            # Darken the original image for the back walls (make 50% composite with black)
            backimage = Image.composite(fullimage,
                Image.new("RGBA", (64, height), (0,0,0)),
                Image.new("L", (64, height), (128)))

            # Make back walls 62.5% transparent
            backmask = Image.new("L", (64, height), (96))

            self.isowall[rtl.RIGHT] = self.rightskew(fullimage)
            self.isowall[rtl.DOWN]  = self.leftskew(fullimage)
            self.isowall[rtl.LEFT]  = self.rightskew(backimage)
            self.isowall[rtl.UP]    = self.leftskew(backimage)
            self.isomask[rtl.RIGHT] = self.rightskew(fullimage)
            self.isomask[rtl.DOWN]  = self.leftskew(fullimage)
            self.isomask[rtl.LEFT]  = self.rightskew(backmask)
            self.isomask[rtl.UP]    = self.leftskew(backmask)

    def issolid(self, infoval):
        """ Checks if this tile type is a solid wall according to the
        given info value. Returns True.
        """
        return True

    def isthin(self, infoval):
        """ Checks if this tile type is a thin wall according to the
        given info value. Returns False.
        """
        return False

class thintile(walltile):
    """ Thin wall tile type to mark a door/fence/window on the map,
    which is typically drawn in the middle of a given space.

    Public member variables:
    height -- the world height in pixels that this tile is generated for
    viewheightovr -- if >=0, this overrides the view height for this
                     tile. Only used for fence tiles, which do not
                     obscure anything behind them.
    debugnum -- the wall number for a debug tile. 0 (unused) by default.
    floor -- list of 4 isometric floor images to draw onto the ground
             under this tile.
    isowall -- a list of isometric wall images, indexed by directional
               facing and adjusted to the map height. Used when this
               thin wall is adjacent to a solid wall to replace the wall
               image.
    isomask -- a list of isometric mask images, indexed by directional
               facing and adjusted to the map height. Used when this
               thin wall is adjacent to a solid wall to replace the wall
               image.
    faces -- a list of two face images for this thin wall, one in each
             orientation. The face is the image placed in the middle of
             the map square, and is typically the actual door/window
             image.
    masks -- a list of two masks for the face images.
    """
    def __init__(self, faceimages, facemasks, sideimages,
            floorimage=None, viewheightoverride=-1):
        """ Initializes according to the following information:

        faceimages -- a list of images to use for the thin tile face
                      (i.e. the door face, or window, etc.). Exact
                      use is as per the categorizeimages method.
        facemasks -- a list of images to use as masks for the equivalent
                     entries in the faceimages list.
        sideimages -- a list of images to use for the side wall to this
                      thin tile, replacing whatever wall may be adjacent.
                      If None, this thin tile does not replace walls.
        floorimage -- the image for the floor to draw under this tile.
        viewheightoverride -- if >=0, this overrides the view height
                     for this tile. Only used for fence tiles, which
                     do not obscure anything behind them

        """
        super(thintile, self).__init__(sideimages)
        if faceimages != None:
            self.faceimages = [image.convert("RGBA") for image in faceimages]
        self.facemasks = []
        for mask in facemasks:
            if mask == None:
                self.facemasks.append(Image.new("L", (64, 64), 255))
            else:
                self.facemasks.append(mask)

        if floorimage != None:
            self.floorimage = floorimage.convert("RGBA")
        else:
            self.floorimage = None

        self.viewheightovr = viewheightoverride

    def generate_isometric(self, height):
        """ Generates isometric views for this tile at the specified
        map height. Creates skewed wall images facing in each direction,
        populating the isowall and isomask member variables, as well
        as faces and masks variables for the thin part of this wall.
        """
        super(thintile, self).generate_isometric(height)

        # Only need 2/4 directions for thin walls. Use "Right" and "Up".
        self.faces = [None]*2
        self.masks = [None]*2

        fullimage = Image.new("RGBA", (64, height))
        fullmask = Image.new("L", (64, height))

        (botface, midface, topface) = self.categorizeimages(self.faceimages)
        (botmask, midmask, topmask) = self.categorizeimages(self.facemasks)

        numtiles = height/64
        for pos in range(numtiles):
            if pos==0 and numtiles > 1:
                fullimage.paste(topface, (0, pos*64))
                fullmask.paste(topmask, (0, pos*64))
            elif pos == numtiles - 1:
                fullimage.paste(botface, (0, pos*64))
                fullmask.paste(botmask, (0, pos*64))
            else:
                fullimage.paste(midface, (0, pos*64))
                fullmask.paste(midmask, (0, pos*64))

        self.faces[rtl.UP]  = self.leftskew(fullimage)
        self.faces[rtl.RIGHT] = self.rightskew(ImageOps.mirror(fullimage))
        self.masks[rtl.UP]  = self.leftskew(fullmask)
        self.masks[rtl.RIGHT] = self.rightskew(ImageOps.mirror(fullmask))

        if self.floorimage != None:
            self.floor = self.floortrans(self.floorimage)

    def issolid(self, infoval):
        """ Checks if this tile type is a solid wall according to the
        given info value. Returns False.
        """
        return False

    def isthin(self, infoval):
        """ Checks if this tile type is a solid wall according to the
        given info value. Returns True.
        """
        return True


class floortile(tile):
    def generate_isometric(self, height):
        """ Generates an isometric set of four images for the floor,
        each of which takes up one block of map space."""
        self.height = height
        self.floor = self.floortrans(self.images[0])


class variabletile(thintile):
    """ A special wall type that can either be thin or solid based
    on its info value. Used by one specific wall image, as well as
    the virtual spacer wall.

    Public member variables:
    height -- the world height in pixels that this tile is generated for
    viewheightovr -- if >=0, this overrides the view height for this
                     tile. Only used for fence tiles, which do not
                     obscure anything behind them.
    debugnum -- the wall number for a debug tile. 0 (unused) by default.
    floor -- list of 4 isometric floor images to draw onto the ground
             under this tile.
    isowall -- a list of isometric wall images, indexed by directional
               facing and adjusted to the map height. Used when this
               hybrid wall is used as a solid wall.
    isomask -- a list of isometric mask images, indexed by directional
               facing and adjusted to the map height. Used when this
               hybrid wall is used as a solid wall.
    faces -- a two-dimensional list of two face images for this thin
             wall, one in each orientation, for each possible special
             value. The face is the image placed in the middle of
             the map square, and is typically the actual door/window
             image. Used when this hybrid wall is used as a thin wall.
    masks -- a two-dimensional list of two masks for the face images,
             for each special value.
    """

    def issolid(self, infoval):
        """ Checks if this tile type is a solid wall according to the
        given info value. True unless special height info values turn
        this wall into a thin wall.
        """
        return infoval not in self.specialheights

    @staticmethod
    def categorizehybrid(images):
        """ Categorizes images used for a hybrid tile face. This is
        mostly to group the images for the spacer tile, as the only
        other hybrid tile has a single image. Returns the following
        list of images in the below order:
        botimg -- the solid image at the base of a stack where more
                  pieces of the stack appear above.
        botshort -- the solid image at the base of a stack, which stands
                    on its own and ends the stack.
        midimg -- a solid image in the middle of the stack, with more
                  pieces above and below.
        midend -- An end piece that ends a stack above the current
                  position. Is non-solid.
        topimg -- An end piece that ends a stack below the current
                  position. Is non-solid.
        topend -- An end piece that is starts from the ceiling and
                  immediately ends. Is solid.
        """
        if len(images)>5:
            topend   = images[5]
            topimg   = images[4]
            midimg   = images[3]
            midend   = images[2]
            botshort = images[1]
        else:
            topend   = images[0]
            topimg   = Image.new("L", (64, 64), 0)
            midimg   = images[0]
            midend   = Image.new("L", (64, 64), 0)
            botshort = images[0]
        botimg = images[0]
        return (botimg, botshort, midimg, midend, topimg, topend)

    def generate_isometric(self, height):
        """ Generates isometric views for this tile at the specified
        map height. Creates skewed wall images facing in each direction,
        populating the isowall and isomask member variables, as well
        as faces and masks variables for the thin part of this wall.
        A valid face is generated for each possible info value.
        """
        super(variabletile, self).generate_isometric(height)

        # Redo faces for all possible info combinations
        fullimage = [None]*10
        fullmask = [None]*10

        for i in self.specialheights:
            fullimage[i] = Image.new("RGBA", (64, height))
            fullmask[i] = Image.new("L", (64, height))

        (botimg, botshort, midimg, midend, topimg, topend) = \
            self.categorizehybrid(self.faceimages)
        (botmask, botshortmask, midmask, midendmask, topmask, topendmask) = \
            self.categorizehybrid(self.facemasks)

        numtiles = height/64

        for pos in range(numtiles):
            if numtiles == 1:
                # Single-height maps. Just fill all possibilties with a
                # solid middle panel. No instances of this have been
                # observed in the game.
                for i in self.specialheights:
                    fullimage[i].paste(midimg, (0, pos*64))
                    fullmask[i].paste(midmask, (0, pos*64))
            elif pos==0:
                # Floor-level position
                fullimage[4].paste(topend, (0, pos*64))
                fullmask[4].paste(topendmask, (0, pos*64))

                if numtiles == 2:
                    fullimage[7].paste(topend, (0, pos*64))
                    fullmask[7].paste(topendmask, (0, pos*64))
                    fullimage[8].paste(topend, (0, pos*64))
                    fullmask[8].paste(topendmask, (0, pos*64))
                else:
                    fullimage[6].paste(topend, (0, pos*64))
                    fullmask[6].paste(topendmask, (0, pos*64))
                    fullimage[7].paste(midimg, (0, pos*64))
                    fullmask[7].paste(midmask, (0, pos*64))
                    fullimage[8].paste(topimg, (0, pos*64))
                    fullmask[8].paste(topmask, (0, pos*64))
                    fullimage[9].paste(topimg, (0, pos*64))
                    fullmask[9].paste(topmask, (0, pos*64))
                    fullimage[1].paste(topimg, (0, pos*64))
                    fullmask[1].paste(topmask, (0, pos*64))
            elif pos == numtiles - 1:
                # Ceiling position
                fullimage[5].paste(botshort, (0, pos*64))
                fullmask[5].paste(botshortmask, (0, pos*64))
                fullimage[6].paste(botshort, (0, pos*64))
                fullmask[6].paste(botshortmask, (0, pos*64))
                if numtiles == 2:
                    fullimage[9].paste(botshort, (0, pos*64))
                    fullmask[9].paste(botshortmask, (0, pos*64))
                    fullimage[1].paste(botshort, (0, pos*64))
                    fullmask[1].paste(botshortmask, (0, pos*64))
                else:
                    fullimage[7].paste(midend, (0, pos*64))
                    fullmask[7].paste(midendmask, (0, pos*64))
                    fullimage[8].paste(midend, (0, pos*64))
                    fullmask[8].paste(midendmask, (0, pos*64))
                    fullimage[9].paste(botimg, (0, pos*64))
                    fullmask[9].paste(botmask, (0, pos*64))
                    fullimage[1].paste(botimg, (0, pos*64))
                    fullmask[1].paste(botmask, (0, pos*64))

            else:
                # Every position between floor and ceiling
                for i in [1] + range(7,10):
                    fullimage[i].paste(midimg, (0, pos*64))
                    fullmask[i].paste(midmask, (0, pos*64))

        self.faces = [[None]*10,[None]*10]
        self.masks = [[None]*10,[None]*10]

        for i in self.specialheights:
            self.faces[rtl.UP][i]    = self.leftskew(fullimage[i])
            self.faces[rtl.RIGHT][i] = self.rightskew(fullimage[i])
            self.masks[rtl.UP][i]    = self.leftskew(fullmask[i])
            self.masks[rtl.RIGHT][i] = self.rightskew(fullmask[i])

    def isthin(self, infoval):
        """ Checks if this tile type is a thin wall according to the
        given info value. False unless special height info values turn
        this wall into a thin wall.
        """
        return infoval in self.specialheights

class walldb:
    """ Database of all known index to floor/wall tile mappings.

    Public member variables:
    tiles -- an array of floor/wall tiles, indexed by the wall id. Each
             position will contain a corresponding tile object.
    """

    def __init__(self, WAD, floorindex):
        """ Populates the index to wall mappings in the wall
        database using the wall/floor/mask images found in the provided
        WAD file instance.

        WAD -- wad file instance to read image data from
        floorindex -- index number of floor tile to use
        """
        self.tiles = [None] * 256
        self.tiles[0] = emptytile(None)

        # Initialize with debug walls:
        for i in range(1,256):
            self.tiles[i] = walltile([Image.new("RGBA", (64, 64), (128,128,128))])
            self.tiles[i].setdebug(i)

        # Fill in floors
        floorimage = WAD.db["UPDN"]["FLRCL{}".format(floorindex)].data
        for i in range(108,153):
            self.tiles[i] = floortile([floorimage])

        # Copy in Wall array (algorithm from ROTT source code)
        for tile in range(90):
            if tile >= 1 and tile <= 32:
                self.tiles[tile] = walltile([WAD.data["WALL"][tile-1].data])
            elif tile >= 36 and tile <= 45:
                self.tiles[tile] = walltile([WAD.data["WALL"][tile-4].data])
            elif tile == 46:
                self.tiles[tile] = walltile([WAD.data["WALL"][73].data])
            elif tile >= 47 and tile <= 48:
                self.tiles[tile] = walltile([WAD.data["EXIT"][tile-47].data,
                    WAD.data["WALL"][21].data])
            elif tile >= 49 and tile <= 71:
                self.tiles[tile] = walltile([WAD.data["WALL"][tile-9].data])
            elif tile >= 72 and tile <= 79:
                self.tiles[tile] = walltile([WAD.data["ELEV"][tile-72].data])
            elif tile >= 80 and tile <= 89:
                self.tiles[tile] = walltile([WAD.data["WALL"][tile-17].data])

        # Special walls (i.e. different above texture)
        self.tiles[11] = walltile([WAD.data["WALL"][10].data,
            WAD.data["WALL"][21].data])
        self.tiles[76] = walltile([WAD.data["ELEV"][4].data,
            WAD.data["WALL"][21].data])
        self.tiles[77] = walltile([WAD.data["ELEV"][5].data,
            WAD.data["WALL"][21].data])
        self.tiles[78] = walltile([WAD.data["ELEV"][6].data,
            WAD.data["WALL"][21].data])
        self.tiles[79] = walltile([WAD.data["ELEV"][7].data,
            WAD.data["WALL"][21].data])

        self.tiles[21] = variabletile(
            [WAD.data["HMSK"][14].data], [WAD.data["HMSK"][14].mask],
            [WAD.data["WALL"][20].data], floorimage)
        self.spacer = variabletile(
            [WAD.data["HMSK"][4].data,
            WAD.data["HMSK"][8].data,
            WAD.data["HMSK"][12].data,
            WAD.data["HMSK"][7].data,
            WAD.data["HMSK"][5].data,
            WAD.data["HMSK"][10].data],
            [WAD.data["HMSK"][4].mask,
            WAD.data["HMSK"][8].mask,
            WAD.data["HMSK"][12].mask,
            WAD.data["HMSK"][7].mask,
            WAD.data["HMSK"][5].mask,
            WAD.data["HMSK"][10].mask],
            [WAD.data["HMSK"][7].data],
            floorimage)

        # Assign known DOORs:
        # TODO: Duplicates?
        self.tiles[90] = thintile(
            [WAD.db["DOOR"]["RAMDOOR1"].data, WAD.data["ABVW"][0].data],
            [None, None],
            [WAD.db["SIDE"]["SIDE8"].data],
            floorimage)
        self.tiles[98] = thintile(
            [WAD.db["DOOR"]["RAMDOOR1"].data, WAD.data["ABVW"][0].data],
            [None, None],
            [WAD.db["SIDE"]["SIDE8"].data],
            floorimage)


        # TODO: Duplicates?
        self.tiles[91] = thintile(
            [WAD.db["DOOR"]["DOOR2"].data, WAD.data["ABVW"][0].data],
            [None, None],
            [WAD.db["SIDE"]["SIDE8"].data],
            floorimage)
        self.tiles[99] = thintile(
            [WAD.db["DOOR"]["DOOR2"].data, WAD.data["ABVW"][0].data],
            [None, None],
            [WAD.db["SIDE"]["SIDE8"].data],
            floorimage)

        # TODO: Duplicates?
        self.tiles[92] = thintile(
            [WAD.db["DOOR"]["TRIDOOR1"].data, WAD.data["ABVW"][0].data],
            [None, None],
            [WAD.db["SIDE"]["SIDE8"].data],
            floorimage)
        self.tiles[93] = thintile(
            [WAD.db["DOOR"]["TRIDOOR1"].data, WAD.data["ABVW"][0].data],
            [None, None],
            [WAD.db["SIDE"]["SIDE8"].data],
            floorimage)
        self.tiles[103] = thintile(
            [WAD.db["DOOR"]["TRIDOOR1"].data, WAD.data["ABVW"][0].data],
            [None, None],
            [WAD.db["SIDE"]["SIDE8"].data],
            floorimage)

        # TODO: Duplicates?
        self.tiles[100] = thintile(
            [WAD.db["DOOR"]["SDOOR4"].data, WAD.data["ABVW"][0].data],
            [None, None],
            [WAD.db["SIDE"]["SIDE8"].data],
            floorimage)
        self.tiles[101] = thintile(
            [WAD.db["DOOR"]["SDOOR4"].data, WAD.data["ABVW"][0].data],
            [None, None],
            [WAD.db["SIDE"]["SIDE8"].data],
            floorimage)
        self.tiles[104] = thintile(
            [WAD.db["DOOR"]["SDOOR4"].data, WAD.data["ABVW"][0].data],
            [None, None],
            [WAD.db["SIDE"]["SIDE8"].data],
            floorimage)

        # Explicitly Locked with Gold Key
        self.tiles[94] = thintile(
            [WAD.db["DOOR"]["SDOOR4"].data, WAD.data["ABVW"][0].data],
            [None, None],
            [WAD.db["SIDE"]["LOCK1"].data],
            floorimage)

        # Explicitly Locked with Silver Key
        self.tiles[95] = thintile(
            [WAD.db["DOOR"]["SDOOR4"].data, WAD.data["ABVW"][0].data],
            [None, None],
            [WAD.db["SIDE"]["LOCK2"].data],
            floorimage)

        # Explicitly Locked with Iron Key
        self.tiles[96] = thintile(
            [WAD.db["DOOR"]["SDOOR4"].data, WAD.data["ABVW"][0].data],
            [None, None],
            [WAD.db["SIDE"]["LOCK3"].data],
            floorimage)

        # Explicitly Locked with Obscuro Key
        self.tiles[97] = thintile(
            [WAD.db["DOOR"]["SDOOR4"].data, WAD.data["ABVW"][0].data],
            [None, None],
            [WAD.db["SIDE"]["LOCK4"].data],
            floorimage)


        self.tiles[102] = thintile(
            [WAD.db["DOOR"]["EDOOR"].data, WAD.data["ABVW"][0].data],
            [None, None],
            [WAD.db["SIDE"]["SIDE8"].data],
            floorimage)


        # Multi-part Door 1
        self.tiles[33] = thintile(
            [WAD.db["DOOR"]["SNDOOR"].data, WAD.data["ABVW"][1].data],
            [None, None],
            [WAD.db["SIDE"]["SIDE16"].data],
            floorimage)
        self.tiles[34] = thintile(
            [WAD.db["DOOR"]["SNADOOR"].data, WAD.data["ABVW"][1].data],
            [None, None],
            [WAD.db["SIDE"]["SIDE16"].data],
            floorimage)
        self.tiles[35] = thintile(
            [WAD.db["DOOR"]["SNKDOOR"].data, WAD.data["ABVW"][1].data],
            [None, None],
            [WAD.db["SIDE"]["SIDE16"].data],
            floorimage)

        # Multi-part Door 2
        self.tiles[154] = thintile(
            [WAD.db["DOOR"]["TNDOOR"].data, WAD.data["ABVW"][2].data],
            [None, None],
            [WAD.db["SIDE"]["SIDE17"].data],
            floorimage)
        self.tiles[155] = thintile(
            [WAD.db["DOOR"]["TNADOOR"].data, WAD.data["ABVW"][2].data],
            [None, None],
            [WAD.db["SIDE"]["SIDE17"].data],
            floorimage)
        self.tiles[156] = thintile(
            [WAD.db["DOOR"]["TNKDOOR"].data, WAD.data["ABVW"][2].data],
            [None, None],
            [WAD.db["SIDE"]["SIDE17"].data],
            floorimage)

        # Fences, Windows, Switches, etc:
        # Multi-part Window
        self.tiles[158] = thintile(
            [WAD.db["MASK"]["MULTI1"].data, WAD.db["ABVM"]["ABOVEM5A"].data, WAD.db["ABVM"]["ABOVEM5"].data],
            [WAD.db["MASK"]["MULTI1"].mask, WAD.db["ABVM"]["ABOVEM5A"].mask, WAD.db["ABVM"]["ABOVEM5"].mask],
            [WAD.db["SIDE"]["SIDE21"].data],
            floorimage)
        self.tiles[159] = thintile(
            [WAD.db["MASK"]["MULTI2"].data, WAD.db["ABVM"]["ABOVEM5B"].data, WAD.db["ABVM"]["ABOVEM5"].data],
            [WAD.db["MASK"]["MULTI2"].mask, WAD.db["ABVM"]["ABOVEM5B"].mask, WAD.db["ABVM"]["ABOVEM5"].mask],
            [WAD.db["SIDE"]["SIDE21"].data],
            floorimage)
        self.tiles[160] = thintile(
            [WAD.db["MASK"]["MULTI3"].data, WAD.db["ABVM"]["ABOVEM5C"].data, WAD.db["ABVM"]["ABOVEM5"].data],
            [WAD.db["MASK"]["MULTI3"].mask, WAD.db["ABVM"]["ABOVEM5C"].mask, WAD.db["ABVM"]["ABOVEM5"].mask],
            [WAD.db["SIDE"]["SIDE21"].data],
            floorimage)

        # Individual Windows
        self.tiles[162] = thintile(
            [WAD.db["MASK"]["MASKED1"].data, WAD.db["ABVM"]["ABOVEM4A"].data, WAD.db["ABVM"]["ABOVEM4"].data],
            [WAD.db["MASK"]["MASKED1"].mask, WAD.db["ABVM"]["ABOVEM4A"].mask, WAD.db["ABVM"]["ABOVEM4"].mask],
            [WAD.db["SIDE"]["SIDE21"].data],
            floorimage)
        self.tiles[163] = thintile(
            [WAD.db["MASK"]["MASKED1A"].data, WAD.db["ABVM"]["ABOVEM4A"].data, WAD.db["ABVM"]["ABOVEM4"].data],
            [WAD.db["MASK"]["MASKED1A"].mask, WAD.db["ABVM"]["ABOVEM4A"].mask, WAD.db["ABVM"]["ABOVEM4"].mask],
            [WAD.db["SIDE"]["SIDE21"].data],
            floorimage)
        self.tiles[164] = thintile(
            [WAD.db["MASK"]["MASKED2"].data, WAD.db["ABVM"]["ABOVEM4A"].data, WAD.db["ABVM"]["ABOVEM4"].data],
            [WAD.db["MASK"]["MASKED2"].mask, WAD.db["ABVM"]["ABOVEM4A"].mask, WAD.db["ABVM"]["ABOVEM4"].mask],
            [WAD.db["SIDE"]["SIDE21"].data],
            floorimage)
        self.tiles[165] = thintile(
            [WAD.db["MASK"]["MASKED2A"].data, WAD.db["ABVM"]["ABOVEM4A"].data, WAD.db["ABVM"]["ABOVEM4"].data],
            [WAD.db["MASK"]["MASKED2A"].mask, WAD.db["ABVM"]["ABOVEM4A"].mask, WAD.db["ABVM"]["ABOVEM4"].mask],
            [WAD.db["SIDE"]["SIDE21"].data],
            floorimage)
        self.tiles[166] = thintile(
            [WAD.db["MASK"]["MASKED3"].data, WAD.db["ABVM"]["ABOVEM4A"].data, WAD.db["ABVM"]["ABOVEM4"].data],
            [WAD.db["MASK"]["MASKED3"].mask, WAD.db["ABVM"]["ABOVEM4A"].mask, WAD.db["ABVM"]["ABOVEM4"].mask],
            [WAD.db["SIDE"]["SIDE21"].data],
            floorimage)
        self.tiles[167] = thintile(
            [WAD.db["MASK"]["MASKED3A"].data, WAD.db["ABVM"]["ABOVEM4A"].data, WAD.db["ABVM"]["ABOVEM4"].data],
            [WAD.db["MASK"]["MASKED3A"].mask, WAD.db["ABVM"]["ABOVEM4A"].mask, WAD.db["ABVM"]["ABOVEM4"].mask],
            [WAD.db["SIDE"]["SIDE21"].data],
            floorimage)
        self.tiles[168] = thintile(
            [WAD.db["MASK"]["MASKED4"].data, WAD.db["ABVM"]["ABOVEM4A"].data, WAD.db["ABVM"]["ABOVEM4"].data],
            [WAD.db["MASK"]["MASKED4"].mask, WAD.db["ABVM"]["ABOVEM4A"].mask, WAD.db["ABVM"]["ABOVEM4"].mask],
            [WAD.db["SIDE"]["SIDE21"].data],
            floorimage)
        self.tiles[170] = thintile(
            [WAD.db["MASK"]["DOGMASK"].data, WAD.db["ABVM"]["ABOVEM9"].data, WAD.db["ABVM"]["ABOVEM4"].data],
            [WAD.db["MASK"]["DOGMASK"].mask, WAD.db["ABVM"]["ABOVEM9"].mask, WAD.db["ABVM"]["ABOVEM4"].mask],
            [WAD.db["SIDE"]["SIDE21"].data],
            floorimage)
        self.tiles[171] = thintile(
            [WAD.db["MASK"]["PEEPMASK"].data, WAD.db["ABVM"]["ABOVEM4A"].data, WAD.db["ABVM"]["ABOVEM4"].data],
            [WAD.db["MASK"]["PEEPMASK"].mask, WAD.db["ABVM"]["ABOVEM4A"].mask, WAD.db["ABVM"]["ABOVEM4"].mask],
            [WAD.db["SIDE"]["SIDE21"].data],
            floorimage)

        # Fence
        self.tiles[179] = thintile(
            [WAD.db["MASK"]["RAILING"].data, Image.new("L", (64, 64), 0)],
            [WAD.db["MASK"]["RAILING"].mask, Image.new("L", (64, 64), 0)],
            None, floorimage, viewheightoverride=48)

        # Switches
        self.tiles[157] = thintile(
            [WAD.db["HMSK"]["HSWITCH1"].data, WAD.db["HMSK"]["HSWITCH2"].data, WAD.db["HMSK"]["HSWITCH3"].data],
            [WAD.db["HMSK"]["HSWITCH1"].mask, WAD.db["HMSK"]["HSWITCH2"].mask, WAD.db["HMSK"]["HSWITCH3"].mask],
            None, floorimage)
        self.tiles[175] = thintile(
            [WAD.db["HMSK"]["HSWITCH1"].data, WAD.db["HMSK"]["HSWITCH2"].data, WAD.db["HMSK"]["HSWITCH3"].data],
            [WAD.db["HMSK"]["HSWITCH1"].mask, WAD.db["HMSK"]["HSWITCH2"].mask, WAD.db["HMSK"]["HSWITCH3"].mask],
            None, floorimage)

        # Exit Tiles
        self.tiles[172] = thintile(
            [WAD.data["EXIT"][2].data, WAD.db["ABVM"]["ABOVEM4A"].data, WAD.db["ABVM"]["ABOVEM4"].data],
            [WAD.data["EXIT"][2].mask, WAD.db["ABVM"]["ABOVEM4A"].mask, WAD.db["ABVM"]["ABOVEM4"].mask],
            [WAD.db["SIDE"]["SIDE21"].data],
            floorimage)
        self.tiles[173] = thintile(
            [WAD.data["EXIT"][3].data, WAD.db["ABVM"]["ABOVEM4A"].data, WAD.db["ABVM"]["ABOVEM4"].data],
            [WAD.data["EXIT"][3].mask, WAD.db["ABVM"]["ABOVEM4A"].mask, WAD.db["ABVM"]["ABOVEM4"].mask],
            [WAD.db["SIDE"]["SIDE21"].data],
            floorimage)
        self.tiles[174] = thintile(
            [WAD.data["EXIT"][4].data, WAD.db["ABVM"]["ABOVEM4A"].data, WAD.db["ABVM"]["ABOVEM4"].data],
            [WAD.data["EXIT"][4].mask, WAD.db["ABVM"]["ABOVEM4A"].mask, WAD.db["ABVM"]["ABOVEM4"].mask],
            [WAD.db["SIDE"]["SIDE21"].data],
            floorimage)

        # Animating Tiles
        # List from RT_STAT.C line 194
        # Mapping from RT_TED.C line 2124
        self.tiles[44] = walltile([WAD.db["ANIM"]["FPLACE1"].data])
        self.tiles[45] = walltile([WAD.db["ANIM"]["ANIMFAC1"].data])

        self.tiles[106] = walltile([WAD.db["ANIM"]["ANIMY1"].data])
        self.tiles[107] = walltile([WAD.db["ANIM"]["ANIMR1"].data])

        self.tiles[224] = walltile([WAD.db["ANIM"]["ANIMONE1"].data])
        self.tiles[225] = walltile([WAD.db["ANIM"]["ANIMTWO1"].data])
        self.tiles[226] = walltile([WAD.db["ANIM"]["ANIMTHR1"].data])
        self.tiles[227] = walltile([WAD.db["ANIM"]["ANIMFOR1"].data])
        self.tiles[228] = walltile([WAD.db["ANIM"]["ANIMBW1"].data])
        self.tiles[229] = walltile([WAD.db["ANIM"]["ANIMYOU1"].data])
        self.tiles[230] = walltile([WAD.db["ANIM"]["ANIMBW1"].data])
        self.tiles[231] = walltile([WAD.db["ANIM"]["ANIMBP1"].data])
        self.tiles[232] = walltile([WAD.db["ANIM"]["ANIMBP1"].data])
        self.tiles[233] = walltile([WAD.db["ANIM"]["ANIMFW1"].data])

        self.tiles[242] = walltile([WAD.db["ANIM"]["ANIMLAT1"].data])
        self.tiles[243] = walltile([WAD.db["ANIM"]["ANIMST1"].data])
        self.tiles[244] = walltile([WAD.db["ANIM"]["ANIMRP1"].data])

    def generate_isometric(self, height):
        """ Generates isometric images for every tile in this database
        at the given map height.
        """
        for wall in self.tiles:
            wall.generate_isometric(height)
        self.spacer.generate_isometric(height)

