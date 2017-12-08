for j in `seq 1 40`; do
for i in `seq 1 32`; do
curl -d 'entry=server'${i}'-number'${j} -X 'POST' 'http://10.1.0.'${i}'/entries' &
done
sleep 1
done
