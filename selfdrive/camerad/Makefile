CC = clang

CFLAGS = -w

INCLUDES = -I/system/comma/usr/local/sdk/native/jni/include/

LFLAGS = -L/system/comma/usr/local/sdk/native/libs -L/system/comma/usr/local/sdk/native/3rdparty/libs #-L/system/lib

LIBS = -lopencv_core -lopencv_highgui -lopencv_imgproc -lc++ -llog -lopencv_androidcamera -lopencv_calib3d -lopencv_contrib -lopencv_core -lopencv_features2d -lopencv_flann -lopencv_gpu -lopencv_legacy -lopencv_ml -lopencv_nonfree -lopencv_objdetect -lopencv_ocl -lopencv_photo -lopencv_stitching -lopencv_superres -lopencv_video -lopencv_videostab -lm -lstdc++  -lcutils -llibtiff -lz -lpng -llibjpeg -ljpeg -llibjasper -lIlmImf

TARGET = capturev4l2

all: $(TARGET)

$(TARGET): $(TARGET).c
	$(CC) $(CFLAGS) -o $(TARGET) $(TARGET).c $(INCLUDES) $(LFLAGS) $(LIBS)
