# Copyright (C) 2020 Hyun Woo Park
#
# This piece of code were from https://github.com/brownbat/autoEaseFactor/
#  - eshapard
#  - ja-dark
#  - cordone
#  - risingorange
#  - the MIA crew
#  - the AnKing
#
# Some adjustment were done by me (Hyun Woo Park). The code was originallylicensed as GPL3, so I'm redistributing it as AGPL3.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import math
from typing import Union, List
from collections import namedtuple

from ..consts import REVLOG_TYPE_REVIEW
from ..utils.configrw import getConfig
from ..utils.debugLog import log
from .extractor import RevlogEntry
from .targetRetentionRate import getTargetRetentionRate


def movingAverage(values, movingAverageWeight, init=None):
    """Provide (float) weighted moving average for list of values."""
    assert len(values) > 0
    if init is None:
        movingAvg = sum(values) / len(values)
    else:
        movingAvg = init
    for this_item in values:
        movingAvg = movingAvg * (1 - movingAverageWeight)
        movingAvg += this_item * movingAverageWeight
    return movingAvg


def recalculateCardEase(cid: int, cardRevlogList: List[RevlogEntry]):
    """Return next ease factor based on config and card performance."""

    # Read config
    config = getConfig("autoEaseConfig")

    leash = config.get("leash", 100)
    targetRetentionRate = getTargetRetentionRate(cid)
    maxEase = config.get("maxEase", 5000)
    minEase = config.get("minEase", 1000)
    movingAverageWeight = config.get("movingAverageWeight")

    # Parse cardRevlogList to match autoEase code.
    lastRevlog = cardRevlogList[-1]
    currentFactor = lastRevlog.factor

    # log("analyzing card %d" % cid)
    cardRevlogList = cardRevlogList[:-1]
    cardRevlogList = [
        log for log in cardRevlogList if log.reviewType == REVLOG_TYPE_REVIEW
    ]
    factorList = [revlog.factor for revlog in cardRevlogList]
    reviewCorrectList = [revlog.ease > 1 for revlog in cardRevlogList]
    # log(" - cardRevlogList: %s" % cardRevlogList)
    # log(" - factorList: %s" % factorList)
    # log(" - reviewCorrectList: %s" % reviewCorrectList)

    # if no reviews, just assume we're on targetRetentionRate
    if reviewCorrectList is None or len(reviewCorrectList) < 1:
        successRate = targetRetentionRate
    else:
        successList = [1 if correct else 0 for correct in reviewCorrectList]
        successRate = movingAverage(
            successList, movingAverageWeight, init=targetRetentionRate
        )

    # log(" - successRate: %s" % successRate)

    # Ebbinghaus formula
    if successRate > 0.99:
        successRate = 0.99  # ln(1) = 0; avoid divide by zero error
    if successRate < 0.01:
        successRate = 0.01
    deltaRatio = math.log(targetRetentionRate) / math.log(successRate)
    if factorList and len(factorList) > 0:
        averageFactor = movingAverage(factorList, movingAverageWeight)
    else:
        # averageFactor should be average ease *excluding* the last factor,
        # but if we don't have any except the last one, we just assume
        # averageFactor to be same as currentFactor.
        #
        # in this case, the last review is a review graduating new card, so
        # its factor should equal to deck's configured card's initial
        # factor. Set averageFactor to that.
        averageFactor = currentFactor
    suggestedFactor = int(round(averageFactor * deltaRatio))
    # log(" - suggestedFactor: %s" % suggestedFactor)

    # anchor this to currentFactor initially
    reviewCount = len(reviewCorrectList)
    maxAllowedFactor = min(maxEase, (currentFactor + (leash * reviewCount)))
    if suggestedFactor > maxAllowedFactor:
        suggestedFactor = maxAllowedFactor
    minAllowedFactor = max(minEase, (currentFactor - (leash * reviewCount)))
    if suggestedFactor < minAllowedFactor:
        suggestedFactor = minAllowedFactor

    # log(" - adjusted suggestedFactor: %s" % suggestedFactor)

    return suggestedFactor
