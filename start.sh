dockerd &

sleep 5

docker-compose up -d

docker-compose stop
