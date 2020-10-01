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

from anki.sched import Scheduler as SchedulerV1
from anki.schedv2 import Scheduler as SchedulerV2
from anki.hooks import wrap, addHook

from aqt import mw
from aqt.qt import QAction
from aqt.main import AnkiQt

from .utils import uuid  # duplicate UUID checked here
from .utils import openChangelog
from .utils.configrw import getConfig, setConfig, setConfigEditor
from .utils.log import log

from .revlog.initialIvl import invalidateInitialIvlTable
from .revlog.extractor import getRevlogMap
from .booster import rescheduleWithIntervalFactor, getBoostedIntervalFactor

from .deckWhitelist import isDeckWhitelisted
from .boostSince import boostSince, boostSinceGUI

from .configUI import configEditor

import time


setConfigEditor(configEditor)


# ----------------------------------------------------------------------------
# Hooks for reviewer: new cards, reviewed cards


def newLogRev(self, card, ease, delay, type, _old):
    _old(self, card, ease, delay, type)
    newIvlFactor = getBoostedIntervalFactor(card)
    if newIvlFactor:
        rescheduleWithIntervalFactor(self.col, card, newIvlFactor)


SchedulerV1._logRev = wrap(SchedulerV1._logRev, newLogRev, "around")
SchedulerV2._logRev = wrap(SchedulerV2._logRev, newLogRev, "around")


def newLogLrn(self, card, ease, conf, leaving, type, lastLeft, _old):
    _old(self, card, ease, conf, leaving, type, lastLeft)
    newIvlFactor = getBoostedIntervalFactor(card)
    if newIvlFactor:
        rescheduleWithIntervalFactor(self.col, card, newIvlFactor)


SchedulerV1._logLrn = wrap(SchedulerV1._logLrn, newLogLrn, "around")
SchedulerV2._logLrn = wrap(SchedulerV2._logLrn, newLogLrn, "around")


# ----------------------------------------------------------------------------


def onStartupOrSync():
    invalidateInitialIvlTable()
    boostSince(time.time() - 86400 * 7)


# rather than using profileloaded, we hook up `loadProfile` instead.
# This is due `profileLoaded` hook being called before sync.
# Maybe one want to modify card content on other device, but this addon may
# overwrite new interval BEFORE sync, effectively invalidating that modification.


def newLoadProfile(self, onsuccess=None, *, _old):
    def newOnSuccess():
        if not self.col:
            # Profile load failed for some reason
            return

        onStartupOrSync()
        if onsuccess():
            onsuccess()

    _old(self, newOnSuccess)


AnkiQt.loadProfile = wrap(AnkiQt.loadProfile, newLoadProfile, "around")

# ----------------------------------------------------------------------------
# Add menu

action = QAction("Interval boost for reviews since...", mw)
action.triggered.connect(boostSinceGUI)
mw.form.menuTools.addAction(action)
