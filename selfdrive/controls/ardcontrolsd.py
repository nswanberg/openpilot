#!/usr/bin/env python
import os
import zmq
import numpy as np
import selfdrive.messaging as messaging

from cereal import car, log

from common.numpy_fast import clip

from selfdrive.config import Conversions as CV
from selfdrive.services import service_list
from common.realtime import sec_since_boot, set_realtime_priority, Ratekeeper
from common.profiler import Profiler

from selfdrive.debug.getframes import eda_getframes

def update_steering_angle(angle):
  if angle <= 75:
    angle += 1
  if angle > 75:
    angle = -75
  return angle

def ardcontrolsd_thread(gctx, rate=100):  #rate in Hz
  # *** log ***
  context = zmq.Context()
  
  carstate = messaging.sub_sock(context, service_list['carState'].port)
  getframes = messaging.sub_sock(context, service_list['getFrames'].port)

  arduino = messaging.pub_sock(context, service_list['arduinoCommand'].port)
  live100 = messaging.pub_sock(context, service_list['live100'].port)

  # controls enabled state
  enabled = False

  autonomyEnabled = os.getenv("AUTONOMOUS_MODE")

  # learned angle offset
  angle_offset = 0

  free_space = 1.0

  # start the loop
  set_realtime_priority(2)

  steering_angle = 0




  rk = Ratekeeper(rate, print_delay_threshold=2./1000)
  #g = eda_getframes.getframes()
  
  while 1:
    cur_time = sec_since_boot()

    if autonomyEnabled:

      cmd = messaging.recv_sock(getframes)
      if enabled and cmd is not None:
        command = cmd.getFrames.command
        steering, throttle = get_servo_from_command(command)
        send_arduino_message(arduino, steering, throttle)

      tsc = messaging.recv_sock(carstate, True)
      if tsc is not None:
        if enabled:
          if tsc.carState.steeringPressed:
            enabled = False
            send_arduino_message(arduino,0,0)
            send_live100(enabled, live100)
        
        else:
          if tsc.carState.gasPressed:
            enabled = True
            send_live100(enabled, live100)

    rk.keep_time() 

def get_servo_from_command(command):
  if "RIGHT" in command:
    return (40, 16)
  elif "LEFT" in command:
    return (-30, 16)
  else:
# zero out at 10
    return (10, 16)

def send_arduino_message(arduino, steering, throttle):
  msg = messaging.new_message()
  msg.init('arduinoCommand')
  msg.arduinoCommand.throttle = throttle
  msg.arduinoCommand.steering = steering
  arduino.send(msg.to_bytes())

def send_live100(enabled, live100):
  msg = messaging.new_message()
  msg.init('live100')
  msg.live100.enabled = enabled
  live100.send(msg.to_bytes())

def main(gctx=None):
  ardcontrolsd_thread(gctx, 20)

if __name__ == "__main__":
  main()
