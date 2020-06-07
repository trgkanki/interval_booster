# -*- coding: utf-8 -*-
#
# addon_template v20.5.4i8
#
# Copyright: trgk (phu54321@naver.com)
# License: GNU AGPL, version 3 or later;
# See http://www.gnu.org/licenses/agpl.html

from .ivlBoost import initIntervalTable
from . import sched1_hook
from anki.hooks import addHook

addHook("profileLoaded", initIntervalTable)
