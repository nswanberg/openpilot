#!/usr/local/bin/python

# Based on boardd and code from http://tytouf.github.io/blog/libusb-arduino-en.html

import array
import os
import sys
import time
import usb.core
import usb.util
import usb.control
import zmq

import selfdrive.messaging as messaging
from common.realtime import Ratekeeper
from common.services import service_list
from selfdrive.swaglog import cloudlog

def can_capnp_to_arduino_list(can, src_filter=None):
  msgs = []
  for msg in can:
    if src_filter is None or msg.src in src_filter:
      msgs.append((msg.address, msg.busTime, msg.dat, msg.src))
  return msg

def arduino_send_many(arduino_list):
  steer_template = "{'type':'steering','value':%s}"
  throttle_template = "{'type':'throttle','value':%s}"

  #for c in "{'type':'steering','value':%s}" % angle: 
  #  dev.write(0x02, c)
  dev.write(0x02, "{'type':'steering','value':%s}" % angle, timeout=50)
  try:
    #print 'Received: "%s"' % dev.read(0x83, 64).tostring()
    response = dev.read(0x83, 64).tostring()
    while len(response):
      print "%s" % response
      response = dev.read(0x83, 64).tostring()
  except:
    print 'read failed'

def arduino_recv():
  pass

def init_arduino()

  # Look for a specific device and open it
  #
  dev = usb.core.find(idVendor=0x1b4f, idProduct=0x9206) # Sparkfun Aruino Pro Micro
  if dev is None:
      raise ValueError('Device not found')

  # Detach interfaces if Linux already attached a driver on it.
  #
  for itf_num in [0, 1]:
      itf = usb.util.find_descriptor(dev.get_active_configuration(),
                                     bInterfaceNumber=itf_num)
      print itf
      if dev.is_kernel_driver_active(itf_num):
          dev.detach_kernel_driver(itf)
      usb.util.claim_interface(dev, itf)

  # set control line state 0x2221
  # set line encoding 0x2021 (9600, 8N1)
  #
  dev.ctrl_transfer(0x21, 0x22, 0x01 | 0x02, 0, None)
  dev.ctrl_transfer(0x21, 0x20, 0, 0,
                    array.array('B', [0x80, 0x25, 0x00, 0x00, 0x00, 0x00, 0x08]))
                    #array.array('B', [0x00, 0xc2, 0x01, 0x00, 0x00, 0x00, 0x08]))

def arduinod_loop():

  rk = Ratekeeper(rate)
  context = zmq.Context()

  init_arduino()

  # Publish
  logcan = messaging.pub_sock(context, service_list['can'].port)

  # Subscribe using sendcan
  sendarduino = messaging.sub_sock(context, service_list['sencan'].port)

  while True:
    tsc = messaging.recv_sock(sendcan)
    if tsc is not None:
      arduino_send_many(can_capnp_to_arduino_list(tsc.sendcan))

def main(gtcx=None):
  if arduinod_loop()

if __name__ == "__main__":
  main()
