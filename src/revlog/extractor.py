import os
import math
from collections import namedtuple
from ..utils.log import log

import aqt
from anki.utils import ids2str

RevlogEntry = namedtuple("RevlogEntry", ["reviewType", "ease", "epoch"])


def getRevlogMap(cardIds=None):
    revlogMap = {}

    if cardIds is None:
        query = "select * from revlog order by id"
    else:
        query = "select * from revlog where cid in %s order by id" % ids2str(cardIds)

    rows = aqt.mw.col.db.all(query)
    for row in rows:
        epoch, cid, usn, ease, ivl, lastIvl, factor, duration, reviewType = row
        if cid not in revlogMap:
            revlogMap[cid] = []

        # Convert to days since col.crt
        epoch /= 1000 * 86400  # ms to day
        revlogMap[cid].append(RevlogEntry(reviewType, ease, epoch))

    log("Total %d revlogs from %d cards" % (len(rows), len(revlogMap)))
    return revlogMap
