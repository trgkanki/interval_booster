import json
import numpy as np
import math
import time

MAX_INDUCTION_LENGTH = 30
targetRetentionRate = 0.85
sampleThreshold = 20
sampleDays = 60


revlog = []
with open('revlog_trgk.txt', 'r') as f:
    for l in f.readlines():
        revlog.append(list(map(int, l.strip()[1:-1].split(','))))

revlogList = {}
for rl in revlog:
    rtime, cid, usn, ease, ivl, lastIvl, factor, duration, rtype = rl
    if cid not in revlogList:
        revlogList[cid] = []

    # Convert to days since col.crt
    rtime /= 1000
    rtime = math.floor((rtime - 72000) / 86400)  # TODO: set 72000 to (col.crt % 86400)
    revlogList[cid].append((rtype, ease, lastIvl, rtime))

# Don't consider too old cards
daysSinceEpoch = round((time.time() - 72000) / 86400)
oldCutoffTime = daysSinceEpoch - sampleDays
for cid in list(revlogList.keys()):
    firstLrnTime = revlogList[cid][0][3]
    if firstLrnTime < oldCutoffTime:
        del revlogList[cid]


firstReviewsAfterLearning = [[] for _ in range(MAX_INDUCTION_LENGTH)]

for cid, cidRevList in revlogList.items():
    lastLearnEnd = None
    for i in range(len(cidRevList) - 1, -1, -1):
        (rtype, ease, lastIvl, rtime) = cidRevList[i]
        if rtype in (0, 3):
            lastLearnEnd = i + 1
            break
    if lastLearnEnd is None:
        continue
    if lastLearnEnd == len(cidRevList):
        continue

    lastLearnBegin = 0
    for i in range(lastLearnEnd - 1, -1, -1):
        if cidRevList[i][0] not in (0, 3):
            lastLearnBegin = i
            break

    inductionLength = lastLearnEnd - lastLearnBegin
    if inductionLength >= MAX_INDUCTION_LENGTH:
        continue

    firstReviewEase = cidRevList[lastLearnEnd][1]
    timeSinceLastCorrect = (cidRevList[lastLearnEnd][3] - cidRevList[lastLearnEnd - 1][3])
    calculatedInterval = cidRevList[lastLearnEnd][2]

    # Ignore too-much advanced review / delayed reviews
    firstReviewDelay = timeSinceLastCorrect / calculatedInterval
    # if abs(timeSinceLastCorrect - calculatedInterval) >= 2 and firstReviewDelay > 1.2 or firstReviewDelay < 0.8:
    #     continue

    firstReviewsAfterLearning[inductionLength].append((
        firstReviewEase != 1,
        timeSinceLastCorrect
    ))

newIntervalMultiplier = [0] * MAX_INDUCTION_LENGTH
totSamplecount = sum(len(frLog) for frLog in firstReviewsAfterLearning)
print('Total %d samples' % totSamplecount)
for inductionLength in range(MAX_INDUCTION_LENGTH):
    frLog = firstReviewsAfterLearning[inductionLength][:]
    if len(frLog) < sampleThreshold:
        continue

    # Ignore top/bottom 5% outliers
    frLog.sort(key=lambda x: x[1])
    count5p = math.floor(len(frLog) * 0.05) + 1
    frLog = frLog[count5p: -count5p]

    # avg = sum(1 / expectedRetentionRate if correct else 0 for correct, expectedRetentionRate, timeSinceLastCorrect in frLog) / len(frLog)
    # If current interval is well-calcualted, avg should be 1
    #   : (1 / expectedRetentionRate) added with (realRetentionRate) probability
    #   :           0         added with (1 - realRetentionRate) probability
    # so if avg deviates from 1, it means that retention rate is either too much or too less expected.
    # e^k(calculatedInterval) = targetRetentionRate
    # (expected retention rate) = e^k(timeSinceLastCorrect) = targetRetentionRate ^ (timeSinceLastCorrect / calculatedInterval)
    expectedRetentionRate = targetRetentionRate ** (timeSinceLastCorrect / calculatedInterval)

    # find calculatedInterval so that average of
    #   : targetRetentionRate ^ -(timeSinceLastCorrect / calculatedInterval)   for correct answers
    #   :           0                                                          for incorrect answers
    # should be 1.

    def avg(ivl):
        return sum(
            targetRetentionRate ** (-timeSinceLastCorrect / ivl) if correct else 0
            for correct, timeSinceLastCorrect in frLog
        ) / len(frLog)

    for ivl in range(2, 20):
        if avg(ivl) <= 1.001:  # using exact value of 1.00 seems a bit unstable.
            ivl -= 1
            break

    print(' - appropriate ivl for induction length %d: %d (%d samples)' % (inductionLength, ivl, len(frLog)))
