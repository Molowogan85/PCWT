from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, escape, Markup, Response, current_app
)
from threading import Thread
from werkzeug.security import check_password_hash, generate_password_hash
import json
import markdown
import bleach
import tldextract
from bleach_whitelist import markdown_tags, markdown_attrs
import uuid
import re
import os
from app.auth import login_required
from app.db import get_db
from app.cron import run, runMasscan, runNmap


bp = Blueprint('api', __name__, url_prefix='/api')


###########################################
@bp.route('/getHostNote', methods=['POST'])
@login_required
def getHostNote():
    db = get_db()
    hostid = request.get_json()['hostid']
    check_access = db.execute(
        'SELECT projects.owner FROM projects INNER JOIN hosts ON projects.id = hosts.project WHERE hosts.id = ?',
        (hostid, )
    ).fetchone()

    if not check_access or not hostid:
        return Response(json.dumps({"status": "not found"}), mimetype='application/json')
    if check_access['owner'] != session['username']:
        return Response(json.dumps({"status": "not found"}), mimetype='application/json')

    note = db.execute(
        'SELECT note FROM hosts WHERE id = ?',
        (hostid,)
    ).fetchone()

    return Response(json.dumps({'note': note['note']}), mimetype='application/json')


@bp.route('/updateHostNote', methods=['POST'])
@login_required
def updateHostNote():
    db = get_db()
    hostid = request.get_json()['hostid']
    note = request.get_json()['note']
    check_access = db.execute(
        'SELECT projects.owner FROM projects INNER JOIN hosts ON projects.id = hosts.project WHERE hosts.id = ?',
        (hostid, )
    ).fetchone()

    if not check_access or not hostid or not note:
        return Response(json.dumps({"status": "not found"}), mimetype='application/json')
    if check_access['owner'] != session['username']:
        return Response(json.dumps({"status": "not found"}), mimetype='application/json')

    db.execute(
        'UPDATE hosts SET note = ? WHERE id = ?',
        (note.strip(), hostid, )
    )
    db.commit()

    return Response(json.dumps({"note": Markup(bleach.clean(markdown.markdown(note), markdown_tags, markdown_attrs))}), mimetype='application/json')


@bp.route('/updateHostStyle', methods=['POST'])
@login_required
def updateHostStyle():
    db = get_db()
    hostid = request.get_json()['hostid']
    styleType = request.get_json()['type']
    check_access = db.execute(
        'SELECT projects.owner FROM projects INNER JOIN hosts ON projects.id = hosts.project WHERE hosts.id = ?',
        (hostid, )
    ).fetchone()

    if not check_access or not hostid or not styleType:
        return Response(json.dumps({"status": "not found"}), mimetype='application/json')
    if check_access['owner'] != session['username']:
        return Response(json.dumps({"status": "not found"}), mimetype='application/json')

    if styleType in ["Checked", "Hacked", "Suspicious", "Default"]:
        style = styleType
    else:
        return Response(json.dumps({"status": "not found"}), mimetype='application/json')

    db.execute(
        'UPDATE hosts SET style = ? WHERE id = ?',
        (style, hostid, )
    )
    db.commit()
    return Response(json.dumps({"style": style}), mimetype='application/json')


@bp.route('/deleteHost', methods=['POST'])
@login_required
def deleteHost():
    db = get_db()
    hostid = request.get_json()['hostid']
    check_access = db.execute(
        'SELECT projects.owner FROM projects INNER JOIN hosts ON projects.id = hosts.project WHERE hosts.id = ?',
        (hostid, )
    ).fetchone()

    if not check_access or not hostid:
        return Response(json.dumps({"status": "not found"}), mimetype='application/json')
    if check_access['owner'] != session['username']:
        return Response(json.dumps({"status": "not found"}), mimetype='application/json')

    db.execute(
        'DELETE FROM ports WHERE host = ?',
        (hostid, )
    )
    db.execute(
        'DELETE FROM hosts WHERE id = ?',
        (hostid, )
    )
    db.commit()
    return Response(json.dumps({"status": "success"}), mimetype='application/json')

###########################################

###########################################


