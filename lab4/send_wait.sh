
curl -d '' -X 'POST' 'http://10.1.0.1/vote/attack'
sleep 2
curl -d '' -X 'POST' 'http://10.1.0.2/vote/attack'
sleep 2
curl -d '' -X 'POST' 'http://10.1.0.3/vote/attack'
sleep 2
curl -d '' -X 'POST' 'http://10.1.0.4/vote/byzantine'
