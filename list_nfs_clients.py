      1 #!/usr/bin/env python
      2 import subprocess
      3 import datetime
      4 import re
      5 import sys
      6
      7 now = datetime.datetime.now()
      8 format_str = '%Y%m%d'
      9 log = open("/tmp/user_nfs_tasks.{}".format(now.strftime(format_str)), "a+")
     10 log.write("++{}\n".format(now))
     11
     12 NodeRE = re.compile("node\d{4}")
     13
     14 def list_nfs_clients(nfs_server):
     15     cmd = ['ssh', nfs_server, 'netstat', '-e']
     16     p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
     17     out = p.communicate()[0].decode('utf-8')
     18     p.wait()
     19     lines = out.split('\n')
     20     formatter = "{:<8} {:>10} {:>10}\n"
     21     log.write(formatter.format('Node', 'recv_q', 'send_q'))
     22     buffer = []
     23     for line in lines[:]:
     24         items = line.split()
     25         if len(items) >= 7 and items[0] == 'tcp':
     26             port = items[3].split(':')[1]
     27             node =  items[4].split(':')[0].split('.')[0]
     28             recv_q = int(items[1])
     29             send_q = int(items[2])
     30             user = items[6]
     31             if port == 'nfs' and (recv_q > 0 or send_q > 0):
     32                 buffer.append((node, recv_q, send_q))
     33
     34     def take_sum(entry):
     35         return entry[1] + entry[2]
     36
     37     buffer.sort(key=take_sum, reverse=True)
     38     for entry in buffer:
     39         log.write(formatter.format(entry[0], entry[1], entry[2]))
     40
     41     def check_node(node):
     42         cmd = ['ssh', node, '/usr/local/hpc/system-scan/list_non_root_process.sh']
     43         #subprocess.call(['ssh', node, '/usr/local/hpc/system-scan/list_non_root_process.sh'])
     44         try:
     45             p = subprocess.Popen(cmd, stdout=subprocess.PIPE)
     46             out = p.communicate()[0]
     47             p.wait()
     48             log.write(out)
     49         except:
     50             print('check_node {} failed: {}'.format(node, sys.exc_info()[:2]))
     51
     52     n = 0
     53     for b in buffer:
     54         if b[1] + b[2] > 100000:
     55             n += 1
     56
     57     for entry in buffer[:n]:
     58         node, recv_q, send_q = entry[0], entry[1], entry[2]
     59         # filter out corrupted node names
     60         if node.startswith(node):
     61             m = NodeRE.match(node)
     62             if m is None:
     63                 continue
     64
     65         log.write("==User processes on {}: recv_q={} send_q={}\n".format(node, recv_q, send_q))
     66         check_node(node)
     67         log.write('\n')
     68
     69
     70 if __name__ == '__main__':
     71
     72     for nfs_server in ['hpcxfs01', 'hpczfs01']:
     73         log.write("NFS Server: {}\n".format(nfs_server))
     74         list_nfs_clients(nfs_server)
     75         log.write('\n')
     76
     77     log.close()