@bp.route('/getPortNote', methods=['POST'])
@login_required
def getPortNote():
    db = get_db()
    portid = request.get_json()['portid']
    check_access = db.execute(
        'SELECT projects.owner FROM projects INNER JOIN hosts ON projects.id = hosts.project INNER JOIN ports ON hosts.id = ports.host WHERE ports.id = ?',
        (portid, )
    ).fetchone()

    if not check_access or not portid:
        return Response(json.dumps({"status": "not found"}), mimetype='application/json')
    if check_access['owner'] != session['username']:
        return Response(json.dumps({"status": "not found"}), mimetype='application/json')

    note = db.execute(
        'SELECT note FROM ports WHERE id = ?',
        (portid, )
    ).fetchone()

    return Response(json.dumps({'note': note['note']}), mimetype='application/json')


@bp.route('/updatePortNote', methods=['POST'])
@login_required
def updatePortNote():
    db = get_db()
    portid = request.get_json()['portid']
    note = request.get_json()['note']

    check_access = db.execute(
        'SELECT projects.owner FROM projects INNER JOIN hosts ON projects.id = hosts.project INNER JOIN ports ON hosts.id = ports.host WHERE ports.id = ?',
        (portid, )
    ).fetchone()

    if not check_access or not portid or not note:
        return Response(json.dumps({"status": "not found"}), mimetype='application/json')
    if check_access['owner'] != session['username']:
        return Response(json.dumps({"status": "not found"}), mimetype='application/json')

    db.execute(
        'UPDATE ports SET note = ? WHERE id = ?',
        (note.strip(), portid)
    )
    db.commit()

    return Response(json.dumps({"note": Markup(bleach.clean(markdown.markdown(note), markdown_tags, markdown_attrs))}), mimetype='application/json')

###########################################

###########################################


@bp.route('/getDomainNote', methods=['POST'])
@login_required
def getDomainNote():
    db = get_db()
    domainid = request.get_json()['domainid']

    check_access = db.execute(
        'SELECT projects.owner FROM projects INNER JOIN domains ON projects.id = domains.project WHERE domains.id = ?',
        (domainid, )
    ).fetchone()

    if not check_access or not domainid:
        return Response(json.dumps({"status": "not found"}), mimetype='application/json')
    if check_access['owner'] != session['username']:
        return Response(json.dumps({"status": "not found"}), mimetype='application/json')

    note = db.execute(
        'SELECT note FROM domains WHERE id = ?',
        (domainid, )
    ).fetchone()

    return Response(json.dumps({'note': note['note']}), mimetype='application/json')


@bp.route('/updateDomainNote', methods=['POST'])
@login_required
def updateDomainNote():
    db = get_db()
    domainid = request.get_json()['domainid']
    note = request.get_json()['note']

    check_access = db.execute(
        'SELECT projects.owner FROM projects INNER JOIN domains ON projects.id = domains.project WHERE domains.id = ?',
        (domainid, )
    ).fetchone()

    if not check_access or not domainid:
        return Response(json.dumps({"status": "not found"}), mimetype='application/json')
    if check_access['owner'] != session['username']:
        return Response(json.dumps({"status": "not found"}), mimetype='application/json')

    db.execute(
        'UPDATE domains SET note = ? WHERE id = ?',
        (note.strip(), domainid, )
    )

    db.commit()

    return Response(json.dumps({"note": Markup(bleach.clean(markdown.markdown(note), markdown_tags, markdown_attrs))}), mimetype='application/json')


@bp.route('/updateDomainStyle', methods=['POST'])
@login_required
def updateDomaintStyle():
    db = get_db()
    domainid = request.get_json()['domainid']
    styleType = request.get_json()['type']
    check_access = db.execute(
        'SELECT projects.owner FROM projects INNER JOIN domains ON projects.id = domains.project WHERE domains.id = ?',
        (domainid, )
    ).fetchone()

    if not check_access or not domainid or not styleType:
        return Response(json.dumps({"status": "not found"}), mimetype='application/json')
    if check_access['owner'] != session['username']:
        return Response(json.dumps({"status": "not found"}), mimetype='application/json')

    if styleType in ["Checked", "Hacked", "Suspicious", "Default"]:
        style = styleType
    else:
        return Response(json.dumps({"status": "not found"}), mimetype='application/json')

    db.execute(
        'UPDATE domains SET style = ? WHERE id = ?',
        (style, domainid, )
    )
    db.commit()
    return Response(json.dumps({"style": style}), mimetype='application/json')


