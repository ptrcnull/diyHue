from datetime import datetime
from uuid import getnode as get_mac
import hashlib
import random
import json

import requests
import hug
from jinja2 import FileSystemLoader, Environment

from huebridgeemulator.tools import generateSensorsState
from huebridgeemulator.web.templates import get_template
from huebridgeemulator.http.websocket import scanDeconz
from huebridgeemulator.tools.light import scanForLights
from threading import Thread
import time

import huebridgeemulator.web.ui
from huebridgeemulator.web.tools import authorized


@hug.get('/api/{uid}/sensors/{resource_id}', requires=authorized)
def api_get_sensors_id(uid, resource_id, request, response):
    """print specified object config."""
    bridge_config = request.context['conf_obj'].bridge
    return bridge_config['sensors']


@hug.get('/api/{uid}/sensors/new', requires=authorized)
def api_get_sensors_new(uid, request, response):
    """return new lights and sensors only."""
    bridge_config = request.context['conf_obj'].bridge
    response = request.context['conf_obj'].get_new_lights()
    request.context['conf_obj'].clear_new_lights()
    return response


@hug.get('/api/{uid}/sensors')
def api_get_lights(uid, request, response):
    bridge_config = request.context['conf_obj'].bridge
    return bridge_config['sensors']


@hug.post('/api/{uid}/sensor', requires=authorized)
def api_post_sensor(uid, body, request, response):
    bridge_config = request.context['conf_obj'].bridge
    if not bool(body):
        Thread(target=scanForLights,
               args=[request.context['conf_obj'],
                     request.context['new_lights']]).start()
        # TODO wait this thread but add a timeout
        time.sleep(7)
        return [{"success": {"/" + uid: "Searching for new devices"}}]


@hug.post('/api/{uid}/sensors', requires=authorized)
def api_post_sensors(uid, body, request, response):
    bridge_config = request.context['conf_obj'].bridge
    post_dictionary = body
    print("create objectcreate objectcreate objectcreate objectcreate object")
    print(request.path)
    # find the first unused id for new object
    new_object_id = request.context['conf_obj'].nextFreeId('sensors')
    if "state" not in post_dictionary:
        post_dictionary["state"] = {}
    if post_dictionary["modelid"] == "PHWA01":
        post_dictionary.update({"state": {"status": 0}})
    generateSensorsState(bridge_config, request.context['sensors_state'])
    bridge_config['sensors'][new_object_id] = post_dictionary
    request.context['conf_obj'].save()
    print(json.dumps([{"success": {"id": new_object_id}}], sort_keys=True, indent=4, separators=(',', ': ')))
    return [{"success": {"id": new_object_id}}]


@hug.delete('/api/{uid}/sensors/{resource_id}', requires=authorized)
def api_delete_sensors_id(uid, resource_id, request, response):
    bridge_config = request.context['conf_obj'].bridge
    del bridge_config['sensors'][resource_id]
    for sensor in list(bridge_config["deconz"]["sensors"]):
        if bridge_config["deconz"]["sensors"][sensor]["bridgeid"] == resource_id:
            del bridge_config["deconz"]["sensors"][sensor]
    request.context['conf_obj'].save()
    return [{"success": "/sensors/" + resource_id + " deleted."}]