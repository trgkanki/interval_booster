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

from .utils.configrw import (
    getConfig,
    setConfig,
    getConfigAll,
    setConfigAll,
)

from .deckWhitelist import invalidateDeckWhitelistCache
from .qdlg import (
    QDlg,
    Text,
    Button,
    ListBox,
    LineEdit,
    Calendar,
    HStack,
    Table,
    Tr,
    Td,
    observable,
    unobserved,
)

from PyQt5.Qt import QDate
from aqt import mw
from aqt.utils import tooltip
from .utils.debugLog import log
import datetime

from .deckWhitelist import isDeckWhitelisted
from .revlog.extractor import getRevlogMap
from .booster import rescheduleWithIntervalFactor, getBoostedIntervalFactor

import anki


@QDlg("Reschedule cards since...", (300, 300))
def dateSelector(dlg, ret):
    def onDateChange(d):
        nonlocal cal
        ret[0] = d

    with Table():
        with Tr():
            with Td():
                Text(
                    "Note: this will reschedule all cards reviewed since selected date with your settings, even those that were already rescheduled."
                ).wordWrap(True)
        with Tr():
            with Td():
                cal = Calendar().onChange(onDateChange)

    with HStack():
        Button("OK").onClick(lambda: dlg.accept()).default()
        Button("Cancel").onClick(lambda: dlg.reject())


def boostSinceGUI():
    ret = [None]

    if dateSelector.run(ret) and ret[0]:
        date = ret[0]
        since = datetime.datetime(
            date.year(), date.month(), date.day(), 0, 0
        ).timestamp()
        boostSince(since, True)


def boostSince(sinceEpoch, force=False):
    col = mw.col
    rows = col.db.all("select id, cid from revlog where id >= %d" % (sinceEpoch * 1000))
    cardIds = set(cid for _id, cid in rows)  # Select unique cardIds

    revlogMap = getRevlogMap()
    boostList = []

    progress = mw.progress
    progress.start(
        immediate=True, min=0, max=len(cardIds), label="Interval boosting..."
    )
    try:
        for i, cid in enumerate(cardIds):

            try:
                progress.update(value=i, max=len(cardIds))
            except TypeError:
                # Anki ~2.1.27 doesn't have keyword argument 'max' for progress bar.
                progress.update(value=i)

            if i % 50 == 0:
                # Make app responsive at least.
                mw.app.processEvents()

            try:
                card = col.getCard(cid)
            except:
                # Card might have been deleted after reviews
                continue
            if isDeckWhitelisted(col, card.did):
                newIvlFactor = getBoostedIntervalFactor(card, revlogMap[cid], force)
                if newIvlFactor:
                    boostList.append((card, newIvlFactor))

        if not boostList:
            return

        log("Rescheduling %d reviews: user request" % len(boostList))
        for card, newIvlFactor in boostList:
            rescheduleWithIntervalFactor(col, card, newIvlFactor)

        tooltip("[Interval booster] Rescheduled %d cards" % len(boostList))

    finally:
        progress.finish()
        # Possible remaining card count update
        mw.reset()