@bp.route('/deleteDomain', methods=['POST'])
@login_required
def deleteDomain():
    db = get_db()
    domainid = request.get_json()['domainid']
    check_access = db.execute(
        'SELECT projects.owner FROM projects INNER JOIN domains ON projects.id = domains.project WHERE domains.id = ?',
        (domainid, )
    ).fetchone()

    if not check_access or not domainid:
        return Response(json.dumps({"status": "not found"}), mimetype='application/json')
    if check_access['owner'] != session['username']:
        return Response(json.dumps({"status": "not found"}), mimetype='application/json')

    db.execute(
        'DELETE FROM domains WHERE id = ?',
        (domainid, )
    )

    db.commit()
    return Response(json.dumps({"status": "success"}), mimetype='application/json')

###########################################

###########################################


@bp.route('/addHost', methods=['POST'])
@login_required
def addHost():
    db = get_db()
    project = request.get_json()['project']
    ip = request.get_json()['ip'].strip()
    ports = request.get_json()['ports']

    check_access = db.execute(
        'SELECT * FROM projects WHERE owner = ? and id = ?',
        (session['username'], project, )
    ).fetchone()

    if not check_access or not ip or not ports or not project:
        return Response(json.dumps({"status": "not found"}), mimetype='application/json')

    hostCheck = db.execute(
        'SELECT * FROM hosts WHERE project = ? and ip = ?',
        (project, ip, )
    ).fetchone()

    if hostCheck is None:
        hostid = str(uuid.uuid4())
        portsq = 0
        db.execute(
            'INSERT INTO hosts (id, ip, note, style, portsq, project) VALUES (?, ?, ?, ?, ?, ?)',
            (hostid, ip, "", "New", portsq, project)
        )
    else:
        hostid = hostCheck['id']
        portsq = int(hostCheck['portsq'])
        db.execute(
            'UPDATE hosts SET style = ? WHERE id = ?',
            ("New", hostid)
        )

    for port in ports:
        p = port['port'].strip()

        portcheck = db.execute(
            'SELECT * FROM ports WHERE host = ? and port = ?',
            (hostid, p, )
        ).fetchone()

        state = "open"
        service = port['service']
        version = port['product']

        if p == "" or service == "":
            return Response(json.dumps({"status": "IP, port and service are required."}), mimetype='application/json')

        if portcheck is None:
            portsq = 1
            portid = str(uuid.uuid4())
            db.execute(
                'INSERT INTO ports (id, port, state, service, version, note, host) VALUES (?, ?, ?, ?, ?, ?, ?)',
                (portid, p, state, service, version, "", hostid)
            )
        else:
            db.execute(
                'UPDATE ports SET service = ?, version = ? WHERE id = ?',
                (service, version, portcheck['id'])
            )

    db.execute(
        'UPDATE hosts SET portsq = ? WHERE id = ?',
        (portsq, hostid)
    )

    db.commit()

    return Response(json.dumps({"status": "success"}), mimetype='application/json')


