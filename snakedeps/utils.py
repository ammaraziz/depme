import os
import sys
import re
import subprocess
from pathlib import Path
from signal import Signals
from textwrap import dedent, indent

from tools_lib import tools_lib

try:
    from signal import SIGKILL
except ImportError:
    # A non-POSIX platform
    SIGKILL = None

def run_shell_command(cmd, raise_errors=True,  print_error=False, extra_env=None):
    """
    Run the given command string via Bash with error checking.
    Returns True if the command exits normally.  Returns False if the command
    exits with failure and "raise_errors" is False (the default).  When
    "raise_errors" is True, exceptions are rethrown.
    If an *extra_env* mapping is passed, the provided keys and values are
    overlayed onto the default subprocess environment.
    """
    return ShellCommandRunner(cmd, 
                              raise_errors=raise_errors, 
                              print_error=print_error, 
                              extra_env=extra_env).run()


class ShellCommandRunner:
    def __init__(self, cmd, *, raise_errors=False, print_error=False, extra_env=None):
        self.cmd = cmd
        self.raise_errors = raise_errors
        self.print_error = print_error
        self.extra_env = extra_env

    def run(self):
        try:
            self.invoke_command()
        except Exception as error:

            if self.print_error:
                self.print_error_message(error)

            if self.raise_errors:
                raise error
            return False

        return True

    def invoke_command(self):
        return subprocess.check_output(
            self.shell_executable + self.shell_args,
            shell=False,
            stderr=subprocess.STDOUT,
            env=self.modified_env,
        )

    @property
    def shell_executable(self):
        if os.name == "posix":
            return ["/bin/bash"]
        else:
            # We try best effort on other systems. For now that means nt/java.
            return ["env", "bash"]

    @property
    def shell_args(self):
        return ["-c", "set -euo pipefail; " + self.cmd]

    @property
    def modified_env(self):
        env = os.environ.copy()

        if self.extra_env:
            env.update(self.extra_env)

        return env

    def print_error_message(self, error):
        if isinstance(error, subprocess.CalledProcessError):
            signal = self.signal_from_error(error)

            if signal:
                message = f"Shell exited from fatal signal {signal.name} when running: {self.cmd}"
            else:
                message = f"Shell exited {error.returncode} when running: {self.cmd}"

            output = (error.output or b'').decode().strip("\n")

            if output:
                message += f"\nCommand output was:\n{indent(output, '  ')}"

            # Bash exits 127 when it cannot find a given command.
            if error.returncode == 127:
                message += "\nAre you sure this program is installed?"

            # Linux's oom-killer issues SIGKILLs to alleviate memory pressure
            elif signal is SIGKILL:
                message += f"\nThe OS may have terminated the command due to an out-of-memory condition."
        elif isinstance(error, FileNotFoundError):
            shell = " and ".join(self.shell_executable)

            message = f"""
                Unable to run shell commands using {shell}!
                Augur requires {shell} to be installed.  Please open an issue on GitHub
                <https://github.com/nextstrain/augur/issues/new> if you need assistance.
                """
        else:
            message = str(error)

        self.print_error(message)

    @staticmethod
    def print_error(message):
        """Prints message to STDERR formatted with textwrap.dedent"""
        print("\nERROR: " + dedent(message).lstrip("\n") + "\n", file=sys.stderr)

    @staticmethod
    def signal_from_error(error):
        """
        Return the :py:class:`signal.Signals` member for the
        :py:attr:`subprocess.CalledProcessError.returncode` of *error*, if any.
        """
        def signal(num):
            try:
                return Signals(num)
            except ValueError:
                return None

        # A grandchild process exited from a signal, which bubbled back up
        # through Bash as 128 + signal number.
        if error.returncode > 128:
            return signal(error.returncode - 128)

        # CalledProcessError documents that fatal signals for the direct child
        # process (bash in our case) are reported as negative exit codes.
        elif error.returncode < 0:
            return signal(abs(error.returncode))

        else:
            return None

class colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def test_executable(tool: str) -> bool:
    """
    Test if tool exists.

    Return True if exists, else False
    """

    call = tools_lib[tool]

    try:
        run_shell_command(" ".join(call))
        return True
    except Exception:
        return False
    
def pretty_print(tool_status: dict) -> None:
    """
    Pretty print to terminal the status of the tools 
    """
    
    print(f"\n{colors.UNDERLINE}Dependencies\n{colors.ENDC}")
    for tool, status in tool_status.items():
        if status == 'Missing':
            col = colors.WARNING
        if status == 'Installed':
            col = colors.OKBLUE
        print(f"{col}{tool}:\t{status}{colors.ENDC}", file=sys.stdout)
    print(file=sys.stdout)

def parse_yaml(filename: Path) -> list:
    """
    Parse yaml file, return list of dependencies
    """
    std_deps = []
    pip_deps = []
    with open(filename, "r") as file:
        for line in file:
            if "dependencies:" in line:
                for line in file:
                    # general clean up
                    line = line.strip().replace(" ", "")
                    line = line.strip().replace("    ", "")
                    line = line = re.sub(r"^-", "", line)
                    # pip_deps
                    if "pip" in line:
                        for line in file:
                            line = line.strip().replace(" ", "")
                            line = line = re.sub(r"\t", "", line)
                            line = line = re.sub(r"^-", "", line)
                            if "=" in line:
                                pos = line.index("=")
                                line = line[:pos]
                            pip_deps = line

                    # std_deps
                    # strip conda syntax
                    if "::" in line:
                        pos = line.index("::")
                        line = line[pos+2:]
                    # strip version
                    if "=" in line:
                        pos = line.index("=")
                        line = line[:pos]
                    std_deps.append(line)
    return(std_deps, pip_deps)

def test_pip(tool):
    import importlib
    loader = importlib.find_loader(tool)
    if loader:
        return(True)
    else:
        return(False)