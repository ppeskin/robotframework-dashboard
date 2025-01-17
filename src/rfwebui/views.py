#!/usr/bin/env python
import subprocess

from flask import render_template, request, redirect, Response, session, url_for
from rfwebui import app
from funcs.helper import ConfigSectionMap, save_settings, read_settings, SETTINGS_FILE_PATH
from glob import glob
from subprocess import Popen
from os import getcwd, path, makedirs
import json


# results_dir = getcwd() + "/static/"
results_dir = path.join(getcwd(), "static")
if not path.exists(results_dir):
    makedirs(results_dir)


def split_filter(s):
    return s.split('.')[0]
app.jinja_env.filters['split'] = split_filter


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    # if not path.isfile("app_configs/settings.ini"):
    if not path.isfile(SETTINGS_FILE_PATH):
        return redirect(url_for('settings'))
    working_dir = ConfigSectionMap("FILES")['path']
    # types = (working_dir + '*.robot', working_dir + '*.txt')
    types = (path.join(working_dir,'*.robot'),)
    files_grabbed = []
    for files in types:
        fwp = glob(files)
        for item in fwp:
            # files_grabbed.append(item.replace(working_dir, ''))
            files_grabbed.append(path.basename(item))
    if not files_grabbed:
        files_grabbed.append('Nothing to show')  # TODO: redirect to error page with proper message
    return render_template('index.html',
                           title='RF Dashboard',
                           tests=files_grabbed)


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    app_settings = read_settings()
    print(app_settings)
    if request.method == 'POST':
        save_settings(request.form['dir_path'])
    return render_template('settings.html',
                           title='RF Dashboard - Settings',
                           settings=app_settings)


@app.route('/cmd', methods=['POST'])
def cmd():
    working_dir = ConfigSectionMap("FILES")['path']
    command = request.form.get('data')
    print("Got data: " + command)
    # output_dir = results_dir + command.split('.')[0] + '/'
    output_dir = path.join(results_dir, path.basename(command).split('.')[0])
    print("output dir: " + output_dir)
    # proc = Popen(["robot", "-d", output_dir, working_dir + command])
    full_command = path.join(working_dir, command)
    print("full_command: " + full_command)
    proc = Popen(["python", "-m", "robot", "-d", output_dir, full_command])
    # with open('logfile.txt', "w+") as log:
    # proc = Popen(f'robot -d {output_dir} {full_command}', shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    proc.wait()
    print("Result code: {}".format(proc.returncode))
    sjson = json.dumps({'test_name': command, 'status_code': proc.returncode})
    return Response(sjson, content_type='text/event-stream')


@app.route('/static')
def results():
    return redirect(url_for('static'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', title='Page not found')

@app.errorhandler(405)
def page_error(e):
    return render_template('405.html', title='Something unexpected happened')
