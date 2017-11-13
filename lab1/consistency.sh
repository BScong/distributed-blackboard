for i in `seq 1 20`; do
curl -d 'entry=server1-number'${i} -X 'POST' 'http://10.1.0.1/entries'
curl -d 'entry=server2-number'${i} -X 'POST' 'http://10.1.0.2/entries'
done