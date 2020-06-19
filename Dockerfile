FROM mohitsharma44/ucslhub:1.0

LABEL maintainer="Mohit Sharma <Mohitsharma44@gmail.com>"

# Add dockerspawner
ADD dockerspawner /tmp/dockerspawner
# Install oAuthenticator
RUN pip install --no-cache oauthenticator /tmp/dockerspawner/
# Add custom files
#COPY videos/ /opt/conda/share/jupyterhub/static/videos
COPY mounts/ /
# load configuration
COPY jupyterhub_config.py admins.txt teaching_assistants.txt /srv/jupyterhub/
