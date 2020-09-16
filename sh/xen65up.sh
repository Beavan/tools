#!/bin/bash

mount -t cifs -o password="" //172.21.23.201/GuestUpload/IT-team/patch/xen6.5 /mnt

cd /mnt 

xe patch-upload file-name=XS65ESP1.xsupdate &> /tmp/a.txt
echo "XS65ESP1.xsupdate is uploaded."
cat /tmp/a.txt |grep "uuid"|awk '{print $2}' > /tmp/uuid.txt
xe patch-pool-apply uuid=`cat /tmp/uuid.txt`
echo "XS65ESP1.xsupdate is installed."

for filename in `ls /mnt`
do 
	if [[ $filename != "XS65ESP1.xsupdate" ]];then
		xe patch-upload file-name=$filename &> /tmp/a.txt
		echo "$filename is uploaded."
		cat /tmp/a.txt |grep "uuid"|awk '{print $2}' > /tmp/uuid.txt
		xe patch-pool-apply uuid=`cat /tmp/uuid.txt`
		echo "$filename is installed."
	fi
done

sleep 5
umount /mnt
