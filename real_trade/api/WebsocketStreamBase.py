#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
import websocket
import threading
import time
import json
import ssl

class WebsocketStreamBase(object):
    def __init__(self, url, run_immediately = True):
        self.ws = None
        self.url = url
        self.running_thread = None
        self.is_started = False
        self.reconnect_and_resubscribe_when_closed = True
        if run_immediately:
            self.run_on_another_thread()

    def set_url(self, url):
        self.url = url

    def run_on_another_thread(self):
        websocket.enableTrace(True)
        url = self.url

        ws = websocket.WebSocketApp(url,
                                    on_open = lambda ws: self.on_open(ws),
                                    on_message = lambda ws,msg: self.on_message(ws,msg),
                                    on_error = lambda ws,err: self.on_error(ws,err),
                                    on_close = lambda ws: self.on_close(ws))
                                    #0bsslopsslopt={"cert_reqs": ssl.CERT_NONE})

        self.is_started = False
        self.ws = ws
        th = threading.Thread(target=self._run_thread)
        th.start()
        self.running_thread = th

    def stop(self):
        if self.ws is None: return

        self.is_started = False
        self.ws.keep_running = False
        self.ws = None
        self.running_thread = None

    def set_reconnect_and_resubscribe_when_closed(self, flag_reconnect):
        self.reconnect_and_resubscribe_when_closed = flag_reconnect

    def _run_thread(self):
        try:
            print("start run")
            self.ws.run_forever(sslopt={"cert_reqs": ssl.CERT_NONE})
        except Exception as e:
            print(str(e))
            print(e.args)
            print(e.message)

    def request(self, request_message_dict):
        assert (self.ws is not None)
            
        request_message = json.dumps(request_message_dict)
        self.ws.send(request_message)

    def on_open(self, ws):
        print("on open")
        self.is_started = True
        self._start_subscribe_after_connect()

    def on_message(self, ws, msg):
        print("msg:"+str(msg))

    def on_error(self, ws, error):
        print("error"+str(error))

    def on_close(self, ws):
        print("on close...")
        if self.reconnect_and_resubscribe_when_closed:
            print("reconnect!")
            self.run_on_another_thread()
            #while self.is_started is False:
            #    time.sleep(0.1)
            #self._start_subscribe_after_connect()

