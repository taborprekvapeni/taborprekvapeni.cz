# -*- coding: utf-8 -*-


import times
import logging
import pymongo
from hashlib import sha1
from flask import request
from functools import wraps
from bson.binary import Binary

try:
    import cPickle as pickle
except ImportError:
    import pickle as pickle

from taborprekvapeni import app


mongo = pymongo.MongoClient(host=app.config['CACHE_URL'])


storage = mongo.taborprekvapeni.cache
storage.ensure_index('at', expire_after_seconds=app.config['CACHE_EXPIRATION'])
eternal_storage = mongo.taborprekvapeni.eternal_cache


def cache(key, fn, exp=None):
    """Cache helper. Uses Redis.

    In case data are found in cache under *key*, they are
    immediately returned. If nothing is under *key*, *fn*
    is called to provide the data. Those are then stored
    to cache twice - once with expiration, once eternally.

    The eternal version of data is used in case an error
    occures during *fn* execution. That means, invalid or
    empty data should never be returned if the first cache
    miss ever was successful. No future irregular errors
    affect the eternal data. Exceptions are logged.
    """

    original_key = key
    key = sha1(original_key).hexdigest()

    # cache hit
    result = storage.find_one({'_id': key})
    if result:
        logging.debug('Cache hit (%s).', original_key)
        return pickle.loads(result['val'])

    # cache miss
    try:
        logging.debug('Cache miss (%s).', original_key)
        result = fn()

    except:
        logging.exception('Cache fallback (%s) due:', original_key)

        # fallback to eternal backup
        result = eternal_storage.find_one({'_id': key})
        return pickle.loads(result['val']) if result else None

    # update cache
    if result:
        pickled = Binary(pickle.dumps(result))
        storage.insert({'_id': key, 'val': pickled, 'at': times.now()})
        eternal_storage.insert({'_id': key, 'val': pickled})

    return result


def cached(exp=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not app.debug:
                return cache(request.path, lambda: f(*args, **kwargs),
                             exp=exp or app.config['CACHE_EXPIRATION'])
            else:
                return f(*args, **kwargs)
        return decorated_function
    return decorator
