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
from aqt.utils import showInfo, askUser
from .utils.log import log
import datetime

from .deckWhitelist import isDeckWhitelisted
from .revlog.extractor import getRevlogMap
from .booster import rescheduleWithInterval, getBoostedInterval


@QDlg("Reschedule cards since...", (300, 300))
def dateSelector(dlg, ret):
    def onDateChange(d):
        nonlocal cal
        ret[0] = d

    with Table():
        with Tr():
            with Td():
                cal = Calendar().onChange(onDateChange)

    with HStack():
        Button("OK").onClick(lambda: dlg.accept()).default()
        Button("Cancel").onClick(lambda: dlg.reject())


def boostSince():
    ret = [None]

    if dateSelector.run(ret) and ret[0]:
        date = ret[0]
        since = datetime.datetime(
            date.year(), date.month(), date.day(), 0, 0
        ).timestamp()
        col = mw.col

        rows = col.db.all("select id, cid from revlog where id >= %d" % (since * 1000))
        cardIds = set(cid for _id, cid in rows)  # Select unique cardIds

        revlogMap = getRevlogMap()
        boostList = []
        for cid in cardIds:
            card = col.getCard(cid)
            if isDeckWhitelisted(col, card.did):
                newIvl = getBoostedInterval(col, card)
                if newIvl:
                    boostList.append((card, newIvl))

        if not boostList:
            showInfo("No card needs rescheduling")
            return

        if not askUser("%d card may need rescheduling. Proceed?" % len(boostList)):
            return

        log("Rescheduling %d reviews: user request" % len(boostList))
        for card, newIvl in boostList:
            rescheduleWithInterval(col, card, newIvl)
