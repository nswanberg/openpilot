# ##!/usr/bin/env python
import array
import sys
import usb
import usb.core
import usb.util
import usb.control

import selfdrive.messaging as messaging
from common.realtime import Ratekeeper
from common.services import service_list

dev = None

def init_arduino():
  global dev
  dev = usb.core.find(idVendor=0x1b4f, idProduct=0x9206) # Sparkfun Aruino Pro Micro
  for itf_num in [0, 1]:
    itf = usb.util.find_descriptor(dev.get_active_configuration(),
                                  bInterfaceNumber=itf_num)
    if dev.is_kernel_driver_active(itf_num):
      dev.detach_kernel_driver(itf)
    usb.util.claim_interface(dev, itf)

  dev.ctrl_transfer(0x21, 0x22, 0x01 | 0x02, 0, None)
  dev.ctrl_transfer(0x21, 0x20, 0, 0,
                    array.array('B', [0x00, 0xc2, 0x01, 0x00, 0x00, 0x00, 0x08]))

def usb_read():
  usb_data = ''
  while True:
    try:
      usb_data = dev.bulkRead(1, 0x83*256)
      break
    except (USBErrorIO, USBErrorOverflow):
      print 'usb error'
  return usb_data

def read_loop(rate=200):
  rk = Ratekeeper(rate)
  context = zmq.Context()

  init_arduino()

  carstate = messaging.pub_sock(context, service_list['carstate'].port)

  while True:
    print usb_read()
    """
    response = ''
    try:
      response = dev.read(0x83, 64).tostring()
      while len(response):
        print response
        response = dev.read(0x83, 64).tostring()
    except usb.core.USBError:
      print 'usb exception'
    except:
      print  'regular exception'
    """
def main():
   init_arduino()
   read_loop()

if __name__ == '__main__':
  main()
