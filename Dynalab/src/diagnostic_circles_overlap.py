#!/usr/bin/env python
from gettext import gettext as _
import math
import inkex

from lib import dynalab
from lib.dynalab import WARNING, ERROR


def ellipse_bbox(cx, cy, rx, ry):
    return (cx - rx, cy - ry, cx + rx, cy + ry)  


def bbox_overlap(a, b):
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    return not (ax2 < bx1 or bx2 < ax1 or ay2 < by1 or by2 < ay1)


def ellipse_polygon(cx, cy, rx, ry, n=48):
    pts = []
    for k in range(n):
        t = 2.0 * math.pi * k / n
        pts.append((cx + rx * math.cos(t), cy + ry * math.sin(t)))
    return pts


def orient(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def on_segment(a, b, p, eps):
    return (
        min(a[0], b[0]) - eps <= p[0] <= max(a[0], b[0]) + eps
        and min(a[1], b[1]) - eps <= p[1] <= max(a[1], b[1]) + eps
    )


def segments_intersect(a, b, c, d, eps):
    o1 = orient(a, b, c)
    o2 = orient(a, b, d)
    o3 = orient(c, d, a)
    o4 = orient(c, d, b)

    if (o1 > eps and o2 < -eps or o1 < -eps and o2 > eps) and (o3 > eps and o4 < -eps or o3 < -eps and o4 > eps):
        return True

    if abs(o1) <= eps and on_segment(a, b, c, eps):
        return True
    if abs(o2) <= eps and on_segment(a, b, d, eps):
        return True
    if abs(o3) <= eps and on_segment(c, d, a, eps):
        return True
    if abs(o4) <= eps and on_segment(c, d, b, eps):
        return True

    return False


def point_in_ellipse(x, y, cx, cy, rx, ry, eps=0.0):
    if rx <= 0 or ry <= 0:
        return False
    dx = (x - cx) / rx
    dy = (y - cy) / ry
    return (dx * dx + dy * dy) <= (1.0 + eps)


class MarkCircleOverlaps(dynalab.Ext):
    """
    detect circle/ellipse overlaps (no transforms)
    """
    name = _("detect circle/ellipse overlaps (no transforms)")

    def add_arguments(self, pars):
        super().add_arguments(pars)
        pars.add_argument("--n", type=int, default=48, help="number of points to approximate ellipses")
        pars.add_argument("--eps", type=float, default=1e-6, help="tolerance in SVG units")

    def effect(self, clean=True):
        self.message(self.name, verbosity=3)

        artifacts_ready = False

        ellipses = []
        for elem in self.selected_or_all(skip_groups=True):
            if isinstance(elem, inkex.Circle):
                cx = float(elem.get("cx", "0"))
                cy = float(elem.get("cy", "0"))
                r = float(elem.get("r", "0"))
                ellipses.append((elem, cx, cy, r, r))

            elif isinstance(elem, inkex.Ellipse):
                cx = float(elem.get("cx", "0"))
                cy = float(elem.get("cy", "0"))
                rx = float(elem.get("rx", "0"))
                ry = float(elem.get("ry", "0"))
                ellipses.append((elem, cx, cy, rx, ry))

        self.message(_("Ellipses found: {n}").format(n=len(ellipses)), verbosity=1)

        eps = float(self.options.eps)
        npts = int(self.options.n)


        data = []
        for elem, cx, cy, rx, ry in ellipses:
            bb = ellipse_bbox(cx, cy, rx, ry)
            poly = ellipse_polygon(cx, cy, rx, ry, n=npts)
            data.append((elem, cx, cy, rx, ry, bb, poly))


        found = 0
        m = len(data)

        for i in range(m):
            e1, cx1, cy1, rx1, ry1, bb1, p1 = data[i]

            for j in range(i + 1, m):
                e2, cx2, cy2, rx2, ry2, bb2, p2 = data[j]


                if not bbox_overlap(bb1, bb2):
                    continue

                if abs(cx1 - cx2) <= eps and abs(cy1 - cy2) <= eps and abs(rx1 - rx2) <= eps and abs(ry1 - ry2) <= eps:
                    found += 1
                    msg = _("Two identical ellipses are superposed: {id1} and {id2}").format(
                        id1=e1.get_id(), id2=e2.get_id()
                    )
                    if not artifacts_ready:
                        self.init_artifact_layer()
                        artifacts_ready = True
                    self.outline_bounding_box(ERROR, e1, msg=msg)
                    self.outline_bounding_box(ERROR, e2, msg=msg)
                    continue

                inter = 0
                for a in range(len(p1)):
                    a1 = p1[a]
                    a2 = p1[(a + 1) % len(p1)]
                    for b in range(len(p2)):
                        b1 = p2[b]
                        b2 = p2[(b + 1) % len(p2)]
                        if segments_intersect(a1, a2, b1, b2, eps):
                            inter += 1
                            if inter >= 2:
                                break
                    if inter >= 2:
                        break

                if inter >= 2:
                    found += 1
                    msg = _("Ellipse overlap detected: {id1} and {id2}").format(id1=e1.get_id(), id2=e2.get_id())
                    if not artifacts_ready:
                        self.init_artifact_layer()
                        artifacts_ready = True
                    self.outline_bounding_box(WARNING, e1, msg=msg)
                    self.outline_bounding_box(WARNING, e2, msg=msg)
                    continue

                if point_in_ellipse(cx1, cy1, cx2, cy2, rx2, ry2, eps=1e-9) or point_in_ellipse(
                    cx2, cy2, cx1, cy1, rx1, ry1, eps=1e-9
                ):
                    found += 1
                    msg = _("Ellipse containment overlap detected: {id1} and {id2}").format(
                        id1=e1.get_id(), id2=e2.get_id()
                    )
                    if not artifacts_ready:
                        self.init_artifact_layer()
                        artifacts_ready = True
                    self.outline_bounding_box(WARNING, e1, msg=msg)
                    self.outline_bounding_box(WARNING, e2, msg=msg)


        if clean and artifacts_ready:
            self.clean_artifacts(force=False)

        self.message(_("Overlapping ellipse pairs found: {n}").format(n=found), verbosity=1)


if __name__ == "__main__":
    MarkCircleOverlaps().run()