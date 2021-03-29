import subprocess
import logging
import shlex

logger = logging.getLogger()


def run_process_on_host(cmd, timeout=60):
    logger.info('Executing command on remote host: {}'.format(cmd))
    p = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        std_out, std_err = p.communicate(timeout=timeout)
        rc = p.returncode
    except subprocess.TimeoutExpired:
        logger.debug('Process is not responding. Sending SIGKILL.')
        p.kill()
        std_out, std_err = p.communicate()
        rc = p.returncode
        output = str(std_out.decode('utf-8') or '')
        error = str(std_err.decode('utf-8') or '')
    logger.debug('process:%s\n'
                 'rc:%s,\n'
                 'std_out:%s\n'
                 'std_err:%s', p.args, rc, std_out, std_err)

    logger.info('Command_finished execution.')
    return std_out, std_err, rc