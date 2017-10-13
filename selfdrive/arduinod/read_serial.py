import array
import sys
import usb
import usb.core
import usb.util
import usb.control

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

def read_loop():
  while True:
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

def main():
   init_arduino()
   read_loop()

if __name__ == '__main__':
  main()
