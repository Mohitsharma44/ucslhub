import os
import sys

# Teaching Assistants (these will be able to create and modify assignments)
teaching_assistants = []
with open('teaching_assistants.txt', 'r') as fh:
    teaching_assistants = list(map(lambda x: x.strip(), fh.readlines()))

# The proxy is in another container
c.ConfigurableHTTPProxy.should_start = False
c.ConfigurableHTTPProxy.api_url = 'http://proxy:8001'

# use oauth
c.JupyterHub.authenticator_class = 'oauthenticator.generic.GenericOAuthenticator'
c.OAuthenticator.client_id = os.environ['OAUTH2_CLIENT_ID']  # oauth2 client id for your app
c.OAuthenticator.client_secret =  os.environ['OAUTH2_CLIENT_SECRET']  # oauth2 client secret for your app..
c.GenericOAuthenticator.token_url = os.environ['OAUTH2_TOKEN_URL'] # oauth2 provider's token url
c.GenericOAuthenticator.userdata_url = os.environ['OAUTH2_USERDATA_URL'] # oauth2 provider's endpoint with user data
c.GenericOAuthenticator.userdata_method = 'GET'  # method used to request user data endpoint
c.GenericOAuthenticator.userdata_params = {"state": "state"} # params to send for userdata endpoint
c.GenericOAuthenticator.username_key = "preferred_username"  # username key from json returned from user data endpoint


with open('admins.txt', 'r') as fh:
    c.Authenticator.admin_users = list(map(lambda x: x.strip(), fh.readlines()))

#c.Authenticator.admin_users = {'mohitsharma44'}

# use SwarmSpawner
# Mount user directory
import pwd
def mount_user_dirs(spawner):
    username = spawner.user.name
    basedir = os.environ['JUPYHOST_BASEDIR']
    nbgraderdir = os.environ['NBGRADER_BASEDIR']
    ucsldir = os.environ['UCSL_BASEDIR']
    userpath = os.path.join(basedir, username)
    # this is run as root, so chown to uscluser
    # get uid and gid for ucsluser
    uid = 1002 #pwd.getpwnam('ucsluser').pw_uid
    gid = 1002 #pwd.getpwnam('ucsluser').pw_gid
    if not os.path.exists(nbgraderdir):
        os.makedirs(nbgraderdir)
        os.chown(nbgraderdir, uid, gid)
    if not os.path.exists(userpath):
        os.makedirs(os.path.join(userpath, 'work', 'assignments'))
        os.chown(userpath, uid, gid)
        for root, dirs, files in os.walk(userpath):
            for dir in dirs:
                os.chown(os.path.join(root, dir), uid, gid)
            for fil in files:
                os.chown(os.path.join(root, fil), uid, gid)
    mounts_user = ["{}:{}:rw".format(userpath, '/home/jovyan/{}'.format(username)),
                   "{}:{}:rw".format(nbgraderdir, '/srv/nbgrader/exchange'),
                   "{}:{}:ro".format(ucsldir, '/home/jovyan/ucsl')]
    env = spawner.get_env()
    if username in teaching_assistants:
        # add some environment vars
        env['ta'] = username
    else:
        env['username'] = username
    env['JUPYTERHUB_USER'] = username
    #spawner.extra_container_spec = {'mounts': mounts_user,
    #				    'env': env}
    #spawner.notebook_dir = '/home/jovyan/{}'.format(username)
    spawner.notebook_dir = '/home/jovyan/'
    extra_container_spec = {'mounts': mounts_user}
    if username in teaching_assistants:
        spawner.image = os.environ['HUB_TA_IMAGE']
        # let this be run as root
        extra_container_spec.update({'user': 'root'})
        env['GRANT_SUDO'] = '1'
        env['UID'] = '0'
    else:
        spawner.image = os.environ['HUB_STUDENT_IMAGE']
    extra_container_spec.update({'env': env})
    spawner.extra_container_spec = extra_container_spec


c.Spawner.pre_spawn_hook = mount_user_dirs
c.JupyterHub.spawner_class = 'dockerspawner.SwarmSpawner'
c.SwarmSpawner.extra_placement_spec = { 'constraints' : ['node.labels.type==ucslworker'] }

# Culling
c.JupyterHub.services = [
    {
        'name': 'cull-idle',
        'admin': True,
        'command': [sys.executable, '/tmp/dockerspawner/tools/cull_idle_servers.py', '--timeout=3600'],
    }
]

# Messing around with JupyterHub
c.JupyterHub.template_paths = ['/tmp/dockerspawner/templates']

# The Hub should listen on all interfaces,
# so user servers can connect
c.JupyterHub.hub_ip = '0.0.0.0'
# this is the name of the 'service' in docker-compose.yml
c.JupyterHub.hub_connect_ip = 'hub'
c.JupyterHub.upgrade_db = True
# this is the network name for jupyterhub in docker-compose.yml
c.SwarmSpawner.network_name = 'ucslhub_jupynet'
c.SwarmSpawner.use_internal_ip = True
#c.SwarmSpawner.extra_host_config = {'network_mode': 'jupyterhub_jupynet'}
#c.SwarmSpawner.remove_services = True
c.Spawner.mem_limit = '1G'
c.Spawner.cpu_limit = 1

# start jupyterlab
c.Spawner.pre_spawn_hook = mount_user_dirs
#c.Spawner.cmd = ["jupyter", "labhub"]
c.Spawner.cmd = ["jupyter", "labhub", "--allow-root"]
c.SwarmSpawner.debug = True
c.Spawner.args = ['--NotebookApp.allow_origin=*']

# debug-logging for testing
import logging
c.JupyterHub.log_level = logging.DEBUG
