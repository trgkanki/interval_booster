from aqt import mw

from ..utils.configrw import getConfig
from ..utils.debugLog import log
from .extractor import getRevlogMap

from ..consts import REVLOG_TYPE_NEW

import math
import time
import collections


MAX_INDUCTION_LENGTH = 30
g_sampleThreshold = 10

_initialIvlTable = None


# ------------------------


def _initInitialIvlTable():
    global _initialIvlTable

    if _initialIvlTable is not None:
        return

    col = mw.col
    revlogMap = getRevlogMap()
    revlogMap = cutoffOldRevlog(col, getConfig("sampleDays", 60), revlogMap)
    firstReviewTable = collectFirstReviewsByInductionLength(col, revlogMap)
    _initialIvlTable = calculateInductionIntervalTable(col, firstReviewTable)
    log("Initial interval table: %s" % _initialIvlTable)


def invalidateInitialIvlTable():
    global _initialIvlTable
    _initialIvlTable = None


def initialIvl(revlogList):
    _initInitialIvlTable()

    inductionLength = 0
    for log in revlogList[::-1]:
        if log.reviewType == REVLOG_TYPE_NEW:
            inductionLength += 1
        else:
            break

    return _initialIvlTable.get(inductionLength, 1)


# -----------------------------------------------------------------------------


def cutoffOldRevlog(col, sampleDays, revlogMap):
    # Don't consider too old cards
    oldCutoffTime = col.sched.today - sampleDays

    for cid in list(revlogMap.keys()):  # keys() may change by del cidRevlogList[cid]
        firstLrnTime = revlogMap[cid][0].epoch
        if firstLrnTime < oldCutoffTime:
            del revlogMap[cid]

    return revlogMap


FirstReviewData = collections.namedtuple("FirstReviewData", ["correct", "firstIvl"])


def collectFirstReviewsByInductionLength(col, revlogMap):
    ret = [[] for _ in range(MAX_INDUCTION_LENGTH)]

    for cid, cidRevList in revlogMap.items():
        # Cards may be learned multiple times. Find the last learning episode
        #  - ex: by rescheduling card to the end of the new card queue.
        lastLearnEnd = None
        for i in range(len(cidRevList) - 1, -1, -1):
            if cidRevList[i].reviewType == REVLOG_TYPE_NEW:  # new card
                lastLearnEnd = i + 1
                break
        if lastLearnEnd is None:
            # haven't learned the card. Maybe user decided to reschedule
            # the card to be 'learnt' without any learning.
            continue

        if lastLearnEnd == len(cidRevList):
            # no reviews yet after induction
            continue

        lastLearnBegin = 0
        for i in range(lastLearnEnd - 1, -1, -1):
            if cidRevList[i].reviewType != REVLOG_TYPE_NEW:
                lastLearnBegin = i
                break

        inductionLength = lastLearnEnd - lastLearnBegin
        if inductionLength >= MAX_INDUCTION_LENGTH:
            continue

        firstReviewEase = cidRevList[lastLearnEnd].ease
        firstIvl = cidRevList[lastLearnEnd].epoch - cidRevList[lastLearnEnd - 1].epoch

        # First review on the same day as today. Outlier.
        if firstIvl == 0:
            continue

        ret[inductionLength].append(FirstReviewData(firstReviewEase != 1, firstIvl))

    return ret


def calculateInductionIntervalTable(col, firstReviewTable):
    initialIvlTable = {}
    targetRetentionRate = getConfig("targetRetentionRate", 0.85)

    newIntervalMultiplier = [0] * MAX_INDUCTION_LENGTH
    totSamplecount = sum(len(frLog) for frLog in firstReviewTable)
    print("Total %d samples" % totSamplecount)
    for inductionLength in range(MAX_INDUCTION_LENGTH):
        frLog = firstReviewTable[inductionLength][:]
        frLog = [x for x in frLog if x.firstIvl != 0]
        if len(frLog) < g_sampleThreshold:
            continue

        # Ignore top/bottom 5% outliers regarding firstIvl
        frLog.sort(key=lambda x: x.firstIvl)
        count5p = math.floor(len(frLog) * 0.05) + 1
        frLog = frLog[count5p:-count5p]

        # avg = sum(1 / expectedRetentionRate if correct else 0 for correct, expectedRetentionRate, firstIvl in frLog) / len(frLog)
        # If current interval is well-calculated, avg should be 1
        #   : (1 / expectedRetentionRate) added with (realRetentionRate) probability
        #   :           0         added with (1 - realRetentionRate) probability
        # so if average deviates from 1, it means that retention rate is either too much or too less expected.

        # e^k(calculatedInterval) = targetRetentionRate
        # (expected retention rate) = e^k(firstIvl) = targetRetentionRate ^ (firstIvl / calculatedInterval)
        # find `calculatedInterval` so that the average of
        #   : targetRetentionRate ^ -(firstIvl / calculatedInterval)   for correct answers
        #   :           0                                                         for incorrect answers
        # is 1.
        def avg(ivl):
            return sum(
                targetRetentionRate ** (-firstIvl / ivl) if correct else 0
                for correct, firstIvl in frLog
            ) / len(frLog)

        for ivl in range(2, 20):
            if avg(ivl) <= 1.001:  # using exact value of 1.00 seems a bit unstable.
                ivl -= 1
                break

        initialIvlTable[inductionLength] = ivl

    return initialIvlTable
