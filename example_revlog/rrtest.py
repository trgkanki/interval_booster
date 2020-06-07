import json
import numpy as np

revlog = []
with open('trgk.json', 'r') as f:
    for l in f.readlines():
        revlog.append(list(map(int, l.strip()[1:-1].split(','))))

revlog.sort()

revlogList = {}
for rl in revlog:
    rtime, cid, usn, ease, ivl, lastIvl, factor, duration, rtype = rl
    if cid not in revlogList:
        revlogList[cid] = []
    revlogList[cid].append((rtype, ease, lastIvl, rtime))

MAX_INDUCTION_LENGTH = 30
firstReviewRight = [0] * MAX_INDUCTION_LENGTH
firstReviewWrong = [0] * MAX_INDUCTION_LENGTH
t = 0
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

    learnCount = lastLearnEnd - lastLearnBegin
    if learnCount >= MAX_INDUCTION_LENGTH:
        continue

    firstReviewEase = cidRevList[lastLearnEnd][1]
    firstReviewDelay = (
        (cidRevList[lastLearnEnd][3] - cidRevList[lastLearnEnd - 1][3]) / 1000 / 86400
        / cidRevList[lastLearnEnd][2]
    )
    if firstReviewDelay > 1.1 or firstReviewDelay < 0.9:
        continue  # too off-interval

    if firstReviewEase == 1:
        firstReviewWrong[learnCount] += 1
    else:
        firstReviewRight[learnCount] += 1

for inductionLength in range(20):
    totRev =  (firstReviewRight[inductionLength] + firstReviewWrong[inductionLength])
    if totRev == 0:
        continue
    rightRev = firstReviewRight[inductionLength]
    print('Right with %2d induction: %.3f (%d samples)' % (inductionLength, rightRev / totRev, totRev))


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

