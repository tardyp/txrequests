Asynchronous Python HTTP Requests for Humans
============================================

.. image:: https://travis-ci.org/tardyp/txrequests.png?branch=master
        :target: https://travis-ci.org/tardyp/txrequests

Small add-on for the python requests_ http library. Makes use twisted's ThreadPool,
so that the requests'API returns deferred

The additional API and changes are minimal and strives to avoid surprises.

The following synchronous code:

.. code-block:: python

    from requests import Session

    session = Session()
    # first requests starts and blocks until finished
    response_one = session.get('http://httpbin.org/get')
    # second request starts once first is finished
    response_two = session.get('http://httpbin.org/get?foo=bar')
    # both requests are complete
    print('response one status: {0}'.format(response_one.status_code))
    print(response_one.content)
    print('response two status: {0}'.format(response_two.status_code))
    print(response_two.content)

Can be translated to make use of futures, and thus be asynchronous by creating
a FuturesSession and catching the returned Future in place of Response. The
Response can be retrieved by calling the result method on the Future:

.. code-block:: python

    from txrequests import Session
    from twisted.internet import defer

    @defer.inlineCallbacks
    def main():
        # use with statement to cleanup session's threadpool, and connectionpool after use
        # you can also use session.close() if want to use session for long term use
        with Session() as session:
            # first request is started in background
            d1 = session.get('http://httpbin.org/get')
            # second requests is started immediately
            d2 = session.get('http://httpbin.org/get?foo=bar')
            # wait for the first request to complete, if it hasn't already
            response_one = yield d1
            print('response one status: {0}'.format(response_one.status_code))
            print(response_one.content)
            # wait for the second request to complete, if it hasn't already
            response_two = yield d2
            print('response two status: {0}'.format(response_two.status_code))
            print(response_two.content)

By default a ThreadPool is created with 4 max workers. If you would like to
adjust that value or share a threadpool across multiple sessions you can provide
one to the Session constructor.

.. code-block:: python

    from twisted.python.threadpool import ThreadPool
    from txrequests import Session

    session = FuturesSession(pool=ThreadPool(maxthreads=10))
    # ...

As a shortcut in case of just increasing workers number you can pass
`minthreads` and/or `maxthreads` straight to the `Session` constructor:

.. code-block:: python

    from txrequests import Session
    session = Session(maxthreads=10)

That's it. The api of requests.Session is preserved without any modifications
beyond returning a Deferred rather than Response. As with all futures exceptions
are shifted to the deferred errback.

Working in the Background
=========================

There is one additional parameter to the various request functions,
background_callback, which allows you to work with the Response objects in the
background thread. This can be useful for shifting work out of the foreground,
for a simple example take json parsing.

.. code-block:: python

    from pprint import pprint
    from txrequests import Session
    from twisted.internet import defer

    @defer.inlineCallbacks
    def main():
        with Session() as session:

            def bg_cb(sess, resp):
                # parse the json storing the result on the response object
                resp.data = resp.json()
                return resp

            d = session.get('http://httpbin.org/get', background_callback=bg_cb)
            # do some other stuff, send some more requests while this one works
            response = yield d
            print('response status {0}'.format(response.status_code))
            # data will have been attached to the response object in the background
            pprint(response.data)

Python 2 Only
=============

Python 2.6 and 2.7 are currently supported. Python 3 is not.


Installation
============

    pip install txrequests


Credits
========

txrequests is based on requests_future_, from Ross McFarland

.. _`requests`: https://github.com/kennethreitz/requests
.. _`requests_future`: https://github.com/ross/requests-futures
