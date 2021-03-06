from .revlog.extractor import getRevlogMap
from .revlog.initialIvl import initialIvl
from .revlog.autoease import recalculateCardEase

from .utils.debugLog import log
from .utils.configrw import getConfig

from .consts import (
    REVLOG_TYPE_NEW,
    REVLOG_TYPE_REVIEW,
    REVLOG_TYPE_CRAM,
    CARD_TYPE_REV,
)

from anki.utils import intTime

import time
import random
import math


def rescheduleWithIntervalFactor(col, card, newIvlFactor):
    newIvl, newFactor = newIvlFactor
    if not newIvl and not newFactor:
        return

    log(
        " - Rescheduling cid=%d: ivl %s->%s, factor %s->%s"
        % (card.id, card.ivl, newIvl, card.factor, newFactor)
    )

    if newIvl:
        card.due = card.due - card.ivl + newIvl
        card.ivl = newIvl
    if newFactor:
        card.factor = newFactor
    card.mod = intTime()
    card.usn = col.usn()
    card.flush()


def getBoostedIntervalFactor(card, revlogList=None, force=False):
    # Ignore cards during custom study
    if card.odid:
        return

    if card.type != CARD_TYPE_REV:
        return

    cid = card.id
    revlogList = revlogList or getRevlogMap([cid])[cid]
    lastReviewLog = revlogList[-1]

    # Ignore cards that have just finished custom studies
    if lastReviewLog.reviewType == REVLOG_TYPE_CRAM:
        return

    # Still in learning/relearning phase → pass
    if lastReviewLog.ivl < 0:
        return

    # Interval or easeFactor already modified
    # Maybe, already have been boosted!
    if not force and (
        lastReviewLog.ivl != card.ivl or lastReviewLog.factor != card.factor
    ):
        return

    # Graduating from initial induction
    if (
        lastReviewLog.reviewType == REVLOG_TYPE_NEW
        and lastReviewLog.ivl > 0
        and card.type == CARD_TYPE_REV  # not has gone back to new cards
    ):
        initialInterval = initialIvl(revlogList)
        if lastReviewLog.ivl < initialInterval:
            log(
                "initial boost: cid=%d, initialInterval=%d" % (card.id, initialInterval)
            )
            return initialInterval, lastReviewLog.factor
        return

    # Boost after review
    if lastReviewLog.reviewType == REVLOG_TYPE_REVIEW:
        newFactor = recalculateCardEase(cid, revlogList)

        # Boost factor for young cards
        # this formula is empirical. There might be a better one.

        # Always make newFactor different from lastReviewLog.factor
        # This is adding 0.1% to factor. 0.1% won't make much difference.
        if newFactor == lastReviewLog.factor:
            newFactor += 1

        # Recalculate interval according to new factor
        if lastReviewLog.ease == 1:
            # Don't recalculate interval for easy cards
            newIvl = None

        elif lastReviewLog.ease == 2:
            # Hard cards have their next interval adjusted independent of card's ease factor
            # so don't modify interval here
            newIvl = None

        else:
            lastIvl = lastReviewLog.lastIvl
            ivl = lastReviewLog.ivl
            newIvl = max(lastIvl + 1, int(ivl / lastReviewLog.factor * newFactor + 0.5))

        return newIvl, newFactor
