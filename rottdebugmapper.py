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

"""Simple Debug Mapper for ROTT maps
This creates an HTML output of the ROTT data for debugging purposes.
"""
import sys, os

import rtl

class debugmapper:
    """Debug Mapper to generate HTML debug maps"""
    def __init__(self, level):
        print("Processing {} '{}'".format(level.index+1, level.name))
        self.level = level

    def savemap(self, outpath):
        """Saves the current level as an HTML debug map"""
        outfile = open(os.path.join(outpath, "{:02}-{}.html".format(self.level.index+1, self.level.name)), 'w')
        outfile.write("""<html><head>
<title>{}</title>
<style>
.info{{ color: blue }}
.sprite{{ color: green }}
.wall {{background-color: #DDD}}
.sky {{background-color: #BBF}}
.nothing {{background-color: #BBB}}
.index {{font-size: 0.8em}}
</style></head><body>
<table>""".format(self.level.name))

        for y in range(128):
            outfile.write('<tr>')
            for x in range(128):
                index = y*128 + x
                # Decide which colour (via class attribute) to draw based
                # on solid wall, floor or empty space
                # Print index and wall id, as applicable
                if self.level.walls[index] == 0:
                    outfile.write('<td class="nothing">')
                elif self.level.info[index] == 13:
                    outfile.write('<td class="sky"><span class="index">{}</span><br>W{}'.format(index, self.level.walls[index]))
                elif self.level.walls[index] in range(108,153):
                    outfile.write('<td><span class="index">{}</span><br>W{}'.format(index, self.level.walls[index]))
                else:
                    outfile.write('<td class="wall"><span class="index">{}</span><br>W{}'.format(index, self.level.walls[index]))

                # Print sprite and info id as applicable
                if self.level.info[index] > 0:
                    outfile.write('<br/><span class="info">I{:04X}</span>'.format(self.level.info[index]))
                if self.level.sprites[index] > 0:
                    outfile.write('<br/><span class="sprite">S{}</span>'.format(self.level.sprites[index]))
                outfile.write('</td>')

            outfile.write('</tr>\n')

        outfile.write("</table></body></html>\n")
        outfile.close()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("""Usage: python rottdebugmapper.py [RTL/RTC FILE]...

Generates a debug HTML file for each level in the specified ROTT RTL or
RTC file. Each index in the map is output into a cell in an HTML table
containing the following information:
The map index
The data in the walls layer, if present, as W###
The data in the info layer, if present, as I###
The data in the sprite layer, if present, as S###
""")
    else:
        for filename in sys.argv[1:]:
            print("Loading Map Data")
            RTL = rtl.RTLFile(filename, noprocess=True)

            outpath = filename.replace('.', ' ') + ' DEBUG'
            if not os.path.exists(outpath):
                os.mkdir(outpath)

            for level in RTL.levels:
                mapper = debugmapper(level)
                mapper.savemap(outpath)

            RTL.close()
