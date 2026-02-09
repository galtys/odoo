#!/usr/bin/env python
import time
import os
import subprocess
import logging
import toml
import galtyslib
from optparse import OptionParser
logger = logging.getLogger("run_in_loop")
#logger = logging.getLogger()
logging.basicConfig(level=logging.INFO)
DBX='dev7'
from datetime import datetime

#logger.setLevel(logging.DEBUG)

parser = OptionParser()
parser.add_option("-d", "--pwd", dest="pwd",
                  help="Set current working path",default='')
parser.add_option("-p", "--period",
                  dest="period_hrs", default='0.01',
                  help="period [hrs]")
parser.add_option("-c", "--config-toml",
                  dest="config_toml", default='pjb.toml',
                  help="period [hrs]")
parser.add_option("-r", "--data-dir",
                  dest="data_dir", default='/home/jan/erp7',
                  help="data dir")

(options, args) = parser.parse_args()

cmd1 = "python allocated_qty.py %s"%DBX

if __name__ == '__main__':
    conf = toml.load(options.config_toml)
    dbx = args[0] #pjb_live or dev7
    erp7=conf['erp7'][dbx]
    dbname = erp7['database']
    server_path = erp7['server_path']
    config_file=erp7['config_file']
    logger.info(config_file)
    
    cnt = 0
    HOUR = 60*60*eval(options.period_hrs)

    if options.pwd:
        os.chdir(options.pwd)
    logger.info('START')
    
    ret=galtyslib.py_common.import_openerp7_server(server_path, config_file)
    from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
    PID=os.getpid()
    def epochtostr(t0):
        dto = datetime.fromtimestamp(t0)
        x=datetime.strftime(dto,DEFAULT_SERVER_DATETIME_FORMAT)
        return x
    while True:
        pool, cr, uid = galtyslib.py_common.get_connection(dbname)
        r_ids = pool.get('run.in.loop').search(cr,uid,[('state','=','running')])
        wait=HOUR
        for ril in pool.get('run.in.loop').browse(cr,uid,r_ids):
           t0=time.time()
           x=epochtostr(t0)
           cr.execute("update run_in_loop set last_run=%s, process_pid=%s where id=%s",
                      (x,PID,ril.id))
           logger.info(x)

           for item in ril.item_ids:
               x=epochtostr(time.time())
               cr.execute("update run_in_loop_item set last_run_hour=%s where id=%s",(x,item.id))
               cmd1 = 'python '+item.name+' '+item.args
               logger.info(cmd1)
               ret=subprocess.call(cmd1, shell=True)
               logger.info(str(ret))
               cr.execute("update run_in_loop_item set exit_code=%s where id=%s",(ret,item.id))
               
           t1=time.time()
           t = t1-t0

           if t<= HOUR:
               wait = HOUR - t
           else:
               wait = HOUR
           msg= "Time: %f minutes, Cnt: %d, wait: %d minutes"%(t/60., cnt, wait/60)

           x=epochtostr(t0+wait)
           cr.execute("update run_in_loop set next_run=%s where id=%s",
                      (x,ril.id))


           logger.info(msg)

           if cnt > (24):
               cnt=0
           else:
               cnt +=1 

        cr.commit()
        cr.close()

        time.sleep(wait)
