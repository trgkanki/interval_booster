from .utils.configrw import getConfig


_deckWhitelistCache = {}


def invalidateDeckWhitelistCache():
    _deckWhitelistCache.clear()


def isDeckWhitelisted(col, did):
    try:
        return _deckWhitelistCache[did]
    except KeyError:
        _whitelistDecks = getConfig("whitelistDecks")

        # No whitelist → apply to all decks
        if not _whitelistDecks:
            _deckWhitelistCache[did] = True
            return True

        deckName = col.decks.get(did)["name"]
        shouldAccept = False
        for whitelistDecks in whitelistDecks:
            if deckName == whitelistDecks:
                shouldAccept = True
                break
            elif deckName.startswith(whitelistDecks + "::"):
                shouldAccept = True
                break

        _deckWhitelistCache[did] = shouldAccept
        return shouldAccept
