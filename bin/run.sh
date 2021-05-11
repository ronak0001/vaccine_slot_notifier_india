#!/bin/bash
PATH=/home/ronak/PycharmProjects/vsn_india2/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin
now=$(date)
echo "Timestamp: $now"

. "/home/ronak/anaconda3/etc/profile.d/conda.sh"
conda activate vsn

cd /home/ronak/PycharmProjects/vsn_india2
source env.sh
python -m main
