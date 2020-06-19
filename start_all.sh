#!/bin/bash

ERR='\033[1;31m'
OK='\033[1;32m'
DBG='\033[1;37m'
NC='\033[0m'

echo -e "${DBG}Stopping existing hub service${NC}"
echo
docker-compose down --remove-orphans > /dev/null 2>&1


docker ps -a | grep  -oP nginx_allow_file_upload > /dev/null 2>&1
nginx_exists=$?
if [ "$nginx_exists" -eq 0 ]; then
  echo -e "${DBG}Starting existing Nginx container${NC}"
  docker start nginx_allow_file_upload
else
  echo -e "${DBG}Creating new Nginx container${NC}"
  docker run --privileged --userns host -d -p 80:80 -p 443:443 --name nginx_allow_file_upload -v /tmp/nginx:/etc/nginx/conf.d -v /nginx_conf/certs:/etc/nginx/certs -t nginx
fi
echo

docker ps -a | grep  -oP docker-gen_allow_file_upload > /dev/null 2>&1
dockergen_exists=$?
if [ "$nginx_exists" -eq 0 ]; then
  echo -e "${DBG}Starting existing docker-gen container${NC}"
  docker start docker-gen_allow_file_upload
else
  echo -e "${DBG}Creating new docker-gen container${NC}"
  docker run --name docker-gen_allow_file_upload -d --privileged --userns host --volumes-from nginx_allow_file_upload -v /nginx_conf/certs:/etc/nginx/certs -v /var/run/docker.sock:/tmp/docker.sock:ro -v /nginx_conf:/etc/docker-gen/templates -t jwilder/docker-gen -notify-sighup nginx_allow_file_upload -watch /etc/docker-gen/templates/nginx.tmpl /etc/nginx/conf.d/default.conf
fi
echo

echo -e "${DBG}Attaching ucsl-network to nginx${NC}"
docker network connect ucsl-network nginx_allow_file_upload > /dev/null 2>&1
if [ $? -eq 1 ]; then
  if [ "$nginx_exists" != 0 ]; then
    echo -e "${ERR}Error attaching ucsl-network to nginx${NC}"
    docker network connect ucsl-network nginx_allow_file_upload
    exit 1
  fi
fi
docker network connect ucsl-network docker-gen_allow_file_upload > /dev/null 2>&1
if [ $? -eq 1 ]; then
  if [ "$nginx_exists" != 0 ]; then
    echo -e "${ERR}Error attaching ucsl-network to docker-gen_allow_file_upload${NC}"
    docker network connect ucsl-network docker-gen_allow_file_upload
    exit 1
  fi
fi
echo

echo -e "${DBG}Starting Keycloak${NC}"
docker start mariadb
docker start keycloak
echo

echo -e "${DBG}Creating Attachable Overlay Network for ucslhub${NC}"
docker network create --attachable --driver overlay --subnet=10.10.11.0/24 ucslhub_jupynet > /dev/null 2>&1
echo

echo -e "${DBG}Connecting the Network to Nginx for name based dynamic reverse proxying${NC}"
docker network connect ucslhub_jupynet nginx_allow_file_upload > /dev/null 2>&1
if [ $? -eq 1 ]; then
  if [ "$nginx_exists" != 0 ]; then
    echo -e "${ERR}Error attaching ucsl-network to nginx${NC}"
    docker network connect ucslhub_jupynet nginx_allow_file_upload
    exit 1
  fi
fi
docker network connect ucslhub_jupynet docker-gen_allow_file_upload > /dev/null 2>&1
if [ $? -eq 1 ]; then
  if [ "$nginx_exists" != 0 ]; then
    echo -e "${ERR}Error attaching ucsl-network to docker-gen_allow_file_upload${NC}"
    docker network connect ucslhub_jupynet docker-gen_allow_file_upload
    exit 1
  fi
fi
echo

echo -e "${DBG}Bringing up the hub${NC}"
echo
docker-compose up -d
echo

echo -e "${OK}Done${NC}"
echo
