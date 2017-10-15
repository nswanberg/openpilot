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
from selfdrive.services import service_list

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

def usb_write(data):
   dev.write(0x02, data, timeout=50)

def in_pressed_range(control_value):
  return abs(control_value) > 50

def arduino_read():
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
        steeringAngle = int(steering)
        ret.steeringAngle = steeringAngle
        ret.steeringPressed = in_pressed_range(steeringAngle)
      except:
        pass
    if throttle:
      try:
        throttleForce = int(throttle)
        ret.gas = throttleForce
        ret.gasPressed = in_pressed_range(throttleForce)
      except:
        pass
    return ret

def make_arduino_command(command, value):
  # enclose in <> for the arduino function
  return "<{'type':'%s','value':%d}>" % (command, value)

def arduino_loop(rate=200):
  rk = Ratekeeper(rate)
  context = zmq.Context()

  init_arduino()
  carstate = messaging.pub_sock(context, service_list['carState'].port)
  arduino = messaging.sub_sock(context, service_list['arduinoCommand'].port)
  live100 = messaging.sub_sock(context, service_list['live100'].port)
  
  while True:

    carStateMsg = arduino_read()

    car_send = messaging.new_message()
    car_send.init('carState') 
    car_send.carState = carStateMsg
    carstate.send(car_send.to_bytes())

    cmd = messaging.recv_sock(arduino)
    if cmd is not None:
      usb_write(make_arduino_command('steering',cmd.arduinoCommand.steering))

    lcmd = messaging.recv_sock(live100)
    if lcmd is not None:
      if lcmd.live100.enabled:
#autonomy enabled, so disable radio
        radioEnabled = 0
      else:
        radioEnabled = 1
      usb_write(make_arduino_command('radio', radioEnabled))

   #rk.keep_time()

def main(gctx=None):
   init_arduino()
   arduino_loop()

if __name__ == '__main__':
  main()
