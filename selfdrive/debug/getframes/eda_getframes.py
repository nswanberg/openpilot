#!/usr/bin/env python
import os
import time
import subprocess
from cffi import FFI
import ctypes
 
import numpy as np
 
import cv2
 
gf_dir = os.path.dirname(os.path.abspath(__file__))
 
subprocess.check_call(["make"], cwd=gf_dir)
 
 
ffi = FFI()
ffi.cdef("""
 
typedef enum VisionStreamType {
  VISION_STREAM_UI_BACK,
  VISION_STREAM_UI_FRONT,
  VISION_STREAM_YUV,
  VISION_STREAM_MAX,
} VisionStreamType;

typedef struct VisionUIInfo {
  int big_box_x, big_box_y;
  int big_box_width, big_box_height;
  int transformed_width, transformed_height;

  int front_box_x, front_box_y;
  int front_box_width, front_box_height;
} VisionUIInfo;

typedef struct VisionStreamBufs {
  VisionStreamType type;

  int width, height, stride;
  size_t buf_len;

  union {
    VisionUIInfo ui_info;
  } buf_info;
} VisionStreamBufs;

typedef struct VIPCBuf {
  int fd;
  size_t len;
  void* addr;
} VIPCBuf;

typedef struct VIPCBufExtra {
  uint32_t frame_id; // only for yuv
} VIPCBufExtra;

typedef struct VisionStream {
  int ipc_fd;
  int last_idx;
  int num_bufs;
  VisionStreamBufs bufs_info;
  VIPCBuf *bufs;
} VisionStream;

int visionstream_init(VisionStream *s, VisionStreamType type, bool tbuffer, VisionStreamBufs *out_bufs_info);
VIPCBuf* visionstream_get(VisionStream *s, VIPCBufExtra *out_extra);
void visionstream_destroy(VisionStream *s);

"""
)

clib = ffi.dlopen(os.path.join(gf_dir, "libvisionipc.so"))


def getframes():
  s = ffi.new("VisionStream*")
  buf_info = ffi.new("VisionStreamBufs*")
  err = clib.visionstream_init(s, clib.VISION_STREAM_UI_BACK, True, buf_info)
  assert err == 0

  w = buf_info.width
  h = buf_info.height
  assert buf_info.stride == w*3
  assert buf_info.buf_len == w*h*3

  while True:
    buf = clib.visionstream_get(s, ffi.NULL)

    pbuf = ffi.buffer(buf.addr, buf.len)
    yield np.frombuffer(pbuf, dtype=np.uint8).reshape((h, w, 3))


def blocks(msk,x1,x2,y1,y2,y3):  
  blocks=[msk[:y1,:x1], msk[:y1,x1:x2], msk[:y1,x2:],msk[y1:y2,:x1], msk[y1:y2,x1:x2], msk[y1:y2,x2:], msk[y2:,:x1], msk[y2:y3,x1:x2], msk[y3:,x1:x2], msk[y2:,x2:]]
  return blocks

def action(blocks,msk,x1,x2,y1,y2,y3):
  if msk.mean()>0.5*255:
    return 'REVERSE'
  if (blocks[7].mean()>0.4*255)&(blocks[4].mean()>0.4*255):
    return 'STOP'
  if (blocks[4].mean()>0.4*255):
    act = 'SLOW'
    if (blocks[3].mean()>blocks[5].mean()*1.2):
      act = act+'; LEFT'
    if (blocks[5].mean()>blocks[3].mean()*1.2):
      act = act+'; RIGHT'    
    return act
  else:
    if (blocks[3]+blocks[4]+blocks[5]).mean()>0.5*255:
      act ='GO'
      if blocks[3].mean()>blocks[5].mean()*1.3:
        act = act+'; RIGHT'
      if blocks[5].mean()>blocks[3].mean()*1.3:
        act = act+'; LEFT'
      return act
    else:
      return 'GO'





def analyze_image(frame):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    msk = rgb.copy()
    raw = rgb.copy()
    xmax = msk.shape[1]
    x1 = int(xmax/3)
    x2 = int(xmax*2/3)
    ymax = msk.shape[0]
    y1 = int(ymax/3)
    y2 = int(ymax*2/3)
    y3 = int(ymax*5/6)
   

    #gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    #edges = cv2.Canny(rgb,50,150)
    #edges3 = np.concatenate([np.zeros(edges.shape+(1,)).astype(edges.dtype), np.zeros(edges.shape+(1,)).astype(edges.dtype), edges.reshape(edges.shape+(1,))], axis=2)
    red = raw[:,:,2]>=1.5*raw[:,:,:2].sum(axis=2) 
    blue = raw[:,:,0]>=1.5*raw[:,:,1:].sum(axis=2)
    hay =  raw[:,:,1]>(raw.sum(axis=2)/3-0.5)
    maybehazard = red+blue+hay
    #msk3 = np.concatenate([blue.reshape(blue.shape+(1,)), hay.reshape(hay.shape+(1,)), red.reshape(red.shape+(1,))], axis=2).astype(rgb.dtype) * 255
    msk = maybehazard.astype(rgb.dtype)*255
#    msk3 = np.concatenate([np.zeros(msk.shape+(1,)).astype(rgb.dtype), np.zeros(msk.shape+(1,)).astype(rgb.dtype), msk.reshape(msk.shape+(1,))], axis=2)
    msk3 = np.concatenate([np.zeros(msk.shape+(1,)).astype(rgb.dtype), msk.reshape(msk.shape+(1,)), msk.reshape(msk.shape+(1,))], axis=2)
    block = blocks(msk,x1,x2,y1,y2,y3)
    act = action(block,msk,x1,x2,y1,y2,y3)
    # apply the overlay
    cv2.addWeighted(msk3, 0.3, rgb, 1 - 0.3,0, rgb)
    #cv2.putText(rgb,str(i), (800,110), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255),2)
    #cv2.putText(rgb,' '.join(gps[i]), (800,130), cv2.FONT_HERSHEY_PLAIN, 1, (255,255,255),2)
    cv2.putText(rgb,act, (800,150), cv2.FONT_HERSHEY_PLAIN, 1, (0,255,0),2)
    cv2.line(rgb, (380, 874), (520, 650), (0,255,0), 2)
    cv2.line(rgb, (800, 874), (590, 650), (0,255,0), 2)
    
    cv2.line(rgb, (400, 800), (800, 800), (0,255,0), 1)
    cv2.line(rgb, (400, 715), (800, 715), (0,255,0), 1)
    cv2.line(rgb, (400, 683), (800, 683), (0,255,0), 1)
    
    cv2.line(rgb, (0, y1), (xmax, y1), (255,255,255), 1)
    cv2.line(rgb, (0, y2), (xmax, y2), (255,255,255), 1)
    cv2.line(rgb, (x1, y3), (x2, y3), (255,255,255), 1)
    cv2.line(rgb, (x1, 0), (x1, ymax), (255,255,255), 1)
    cv2.line(rgb, (x2, 0), (x2, ymax), (255,255,255), 1)
    #for point in zip(list((np.array(mod[i])*xmax/2+xmax/2).astype('int')), list((np.arange(50)*ymax/2/50-ymax)*(-1))):
     #   cv2.circle(rgb,tuple(point),2,(100,100,255))
    return act


if __name__ == "__main__":
  for buf in getframes():
  #buf = bufgen.next()
  #buf = cv2.flip(buf,1)
  #print buf.shape, buf[101, 101]
    print(analyze_image(buf))
  #cv2.imwrite('test.png', rgb)
  #os.system("mv test.png /sdcard/testimg/")
