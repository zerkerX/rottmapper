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

""" Bitmap font based on the ROTT Font format """
from PIL import Image, ImageChops

class rottfont(object):
    """ Bitmap font based on the ROTT Font format """
    def __init__(self, fontlump, colour = None):
        """ Initializes the font object, re-colouring as desired

        fontlump -- the lump instance from the ROTT wad module which
                    contains the font data
        colour -- the desired colour to use for this font
        """

        self.images = [None] * 128
        self.masks = [None] * 128

        # Copy over all of the standard ASCII symbols
        for i in range(1,96):
            if colour != None:
                # Re-colour the font
                tempimg = Image.new("RGB", fontlump.data[i].size, colour)
                self.images[i-1+0x20] = ImageChops.multiply(tempimg, fontlump.data[i].convert("RGB"))
            else:
                self.images[i-1+0x20] = fontlump.data[i]
            self.masks[i-1+0x20] = fontlump.mask[i]

    def writetext(self, picture, offset, text, mask=None):
        """ Writes the specified text to the image using this font

        picture -- image object to write to
        offset -- (x, y) coordinate for the top-left corner to start
                  writing text.
        text -- string of text to write
        mask -- image mask to write over using this font. I.e. if writing
                text on an image/mask pair, this will ensure the mask
                represents the text area as opaque
        """
        cursor = offset
        for character in text:
            if character == '\r':
                pass
            elif character == '\n':
                cursor = (offset[0], cursor[1]+self.images[0x20].size[1])
            else:
                picture.paste(self.images[ord(character)],
                    cursor, self.masks[ord(character)])
                if mask != None:
                    mask.paste(self.masks[ord(character)],
                        cursor, self.masks[ord(character)])
                cursor = (cursor[0] + self.images[ord(character)].size[0], cursor[1])
