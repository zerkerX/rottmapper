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

""" Module for processing ROTT wad files (same format as DOOM wad files,
but different file formats inside).

Also dumps the complete contents of the wad file to disk if run directly.
Only tested for DARKWAR.WAD.
"""
import pdb
import struct, sys, os.path

from PIL import Image, ImageOps

# Lump types
(UNLOADED, FLOORCEIL, SKY, WALL, PATCH, PIC, RAW, FONT, LBM) = list(range(9))

class WadFile:
    """ Wad file main class. Represents the contents of a ROTT wad file.

    Public member variables:
    data -- dictionary of lists of lumps, keyed by WAD section. Within
            each section, the lumps are presented as a straight list.
    db -- dictionary of dictionary of lumps, keyed by WAD section.
          Within each section, the lumps are presented as another
          dictionary, keyed by lump name.
    palette -- the main ROTT palette lump
    """
    # Wad Header
    #typedef struct
    #{
        #char   identification[4];
        #long   numlumps;
        #long   infotableofs;
    #} wadinfo_t;
    wadheader = '<4sll'

    def __init__(self, filename):
        """ Initializes the current WAD instance by loading from
        the specified file. Will populate the lists of lumps, but will
        not load them yet.
        """
        self.filedata = open(filename, 'rb')
        (self.wadid, self.numlumps, infotable) = struct.unpack(self.wadheader,
            self.filedata.read(struct.calcsize(self.wadheader)))

        self.filedata.seek(infotable)
        self.data = {}
        self.db = {}
        self.palette = None
        self.filename = filename

        block = 'General'
        for lumpnum in range(self.numlumps):
            templump = Lump(self.filedata)

            if templump.size == 0:
                if templump.name.endswith("STOP"):
                    block = 'General'
                elif templump.name.endswith("STRT"):
                    block = templump.name[:-4]
                elif templump.name.endswith("START"):
                    block = templump.name[:-5]
                else:
                    block = templump.name
            elif templump.name == "PAL":
                self.palette = templump
            else:
                if not block in self.data:
                    self.data[block] = []
                    self.db[block] = dict()
                self.data[block].append(templump)
                self.db[block][templump.name] = templump

        if self.palette != None:
            self.palette.load_raw()


    def listing(self, listfile):
        """ Creates a directory listing file of the contents of this
        wad file, grouped by section. Saves to the specified file name.
        """
        listing = open(listfile, 'w')

        listing.write("{}\t{}\n============================\n".format(
            self.wadid, self.numlumps))
        if self.palette != None:
            listing.write("Palette\n----------------------------\n")
            listing.write('{}\t{}\n'.format(self.palette.name, self.palette.size))
        for block in list(self.data.keys()):
            listing.write("\n{}\n----------------------------\n".format(block))
            for lump in self.data[block]:
                listing.write('{}\t{}\n'.format(lump.name, lump.size))

        listing.close()

    def cacheimages(self):
        """ Caches (i.e. read from disk and processes) the important
        images for rendering a map.
        """
        for lumptype in ["WALL", "ELEV", "ANIM", "DOOR", "EXIT", "SIDE", "ABVW"]:
            for lump in self.data[lumptype]:
                if (lump.is_wall()):
                    lump.load_wall(self.palette.data)
                else:
                    lump.load_patch(self.palette.data)
        for lump in self.data["UPDN"]:
            lump.load_floorceil(self.palette.data)
        for lumptype in ["SHAP", "MASK", "HMSK", "ABVM"]:
            for lump in self.data[lumptype]:
                lump.load_patch(self.palette.data)
        self.db["General"]["NEWFNT1"].load_font(self.palette.data)
        self.db["General"]["SMALLFON"].load_font(self.palette.data)
        self.db["General"]["KEY1"].load_pic(self.palette.data)
        self.db["General"]["KEY2"].load_pic(self.palette.data)
        self.db["General"]["KEY3"].load_pic(self.palette.data)
        self.db["General"]["KEY4"].load_pic(self.palette.data)

    def loadall(self):
        """ Loads and processes all data from the wad file."""
        self.cacheimages()

        # Manually load any entries that need to be loaded specially
        # Note: Order matters! Load palettes first!
        self.db["PLAYMAPS"]["FINDRPAL"].load_raw()
        self.db["PLAYMAPS"]["FINFRPAL"].load_raw()
        self.db["PLAYMAPS"]["NICPAL"].load_raw()
        self.db["PLAYMAPS"]["BOATPAL"].load_raw() # Not sure what uses this
        self.db["General"]["AP_PAL"].load_raw()

        self.db["PLAYMAPS"]["FINLDOOR"].load_patch(self.db["PLAYMAPS"]["FINDRPAL"].data)
        self.db["PLAYMAPS"]["FINLFIRE"].load_patch(self.db["PLAYMAPS"]["FINFRPAL"].data)
        self.db["PLAYMAPS"]["BUDGCUT"].load_patch(self.db["PLAYMAPS"]["NICPAL"].data)
        self.db["PLAYMAPS"]["NICOLAS"].load_patch(self.db["PLAYMAPS"]["NICPAL"].data)
        self.db["PLAYMAPS"]["ONEYEAR"].load_patch(self.db["PLAYMAPS"]["NICPAL"].data)
        self.db["General"]["AP_TITL"].load_patch(self.db["General"]["AP_PAL"].data)
        self.db["General"]["AP_WRLD"].load_pic(self.db["General"]["AP_PAL"].data)

        self.db["General"]["TINYFONT"].load_font(self.palette.data)
        self.db["General"]["ITNYFONT"].load_font(self.palette.data)
        self.db["General"]["IFNT"].load_font(self.palette.data)
        self.db["General"]["SIFONT"].load_font(self.palette.data)
        self.db["General"]["LIFONT"].load_font(self.palette.data)
        self.db["PLAYMAPS"]["BOOTBLOD"].load_lbm()
        self.db["PLAYMAPS"]["BOOTNORM"].load_lbm()
        self.db["PLAYMAPS"]["DEADBOSS"].load_lbm()
        self.db["PLAYMAPS"]["IMFREE"].load_lbm()

        # Load the rest of the entries
        for lump in self.data["SKY"]:
            lump.load_sky(self.palette.data)
        for lumptype in ["GUN", "General", "ORDR", "PLAYMAPS"]:
            for lump in self.data[lumptype]:
                if lump.contents == UNLOADED:
                    lump.load_patch(self.palette.data)
                    if lump.contents == UNLOADED:
                        lump.load_pic(self.palette.data)
                    if lump.contents == UNLOADED:
                        lump.load_raw()
        for lumptype in ["DIGI", "SONG", "AD", "SPECMAPS", "PC"]:
            for lump in self.data[lumptype]:
                lump.load_raw()

    @staticmethod
    def createpath(pathname):
        """ Simple utility method for creating a path only if it does
        not already exist.
        """
        if not os.path.exists(pathname):
            os.mkdir(pathname)

    def dumpcontents(self, outpath):
        """ Dumps the complete contents of this WAD file to disk in
        the specified folder. Each grouping of the WAD file will be
        written to a separate subfolder. Each entry in that group
        will be indexed by its position in the section.
        """
        self.createpath(outpath)

        debugfile = open(os.path.join(outpath, 'patchinfo.txt'), 'w')
        for lumptype in list(self.data.keys()):
            self.createpath(os.path.join(outpath, lumptype))
            for index, lump in enumerate(self.data[lumptype]):
                if (lump.contents == WALL or lump.contents == FLOORCEIL
                        or lump.contents == SKY or lump.contents == PIC
                        or lump.contents == LBM):

                    lump.data.save(os.path.join(outpath, lumptype,
                        "{:04}_{}.png".format(index, lump.name)))
                elif lump.contents == PATCH:
                    # Masks need to be recombined with their image for proper transparency on output
                    compositeimage = Image.new("RGBA", (lump.actwidth, lump.actheight))
                    compositeimage.paste(lump.data, (0, 0), lump.mask)
                    compositeimage.save(os.path.join(outpath, lumptype,
                        "{:04}_{}.png".format(index, lump.name)))

                    # Print debug header information for each image
                    debugfile.write("{} {} {}x{} {},{}".format(lump.name,
                        lump.origsize, lump.width, lump.height, lump.leftoffset,
                        lump.topoffset))
                    if lump.translevel != None:
                        debugfile.write(" Trans:{}".format(lump.translevel))
                    debugfile.write("\n")

                elif lump.contents == RAW:
                    if lumptype == 'DIGI':
                        extension = '.VOC'
                    elif lumptype == 'SONG':
                        extension = '.MID'
                    elif lumptype == 'AD':
                        extension = '.IMF' # Just a guess, can't get to work in AdPlug
                    elif lump.name in ['SHARTITL', 'SHARTIT2', 'GUSMIDI', 'LICENSE']:
                        extension = '.TXT'
                    else:
                        extension = ''

                    tempfile = open(os.path.join(outpath, lumptype,
                        "{:04}_{}{}".format(index, lump.name, extension)), 'wb')
                    tempfile.write(lump.data)
                    tempfile.close()

                elif lump.contents == FONT:
                    fontpath = os.path.join(outpath, lumptype,
                        "{:04}_{}".format(index, lump.name))
                    self.createpath(fontpath)

                    for index, fontchar in enumerate(lump.data):
                        if fontchar != None:
                            # Masks need to be recombined with their image for proper transparency on output
                            compositeimage = Image.new("RGBA", fontchar.size)
                            compositeimage.paste(fontchar, (0, 0), lump.mask[index])
                            compositeimage.save(os.path.join(fontpath, "{:03}.png".format(index)))

        # Special handling for palette. Generate an image file as well as raw dump:
        # TODO: do the same for alternate palettes?
        tempfile = open(os.path.join(outpath, "PAL"), 'wb')
        tempfile.write(self.palette.data)
        tempfile.close()

        tempimg = Image.new("P", (16,16))
        tempimg.putdata(list(range(256)))
        tempimg.putpalette(self.palette.data)
        tempimg.save(os.path.join(outpath, "PAL.png"))

        debugfile.close()

    def close(self):
        """ Closes the wad file."""
        self.filedata.close()

