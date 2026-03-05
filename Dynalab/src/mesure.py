#!/usr/bin/env python3
# coding=utf-8
#
# Copyright (C) 2015 ~suv <suv-sf@users.sf.net>
# Copyright (C) 2010 Alvin Penner
# Copyright (C) 2006 Georg Wiora
# Copyright (C) 2006 Nathan Hurst
# Copyright (C) 2005 Aaron Spike, aaron@ekips.org
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#
"""
This extension module can measure arbitrary path and object length
It adds text to the selected path containing the length in a given unit.
Area and Center of Mass calculated using Green's Theorem:
http://mathworld.wolfram.com/GreensTheorem.html
"""

import inkex

from gettext import gettext as _

from lib import dynalab,csvReader


from inkex.bezier import csparea, cspcofm
from inkex.localization import inkex_gettext as _
from inkex.paths.interfaces import LengthSettings


class MeasureLength(dynalab.Ext):
    """Measure the length of selected paths"""

    def add_arguments(self, pars):
        pars.add_argument(
            "--type", dest="mtype", default="length", help="Type of measurement"
        )

        pars.add_argument(
            "--materials", dest="materials", type=int, default=1, help="Type of materials"
        )
        
        pars.add_argument(
            "--presetFormat", default="default", help="Preset text layout"
        )
        pars.add_argument(
            "--startOffset", default="custom", help="Text Offset along Path"
        )
        pars.add_argument(
            "--startOffsetCustom", type=int, default=50, help="Text Offset along Path"
        )
        pars.add_argument("--anchor", default="start", help="Text Anchor")
        pars.add_argument("--position", default="start", help="Text Position")
        pars.add_argument("--angle", type=float, default=0, help="Angle")
        pars.add_argument(
            "-f",
            "--fontsize",
            type=int,
            default=12,
            help="Size of length label text in px",
        )
        pars.add_argument(
            "-o",
            "--offset",
            type=float,
            default=-6,
            help="The distance above the curve",
        )
        pars.add_argument(
            "-u", "--unit", default="px", help="The unit of the measurement"
        )
        pars.add_argument(
            "-p",
            "--precision",
            type=int,
            default=2,
            help="Number of significant digits after decimal point",
        )
        pars.add_argument(
            "-s",
            "--scale",
            type=float,
            default=1.0,
            help="Scale Factor (Drawing:Real Length)",
        )

    def effect(self):
        tMin,tMax = 0,0
        # get number of digits
        prec = int(self.options.precision)
        scale = self.svg.viewport_to_unit(
            "1" + self.svg.document_unit
        )  # convert to document units
        self.options.offset *= scale
        factor = self.svg.unit_to_viewport(1, self.options.unit)

        paths = []

        for elem in self.svg.selection.values():
            if isinstance(elem, inkex.PathElement):
                paths.append(elem)
            else:
                new_elem = elem.to_path_element()
                elem.replace_with(new_elem)
                paths.append(new_elem)

        if not paths:
            raise inkex.AbortExtension(_("Please select at least one object."))
        
        for node in paths:            
            path: inkex.Path = node.path.transform(node.composed_transform())
            if self.options.mtype == "length":
                settings = LengthSettings(error=1e-8)
                stotal = sum(
                    command.length(settings=settings)
                    for command in path.proxy_iterator()
                    if command.letter not in "mM"
                )
                #self.group = node.getparent().add(TextElement())
            elif self.options.mtype == "area":
                csp = path.to_superpath()
                stotal = abs(csparea(csp) * factor * self.options.scale)
            else:
                continue
            # Format the length as string
            val = round(stotal * factor * self.options.scale, prec)
            if self.options.mtype == "area":
                values = csvReader.readAreaCSV(self.options.materials)
                tMin += values[0] * val
                tMax += values[1] * val
            else:
                values = csvReader.readLengthCSV(self.options.materials)
                tMin += values[0] * val
                tMax += values[1] * val

        self.message(
            _(
                """
                Le chemin va prendre entre {tMin:.2f} s et {tMax:.2f} s à être dessiné
                """
            ).format(tMin=tMin,tMax=tMax)
        )

   
if __name__ == "__main__":
    MeasureLength().run()
