while true
do
  lsusb -d -v | grep 1b4f
  sleep 1
done
