#! /bin/bash
sudo docker build -t amozgov/app .
sudo docker push amozgov/app
sudo docker compose up -d
sudo docker ps -a