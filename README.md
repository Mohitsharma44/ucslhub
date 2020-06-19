# UCSLHub

UCSLHUB is the horizontally scalable backend infrastructure leveraging Docker Swarm for hosting the 
JupyterHub server and spawning JupyterNotebooks and JupyterLab on the worker nodes for NYU CUSP 
students to access. 

Some of the features inclue:

- Keycloak as the Identity Provider (using OAuth2 tokens).
- Spawning Notebooks as a service.
- Separate Notebooks for TeachingAssistants/CourseAdmins and Students.
- Automatic culling of the notebooks after set interval.
- NBgrader integration.

## Running the UCSLHUB

There are 3 steps involved in running the UCSLHUB:

1. Running Nginx Server for reverse proxy.
You can use an opensource project like [`Letsencrypt-Nginx-Proxy`](https://github.com/evertramos/docker-compose-letsencrypt-nginx-proxy-companion)
a nifty tool by [@evertramos](https://github.com/evertramos) or run things manually (or create a `docker-compose` file) as:
    - Running Nginx server (and mounting location for SSL certs)
      ```
      docker run --privileged --userns host -d -p 80:80 -p 443:443 --name nginx \
      -v /tmp/nginx:/etc/nginx/conf.d -v /nginx_conf/certs:/etc/nginx/certs -t nginx
      ```
    - Running script to generate certificates separately (this monitors for docker services and requests letsencrypt certs on the fly):
      ```
      docker run --name docker-gen --privileged --userns host --volumes-from nginx -v /nginx_conf/certs:/etc/nginx/certs \
      -v /var/run/docker.sock:/tmp/docker.sock:ro -v /nginx_conf:/etc/docker-gen/templates \
      -t jwilder/docker-gen -notify-sighup nginx \
      -watch /etc/docker-gen/templates/nginx.tmpl /etc/nginx/conf.d/default.conf
      ```

2. Setting up and Running the Keycloak server as an Identity Provider:
(Setting up part is too broad for the readme file, I'll assume that you can setup the Keycloak authenticator for providing 
OAuth2 tokens). 
Running part is fairly straight forward although, it involves two parts (you can create a `docker-compose` file and I'll probably do that at some point):
    - Running MariaDB: 
    I prefer using MariaDB as the database for storing Keycloak data in. You can run MariaDB with persistent
    storage in a container by running:
      ```
      docker run -d --name mariadb --net ucsl-network -v /maria-db-data:/var/lib/mysql \
      -e MYSQL_ROOT_PASSWORD=<FANCY ROOT PASSWORD> -e MYSQL_DATABASE=keycloak \
      -e MYSQL_USER=keycloak -e MYSQL_PASSWORD=<FANCY PASSWORD FOR KEYCLOAK> mariadb
      ```
  
    - Running Keycloak:
      ```
      docker run -d --net ucsl-network --name keycloak -p 8080:8080 --expose 8080 \
      -e DB_VENDOR=mariadb -e DB_USER=keycloak -e DB_PASSWORD=<FANCY PASSWORD FOR KEYCLOAK SAME AS SET IN MARIADB> \
      -e KEYCLOAK_USER=admin -e KEYCLOAK_PASSWORD=<FANCY ADMIN PASSWORD FOR WEBUI> \
      -e PROXY_ADDRESS_FORWARDING=true -e VIRTUAL_HOST=id.ucsl.cusp.nyu.edu jboss/keycloak
      ```

3. Finally, run the ucslhub:
You must fill out the `penv` and `henv` from the keycloak setup and rename them to `.pyenv` and `.henv`.
Now, you can simply run:
    - [`start_hub.sh`](https://github.com/Mohitsharma44/ucslhub/blob/master/start_hub.sh) to start the ucslhub
    - [`stop_hub.sh`](https://github.com/Mohitsharma44/ucslhub/blob/master/stop_hub.sh) to stop the ucslhub

## System Architecture

![Architecture](https://github.com/Mohitsharma44/ucslhub/blob/master/documentation/high-level-overview/Canvas%201.png)

### Working

The Users (ucsl admin and the students) access the UCSLHUB or Keycloak by first hitting the Nginx server.
Nginx performs sub-domain based routing and forwards the traffic to the UCSLHUB server or the Identity server based on the
subdomain.

#### For Keycloak / Account Management

If accessing id.ucsl.cusp.nyu.edu, the users are routed to the keycloak authentication module where they can manage 
their account and if accessing ucsl.cusp.nyu.edu, they are dropped onto the login page of the ucslhub where they can change 
attributes such as username, email address, passwords and other things.

#### For accessing the UCSLHUB

I'll let the following flow describe the process:

![Working](https://github.com/Mohitsharma44/ucslhub/blob/master/documentation/high-level-overview/Canvas%202.png)

### Configuration

You can add all your administrators for the Hub inside [`admins.txt`](https://github.com/Mohitsharma44/ucslhub/blob/master/admins.txt) file

You can only add 1 TA (this is a limitation right now) inside [`teaching_assistants.txt`](https://github.com/Mohitsharma44/ucslhub/blob/master/teaching_assistants.txt) file

All of the configuration/ configurable settings is mentioned in the [`jupyter_config.py`](https://github.com/Mohitsharma44/ucslhub/blob/master/jupyterhub_config.py)
file which should be pretty self-explanatory but incase you need some help, feel free to create an issue.


## Credits

This project has been built using several tools made by and contributed to the opensource community. Some of them used are:
- [Nginx Proxy](https://github.com/jwilder/nginx-proxy) container by @jwilder.
- SwarmSpawner using [dockerspawner](https://github.com/jupyterhub/dockerspawner) module by @Jupyterhub.
- [Keycloak](https://hub.docker.com/r/jboss/keycloak/) container by @Jboss.
- [MariaDB](https://hub.docker.com/_/mariadb) container by the MariaDB community.

## License MIT
MIT License

Copyright (c) 2019 Mohit

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

