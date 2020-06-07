import json
import numpy as np
import math
import time

MAX_INDUCTION_LENGTH = 30
targetRetentionRate = 0.85


revlog = []
with open('trgk.json', 'r') as f:
    for l in f.readlines():
        revlog.append(list(map(int, l.strip()[1:-1].split(','))))

revlogList = {}
for rl in revlog:
    rtime, cid, usn, ease, ivl, lastIvl, factor, duration, rtype = rl
    if cid not in revlogList:
        revlogList[cid] = []

    # Convert to days since col.crt
    rtime /= 1000
    rtime = (rtime - 72000) / 86400  # TODO: set 72000 to (col.crt % 86400)
    revlogList[cid].append((rtype, ease, lastIvl, rtime))

# Don't consider too old cards
daysSinceEpoch = round((time.time() - 72000) / 86400)
oldCutoffTime = daysSinceEpoch - 30
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
    if abs(timeSinceLastCorrect - calculatedInterval) >= 2 and firstReviewDelay > 1.1 or firstReviewDelay < 0.9:
        continue

    # e^k(calculatedInterval) = targetRetentionRate
    # (expected retention rate) = e^k(timeSinceLastCorrect) = targetRetentionRate ^ (timeSinceLastCorrect / calculatedInterval)
    expectedRetentionRate = targetRetentionRate ** (timeSinceLastCorrect / calculatedInterval)
    firstReviewsAfterLearning[inductionLength].append((
        firstReviewEase != 1,
        expectedRetentionRate,
        timeSinceLastCorrect
    ))

newIntervalMultiplier = [0] * MAX_INDUCTION_LENGTH
for inductionLength in range(MAX_INDUCTION_LENGTH):
    frLog = firstReviewsAfterLearning[inductionLength]
    if not frLog:
        continue

    # If current interval is well-calcualted, avg should be 1
    #   : (1 / expectedRetentionRate) added with (realRetentionRate) probability
    #   :           0         added with (1 - realRetentionRate) probability
    # so if avg deviates from 1, it means that retention rate is either too much or too less expected.
    avg = sum(1 / expectedRetentionRate if correct else 0 for correct, expectedRetentionRate, timeSinceLastCorrect in frLog) / len(frLog)
    tavg = sum(1 if correct else 0 for correct, expectedRetentionRate, timeSinceLastCorrect in frLog) / len(frLog)
    # avg = realRetentionRate / expectedRetentionRate
    # realRetentionRate = expectedRetentionRate * avg
    # if avg is too high, then realRetentionRate is higher than expected.
    #   → need to deviate timeSinceLastCorrect a bit!

    # goal: set newInterval so that targetRetentionRate
    # retention rate at 'timeSinceLastCorrect' = expectedRetentionRate * avg = targetRetentionRate * avg
    # e^(k * newInterval) = targetRetentionRate
    # e^(k * timeSinceLastCorrect) = targetRetentionRate * avg
    # k = ln(targetRetentionRate) / newInterval = ln(targetRetentionRate * avg) / timeSinceLastCorrect
    # newInterval = timeSinceLastCorrect * ln(targetRetentionRate) / ln(targetRetentionRate * avg)
    newInterval = sum(l[2] for l in frLog) / len(frLog) * math.log(targetRetentionRate) / math.log(targetRetentionRate * avg)
    print('Right with %2d induction: avg %.3f tavg %.3f, newInterval %.3f (%d samples)' % (inductionLength, avg, tavg, newInterval, len(frLog)))
    print(targetRetentionRate, targetRetentionRate * avg)


# -- revlog is a review history; it has a row for every review you've ever done!
# CREATE TABLE revlog (
#     id              integer primary key,
#        -- epoch-milliseconds timestamp of when you did the review
#     cid             integer not null,
#        -- cards.id
#     usn             integer not null,
#         -- update sequence number: for finding diffs when syncing.
#         --   See the description in the cards table for more info
#     ease            integer not null,
#        -- which button you pushed to score your recall.
#        -- review:  1(wrong), 2(hard), 3(ok), 4(easy)
#        -- learn/relearn:   1(wrong), 2(ok), 3(easy)
#     ivl             integer not null,
#        -- interval (i.e. as in the card table)
#     lastIvl         integer not null,
#        -- last interval (i.e. the last value of ivl. Note that this value is not necessarily equal to the actual interval between this review and the preceding review)
#     factor          integer not null,
#       -- factor
#     time            integer not null,
#        -- how many milliseconds your review took, up to 60000 (60s)
#     type            integer not null
#        --  0=learn, 1=review, 2=relearn, 3=cram
# );

