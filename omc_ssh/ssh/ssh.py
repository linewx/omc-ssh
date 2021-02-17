import functools
import os
import argparse
from omc.common import CmdTaskMixin
from omc.config import settings
from omc.core import simple_completion
from omc.core.decorator import filecache
from omc.core.resource import Resource
from omc_ssh.service.ssh_config import SshConfigService


class Ssh(Resource, CmdTaskMixin):

    def _description(self):
        return 'SSH(Secure Shell) Smart Tool Set'

    @filecache(duration=60 * 60, file=Resource._get_cache_file_name)
    def _completion(self, short_mode=True):
        results = []
        results.append(super()._completion(True))
        if not self._have_resource_value():
            if not os.path.exists(settings.SSH_CONFIG_FILE):
                return

            ssh_hosts = []
            with open(settings.SSH_CONFIG_FILE) as f:
                for one_line in f.readlines():
                    try:
                        one_line = one_line.strip()
                        if one_line.startswith("Host "):
                            hostname = one_line.replace("Host", "").strip()
                            if hostname:
                                ssh_hosts.append(hostname)
                    except:
                        pass

            results.extend(ssh_hosts)
        return "\n".join(results)

    @simple_completion(['--dry-run'])
    def add(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--dry-run', action='store_true')
        args = parser.parse_args(self._get_action_params())
        ssh_host = self._get_one_resource_value()
        self._add_ssh_host(ssh_host)
        cmd = "ssh-copy-id %s" % ssh_host

        if args.dry_run:
            print(cmd)
        else:
            self.run_cmd(cmd)

    def _prompt(self, question, required=False, isBool=False, default=None):
        while True:
            result = input(question)
            if required and result:
                if isBool:
                    if result[0].lower() == 'y':
                        return True
                    elif result[0].lower() == 'n':
                        return False

                else:
                    return result

            elif required:
                # result is None
                if default is not None:
                    return default
                else:
                    continue
            else:
                # not required
                if isBool:
                    if result:
                        if default is not None:
                            return default
                    else:
                        if result[0].lower() == 'y':
                            return True
                        elif result[0].lower() == 'n':
                            return False

                else:
                    return result

    def _add_ssh_host(self, ssh_host):
        if ssh_host is None:
            raise Exception("hostname shouldn't be empty")

        ssh_config = {}
        hostconfig = SshConfigService.get_instance().get(ssh_host)
        if hostconfig is None:
            for one_config, required in SshConfigService.get_instance().config_keys:
                required = False
                result = self._prompt("Please input %s: " % one_config, required)
                if result:
                    ssh_config[one_config] = result
        else:
            print('the host %s has been added already!' % ssh_host)
            return

        ssh_config_item = SshConfigService.get_instance().format(ssh_host, ssh_config)
        print('ssh config:')
        print(ssh_config_item)
        confirmed = self._prompt("are you sure you want add ssh host as above? (y/n)", isBool=True, required=True, default=True)
        if not confirmed:
            return

        connected = SshConfigService.get_instance().test(ssh_host, ssh_config)
        if not connected:
            confirmed = self._prompt("the connection is refused, are you sure to add the ssh host anyway? (y/n)", isBool=True, required=True, default=False)
            if not confirmed:
                return

        SshConfigService.get_instance().add(ssh_host, ssh_config)

    def _run(self):
        ssh_host = self._get_one_resource_value()
        cmd = 'ssh %s' % ssh_host
        if '--dry-run' in self._get_resource_values():
            print(cmd)
        else:
            self.run_cmd(cmd)

    @simple_completion(['--dry-run'])
    def exec(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('cmd', nargs='*')
        args = parser.parse_args(self._get_action_params())

        ssh_host = self._get_one_resource_value()
        cmd = "ssh %s -C '%s'" % (ssh_host, " ".join(args.cmd))
        if args.dry_run:
            print(cmd)
        else:
            self.run_cmd(cmd)

    @simple_completion(['-r', '--local', '--remote', '--dry-run'])
    def upload(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-r', '--recursive', action='store_true')
        parser.add_argument('--local', nargs='?', help='local files')
        parser.add_argument('--remote', nargs='?', help='remote files')
        parser.add_argument('--dry-run', action='store_true')

        ssh_host = self._get_one_resource_value()

        args = parser.parse_args(self._get_action_params())
        cmd = "scp %s %s %s:%s" % ('-r' if args.recursive else '', args.local, ssh_host, args.remote)
        if args.dry_run:
            print(cmd)
        else:
            self.run_cmd(cmd)

    @simple_completion(['-r', '--local', '--remote', '--recursive', '--dry-run'])
    def download(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('-r', '--recursive', action='store_true')
        parser.add_argument('--local', nargs='?', help='local files')
        parser.add_argument('--remote', nargs='?', help='remote files')
        parser.add_argument('--dry-run', action='store_true')

        ssh_host = self._get_one_resource_value()

        args = parser.parse_args(self._get_action_params())
        cmd = "scp %s %s:%s %s" % ('-r' if args.recursive else '', ssh_host, args.remote, args.local)
        if args.dry_run:
            print(cmd)
        else:
            self.run_cmd(cmd)

    @simple_completion(['--local-port', '--remote-port', '--remote-host', '--dry-run'])
    def tunnel(self):
        tunnel_template = "ssh -nNT -L %(local_port)s:%(remote_host)s:%(remote_port)s %(bridge)s"
        bridge = self._get_one_resource_value()

        parser = argparse.ArgumentParser()
        parser.add_argument('--local-port', nargs='?', help='local port')
        parser.add_argument('--remote-port', nargs='?', help='remote port')
        parser.add_argument('--remote-host', nargs='?', help='remote host')
        parser.add_argument('--dry-run', action='store_true')

        args = parser.parse_args(self._get_action_params())
        cmd = tunnel_template % {
            'bridge': bridge,
            'local_port': args.local_port,
            'remote_port': args.remote_port,
            'remote_host': args.remote_host,
        }

        if args.dry_run:
            print(cmd)
        else:
            self.run_cmd(cmd)
