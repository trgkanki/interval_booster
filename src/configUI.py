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
    HStack,
    Table,
    Tr,
    Td,
    observable,
    unobserved,
)

from PyQt5.Qt import QAbstractItemView
from aqt import mw


@QDlg("Configure induction_booster", (400, 600))
def addonConfigWindow(dlg, allDecks, config):
    with Table():
        with Tr():
            with Td():
                Text("Target retention rate")
            with Td():
                LineEdit().model(config, index="targetRetentionRate")

        with Tr():
            with Td():
                Text("SampleDays")
            with Td():
                LineEdit().model(config, index="sampleDays")

        with Tr():
            with Td(colspan=2):
                Text("<b>Deck whitelist</b>")

        with Tr():
            with Td(colspan=2):
                Text(
                    "<i>Note: with no deck whitelist set, all deck will be whitelisted</i>"
                )

        with Tr():
            with Td(colspan=2):
                (
                    ListBox(allDecks, renderer=lambda d: d["name"])
                    .multiselect(QAbstractItemView.MultiSelection)
                    .model(config, index="whitelistDecks")
                    .sorted()
                )

    with HStack():
        Button("OK").onClick(lambda: dlg.accept()).default()
        Button("Cancel").onClick(lambda: dlg.reject())


def configEditor():
    addonConfig = observable(getConfigAll())
    addonConfig["targetRetentionRate"] = str(addonConfig["targetRetentionRate"])
    addonConfig["sampleDays"] = str(addonConfig["sampleDays"])

    allDecks = [{"id": v["id"], "name": v["name"]} for v in mw.col.decks.all()]
    allDecksNameDict = {v["name"]: v for v in allDecks}
    addonConfig["whitelistDecks"] = [
        allDecksNameDict[i] for i in addonConfig["whitelistDecks"]
    ]

    if addonConfigWindow.run(allDecks, addonConfig):
        addonConfig = unobserved(addonConfig)
        addonConfig["targetRetentionRate"] = float(addonConfig["targetRetentionRate"])
        addonConfig["sampleDays"] = int(addonConfig["sampleDays"])
        addonConfig["whitelistDecks"] = [
            v["name"] for v in addonConfig["whitelistDecks"]
        ]
        setConfigAll(addonConfig)
        invalidateDeckWhitelistCache()
