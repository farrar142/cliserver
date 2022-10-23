import asyncio
from io import BytesIO
import os
import re
import threading
import time
from select import select
from typing import Any, Dict, Optional, TypedDict, TypeVar

import paramiko
from paramiko.channel import ChannelFile
from typing_extensions import Self
from .tasks import send_ws_message


class HostInformation(TypedDict):
    hostname: str
    username: str
    password: str
    port: int


class ParamikoConnectInformation(TypedDict):
    self: Any
    cli: paramiko.SSHClient
    target: paramiko.Channel
    params: HostInformation


def ansi_decoder(context) -> str:
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', context)


class TimeoutChannel:

    def __init__(self, channel: paramiko.Channel, timeout):
        self.expired = False
        self.channel = channel
        self.timeout = timeout

    def __enter__(self):
        self.timer = threading.Timer(self.timeout, self.kill_client)
        self.timer.start()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("Exited Timeout. Timed out:", self.expired)
        self.timer.cancel()

        if exc_val:
            return False  # Make sure the exceptions are re-raised

        if self.expired:
            return True

    def kill_client(self):
        self.expired = True
        print("Should kill client")
        if self.channel:
            print("We have a channel")


class CliBase:
    cli: paramiko.SSHClient
    target: paramiko.Channel

    @classmethod
    def get_or_connect(cls):
        raise Exception("override this")

    def close(self):
        self.target.close()
        self.cli.close()

    def connect(self, info: dict):
        self.cli.connect(**info)

    def send(self, cmd):
        self.target.send(cmd+"\n")

    def receive(self, bool=True):
        time.sleep(0.02)  # 기본대기시간
        while True:
            if self.target.recv_ready():
                time.sleep(0.06)  # 기본대기시간
                break
            else:
                time.sleep(0.5)
        result = self.target.recv(65536).decode('utf-8')
        result = ansi_decoder(result)
        return result


class CliInterface(CliBase):
    instances: Dict[int, Self] = {}

    @classmethod
    def get_or_connect(cls, user_id: int, params: HostInformation):
        instance = cls.instances.get(user_id)
        if not instance:
            return cls(user_id, params)
        return instance

    def __init__(self, user_id: int, params: HostInformation):
        self.user_id = user_id
        self.cli = paramiko.SSHClient()
        self.cli.load_system_host_keys
        self.cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.cli.connect(**params, timeout=3, allow_agent=False)  # 여기까지
        self.target = self.cli.invoke_shell()
        self.target.settimeout(10)
        self.stdin = self.target.makefile('wb')
        self.stdout = self.target.makefile('r')

    def exec_command(self, command: str):
        channel = self.target
        with TimeoutChannel(self.target, 5):
            # print(channel.recv(2048).decode())
            channel.send(f"{command}\n".encode())
            res = line_buffered(self.target)
            for i in res:
                send_ws_message.delay(1, {
                    'type': 'emit',
                    "order": "order",
                    "username": "username",
                    "data": i
                })
        print("exit exec command")
        # with TimeoutChannel(self.cli, 3) as c:
        #     res = c.exec(
        #         command)    # non-blocking
        #     if not res:
        #         return 0
        #     ssh_stdin, ssh_stdout, ssh_stderr = res
        #     # block til done, will complete quickly
        #     exit_status = ssh_stdout.channel.recv_exit_status()
        #     yield ssh_stdout.read().decode("utf8")

    def execute(self, cmd):
        """

        :param cmd: the command to be executed on the remote computer
        :examples:  execute('ls')
                    execute('finger')
                    execute('cd folder_name')
        """
        cmd = cmd.strip('\n')
        self.stdin.write(cmd + '\n')
        finish = 'end of stdOUT buffer. finished with exit status'
        echo_cmd = 'echo {} $?'.format(finish)
        self.stdin.write(echo_cmd + '\n')
        shin = self.stdin
        self.stdin.flush()

        shout = []
        sherr = []
        exit_status = 0
        for line in self.stdout:
            if str(line).startswith(cmd) or str(line).startswith(echo_cmd):
                # up for now filled with shell junk from stdin
                shout = []
            elif str(line).startswith(finish):
                # our finish command ends with the exit status
                exit_status = int(str(line).rsplit(maxsplit=1)[1])
                if exit_status:
                    # stderr is combined with stdout.
                    # thus, swap sherr with shout in a case of failure.
                    sherr = shout
                    shout = []
                break
            else:
                # get rid of 'coloring and formatting' special characters
                shout.append(re.compile(
                    r'(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]').sub('', line).replace('\b', '').replace('\r', ''))

        # first and last lines of shout/sherr contain a prompt
        if shout and echo_cmd in shout[-1]:
            shout.pop()
        if shout and cmd in shout[0]:
            shout.pop(0)
        if sherr and echo_cmd in sherr[-1]:
            sherr.pop()
        if sherr and cmd in sherr[0]:
            sherr.pop(0)

        return shin, shout, sherr

    def run(self):
        while True:
            cmd = input("입력) ")
            if cmd == "exit":
                return
            self.send(cmd)
            self.receive(True)

    def single_order(self, cmd):
        self.send(cmd)
        return self.receive(True)

    #커스텀 로직들#

    def ls_al(self, *args):
        context = self.custom_order("ls -al")
        result = []
        for i in context:
            cur = i.split(" ")  # 나누기
            cur = ' '.join(cur).split()  # 공백지우기
            if len(cur) == 9:
                if cur[0].startswith('-'):
                    result.append(["file", cur[-1]])
                elif cur[0].startswith('d'):
                    result.append(["dir", cur[-1]])

        # [print(i) for i in result]
        return result

    def cd(self, path):
        self.send("cd "+path)
        # self.receive()

    #커스텀 로직 끝#
    def custom_order(self, cmd):
        self.send(cmd)
        context = self.receive(False)
        context = context.splitlines()
        return context

    def custom_cmd(self, cmd, *args):
        return getattr(self, cmd)(*args)

    @classmethod
    def from_api(cls, user_id: int, hostname: str, username: str, password: str, port: int = 22, *args, **kwargs):
        setting: HostInformation = {
            "hostname": hostname,
            "username": username,
            "password": password,
            "port": port
        }
        # print(setting)
        instance = CliInterface.get_or_connect(user_id, setting)
        return instance
        # test.receive()
        # test.custom_cmd("cd", directory)
        # files = test.custom_cmd("ls_al")
        # test.close()
        # return {"files": files}


# async def main():
#     #     setting = {
#     #         "hostname": "49.50.174.121",
#     #         "username": "root",
#     #         "password": "eowjsrhkddurtlehdrneowjsfh304qjsrlf28"
#     #     }
#     #     # test = CliInterface()
#     #     # test.get_or_connect(setting)
#     #     # test.receive()
#     #     # # test.run()
#     #     # test.custom_cmd("cd", "/home/test")
#     #     # test.custom_cmd("ls_al")
#     CliInterface().from_api("49.50.174.121", "root",
#                             "eowjsrhkddurtlehdrneowjsfh304qjsrlf28", "/home/test")
# asyncio.run(main())
def line_buffered(f: paramiko.Channel):
    line_buf = ""
    while not f.exit_status_ready():
        try:
            line_buf += f.recv(1).decode()  # .read(1).decode()
            if line_buf.endswith('\n'):
                yield line_buf
                line_buf = ''

        except StopIteration:
            print("stop iter")
            break
