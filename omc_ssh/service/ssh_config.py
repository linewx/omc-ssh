from omc.config import settings


class SshConfigService:
    def __init__(self, config_file):
        self.config_file = config_file if config_file is not None else settings.SSH_CONFIG_FILE
        self.configs = {}

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







    def get(self, hostname):
        pass

    def print(self):
        print(self.configs)

if __name__ == '__main__':
    ssh_config = SshConfigService('/Users/luganlin/.ssh/config')
    ssh_config.load()
    ssh_config.print()





