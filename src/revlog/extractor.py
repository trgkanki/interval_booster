import os
import math
from collections import namedtuple
from ..utils.log import log

import aqt

RevlogEntry = namedtuple("RevlogEntry", ["reviewType", "ease", "epoch"])

_revlogMap = {}


def createRevlogMap():
    global _revlogMap
    _revlogMap = {}
    rows = aqt.mw.col.db.all("select * from revlog order by id ASC")

    for row in rows:
        epoch, cid, usn, ease, ivl, lastIvl, factor, duration, reviewType = row
        if cid not in _revlogMap:
            _revlogMap[cid] = []

        # Convert to days since col.crt
        epoch /= 1000 * 86400  # ms to day
        _revlogMap[cid].append(RevlogEntry(reviewType, ease, epoch))

    log("Total %d revlogs from %d cards" % (len(rows), len(_revlogMap)))
    return _revlogMap


def getRevlogMap():
    return _revlogMap
