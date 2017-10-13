#!/usr/bin/env python
import time
import websocket
import zmq

import selfdrive.messaging as messaging
from common.services import service_list
from selfdrive.swaglog import cloudlog





# PORTS
# A is steering, B is motor

def steer(degrees):
  """
  degrees: steering angle from 0 to 90
  The car seems happier with 10 to 80
  """
  ws.send('RA' + str(degrees))

def forward(speed):
  """
  speed: forward is 100 to 180
  reverse is 95 to 0
  (roughly)
  """

  # only go forward slowly for now
  if speed < 100:
    speed = 100
  elif speed > 120:
    speed = 120

  ws.send('RB' + str(speed))

def espd_thread():
  context = zmq.Context()
  sendesp = messaging.sub_sock(context, service_list['sendesp'].port) 

  ws = websocket.WebSocket()
  ws.connect("ws://192.168.4.1")
  cloudlog.info('connected to esp32')

  while(1):
    msg = messaging.recv_sock(sendesp)
    if msg is not None:
      forward(msg.speed)
      steer(msg.degrees)

def main(gctx=None):
  espd_thread()

if __name__ == "__main__":
  main()
