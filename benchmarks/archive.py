"""Exclusive output creation shared by run JSON and paired figures."""

from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from pathlib import Path
from typing import BinaryIO


@contextmanager
def create_outputs(paths: list[Path]) -> Iterator[list[BinaryIO]]:
    """Reserve every output without clobbering; remove owned files on failure.

    Exclusive creation closes the check-then-write race. Failed paired rendering
    removes only files created by this call, never a pre-existing light/dark figure.
    Process termination may leave incomplete files; readers must validate evidence.
    """
    created: list[Path] = []
    try:
        with ExitStack() as stack:
            streams: list[BinaryIO] = []
            for path in paths:
                path.parent.mkdir(parents=True, exist_ok=True)
                stream = stack.enter_context(path.open("xb"))
                created.append(path)
                streams.append(stream)
            yield streams
    except BaseException:
        for path in created:
            path.unlink()
        raise
