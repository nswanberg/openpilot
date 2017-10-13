#include <sys/ioctl.h>

int main(int argc, char** argv)
{
  int i,r,fd;

  fd = open("/dev/video0", O_RDWR);

  struct v4l2_capability caps = {};
  
  for(i=0; i<10; i++)
  {
     r = ioctl (fd, i, &caps);
     printf("%i %i %i\n", i, r, errno);
  }
}

