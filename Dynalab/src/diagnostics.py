#!/usr/bin/env python

from gettext import gettext as _
from gettext import ngettext

import inkex

from diagnostic_clones import MarkClones
from diagnostic_effects import MarkEffects
from diagnostic_groups import MarkGroups
from diagnostic_images import MarkImages
from diagnostic_open_paths import MarkOpenPaths
from diagnostic_outside_page import MarkOutside
from diagnostic_shapes import MarkShapes
from diagnostic_text import MarkText
from diagnostic_tiny import MarkTiny
from lib import dynalab

EXTENSIONS = {
    "non_paths": [MarkText, MarkImages, MarkShapes, MarkClones, MarkEffects],
    "groups": [MarkGroups],
    "tiny": [MarkTiny],
    "outside_objects": [MarkOutside],
    "open_paths": [MarkOpenPaths],
}


class Battery(dynalab.Ext):
    """
    battery of simple diagnostics run sequentially
    """

    name = _("diagnostics")

    def add_arguments(self, pars):
        pars.add_argument(
            "--non-paths", type=inkex.Boolean, default=True, help="mark non path objets", dest="non_paths"
        )
        pars.add_argument("--tiny", type=inkex.Boolean, default=True, help="mark tiny elements")
        pars.add_argument("--groups", type=inkex.Boolean, default=True, help="mark groups, layers and symbols")
        pars.add_argument(
            "--outside-objects",
            type=inkex.Boolean,
            default=True,
            help="mark objects outside the page",
            dest="outside_objects",
        )
        pars.add_argument("--open-paths", type=inkex.Boolean, default=True, help="mark open paths", dest="open_paths")

        pars.add_argument(
        "--max_time",
        type=float,
        default=0.0,
        help="Maximum running time in seconds (0 = unlimited)",
        )

        for Ext in EXTENSIONS.values():
            for ext in Ext:
                inst = ext(reset_artifacts=False)
                inst.add_arguments(pars)

    def effect(self):
        stopped_early = False
        reset_artifacts = True
        inst = None
        counter = 0
        BB = {}

        max_time_s = getattr(self.options, "max_time", 0.0)
        max_time_ms = max_time_s * 1000.0

        def time_exceeded():
            return max_time_ms > 0 and self.get_timer() >= max_time_ms
        
        for name, Ext in EXTENSIONS.items():
            if getattr(self.options, name):

                if time_exceeded():
                    stopped_early = True
                    break

                for ext in Ext:
                    if time_exceeded():
                        stopped_early = True
                        break
                    inst = ext(reset_artifacts=reset_artifacts)
                    reset_artifacts = False
                    inst.options = self.options
                    inst.document = self.document
                    inst.svg = self.svg
                    inst.BB = BB
                    inst.effect(clean=False)
                    BB = inst.BB
                    counter += 1
                if stopped_early:
                    break
        if inst:
            inst.clean_artifacts(force=False)
        if stopped_early:
            self.message(
                _("Analyse interrompue : limite de temps atteinte (résultats partiels)."),
                verbosity=1,
            )

        self.message(
            ngettext(
                "{counter} diagnostic extension was run", "{counter} diagnostic extensions were run", counter
            ).format(counter=counter),
            verbosity=1,
        )
        self.message(
            _("{extension:s}: running time = {time:.0f}ms").format(extension=self.name, time=self.get_timer()),
            verbosity=3,
        )
        self.message("", verbosity=1)


if __name__ == "__main__":
    Battery().run()
