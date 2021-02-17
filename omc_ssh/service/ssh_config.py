from telnetlib import Telnet

from omc.config import settings
from omc.utils import prompt


class SshConfigService:
    _instance = None

    @classmethod
    def get_instance(cls, config_file=None):
        if cls._instance is None:
            cls._instance = SshConfigService(config_file)

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
        print(self.configs)

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
        #print(result)
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
            print('the host %s has been added already!' % ssh_host)
            return

        ssh_config_item = self.format(ssh_host, ssh_config)
        print('ssh config:')
        print(ssh_config_item)
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


if __name__ == '__main__':
    ssh_config = SshConfigService('/Users/luganlin/.ssh/config')
    ssh_config.load()
    hostname = 'test'
    config = {
        'HostName': 'shc-sma-cd212.hpeswlab.net',
        'Port': '21',
        'User': 'root'
    }
    print(ssh_config.format(hostname, config))
    print(ssh_config.test(hostname, config))
