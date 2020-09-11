from .extractor import getRevlogMap
from .initialIvl import initialIvl
from ..utils.log import log
from ..consts import (
    REVLOG_TYPE_NEW,
    REVLOG_TYPE_REVIEW,
    REVLOG_TYPE_CRAM,
    CARD_TYPE_REV,
)

from anki.utils import intTime

import time
import random
import math


def rescheduleCard(col, card, newIvl):
    log(" - Rescheduling cid=%d: ivl %d->%d" % (card.id, card.ivl, newIvl))
    if card.ivl == newIvl:
        log("  [ skipping: identical ivl ]")
    card.due = card.due - card.ivl + newIvl
    card.ivl = newIvl
    card.mod = intTime()
    card.usn = col.usn()
    card.flush()


def boostCard(col, card):
    # Ignore cards during custom study
    if card.odid:
        return

    if card.type != CARD_TYPE_REV:
        return

    cid = card.id
    revlogList = getRevlogMap([cid])[cid]
    lastReviewLog = revlogList[-1]

    # Ignore cards that have just finished custom studies
    if lastReviewLog.reviewType == REVLOG_TYPE_CRAM:
        return

    # Interval already modified
    if lastReviewLog.ivl != card.ivl:
        return

    # Graduating from initial
    if (
        lastReviewLog.reviewType == REVLOG_TYPE_NEW
        and card.ivl > 0
        and card.type == CARD_TYPE_REV  # not has gone back to new cards
    ):
        initialInterval = initialIvl(revlogList)
        if card.ivl < initialInterval:
            log(
                "initial boost: cid=%d, initialInterval=%d" % (card.id, initialInterval)
            )
            rescheduleCard(col, card, initialInterval)
        return

    # Young card interval booster
    # Pressed 'good'
    if lastReviewLog.reviewType == REVLOG_TYPE_REVIEW and lastReviewLog.ease == 3:
        origInterval = lastReviewLog.ivl
        if lastReviewLog.ivl < 10:
            targetInterval = origInterval * 2
        else:
            targetInterval = 10 * 2 + (origInterval - 10)
        realInterval = card.ivl
        if not (targetInterval - 1 <= realInterval <= targetInterval + 1) and not (
            targetInterval * 0.9 <= realInterval <= targetInterval * 1.1
        ):
            newInterval = random.randint(
                math.ceil(targetInterval * 0.9), math.floor(targetInterval * 1.1)
            )
            rescheduleCard(col, card, newInterval)
        return
