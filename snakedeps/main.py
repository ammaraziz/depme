import argparse
import sys
from collections import defaultdict
from pathlib import Path

##############
#### Tools ###
##############

tools_lib = {

    # languages
    "R"          : ["R", "--version"],
    "perl"       : ["perl", "-v"],
    "python"     : ["python", "--version"],

    # mappers
    "bowtie2"    : ["bowtie2", "version"],
    "bwa"        : ["bwa", "mem"],

    # aligners
    "mafft"      : ["mafft", "--version"],
    "muscle"     : ["muscle", "--version"],
    "blast"      : ["blastn", "-version"],
    "irma"       : ["IRMA"],

    # trimmers
    "cutadapt"   : ["cutadapt", "--version"],

    # toolkits
    "seqkit"     : ["seqkit", "version"],
    "bcftools"   : ["bcftools", "version"],
    "bedtools"   : ["bedtools", "version"],
    "bbmap"      : ["bbversion.sh"],

    # nextstrain
    "nextclade" : ["nextclade", "--version"],
    "augur"      : ["augur", "--version"],

    # workflows
    "snakemake"  : ["snakemake", "--version"],
    "nextflow"   : ["nextflow", "-version"],
}

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

#################
### Functions ###
#################
import os
import sys
import re
import subprocess
from pathlib import Path
from signal import Signals
from textwrap import dedent, indent

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
    def __init__(self, cmd, *, raise_errors=True, print_error=False, extra_env=None):
        self.cmd = cmd
        self.raise_errors = raise_errors
        self.print_error = print_error
        self.extra_env = extra_env

    def run(self):
        try:
            self.invoke_command()
        except subprocess.CalledProcessError as error:
            if error.returncode == 1:
                return(True)
            else:
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

# def indentation(s, tabsize=4):
#     sx = s.expandtabs(tabsize)
#     return 0 if sx.isspace() else len(sx) - len(sx.lstrip())

def test_executable(tool: str) -> bool:
    """
    Test if tool exists.

    Return True if exists, else False
    """
    try:
        call = tools_lib[tool]
    except KeyError as e:
        return "Not tested"
    try:
        run_shell_command(" ".join(call))
        return "Installed"
    except Exception:
        return "Missing"
    
def pretty_print(tool_status: dict, type: str) -> None:
    """
    Pretty print to terminal the status of the tools 
    """
    
    print(f"\n{colors.UNDERLINE}{type} Dependencies{colors.ENDC}")
    for tool, status in tool_status.items():
        if status == 'Installed':
            col = colors.OKBLUE
        else:
            col = colors.WARNING
        print(f"{col:10s}{tool:10s} \t{status}{colors.ENDC}", file=sys.stdout)

def parse_file(filename: Path) -> list:
    """
    Parse text file, one line per deps
    """
    std_deps = []
    pip_deps = []

    with open(filename, "r") as file:
        for line in file:
            line = line.strip()
            std_deps.append(line)
    return(std_deps, pip_deps)

def count_indentation(string):
    spaces = len(string) - len(string.lstrip(' '))
    return spaces

# this needs to be refractored. It's a mess.
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
                    indent_amount = count_indentation(line)
                    # general clean up
                    line = line.strip().replace(" ", "").replace("    ", "")
                    line = line = re.sub(r"^-", "", line)

                    # pip_deps
                    if "pip" in line and indent_amount == 2:
                        for line in file:
                            if indent_amount == 2:
                                line = line.strip().replace(" ", "") # whitespace
                                line = line = re.sub(r"\t", "", line) # strip tab
                                line = line = re.sub(r"^-", "", line) # strip starting dash
                                if "=" in line:
                                    pos = line.index("=") 
                                    line = line[:pos] # skip version
                                if "pip:" in line:
                                    continue
                                pip_deps.append(line)

                    # std_deps
                    if "::" in line: # strip conda syntax
                        pos = line.index("::")
                        line = line[pos+2:]
                    # strip version
                    if "=" in line:
                        pos = line.index("=")
                        line = line[:pos]
                    std_deps.append(line)
                    
                    # detect and ignore r packages
                    # not implemented
                    # if "r-" in line:
                    #     
                    
    return(std_deps, pip_deps)