@bp.route('/addDomain', methods=['POST'])
@login_required
def addDomain():
    db = get_db()

    project = request.get_json()['project']
    domain = request.get_json()['domain']
    ip = request.get_json()['ip']

    check_access = db.execute(
        'SELECT * FROM projects WHERE owner = ? and id = ?',
        (session['username'], project, )
    ).fetchone()

    if not check_access or not domain or not ip:
        return Response(json.dumps({"status": "not found"}), mimetype='application/json')

    VALIDATEIP = "^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])$"
    VALIDATEDOMAIN = "^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])(\:([0-9]{1,4}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5]))?$"
    ipre = re.compile(VALIDATEIP)
    domainre = re.compile(VALIDATEDOMAIN)

    if not ipre.match(ip) or not domainre.match(domain):
        return Response(json.dumps({"status": "Validation error"}), mimetype='application/json')

    checkIfHostExists = db.execute(
        'SELECT * FROM hosts WHERE project = ? and ip = ?',
        (project, ip, )
    ).fetchone()

    if checkIfHostExists is None:
        hostid = str(uuid.uuid4())
        db.execute(
            'INSERT INTO hosts (id, ip, note, style, portsq, project) VALUES (?, ?, ?, ?, ?, ?)',
            (hostid, ip, "", "New", 0, project)
        )

    checkIfExists = db.execute(
        'SELECT * FROM domains WHERE project = ? and domain = ?',
        (project, domain, )
    ).fetchone()

    if checkIfExists is None:
        domainid = str(uuid.uuid4())
        ext = tldextract.extract(domain)
        lvl = ext[1] + "." + ext[2]
        db.execute(
            'INSERT INTO domains (id, domain, lvl, ip, note, style, project) VALUES (?, ?, ?, ?, ?, ?, ?)',
            (domainid, domain, lvl, ip, "", "New", project)
        )
    else:
        domainid = checkIfExists['id']
        db.execute(
            'UPDATE domains SET ip = ? WHERE id = ?',
            (ip, domainid)
        )

    db.commit()
    return Response(json.dumps({"status": "success"}), mimetype='application/json')


###########################################
@bp.route('/changepass', methods=['POST'])
@login_required
def changePass():
    db = get_db()
    oldpwd = request.get_json()['oldpwd']
    pwd = request.get_json()['pwd']
    pwdconfirm = request.get_json()['pwdconfirm']

    user = db.execute(
        'SELECT password FROM users WHERE username = ?',
        (session['username'], )
    ).fetchone()

    if not oldpwd or not pwd or not pwdconfirm:
        return Response(json.dumps({"status": "error", "msg": "All fields must be filled"}), mimetype='application/json')

    if not check_password_hash(user['password'], oldpwd):
        return Response(json.dumps({"status": "error", "msg": "Incorrect current password"}), mimetype='application/json')

    if pwd != pwdconfirm:
        return Response(json.dumps({"status": "error", "msg": "New passwords do not match"}), mimetype='application/json')

    db.execute(
        'UPDATE users SET password = ? WHERE username = ?',
        (generate_password_hash(pwd), session['username'], )
    )
    db.commit()

    return Response(json.dumps({"status": "success", "msg": "Password was successfully updated"}), mimetype='application/json')
###########################################


@bp.route('/delete', methods=['POST'])
@login_required
def delproject():
    db = get_db()
    projectid = request.get_json()['id']

    project = db.execute(
        'SELECT id, name FROM projects WHERE id = ? and owner = ?',
        (projectid, session['username'], )
    ).fetchone()

    if not project:
        return Response(json.dumps({"status": "not found"}), mimetype='application/json')

    delete(db, projectid)

    db.commit()
    return Response(json.dumps({"status": "success"}), mimetype='application/json')


@bp.route('/deleteuser', methods=['POST'])
@login_required
def deluser():
    db = get_db()

    projects = db.execute(
        'SELECT id FROM projects WHERE owner = ?',
        (session['username'], )
    ).fetchall()

    for project in projects:
        delete(db, project["id"])

    db.execute(
        'DELETE FROM users WHERE username = ?',
        (session['username'], )
    )

    session.clear()
    db.commit()
    return Response(json.dumps({"status": "success"}), mimetype='application/json')


def delete(db, projectid):
    hosts = db.execute(
        'SELECT * FROM hosts WHERE project = ?',
        (projectid,)
    ).fetchall()

    # delete ports
    for host in hosts:
        db.execute(
            'DELETE FROM ports WHERE host = ?',
            (host['id'], )
        )
    # delete hosts
    db.execute(
        'DELETE FROM hosts WHERE project = ?',
        (projectid, )
    )

    # delete domains
    db.execute(
        'DELETE FROM domains WHERE project = ?',
        (projectid, )
    )

    # delete cron
    db.execute(
        'DELETE FROM crontab WHERE project = ?',
        (projectid, )
    )

    # delete project
    db.execute(
        'DELETE FROM projects WHERE id = ?',
        (projectid, )
    )


