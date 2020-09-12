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
from .utils.configrw import getConfig, setConfig

from .utils.log import log

from anki.sched import Scheduler as SchedulerV1
from anki.schedv2 import Scheduler as SchedulerV2
from anki.hooks import wrap, addHook

from .revlog.initialIvl import invalidateInitialIvlTable
from .revlog.booster import boostCard
from .revlog.extractor import getRevlogMap

from .deckWhitelist import isDeckWhitelisted
from aqt import mw
from aqt.qt import QAction

from .consts import CARD_TYPE_NEW, CARD_TYPE_LRN, CARD_TYPE_REV
from .utils.configrw import setConfigEditor
from .configUI import configEditor
from .boostSince import boostSince


def newLogRev(self, card, ease, delay, type, _old):
    _old(self, card, ease, delay, type)
    boostCard(self.col, card)


SchedulerV1._logRev = wrap(SchedulerV1._logRev, newLogRev, "around")
SchedulerV2._logRev = wrap(SchedulerV2._logRev, newLogRev, "around")


def newLogLrn(self, card, ease, conf, leaving, type, lastLeft, _old):
    _old(self, card, ease, conf, leaving, type, lastLeft)
    boostCard(self.col, card)


SchedulerV1._logLrn = wrap(SchedulerV1._logLrn, newLogLrn, "around")
SchedulerV2._logLrn = wrap(SchedulerV2._logLrn, newLogLrn, "around")


## ----------------------------------------------------------------------------


def onProfileLoaded():
    invalidateInitialIvlTable()

    _lastProcessedRevlogId = getConfig("_lastProcessedRevlogId", None)
    if _lastProcessedRevlogId is not None:
        assert type(_lastProcessedRevlogId) in [int, float]

        col = mw.col
        rows = col.db.all(
            "select id, cid from revlog where id > %f" % (_lastProcessedRevlogId)
        )
        if not rows:
            return

        cardIds = set(cid for _id, cid in rows)  # Select unique cardIds
        log("Rescheduling %d new reviews on startup" % len(cardIds))

        revlogMap = getRevlogMap()
        for cid in cardIds:
            card = col.getCard(cid)
            if isDeckWhitelisted(col, card.did):
                boostCard(col, card, revlogMap)

        _lastProcessedRevlogId = max(_id for _id, cid in rows)
        setConfig("_lastProcessedRevlogId", _lastProcessedRevlogId)


addHook("profileLoaded", onProfileLoaded)

setConfigEditor(configEditor)

# Add menu
action = QAction("Interval boost for reviews since...", mw)
action.triggered.connect(boostSince)
mw.form.menuTools.addAction(action)