class Lump:
    """ Class for a lump entry in the WAD file. Contains functions
    for loading and processing most types of lumps used by ROTT.

    Public member variables:
    name -- the directory listing name for this lump
    size -- the file size of this lump
    contents -- an enumeration (defined at the top of this file)
                representing what type of data is loaded into this lump.
    data -- the decoded data for this lump. Typically a PIL image object,
            but can also be a raw byte array.
    mask -- for patches, this contains the transparency mask to combine
            with the main image data.
    """

    #typedef struct
    #{
        #long       filepos;
        #long       size;
        #char       name[8];
    #} lumpinfo_t;
    direntry = '<ll8s'

    def __init__(self, filedata):
        """ Initializes the basic information about a lump described
        at the current position in the file.

        filedata -- a file handle open for the wad file. The file handle
                    needs to be at the position to read a lump header.
        """
        (self.pos, self.size, tempname) = struct.unpack(self.direntry,
            filedata.read(struct.calcsize(self.direntry)))
        self.name = tempname.rstrip('\0')
        self.contents = UNLOADED

        # Cache file handle for future reads. Note that this will be invalid
        # if the WAD file itself is closed.
        self.filedata = filedata

    def is_wall(self):
        """ Tests if this lump is a WALL lump type. """
        return (self.size == 4096 and self.name != 'SDOOR4A')

    def load_wall(self, palette):
        """ Loads and decodes a WALL lump, storing the resulting data
        as a PIL Image object.
        """
        # Note that WALL data is actually stored column-first, but we
        # can load directly and rotate for simplicity since it is square.
        if self.is_wall():
            self.filedata.seek(self.pos)
            self.data = ImageOps.mirror(Image.fromstring("P", (64,64),
                self.filedata.read(self.size)).rotate(-90))
            self.data.putpalette(palette)
            self.contents = WALL

    #typedef struct
    #{
       #short     width,height;
       #short     orgx,orgy;
       #byte     data;
    #} lpic_t;
    floorceil = '<hhhh'

    def load_floorceil(self, palette):
        """ Loads a floor or ceiling tile lump, storing the resulting
        data as a PIL Image object.
        """
        self.filedata.seek(self.pos)
        (width, height, self.orgx, self.orgy) = struct.unpack(self.floorceil,
            self.filedata.read(struct.calcsize(self.floorceil)))
        self.data = Image.fromstring("P", (width, height),
            self.filedata.read(self.size-struct.calcsize(self.floorceil)))
        self.data.putpalette(palette)
        self.contents = FLOORCEIL

    def load_sky(self, palette):
        """ Loads and decodes a SKY lump, storing the resulting data
        as a PIL Image object.
        """
        # Note that WALL data is actually stored column-first, but we
        # can load directly and rotate for simplicity since it is square.
        self.filedata.seek(self.pos)
        (self.data, temp) = self.load_col_first(256, 200, palette)
        self.data.putpalette(palette)
        self.contents = SKY

    def load_col_first(self, width, height, palette, maskcol = -1):
        """ Loads an image of the specified size in a column-first
        arrangement. Since PIL expects a row-first orientation, this
        function is necessary to transpose loaded image data so
        PIL's raw picture mode can interpret it.

        width -- the width of the resulting image
        height -- the height of the resulting image
        palette -- the palette data for the ROTT palette
        maskcol -- the index in the ROTT palette that should be treated
                   as transparent.

        Returns an (image, mask) tuple of the loaded data as PIL Image
        objects.
        """
        tempdata = [0] * width * height
        tempmask = [0] * width * height
        tempread = struct.unpack('<{}B'.format(width * height),
            self.filedata.read(width * height))

        for y in range(height):
            for x in range(width):
                tempdata[y*width + x] = tempread[x*height + y]
                tempmask[y*width + x] = int(tempread[x*height + y] != maskcol) * 255

        tempimg = Image.new("P", (width, height))
        tempimg.putpalette(palette)
        tempimg.putdata(tempdata)

        tempmaskimg = Image.new("L", (width, height))
        tempmaskimg.putdata(tempmask)

        return (tempimg, tempmaskimg)

    #typedef struct
    #{
    #   short height;
    #   char  width[256];
    #   short charofs[256];
    #   byte  data;       // as much as required
    #} font_t;
    normfont = '<h'

    #typedef struct
    #{
    #   byte  color; (treat as short??)
    #   short height;
    #   char  width[256];
    #   short charofs[256];
    #   byte  pal[0x300];
    #   byte  data;       // as much as required
    #} cfont_t;
    cfont = '<hh'

    def load_font(self, palette = None):
        """ Loads a font lump, storing the resulting
        data as a list of 256 PIL Image objects, one for each
        character in the font.
        """

        self.filedata.seek(self.pos)
        if self.name in ["IFNT", "ITNYFONT", "SIFONT", "LIFONT"]:
            (self.colour, self.height) = struct.unpack(self.cfont,
                self.filedata.read(struct.calcsize(self.cfont)))
        else:
            (self.height,) = struct.unpack(self.normfont,
                self.filedata.read(struct.calcsize(self.normfont)))

        self.widths = struct.unpack('<256b', self.filedata.read(256))
        self.charoffs = struct.unpack('<256h', self.filedata.read(512))
        if self.name in ["IFNT", "ITNYFONT", "SIFONT", "LIFONT"]:
            self.paldata = self.filedata.read(0x300)
            #palette = self.paldata

        self.data = [None]*256
        self.mask = [None]*256
        for i in range(256):
            if self.widths[i] > 0:
                self.filedata.seek(self.pos + self.charoffs[i])
                (self.data[i], self.mask[i]) = self.load_col_first(self.widths[i], self.height, palette, 0)
        self.contents = FONT

    #typedef struct
    #{
    #   byte     width,height;
    #   byte     data;
    #} pic_t;
    smallpic = '<BB'

    #typedef struct
    #{
    #   short     width,height;
    #   short     orgx,orgy;
    #   byte     data;
    #} lpic_t;
    largepic = '<hhhh'

    def load_pic(self, palette):
        """ Loads a picture lump, either large or small-type, storing
        the resulting data as a PIL Image object.
        """

        # Try large pic first:
        self.filedata.seek(self.pos)
        (width, height, orgx, orgy) = struct.unpack(self.largepic,
            self.filedata.read(struct.calcsize(self.largepic)))
        if width * height + 8 == self.size:
            self.data = Image.fromstring("P", (height, width),
                self.filedata.read(self.size-struct.calcsize(self.largepic))).rotate(-90)
            self.data.putpalette(palette)
            self.contents = PIC
        else:
            self.filedata.seek(self.pos)
            (width, height) = struct.unpack(self.smallpic,
                self.filedata.read(struct.calcsize(self.smallpic)))
            width = width * 4

            # Small images seem to have two padding bytes on the end
            if (width * height + 2 <= self.size and self.size <= width * height + 4):
                # They also appear to be interlaced by 4 somehow
                tempdata = [0] * width * height
                tempread = struct.unpack('<{}B'.format(width * height),
                    self.filedata.read(width * height))
                phasesize = width * height / 4
                for phase in range(4):
                    for pos in range(phasesize):
                        tempdata[pos*4 + phase] = tempread[phasesize * phase + pos]

                self.data = Image.new("P", (width, height))
                self.data.putpalette(palette)
                self.data.putdata(tempdata)
                self.contents = PIC

    #typedef struct
    #{
       #short          origsize;         // the orig size of "grabbed" gfx
       #short          width;            // bounding box size
       #short          height;
       #short          leftoffset;       // pixels to the left of origin
       #short          topoffset;        // pixels above the origin
       #unsigned short collumnofs[320];  // only [width] used, the [0] is &collumnofs[width]
    #} patch_t;
    patch = '<hhhhh'

    def load_patch(self, palette):
        """ Loads a patch lump, storing the resulting data as a PIL
        Image object, with another PIL Image for the patch mask.
        """
        try:
            # Load patch header
            self.filedata.seek(self.pos)
            (self.origsize, self.width, self.height, self.leftoffset,
                self.topoffset) = struct.unpack(self.patch,
                self.filedata.read(struct.calcsize(self.patch)))

            if (self.origsize > 320 or self.width > 320
                or self.height > 320 or self.width > self.origsize
                or -self.topoffset > self.origsize
                or -self.leftoffset > self.origsize):

                return

            # Test for translevel or collumnofs. First columnofs entry
            # always points to the location just after the collumnofs array:
            (translevel,) = struct.unpack('<H', self.filedata.read(2))
            if translevel != struct.calcsize(self.patch) + self.width*2:
                self.translevel = translevel
            else:
                self.translevel = None
                self.filedata.seek(-2, os.SEEK_CUR)

            self.actwidth = max(self.width-self.leftoffset, self.origsize)
            self.actheight = max(self.height-self.topoffset, self.origsize)

            tempdata = [0]*(self.actwidth * self.actheight)
            tempmask = [0]*(self.actwidth * self.actheight)

            self.collumnofs = struct.unpack('<{}H'.format(self.width),
                self.filedata.read(self.width * 2))

            #if self.name == 'DEADTOM':
            #    pdb.set_trace()

            # Load the image column-by-column by working through the colummn offset array
            for x, offset in enumerate(self.collumnofs):
                self.filedata.seek(self.pos + offset)
                if x == len(self.collumnofs)-1:
                    colsize = self.size - offset
                else:
                    colsize = self.collumnofs[x+1] - offset
                coldata = struct.unpack('<{}B'.format(colsize),
                    self.filedata.read(colsize))

                index = 0
                while (index < len(coldata)-1):
                    ystart = coldata[index]
                    numpix = coldata[index+1]
                    index = index + 2

                    if ystart == 255:
                        break
                    elif self.translevel != None and coldata[index] == 254:
                        for y in range(ystart, ystart+numpix):
                            tempdata[(y-self.topoffset)*self.actwidth + (x-self.leftoffset)] = 0
                            tempmask[(y-self.topoffset)*self.actwidth + (x-self.leftoffset)] = 128
                        index = index + 1
                    else:
                        for indexoffs, y in enumerate(range(ystart, ystart+numpix)):
                            tempdata[(y-self.topoffset)*self.actwidth + (x-self.leftoffset)] = coldata[index+indexoffs]
                            tempmask[(y-self.topoffset)*self.actwidth + (x-self.leftoffset)] = 255
                        index = index + numpix


            self.data = Image.new("P", (self.actwidth, self.actheight))
            self.data.putpalette(palette)
            self.data.putdata(tempdata)

            self.mask = Image.new("L", (self.actwidth, self.actheight))
            self.mask.putdata(tempmask)
            self.contents = PATCH

        except:
            pass

    #typedef struct
    #{
    #   short width;
    #   short height;
    #   byte palette[768];
    #   byte data;
    #} lbm_t;
    lbm = '<hh'

    def load_lbm(self):
        """ Loads an LBM-format image (such as the infamous I'm Free
        image), storing the result as a PIL Image object.
        """
        self.filedata.seek(self.pos)
        (width, height) = struct.unpack(self.lbm,
            self.filedata.read(struct.calcsize(self.lbm)))
        #if width * height + 8 == self.size:
        # Need good sanity check. Or just manually load LBMs

        paldata = self.filedata.read(768)
        tempdata = [0]*(width * height)

        # Decode per PackBits compression algorithm
        # http://en.wikipedia.org/wiki/PackBits
        datasize = self.size - (self.filedata.tell() - self.pos)
        tempread = struct.unpack('<{}B'.format(datasize),
            self.filedata.read(datasize))

        index = 0
        pos = 0
        while pos < len(tempread) and index < (width * height):
            headerbyte = tempread[pos]
            pos = pos + 1
            if headerbyte < 0x80:
                # N+1 bytes of literal data:
                for dataoffs in range(headerbyte+1):
                    tempdata[index+dataoffs] = tempread[pos+dataoffs]
                pos = pos + headerbyte + 1
                index = index + headerbyte + 1
            elif headerbyte > 0x80 and headerbyte <= 0xFF:
                # 2's compliment bytes +1 repetition of the following data:
                repeat = (headerbyte-1 ^ 0xFF) + 1
                for dataoffs in range(repeat):
                    tempdata[index+dataoffs] = tempread[pos]
                pos = pos + 1
                index = index + repeat

        self.data = Image.new("P", (width, height))
        self.data.putpalette(paldata)
        self.data.putdata(tempdata)

        self.contents = LBM


    def load_raw(self):
        """ Loads the raw contents of a lump, storing the resulting
        data as a byte array.
        """
        self.filedata.seek(self.pos, 0)
        self.data = self.filedata.read(self.size)
        self.contents = RAW


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("""Usage: python wad.py [WAD FILE]

Extracts the complete contents of a give ROTT wad file. Currently only
supports DARKWAR.WAD. All images will be written as PNG files,
other data will remain in its original format (e.g. .mid for music,
.voc for SFX). Unidentified data will be written with no extension.
""")
    else:
        for filename in sys.argv[1:]:
            wad = WadFile(filename)

            outdir = filename + "_output"
            if not os.path.exists(outdir):
                os.mkdir(outdir)

            wad.loadall()
            wad.listing(os.path.join(outdir, 'listing.txt'))
            wad.dumpcontents(outdir)

            wad.close()