@bp.route('/editName', methods=['POST'])
@login_required
def editName():
    db = get_db()
    projectid = request.get_json()['id']
    name = request.get_json()['name']

    project = db.execute(
        'SELECT id, name FROM projects WHERE id = ? and owner = ?',
        (projectid, session['username'], )
    ).fetchone()

    if not project:
        return Response(json.dumps({"status": "not found"}), mimetype='application/json')

    db.execute(
        'UPDATE projects SET name = ? WHERE id = ?',
        (name, projectid)
    )

    db.commit()

    return Response(json.dumps({"status": "success"}), mimetype='application/json')
###########################################


@bp.route('/subdomains', methods=['POST'])
@login_required
def subdomains():
    amass = current_app.config['AMASS']
    findomain = current_app.config['FINDOMAIN']

    if amass == "" or not os.path.isfile(amass):
        return Response(json.dumps({"status": "Invalid amass path"}), mimetype='application/json')

    if findomain == "" or not os.path.isfile(findomain):
        return Response(json.dumps({"status": "Invalid findomain path"}), mimetype='application/json')

    db = get_db()
    projectid = request.get_json()['id']
    domain = request.get_json()['domain']
    period = request.get_json()['period']

    project = db.execute(
        'SELECT id, name FROM projects WHERE id = ? and owner = ?',
        (projectid, session['username'], )
    ).fetchone()

    if not project:
        return Response(json.dumps({"status": "not found"}), mimetype='application/json')

    if domain == "" or period == "":
        return Response(json.dumps({"status": "validation error"}), mimetype='application/json')

    VALIDATEDOMAIN = "^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])(\:([0-9]{1,4}|[1-5][0-9]{4}|6[0-4][0-9]{3}|65[0-4][0-9]{2}|655[0-2][0-9]|6553[0-5]))?$"
    domainre = re.compile(VALIDATEDOMAIN)

    if not domainre.match(domain):
        return Response(json.dumps({"status": "validation error"}), mimetype='application/json')

    if period not in ["1", "2", "3", "4", "5"]:
        return Response(json.dumps({"status": "validation error"}), mimetype='application/json')

    taskid = str(uuid.uuid4())
    status = 1

    if period == "1":
        status = 0

    db.execute(
        'INSERT INTO crontab (id, domain, period, status, project) VALUES (?, ?, ?, ?, ?)',
        (taskid, domain, period, status, projectid)
    )

    db.commit()

    task = {}
    task['id'] = taskid
    task['project'] = projectid
    task['domain'] = domain
    tasks = [task]

    thread = Thread(target=run, args=(tasks,))
    thread.start()

    return Response(json.dumps({"status": "success"}), mimetype='application/json')


@bp.route('/deleteCron', methods=['POST'])
@login_required
def deleteCron():
    db = get_db()
    cronid = request.get_json()['cronid']
    check_access = db.execute(
        'SELECT projects.owner FROM projects INNER JOIN crontab ON projects.id = crontab.project WHERE crontab.id = ?',
        (cronid, )
    ).fetchone()

    if not check_access or not cronid:
        return Response(json.dumps({"status": "not found"}), mimetype='application/json')

    if check_access['owner'] != session['username']:
        return Response(json.dumps({"status": "not found"}), mimetype='application/json')

    db.execute(
        'DELETE FROM crontab WHERE id = ?',
        (cronid, )
    )

    db.commit()
    return Response(json.dumps({"status": "success"}), mimetype='application/json')


@bp.route('/statusCron', methods=['POST'])
@login_required
def statusCron():
    db = get_db()

    cronid = request.get_json()['cronid']
    status = request.get_json()['status']

    check_access = db.execute(
        'SELECT projects.owner FROM projects INNER JOIN crontab ON projects.id = crontab.project WHERE crontab.id = ?',
        (cronid, )
    ).fetchone()

    if not check_access or not cronid or not status:
        return Response(json.dumps({"status": "not found"}), mimetype='application/json')

    if check_access['owner'] != session['username']:
        return Response(json.dumps({"status": "not found"}), mimetype='application/json')

    if status not in ["1", "0"]:
        return Response(json.dumps({"status": "not found"}), mimetype='application/json')

    cron = db.execute(
        'SELECT * FROM crontab WHERE id = ?',
        (cronid, )
    ).fetchone()

    if cron['period'] == "1":
        return Response(json.dumps({"status": "not found"}), mimetype='application/json')

    db.execute(
        'UPDATE crontab SET status = ? WHERE id = ?',
        (int(status), cronid)
    )

    db.commit()
    return Response(json.dumps({"status": "success"}), mimetype='application/json')

