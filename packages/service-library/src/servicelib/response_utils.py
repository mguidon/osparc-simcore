"""

FIXME: these are prototype! do not use in production
"""

from typing import Dict, Tuple

import attr
from aiohttp import web
from functools import partial

from .rest_models import LogMessageType

try:
    import ujson as json
except ImportError:
    import json

ENVELOPE_KEYS = ('data', 'error')



def unwrap_envelope(payload: Dict) -> Tuple:
    return tuple(payload.get(k) for k in ENVELOPE_KEYS) if payload else (None, None)

#def wrap_envelope(*, data=None, error=None) -> Dict:
#    raise NotImplementedError("")
#    # TODO should convert data, error to dicts!


# uses ujson if available
json_response = partial(web.json_response, dumps=json.dumps)


def log_response(msg: str, level: str) -> web.Response:
    """ Produces an enveloped response with a log message

    Analogous to  aiohttp's web.json_response
    """
    # TODO: link more with real logger
    msg = LogMessageType(msg, level)
    response = json_response(data={
        'data': attr.asdict(msg),
        'error': None
    })
    return response


__all__ = (
    'unwrap_envelope',
    'log_response'
)
