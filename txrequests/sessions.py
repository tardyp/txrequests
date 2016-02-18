# -*- coding: utf-8 -*-
"""
txrequests
~~~~~~~~~~~~~~~~

This module provides a small add-on for the requests http library. It makes use
of twisted threadpool.

    from txrequests import Session

    session = Session()
    # request is run in the background
    d = session.get('http://httpbin.org/get')
    # ... do other stuff ...
    # wait for the request to complete, if it hasn't already
    @d.addCallback
    def print_res(response):
        print('response status: {0}'.format(response.status_code))
        print(response.content)

"""

from twisted.internet import defer, reactor
from requests import Session as requestsSession
from twisted.python.threadpool import ThreadPool


class Session(requestsSession):

    def __init__(self, pool=None,  minthreads=1, maxthreads=4, **kwargs):
        """Creates a twisted aware Session

        Notes
        ~~~~~

        * If you provide both `pool` and `max_workers`, the latter is
          ignored and provided threadpool is used as is.
        """
        requestsSession.__init__(self, **kwargs)
        self.ownPool = False
        if pool is None:
            self.ownPool = True
            pool = ThreadPool(minthreads=minthreads, maxthreads=maxthreads)
            # unclosed ThreadPool leads to reactor hangs at shutdown
            # this is a problem in many situation, so better enforce pool stop here
            reactor.addSystemEventTrigger("after", "shutdown", lambda:pool.stop())
        self.pool = pool
        if self.ownPool:
            pool.start()

    def close(self):
        requestsSession.close(self)
        if self.ownPool:
            self.pool.stop()

    def request(self, *args, **kwargs):
        """Maintains the existing api for Session.request.

        Used by all of the higher level methods, e.g. Session.get.

        The background_callback param allows you to do some processing on the
        response in the background, e.g. call resp.json() so that json parsing
        happens in the background thread.
        """
        def func():
            try:
                background_callback = kwargs.pop('background_callback', None)
                res = requestsSession.request(self, *args, **kwargs)
                if background_callback is not None:
                    res = background_callback(self, res)
                reactor.callFromThread(d.callback, res)
            except Exception as e:
                reactor.callFromThread(d.errback, e)

        d = defer.Deferred()
        self.pool.callInThread(func)
        return d
