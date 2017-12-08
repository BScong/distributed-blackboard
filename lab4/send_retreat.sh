#!/bin/sh
for i in `seq 1 4`; do
  curl -d '' -X 'POST' 'http://10.1.0.'${i}'/vote/retreat'
done
