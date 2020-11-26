import os
import math
from collections import namedtuple
from ..utils.debugLog import log

import aqt
from anki.utils import ids2str

RevlogEntry = namedtuple(
    "RevlogEntry", ["reviewType", "ease", "epoch", "ivl", "lastIvl", "factor"]
)


def getRevlogMap(cardIds=None):
    revlogMap = {}

    if cardIds is None:
        query = "select * from revlog order by id"
    else:
        query = "select * from revlog where cid in %s order by id" % ids2str(cardIds)

    col = aqt.mw.col

    rows = col.db.all(query)
    # This seemingly innocent attribute query issues python ↔ rust barrier cross
    # every time, so this property getter shouldn't be inside the loop.
    colCrt = col.crt
    for row in rows:
        epoch, cid, usn, ease, ivl, lastIvl, factor, duration, reviewType = row
        if cid not in revlogMap:
            revlogMap[cid] = []

        # Convert to days since col.crt
        epoch = (epoch / 1000 - colCrt) / 86400  # ms to day
        revlogMap[cid].append(
            RevlogEntry(reviewType, ease, epoch, ivl, lastIvl, factor)
        )

    return revlogMap
