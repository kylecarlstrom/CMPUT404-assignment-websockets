#!/usr/bin/env python
# coding: utf-8
# Copyright (c) 2013-2014 Abram Hindle, Kyle Carlstrom, Tian Zhi Wang
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import flask
from flask import Flask, request, redirect
from flask_sockets import Sockets
import gevent
from gevent import queue
import time
import json
import os

app = Flask(__name__)
sockets = Sockets(app)
app.debug = True

# https://github.com/abramhindle/WebSocketsExamples/blob/master/chat.py Abram Hindle (https://github.com/abramhindle) (Apache 2.0)
class Client:
    def __init__(self):
        self.queue = queue.Queue()

    def put(self, entity, data):
        value = {}
        value[entity] = data
        self.queue.put_nowait(json.dumps(value))

    def get(self):
        return self.queue.get()
# End Citation https://github.com/abramhindle/WebSocketsExamples/blob/master/chat.py Abram Hindle (https://github.com/abramhindle) (Apache 2.0)

class World:
    def __init__(self):
        self.clear()
        # we've got listeners now!
        self.listeners = list()
        
    def add_set_listener(self, listener):
        self.listeners.append( listener )

    def update(self, entity, key, value):
        entry = self.space.get(entity,dict())
        entry[key] = value
        self.space[entity] = entry
        self.update_listeners( entity )

    def set(self, entity, data):
        self.space[entity] = data
        self.update_listeners( entity )

    def update_listeners(self, entity):
        '''update the set listeners'''
        for listener in self.listeners:
            listener(entity, self.get(entity))

    def clear(self):
        self.space = dict()

    def get(self, entity):
        return self.space.get(entity,dict())
    
    def world(self):
        return self.space

myWorld = World()
        
@app.route('/')
def hello():
    '''Return something coherent here.. perhaps redirect to /static/index.html '''
    # https://github.com/abramhindle/WebSocketsExamples/blob/master/chat.py Abram Hindle (https://github.com/abramhindle) (Apache 2.0)
    return redirect("/static/index.html")

def read_ws(ws,client):
    '''A greenlet function that reads from the websocket and updates the world'''
    # Start Citation: https://github.com/abramhindle/WebSocketsExamples/blob/master/chat.py Abram Hindle (https://github.com/abramhindle) (Apache 2.0)
    try:
        while True:
            msg = ws.receive()
            if (msg is not None):
                packet = json.loads(msg)
                for entity, data in packet.items():
                    myWorld.set(entity, data)
            else:
                break
    except Exception as e:
        '''Done'''
        print(e)
    # End Citation https://github.com/abramhindle/WebSocketsExamples/blob/master/chat.py Abram Hindle (https://github.com/abramhindle) (Apache 2.0)

@sockets.route('/subscribe')
def subscribe_socket(ws):
    '''Fufill the websocket URL of /subscribe, every update notify the
       websocket and read updates from the websocket '''
    # Start Citation: https://github.com/abramhindle/WebSocketsExamples/blob/master/chat.py Abram Hindle (https://github.com/abramhindle) (Apache 2.0)
    client = Client()
    myWorld.add_set_listener(client.put)
    g = gevent.spawn( read_ws, ws, client )    
    try:
        stateOfWorld = json.dumps(myWorld.world())
        ws.send(stateOfWorld)
        while True:
            # block here
            msg = client.get()
            ws.send(msg)
    except Exception as e:# WebSocketError as e:
        print "WS Error %s" % e
    finally:
        gevent.kill(g)
    # End Citation https://github.com/abramhindle/WebSocketsExamples/blob/master/chat.py Abram Hindle (https://github.com/abramhindle) (Apache 2.0)


def flask_post_json():
    '''Ah the joys of frameworks! They do so much work for you
       that they get in the way of sane operation!'''
    if (request.json != None):
        return request.json
    elif (request.data != None and request.data != ''):
        return json.loads(request.data)
    else:
        return json.loads(request.form.keys()[0])

# Start citation: From assignment 4, https://github.com/kylecarlstrom/CMPUT404-assignment-ajax Abram Hindle, Kyle Carlstrom and Tian Zhi Wang
@app.route("/entity/<entity>", methods=['POST','PUT'])
def update(entity):
    '''update the entities via this interface'''
    data = flask_post_json()
    myWorld.set(entity, data)
    return json.dumps(myWorld.get(entity))

@app.route("/world", methods=['POST','GET'])    
def world():
    '''you should probably return the world here'''
    return json.dumps(myWorld.world())

@app.route("/entity/<entity>")    
def get_entity(entity):
    '''This is the GET version of the entity interface, return a representation of the entity'''
    return json.dumps(myWorld.get(entity))


@app.route("/clear", methods=['POST','GET'])
def clear():
    '''Clear the world out!'''
    myWorld.clear()
    return json.dumps(myWorld.world())
# End citation: From assignment 4, https://github.com/kylecarlstrom/CMPUT404-assignment-ajax Abram Hindle, Kyle Carlstrom and Tian Zhi Wang


if __name__ == "__main__":
    ''' This doesn't work well anymore:
        pip install gunicorn
        and run
        gunicorn -k flask_sockets.worker sockets:app
    '''
    app.run()