def test_pip(tool: str) -> bool:
    from importlib import util
    loader = util.find_spec(tool)

    if loader:
        return("Installed")
    else:
        return("Missing")

############
### Main ###
############

def run(args):
    """
    Run everything.
    If importing as a module, this is the entry point.

    import depme
    from argparse import Namespace
    depme.run(Namespace(ArgsGoHere))
    """
    
    tested_deps = defaultdict(dict)
    tested_pips = defaultdict(dict)

    if args.input:
        for dep in args.input:
            tested_deps[dep] = test_executable(dep)

    if args.file:
        # only std_deps are supported here
        std_deps, pip_deps = parse_file(args.file)
        for dep in std_deps:
            tested_deps[dep] = test_executable(dep)
    
    if args.yaml:
        std_deps, pip_deps = parse_yaml(args.yaml)
        for dep in std_deps:
            tested_deps[dep] = test_executable(dep)
        for dep in pip_deps:
            tested_pips[dep] = test_pip(dep)

    if "Missing" in tested_deps.values():
        missing = True
    else:
        missing = False

    pretty_print(tested_deps, type="Conda")
    pretty_print(tested_pips, type="Pip")

    if args.error and missing:
        print(f"\n{colors.WARNING}Testing complete - Missing dependencies detected.{colors.ENDC}")
        sys.exit(1)
    else:
        print(f"\n{colors.OKCYAN}Testing complete.{colors.ENDC}")

usage=f"""depme [-h] [-f FILE] [-y YAML] [-o OUTPUT] [-p] [-e] [input ...]

Examples:\n
    Terminal:\t depme snakemake nextflow mafft
    File:\t depme -f deps.txt
    Yaml:\t depme -y deps.yaml
    \t Add -o depsme.tsv to save output
    \t Add -p to print to terminal
    \t Use -e to disable returning exit status code 1 if any tool is missing 
"""

def main():
    parser = argparse.ArgumentParser(
        description="Test workflow dependencies. Enter the name of the tool",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
        prog="depme",
        usage=usage)

    parser.add_argument('input', nargs='*', 
                        help="Read from std input")
    parser.add_argument("-f", "--file", type=Path,
                        help="Read deps from .txt - one per line"),
    parser.add_argument("-y", "--yaml", type=Path,
                        help="Read deps from .yaml file - eg used in conda install.")
    parser.add_argument("-o", "--output", type=Path,
                        help="Write to file - output is tsv with headers")
    parser.add_argument("-p", "--pretty-print",
                        action="store_false",
                        default=True,
                        help="Pretty print to stdout?")
    parser.add_argument("-e", "--error",
                        action="store_false",
                        default=True,
                        help="Return error code if any dependency is missing.")
    args = parser.parse_args(args=None if sys.argv[1:] else ["--help"])
    
    # check if both positional and file inputs are provided 
    if args.input and args.yaml:
        print(usage)
        print(f"{colors.WARNING}Specify input from terminal OR from file. Can't not perform checks on both.{colors.ENDC}")
        sys.exit()

    # check at least one input is specified
    if not any([args.input, args.file, args.yaml]):
        print(usage)
        print(f"{colors.WARNING}Must specify one input type: terminal, file [-f] or yaml [-y].{colors.ENDC}")
        sys.exit()

    # check if files exist
    if args.file:
        if not args.file.is_file():
            print(f"{colors.WARNING}File not detected, check if it exists: {args.file}{colors.ENDC}")
            sys.exit()
    if args.yaml:
        if not args.yaml.is_file():
            print(f"{colors.WARNING}File not detected, check if it exists: {args.file}{colors.ENDC}")
            sys.exit()
    run(args)

if __name__ == "__main__":
    main()