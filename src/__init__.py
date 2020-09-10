# Copyright (C) 2020 Hyun Woo Park
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

# -*- coding: utf-8 -*-
#
# induction_booster v20.5.4i8
#
# Copyright: trgk (phu54321@naver.com)
# License: GNU AGPL, version 3 or later;
# See http://www.gnu.org/licenses/agpl.html

from .utils import openChangelog
from .utils import uuid  # duplicate UUID checked here

from aqt import mw
from aqt.utils import tooltip

from anki.sched import Scheduler as SchedulerV1
from anki.schedv2 import Scheduler as SchedulerV2
from anki.hooks import wrap, addHook

from .revlog.extractor import createRevlogMap
from .revlog.initialIvl import initialIvl


def init():
    createRevlogMap(mw.col)


addHook("profileLoaded", init)


CARD_TYPE_NEW = 0
CARD_TYPE_LRN = 1
CARD_TYPE_REVIEW = 2


# Yeah two duplicate function only because of
def newGraduatingIvl(self, card, conf, early, adjOrFuzz, *, _old=None):
    if card.type in (CARD_TYPE_NEW, CARD_TYPE_LRN):
        return initialIvl(card.id)

    return _old(self, card, conf, early, adjOrFuzz)


def newGraduatingIvl1(self, card, conf, early, adj=True, *, _old=None):
    return newGraduatingIvl(self, card, conf, early, adj, _old=_old)


def newGraduatingIvl2(self, card, conf, early, fuzz=True, *, _old=None):
    return newGraduatingIvl(self, card, conf, early, fuzz, _old=_old)


SchedulerV1._graduatingIvl = wrap(
    SchedulerV1._graduatingIvl, newGraduatingIvl1, "around"
)
SchedulerV2._graduatingIvl = wrap(
    SchedulerV2._graduatingIvl, newGraduatingIvl2, "around"
)


def newRevConf(self, card, *, _old=None):
    conf = _old(self, card)
    if card.ivl <= 30:
        conf["ivlFct"] = 2
    else:
        conf["ivlFct"] = 1

    return conf


# TODO: add scheduler V2 support
SchedulerV1._revConf = wrap(SchedulerV1._revConf, newRevConf, "around")
