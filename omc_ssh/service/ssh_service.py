import logging
import os
from telnetlib import Telnet

import psutil
from omc.common import CmdTaskMixin
from omc.config import settings
from omc.core import console
from omc.utils import prompt


class SshService(CmdTaskMixin):
    _instance = None

    @classmethod
    def get_instance(cls, config_file=None):
        if cls._instance is None:
            cls._instance = SshService(config_file)

        return cls._instance

    def __init__(self, config_file=None):
        self.config_file = config_file if config_file is not None else settings.SSH_CONFIG_FILE
        self.configs = {}
        # required or not
        self.config_keys = [('HostName', True), ('User', True), ('Port', False), ('IdentityFile', False)]
        self.load()

    def load(self):
        current_name = None
        current_config = {}

        with open(self.config_file) as f:
            for one_line in f.readlines():
                stripped_line = one_line.strip()
                if stripped_line:
                    if stripped_line.startswith("Host "):
                        if current_name:
                            self.configs[current_name] = current_config

                        current_name = stripped_line.replace("Host", "").strip()
                        current_config = {}
                    else:
                        key, value = stripped_line.split(" ", 1)
                        current_config[key] = value

            if current_name:
                self.configs[current_name] = current_config

    def get(self, host):
        if host in self.configs:
            return self.configs.get(host)

    def print(self):
        console.log(self.configs)

    def format(self, hostname, config):
        if not hostname or not config:
            raise Exception("host or config is empty")

        result = []
        result.append('Host %s' % hostname)
        for one_key, key_required in self.config_keys:
            if one_key in config:
                result.append(("    %s %s") % (one_key, config.get(one_key)))

        return ("\n".join(result))

    def add(self, hostname, config):
        result = self.format(hostname, config)
        # console.log(result)
        with open(self.config_file, "a") as f:
            f.write('\n')
            f.write(result)
            f.write('\n')

    def test(self, hostname, config):
        host = config.get('HostName')
        port = int(config.get('Port') if config.get('Port') else '22')
        try:
            Telnet(host, port)
            return True
        except:
            return False

    def add_ssh_host(self, ssh_host):
        if ssh_host is None:
            raise Exception("hostname shouldn't be empty")

        ssh_config = {}
        hostconfig = self.get(ssh_host)
        if hostconfig is None:
            for one_config, required in self.config_keys:
                required = False
                result = prompt("Please input %s: " % one_config, required)
                if result:
                    ssh_config[one_config] = result
        else:
            console.log('the host %s has been added already!' % ssh_host)
            return

        ssh_config_item = self.format(ssh_host, ssh_config)
        console.log('ssh config:')
        console.log(ssh_config_item)
        confirmed = prompt("are you sure you want add ssh host as above? (y/n)", isBool=True, required=True,
                           default=True)
        if not confirmed:
            return

        connected = self.test(ssh_host, ssh_config)
        if not connected:
            confirmed = prompt("the connection is refused, are you sure to add the ssh host anyway? (y/n)", isBool=True,
                               required=True, default=False)
            if not confirmed:
                return

        self.add(ssh_host, ssh_config)

    def _socks_proxy(self, host, port):
        cmd = "ssh -fN -D %(port)s %(host)s" % locals()
        self.run_cmd(cmd)

    def _port_forward(self, local_port, remote_host, remote_port, ssh_proxy_host):
        port_forward_cmd = "ssh -nNT -L %(local_port)s:%(remote_host)s:%(remote_port)s %(ssh_proxy_host)s" % locals()
        self.run_cmd(port_forward_cmd)

    def find_process_by_port(self, port):
        for one_process in psutil.process_iter():
            try:
                for one_connection in one_process.connections(kind='inet'):
                    if one_connection.laddr.port == port:
                        return one_process.pid
            except:
                pass

    def start_socks_proxy(self, host, port):
        pid = self.find_process_by_port(port)
        if pid is not None:
            logging.info("shutdown previous proxy server firstly on port %s" % str(port))
            os.kill(pid, 9)
        self._socks_proxy(host, port)

    def stop_socks_proxy(self, host, port):
        pid = self.find_process_by_port(port)
        os.kill(pid, 9)

    def list_socks_proxies(self, host=None, port=None):
        results = []
        for one_process in psutil.process_iter():
            try:
                # match strict proxy pattern

                one_cmd = one_process.cmdline()
                if one_process.name() == 'ssh' and '-fN' in one_cmd and '-D' in one_cmd:
                    if host is not None and host != one_cmd[-1]:
                        continue

                    if port is not None and port != one_cmd[-2]:
                        continue

                    results.append({
                        'process': one_process,
                        'port': one_cmd[-2],
                        'host': one_cmd[-1],
                    })

            except:
                pass

        return results


if __name__ == '__main__':
    # ssh_config = SshService('/Users/luganlin/.ssh/config')
    # ssh_config.load()
    # hostname = 'test'
    # config = {
    #     'HostName': 'shc-sma-cd212.hpeswlab.net',
    #     'Port': '21',
    #     'User': 'root'
    # }
    # console.log(ssh_config.format(hostname, config))
    # console.log(ssh_config.test(hostname, config))

    ssh_config = SshService('/Users/luganlin/.ssh/config')
    ssh_config.start_socks_proxy('cd150', 7777)
    console.log(ssh_config.find_process_by_port(7777))
