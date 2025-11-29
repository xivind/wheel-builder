#!/bin/bash
# Script to backup database for Wheel Builder

set -o xtrace

docker container stop wheel-builder
sleep 5
rm -vf /home/pi/backup/wheel_builder.db
cp /home/pi/code/container_data/wheel_builder.db /home/pi/backup/wheel_builder.db
docker container start wheel-builder
