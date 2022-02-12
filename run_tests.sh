close() {
  echo "=========================== Cleanup ==========================="
  docker-compose down
  exit $1
}

echo "=========================== Build ==========================="
docker-compose build ws-proxy-test || close 1

echo "=========================== Test ==========================="
docker-compose run --rm ws-proxy-test || close 1
close 0