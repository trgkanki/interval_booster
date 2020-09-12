from .utils.configrw import getConfig


_deckWhitelistCache = {}


def invalidateDeckWhitelistCache():
    _deckWhitelistCache.clear()


def isDeckWhitelisted(col, did):
    try:
        return _deckWhitelistCache[did]
    except KeyError:
        whitelistDecks = getConfig("whitelistDecks")

        # No whitelist → apply to all decks
        if not whitelistDecks:
            _deckWhitelistCache[did] = True
            return True

        deckName = col.decks.get(did)["name"]
        shouldAccept = False
        for whiteDeck in whitelistDecks:
            if deckName == whiteDeck:
                shouldAccept = True
                break
            elif deckName.startswith(whiteDeck + "::"):
                shouldAccept = True
                break

        _deckWhitelistCache[did] = shouldAccept
        return shouldAccept
