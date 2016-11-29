#!/bin/bash
docker build -t mordred .
docker-compose stop
docker-compose rm -f
docker-compose up
