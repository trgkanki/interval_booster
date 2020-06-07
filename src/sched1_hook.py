from anki.sched import Scheduler
from anki.hooks import wrap

from .ivlBoost import inductionInterval

CARD_TYPE_NEW = 0
CARD_TYPE_LRN = 1


def newGraduatingIvl(self, card, conf, early, adj=True, *, _old=None):
    if card.type in (CARD_TYPE_NEW, CARD_TYPE_LRN):
        return inductionInterval(card.id)

    return _old(self, card, conf, early, adj)

Scheduler._graduatingIvl = wrap(Scheduler._graduatingIvl, newGraduatingIvl, 'around')
