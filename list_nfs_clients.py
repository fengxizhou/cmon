#!/usr/bin/env python
import subprocess
import datetime
import re
import sys

now = datetime.datetime.now()
format_str = '%Y%m%d'
log = open("/tmp/user_nfs_tasks.{}".format(now.strftime(format_str)), "a+")
log.write("++{}\n".format(now))

NodeRE = re.compile("node\d{4}")

def list_nfs_clients(nfs_server):
    cmd = ['ssh', nfs_server, 'netstat', '-e']
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
    out = p.communicate()[0].decode('utf-8')
    p.wait()
    lines = out.split('\n')
    formatter = "{:<8} {:>10} {:>10}\n"
    log.write(formatter.format('Node', 'recv_q', 'send_q'))
    buffer = []
    for line in lines[:]:
        items = line.split()
        if len(items) >= 7 and items[0] == 'tcp':
            port = items[3].split(':')[1]
            node =  items[4].split(':')[0].split('.')[0]
            recv_q = int(items[1])
            send_q = int(items[2])
            user = items[6]
            if port == 'nfs' and (recv_q > 0 or send_q > 0):
                buffer.append((node, recv_q, send_q))

    def take_sum(entry):
        return entry[1] + entry[2]

    buffer.sort(key=take_sum, reverse=True)
    for entry in buffer:
        log.write(formatter.format(entry[0], entry[1], entry[2]))

    def check_node(node):
        cmd = ['ssh', node, '/usr/local/hpc/system-scan/list_non_root_process.sh']
        #subprocess.call(['ssh', node, '/usr/local/hpc/system-scan/list_non_root_process.sh'])
        try:
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
            out = p.communicate()[0]
            p.wait()
            log.write(out)
        except:
            print('check_node {} failed: {}'.format(node, sys.exc_info()[:2]))

    n = 0
    for b in buffer:
        if b[1] + b[2] > 100000:
            n += 1

    for entry in buffer[:n]:
        node, recv_q, send_q = entry[0], entry[1], entry[2]
        # filter out corrupted node names
        if node.startswith(node):
            m = NodeRE.match(node)
            if m is None:
                continue

        log.write("==User processes on {}: recv_q={} send_q={}\n".format(node, recv_q, send_q))
        check_node(node)
        log.write('\n')


if __name__ == '__main__':

    for nfs_server in ['hpcxfs01', 'hpczfs02']:
        log.write("NFS Server: {}\n".format(nfs_server))
        list_nfs_clients(nfs_server)
        log.write('\n')

    log.close()
