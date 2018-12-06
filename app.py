# This is an example Git server. http://blog.nerds.kr/post/106956608369/implementing-a-git-http-server-in-python
# http://stewartjpark.com/2015/01/02/implementing-a-git-http-server-in-python.html
# Stewart Park <stewartpark92@gmail.com> 
# @see
#  https://gist.github.com/stewartpark/1b079dc0481c6213def9
import os
import gzip
import configparser
import logging
import logging.config
from flask import Flask, make_response, request, abort
import subprocess

app = Flask(__name__)
logging.config.fileConfig('logging.ini')    # by logging config file.

# Read config.
config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')
conf = config['General']
BASE_DIR = conf.get('base.dir', 'repos')
THREADED = conf.getboolean('threaded', True)
IS_DEBUG_MODE = conf.getboolean('is.debug.mode', False)
HOST = conf.get('host', None)
PORT = conf.get('port', None)


def getRepositoryPath(projectName):
    return os.path.join(BASE_DIR, projectName)


@app.route('/')
def index():
    return 'git clone ' + request.url + '/repositoryname'


@app.route('/info/refs', defaults={'project_name': ''})
@app.route('/<string:project_name>/info/refs')
def info_refs(project_name):
    service = request.args.get('service')
    if service[:4] != 'git-':
        abort(500)
    repoPath = getRepositoryPath(project_name)
    app.logger.debug(repoPath)
    p = subprocess.Popen([service, '--stateless-rpc', '--advertise-refs', repoPath], stdout=subprocess.PIPE)
    packet = '# service=%s\n' % service
    length = len(packet) + 4
    prefix = "{:04x}".format(length & 0xFFFF)
    data = (prefix + packet + '0000').encode()
    data += p.stdout.read()
    res = make_response(data)
    res.headers['Expires'] = 'Fri, 01 Jan 1980 00:00:00 GMT'
    res.headers['Pragma'] = 'no-cache'
    res.headers['Cache-Control'] = 'no-cache, max-age=0, must-revalidate'
    res.headers['Content-Type'] = 'application/x-%s-advertisement' % service
    p.stdout.flush()
    p.wait()
    return res


@app.route('/git-receive-pack', defaults={'project_name': ''}, methods=('POST',))
@app.route('/<string:project_name>/git-receive-pack', methods=('POST',))
def git_receive_pack(project_name):
    repoPath = getRepositoryPath(project_name)
    p = subprocess.Popen(['git-receive-pack', '--stateless-rpc', repoPath], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    p.stdin.write(request.data)
    p.stdin.flush()
    data_out = p.stdout.read()
    res = make_response(data_out)
    res.headers['Expires'] = 'Fri, 01 Jan 1980 00:00:00 GMT'
    res.headers['Pragma'] = 'no-cache'
    res.headers['Cache-Control'] = 'no-cache, max-age=0, must-revalidate'
    res.headers['Content-Type'] = 'application/x-git-receive-pack-result'
    p.wait()
    return res


@app.route('/git-upload-pack', defaults={'project_name': ''}, methods=('POST',))
@app.route('/<string:project_name>/git-upload-pack', methods=('POST',))
def git_upload_pack(project_name):
    repoPath = getRepositoryPath(project_name)
    if 'Content-Encoding' in request.headers:
        # gzip
        app.logger.debug('Content-Encoding: ' + request.headers['Content-Encoding'])
        reqData = gzip.decompress(request.data)
    else:
        reqData = request.data
    p = subprocess.Popen(['git-upload-pack', '--stateless-rpc', repoPath], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    p.stdin.write(reqData)
    p.stdin.flush()
    data = p.stdout.read()
    res = make_response(data)
    res.headers['Expires'] = 'Fri, 01 Jan 1980 00:00:00 GMT'
    res.headers['Pragma'] = 'no-cache'
    res.headers['Cache-Control'] = 'no-cache, max-age=0, must-revalidate'
    res.headers['Content-Type'] = 'application/x-git-upload-pack-result'
    p.wait()
    return res


if __name__ == '__main__':
    app.run(debug=IS_DEBUG_MODE, host=HOST, port=PORT, threaded=THREADED)