###########################################


@bp.route('/masscan', methods=['POST'])
@login_required
def masscan():
    masscan = current_app.config['MASSCAN'].strip()
    if masscan == "" or not os.path.isfile(masscan):
        return Response(json.dumps({"status": "Invalid masscan path"}), mimetype='application/json')

    db = get_db()
    projectid = request.get_json()['id']
    ips = request.get_json()['ips'].strip()
    t = request.get_json()['type']

    project = db.execute(
        'SELECT id, name FROM projects WHERE id = ? and owner = ?',
        (projectid, session['username'], )
    ).fetchone()

    if not project:
        return Response(json.dumps({"status": "not found"}), mimetype='application/json')

    if t not in ["1", "2", "3"]:
        return Response(json.dumps({"status": "Validation error"}), mimetype='application/json')

    if t == "1":
        hosts = db.execute(
            'SELECT ip FROM hosts where project = ? and portsq = 0)',
            (projectid, )
        ).fetchall()
        ips = ",".join(map(lambda x: x['ip'], hosts))
    elif t == "2":
        hosts = db.execute(
            'SELECT ip FROM hosts WHERE project = ? ',
            (projectid, )
        ).fetchall()
        ips = ",".join(set(map(lambda x: x['ip'], hosts)))
    else:
        if not checkips(ips):
            return Response(json.dumps({"status": "Validation error"}), mimetype='application/json')

    thread = Thread(target=runMasscan, args=(project['id'], project['name'], ips, t, ))
    thread.start()
    return Response(json.dumps({"status": "success"}), mimetype='application/json')


@bp.route('/nmap', methods=['POST'])
@login_required
def nmap():
    nmap = current_app.config['NMAP'].strip()
    if nmap == "" or not os.path.isfile(nmap):
        return Response(json.dumps({"status": "Invalid nmap path"}), mimetype='application/json')

    db = get_db()
    projectid = request.get_json()['id']
    ips = request.get_json()['ips'].strip()
    t = request.get_json()['type']

    project = db.execute(
        'SELECT id, name FROM projects WHERE id = ? and owner = ?',
        (projectid, session['username'], )
    ).fetchone()

    if not project:
        return Response(json.dumps({"status": "not found"}), mimetype='application/json')

    if t not in ["1", "2", "3"]:
        return Response(json.dumps({"status": "Validation error"}), mimetype='application/json')

    if t == "1":
        hosts = db.execute(
            'SELECT ip FROM hosts where project = ? and portsq = 0',
            (projectid, )
        ).fetchall()
        ips = list(map(lambda x: x['ip'], hosts))
    elif t == "2":
        hosts = db.execute(
            'SELECT ip FROM hosts WHERE project = ?',
            (projectid, )
        ).fetchall()
        ips = list(set(map(lambda x: x['ip'], hosts)))
    else:
        if not checkips(ips):
            return Response(json.dumps({"status": "Validation error"}), mimetype='application/json')
        else:
            ips = ips.split(',')

    thread = Thread(target=runNmap, args=(project['id'], project['name'], ips, t, ))
    thread.start()
    return Response(json.dumps({"status": "success"}), mimetype='application/json')


def checkips(ips):
    VALIDATEIP = "^(([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])\.){3}([0-9]|[1-9][0-9]|1[0-9]{2}|2[0-4][0-9]|25[0-5])(\/([0-9]|[1-2][0-9]|3[0-2]))?$"
    ipre = re.compile(VALIDATEIP)

    for ip in ips.split(','):
        if not ipre.match(ip):
            return False

    return True
