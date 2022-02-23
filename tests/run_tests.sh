close() {
  echo "=========================== Cleanup ==========================="
  docker-compose down
  exit $1
}

echo "=========================== Build ==========================="
docker-compose build test || close 1

echo "=========================== Test ==========================="
docker-compose run --rm test || close 1
close 0
