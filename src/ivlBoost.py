from .utils.configrw import getConfig
from aqt import mw

import math
import time

MAX_INDUCTION_LENGTH = 30
g_targetRetentionRate = 0.85
g_sampleThreshold = 10
g_sampleDays = 60


_inductionIntervalTable = None

def initIntervalTable():
    global _inductionIntervalTable

    if _inductionIntervalTable is not None:
        return

    col = mw.col
    cidRevlogDict = collectRevlogByCardID(col)
    cidRevlogDict = cutoffOldRevlog(col, getConfig('sampleDays', 60), cidRevlogDict)
    firstReviewTable = collectFirstReviewsByInductionLength(col, cidRevlogDict)
    _inductionIntervalTable = calculateInductionIntervalTable(col, firstReviewTable)


def invalidateIntervalTable():
    global _inductionIntervalTable
    _inductionIntervalTable = None


def inductionInterval(cid):
    initIntervalTable()

    col = mw.col
    inductionLength = 1
    for row in col.db.all('select * from revlog where cid = ? order by id DESC', cid):
        rtime, cid, usn, ease, ivl, lastIvl, factor, duration, rtype = row
        if rtype == 0:
            inductionLength += 1
        else:
            break

    return _inductionIntervalTable.get(inductionLength, 1)


# -----------------------------------------------------------------------------


def collectRevlogByCardID(col):
    cidRevlogDict = {}
    epochMidnightAdjust = col.crt % 86400
    for rtime, cid, usn, ease, ivl, lastIvl, factor, duration, rtype in col.db.all('select * from revlog order by id'):
        if cid not in cidRevlogDict:
            cidRevlogDict[cid] = []

        # Quantize epoch to current collection's day start seconds.
        rtime = math.floor((rtime / 1000 - epochMidnightAdjust) / 86400)
        cidRevlogDict[cid].append((rtype, ease, lastIvl, rtime))

    return cidRevlogDict

def cutoffOldRevlog(col, sampleDays, cidRevlogDict):
    # Don't consider too old cards
    epochMidnightAdjust = col.crt % 86400
    daysSinceEpoch = round((time.time() - epochMidnightAdjust) / 86400)
    oldCutoffTime = daysSinceEpoch - sampleDays
    for cid in list(cidRevlogDict.keys()):
        firstLrnTime = cidRevlogDict[cid][0][3]
        if firstLrnTime < oldCutoffTime:
            del cidRevlogDict[cid]

    return cidRevlogDict


def collectFirstReviewsByInductionLength(col, cidRevlogDict):
    ret = [[] for _ in range(MAX_INDUCTION_LENGTH)]

    for cid, cidRevList in cidRevlogDict.items():
        # Cards may be learned multiple times. Find the last learning episode
        #  - ex: by rescheduling card to the end of the new card queue.
        lastLearnEnd = None
        for i in range(len(cidRevList) - 1, -1, -1):
            rtype, ease, lastIvl, rtime = cidRevList[i]
            if rtype == 0:  # new card
                lastLearnEnd = i + 1
                break
        if lastLearnEnd is None:  # haven't finished initial learning
            continue
        if lastLearnEnd == len(cidRevList):  # first review not yet done
            continue

        lastLearnBegin = 0
        for i in range(lastLearnEnd - 1, -1, -1):
            if cidRevList[i][0] != 0:
                lastLearnBegin = i
                break

        inductionLength = lastLearnEnd - lastLearnBegin
        if inductionLength >= MAX_INDUCTION_LENGTH:
            continue

        firstReviewEase = cidRevList[lastLearnEnd][1]
        daysSinceInduction = cidRevList[lastLearnEnd][3] - cidRevList[lastLearnEnd - 1][3]

        # First review on the same day as today. Outlier.
        if daysSinceInduction == 0:
            continue

        ret[inductionLength].append((
            firstReviewEase != 1,
            daysSinceInduction
        ))

    return ret

def calculateInductionIntervalTable(col, firstReviewTable):
    inductionIntervalTable = {}
    targetRetentionRate = getConfig('targetRetentionRate', 0.85)

    newIntervalMultiplier = [0] * MAX_INDUCTION_LENGTH
    totSamplecount = sum(len(frLog) for frLog in firstReviewTable)
    print('Total %d samples' % totSamplecount)
    for inductionLength in range(MAX_INDUCTION_LENGTH):
        frLog = firstReviewTable[inductionLength][:]
        if len(frLog) < g_sampleThreshold:
            continue

        # Ignore top/bottom 5% outliers regarding daysSinceInduction
        frLog.sort(key=lambda x: x[1])
        count5p = math.floor(len(frLog) * 0.05) + 1
        frLog = frLog[count5p: -count5p]

        # avg = sum(1 / expectedRetentionRate if correct else 0 for correct, expectedRetentionRate, daysSinceInduction in frLog) / len(frLog)
        # If current interval is well-calcualted, avg should be 1
        #   : (1 / expectedRetentionRate) added with (realRetentionRate) probability
        #   :           0         added with (1 - realRetentionRate) probability
        # so if average deviates from 1, it means that retention rate is either too much or too less expected.

        # e^k(calculatedInterval) = targetRetentionRate
        # (expected retention rate) = e^k(daysSinceInduction) = targetRetentionRate ^ (daysSinceInduction / calculatedInterval)
        # find `calculatedInterval` so that the average of
        #   : targetRetentionRate ^ -(daysSinceInduction / calculatedInterval)   for correct answers
        #   :           0                                                         for incorrect answers
        # is 1.
        def avg(ivl):
            return sum(
                targetRetentionRate ** (-daysSinceInduction / ivl) if correct else 0
                for correct, daysSinceInduction in frLog
            ) / len(frLog)

        for ivl in range(2, 20):
            if avg(ivl) <= 1.001:  # using exact value of 1.00 seems a bit unstable.
                ivl -= 1
                break

        inductionIntervalTable[inductionLength] = ivl

    return inductionIntervalTable
