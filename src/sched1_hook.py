from anki.sched import Scheduler
from anki.hooks import wrap

from .revlog.initialIvl import initialIvl
from aqt.utils import tooltip

CARD_TYPE_NEW = 0
CARD_TYPE_LRN = 1
CARD_TYPE_REVIEW = 2


def newGraduatingIvl(self, card, conf, early, adj=True, *, _old=None):
    if card.type in (CARD_TYPE_NEW, CARD_TYPE_LRN):
        return initialIvl(card.id)

    return _old(self, card, conf, early, adj)


Scheduler._graduatingIvl = wrap(Scheduler._graduatingIvl, newGraduatingIvl, "around")


def newRevConf(self, card, *, _old=None):
    conf = _old(self, card)
    if card.ivl <= 30:
        conf["ivlFct"] = 2
    else:
        conf["ivlFct"] = 1

    return conf


Scheduler._revConf = wrap(Scheduler._revConf, newRevConf, "around")
