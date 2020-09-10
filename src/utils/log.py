from .resource import getResourcePath

fp = None


def log(s: str) -> None:
    global fp

    if not fp:
        fp = open(getResourcePath("log.txt"), "a", encoding="utf-8")

    fp.write("%s\n" % s)
    fp.flush()
