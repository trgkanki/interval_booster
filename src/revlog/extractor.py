import os
import math
from collections import namedtuple
from ..utils.log import log

RevlogEntry = namedtuple("RevlogEntry", ["reviewType", "ease", "epoch"])


def readRevlog(col):
    revlogMap = {}
    rows = col.db.all("select * from revlog order by id ASC")

    for row in rows:
        epoch, cid, usn, ease, ivl, lastIvl, factor, duration, reviewType = row
        if cid not in revlogMap:
            revlogMap[cid] = []

        # Convert to days since col.crt
        epoch /= 1000 * 86400  # ms to day
        revlogMap[cid].append(RevlogEntry(reviewType, ease, epoch))

    log("Total %d revlogs from %d cards" % (rows, len(revlogMap)))
    return revlogMap
