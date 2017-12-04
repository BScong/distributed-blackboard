for j in `seq 1 50`; do
for i in `seq 1 8`; do
curl -d 'entry=server'${i}'-number'${j} -X 'POST' 'http://10.1.0.'${i}'/entries'
done
done