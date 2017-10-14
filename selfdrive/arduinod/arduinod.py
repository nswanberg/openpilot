#!/usr/bin/env python
import array
import json
import sys
import usb
import usb.core
import usb.util
import usb.control
import zmq

import selfdrive.messaging as messaging
from common.realtime import Ratekeeper
from common.services import service_list

from cereal import car

dev = None

def init_arduino():
  global dev
  try:
    dev = usb.core.find(idVendor=0x1b4f, idProduct=0x9206) # Sparkfun Aruino Pro Micro
  except:
    print 'error connecting to arduino'
  try:
    for itf_num in [0, 1]:
      itf = usb.util.find_descriptor(dev.get_active_configuration(),
                                    bInterfaceNumber=itf_num)
      if dev.is_kernel_driver_active(itf_num):
        dev.detach_kernel_driver(itf)
      usb.util.claim_interface(dev, itf)
  except:
    print 'error showing interfaces'
  try:
    dev.ctrl_transfer(0x21, 0x22, 0x01 | 0x02, 0, None)
    dev.ctrl_transfer(0x21, 0x20, 0, 0,
                      array.array('B', [0x00, 0xc2, 0x01, 0x00, 0x00, 0x00, 0x08]))
  except:
    print 'error sending ctrl transfer'

def usb_read():
  usb_data = ''
  while True:
    try:
      usb_data = dev.read(0x83, 256).tostring()
      break
    except:
      print 'usb error'
  return usb_data

def read_loop(rate=200):
  rk = Ratekeeper(rate)
  context = zmq.Context()

  init_arduino()
  print 'inited'
  carstate = messaging.pub_sock(context, service_list['carState'].port)

  while True:
    data_string = usb_read()
    lines = data_string.split('\n')
    for line in lines:
      steering = None
      throttle = None
      try:
        # doesn't always get a full steering/throttle pair
        steering, throttle = line.split()
        #print 'steering: ' + steering
        #print 'throttle: ' + throttle
      except:
        pass

      ret = car.CarState.new_message()
      if steering:
        try:
          # doesn't always get a number
          ret.steeringAngle = int(steering)
        except:
          pass
      if throttle:
        try:
          ret.gas = int(throttle)
        except:
          pass

      car_send = messaging.new_message()
      car_send.init('carState') 
      car_send.carState = ret
      carstate.send(car_send.to_bytes())

def main(gctx=None):
   init_arduino()
   read_loop()

if __name__ == '__main__':
  main()
