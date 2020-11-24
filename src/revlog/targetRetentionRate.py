from aqt import mw
from ..utils.configrw import getConfig


_retentionRateDefault = None
_retentionRateOverrides = None


def _initCache():
    global _retentionRateDefault, _retentionRateOverrides
    if _retentionRateDefault is None:
        _retentionRateDefault = getConfig("targetRetentionRate")
        _retentionRateOverrides = getConfig("targetRetentionRateOverrides")


def getTargetRetentionRate(cid: int):
    _initCache()
    col = mw.col
    for d in _retentionRateOverrides[::-1]:
        try:
            q = "cid:%d and (%s)" % (cid, d["query"])
            if cid in col.find_cards(q):
                return d["override"]
        except KeyError:
            pass
    return _retentionRateDefault
