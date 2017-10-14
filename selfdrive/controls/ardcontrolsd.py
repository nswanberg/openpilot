#!/usr/bin/env python
import os
import zmq
import numpy as np
import selfdrive.messaging as messaging

from cereal import car

from common.numpy_fast import clip

from selfdrive.config import Conversions as CV
from common.services import service_list
from common.realtime import sec_since_boot, set_realtime_priority, Ratekeeper
from common.profiler import Profiler

def ardcontrolsd_thread(gctx, rate=100):  #rate in Hz
  # *** log ***
  context = zmq.Context()
  
  carstate = messaging.sub_sock(context, service_list['carState'].port)
  model = messaging.sub_sock(context, service_list['model'].port)

  # controls enabled state
  enabled = False

  autonomyEnabled = os.getenv("AUTONOMOUS_MODE")

  # learned angle offset
  angle_offset = 0

  free_space = 1.0

  # start the loop
  set_realtime_priority(2)

  rk = Ratekeeper(rate, print_delay_threshold=2./1000)
  while 1:
    cur_time = sec_since_boot()

    if autonomyEnabled:
      tsc = messaging.recv_sock(carstate, True)
      if tsc is not None:
        if enabled:
          if tsc.carState.steeringPressed:
            enabled = False
            print 'disabled!'
        else:
          if tsc.carState.gasPressed:
            enabled = True
            print 'enabled!'
    

def main(gctx=None):
  ardcontrolsd_thread(gctx, 100)

if __name__ == "__main__":
  main()
