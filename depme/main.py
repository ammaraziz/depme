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
    "r-base"     : ["R", "--version"],
    "perl"       : ["perl", "-v"],
    "python"     : ["python", "--version"],
    # rust
    # go
    # java

    # mappers
    "bowtie2"    : ["bowtie2", "version"],
    "bwa"        : ["bwa", "mem"],
    #minimap2

    # aligners
    "mafft"      : ["mafft", "--version"],
    "muscle"     : ["muscle", "--version"],
    "blast"      : ["blastn", "-version"],
    "irma"       : ["IRMA"],

    # trimmers
    "cutadapt"   : ["cutadapt", "--version"],
    #trimmomatic
    #fastp

    # toolkits
    "seqkit"     : ["seqkit", "version"],
    "bcftools"   : ["bcftools", "version"],
    "bedtools"   : ["bedtools", "version"],
    "bbmap"      : ["bbversion.sh"],

    # nextstrain <3
    "nextclade" : ["nextclade", "--version"],
    "augur"      : ["augur", "--version"],
    # auspice
    # nextstrain

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
import subprocess
from pathlib import Path
from textwrap import dedent, indent

try:
    from signal import SIGKILL
except ImportError:
    # A non-POSIX platform
    SIGKILL = None

def run_shell_command(cmd, raise_errors=True, extra_env=None): # print_error=False
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
                              #print_error=print_error, 
                              extra_env=extra_env).run()


class ShellCommandRunner:
    def __init__(self, cmd, *, raise_errors=True, extra_env=None): # print_error=False
        self.cmd = cmd
        self.raise_errors = raise_errors
        #self.print_error = print_error
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

    # @staticmethod
    # def print_error(message):
    #     """Prints message to STDERR formatted with textwrap.dedent"""
    #     print("\nERROR: " + dedent(message).lstrip("\n") + "\n", file=sys.stderr)

    # @staticmethod
    # def signal_from_error(error):
    #     """
    #     Return the :py:class:`signal.Signals` member for the
    #     :py:attr:`subprocess.CalledProcessError.returncode` of *error*, if any.
    #     """
    #     def signal(num):
    #         try:
    #             return Signals(num)
    #         except ValueError:
    #             return None

    #     # A grandchild process exited from a signal, which bubbled back up
    #     # through Bash as 128 + signal number.
    #     if error.returncode > 128:
    #         return signal(error.returncode - 128)

    #     # CalledProcessError documents that fatal signals for the direct child
    #     # process (bash in our case) are reported as negative exit codes.
    #     elif error.returncode < 0:
    #         return signal(abs(error.returncode))

    #     else:
    #         return None

def test_executable(tool: str) -> bool:
    """
    Test if tool exists.

    Return True if exists, else False
    """
    # drop version
    if "=" in tool:
        pos = tool.index("=") 
        tool = tool[:pos] 

    try:
        call = tools_lib[tool]
    except KeyError as e:
        return "Not tested"
    try:
        run_shell_command(" ".join(call))
        return "Installed"
    except Exception:
        return "Missing"

def test_pip(tool: str) -> bool:
    from importlib import util

    # skip version
    if "=" in tool:
        pos = tool.index("=") 
        tool = tool[:pos] 

    loader = util.find_spec(tool)

    if loader:
        return("Installed")
    else:
        return("Missing")

def test_r(r_packages: list) -> list[bool]:
    '''
    Function to test R deps.
    Runs R with a function that checks if R can find the path to the package
    Tests all the packages in a single call to subprocess

    Returns a list of string values (Missing or Installed), one for each package
    '''
    # clean up package names
    r_packages = [package.replace("r-", "") for package in r_packages]
    # form array string for R to handle inputs
    r_packages = "'" + "', '".join(r_packages) + "'"
    call = [
        "echo",
        "\"is_inst = function(dependencies) {nzchar(system.file(package = dependencies))};",
        f"rdeps = c({r_packages});", # rdeps = c("dplyr", "lattice")
        "cat(unlist(lapply(rdeps, is_inst)), sep=" ", file=stdout());",
        "\"| R --slave"
    ]
    # output is bytes of bool eg b'FALSE TRUE FALSE'
    call_output = subprocess.check_output(" ".join(call), shell=True).decode("utf-8")
    
    bool_of_packages = []
    for b in call_output.split(" "):
        if b == "TRUE":
            bool_of_packages.append("Installed")
        else:
            bool_of_packages.append("Missing")    

    return(bool_of_packages)

def pretty_print(tested_tools: dict, type: str, pp: bool) -> None:
    """
    Pretty print to terminal the status of the tools 
    """
    if pp:
        print(f"\n{colors.UNDERLINE}{type} Dependencies{colors.ENDC}")
        if tested_tools:
            for tool, status in tested_tools.items():
                if status == 'Installed':
                    col = colors.OKBLUE
                else:
                    col = colors.WARNING
                print(f"{col:10s}{tool:10s} \t{status}{colors.ENDC}", file=sys.stdout)
        else:
            print(f"{colors.WARNING:10s}{tool:10s} \t{status}{colors.ENDC}", file=sys.stdout)
    else:
        pass

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

def write_results(filename: Path, 
                tested_deps: list, 
                tested_pip: list, 
                tested_r: list) -> None:
    '''
    Write out status of tested tools
    '''
    all_tests = {**tested_deps, **tested_pip, **tested_r}
    with open(filename, "w") as outfile:
        for key, value in all_tests.items():
            outfile.write(f"{key}\t{value}\n")

# def count_indentation(string):
#     spaces = len(string) - len(string.lstrip(' '))
#     return spaces

# functions related to yaml parsing
# this needs to be refractored. It's a mess.
# def parse_yaml(filename: Path) -> list:
#     """
#     Parse yaml file, return list of dependencies
#     """
#     std_deps = []
#     pip_deps = []

#     with open(filename, "r") as file:
#         for line in file:
#             if "dependencies:" in line:
#                 for line in file:
#                     indent_amount = count_indentation(line)
#                     # general clean up
#                     line = line.strip().replace(" ", "").replace("    ", "")
#                     line = line = re.sub(r"^-", "", line)

#                     # pip_deps
#                     if "pip" in line and indent_amount == 2:
#                         for line in file:
#                             if indent_amount == 2:
#                                 line = line.strip().replace(" ", "") # whitespace
#                                 line = line = re.sub(r"\t", "", line) # strip tab
#                                 line = line = re.sub(r"^-", "", line) # strip starting dash
#                                 if "=" in line:
#                                     pos = line.index("=") 
#                                     line = line[:pos] # skip version
#                                 if "pip:" in line:
#                                     continue
#                                 pip_deps.append(line)

#                     # std_deps
#                     if "::" in line: # strip conda syntax
#                         pos = line.index("::")
#                         line = line[pos+2:]
#                     # strip version
#                     if "=" in line:
#                         pos = line.index("=")
#                         line = line[:pos]
#                     std_deps.append(line)
                    
#                     # detect and ignore r packages
#                     # not implemented
#                     # if "r-" in line:
#                     #     
                    
#     return(std_deps, pip_deps)
def strip(string: str) -> str:
    return(string.replace("- ", "").replace(":", ""))

def detect_r_deps(string: str) -> str:
    if "r-" in string:
        return True

def is_float(string: str) -> bool:
    try:
        float(string)
        return True
    except ValueError:
        return False

def is_integer(string: str) -> bool:
    try:
        int(string)
        return True
    except ValueError:
        return False

def load(path: str) -> dict:
    '''
    Parse yaml file into a nested dict.
    From https://stackoverflow.com/a/71560949/8536677
    '''
    with open(path, "r") as yaml:
        levels = []
        data = {}
        indentation_str = ""

        for line in yaml.readlines():
            if line.replace(line.lstrip(), "") != "" and indentation_str == "":
                indentation_str = line.replace(line.lstrip(), "").rstrip("\n")
            if line.strip() == "":
                continue
            elif line.rstrip()[-1] == ":":
                key = line.strip()[:-1]
                quoteless = (
                    is_float(key)
                    or is_integer(key)
                    or key == "True"
                    or key == "False"
                    or ("[" in key and "]" in key)
                )

                if len(line.replace(line.strip(), "")) // 2 < len(levels):
                    if quoteless:
                        levels[len(line.replace(line.strip(), "")) // 2] = f"[{key}]"
                    else:
                        levels[len(line.replace(line.strip(), "")) // 2] = f"['{key}']"
                else:
                    if quoteless:
                        levels.append(f"[{line.strip()[:-1]}]")
                    else:
                        levels.append(f"['{line.strip()[:-1]}']")
                if quoteless:
                    exec(
                        f"data{''.join(str(i) for i in levels[:line.replace(line.lstrip(), '').count(indentation_str) if indentation_str != '' else 0])}[{key}]"
                        + " = {}"
                    )
                else:
                    exec(
                        f"data{''.join(str(i) for i in levels[:line.replace(line.lstrip(), '').count(indentation_str) if indentation_str != '' else 0])}['{key}']"
                        + " = {}"
                    )

                continue

            key = line.split(":")[0].strip()
            value = ":".join(line.split(":")[1:]).strip()

            if (
                is_float(value)
                or is_integer(value)
                or value == "True"
                or value == "False"
                or ("[" in value and "]" in value)
            ):
                if (
                    is_float(key)
                    or is_integer(key)
                    or key == "True"
                    or key == "False"
                    or ("[" in key and "]" in key)
                ):
                    exec(
                        f"data{'' if line == line.strip() else ''.join(str(i) for i in levels[:line.replace(line.lstrip(), '').count(indentation_str) if indentation_str != '' else 0])}[{key}] = {value}"
                    )
                else:
                    exec(
                        f"data{'' if line == line.strip() else ''.join(str(i) for i in levels[:line.replace(line.lstrip(), '').count(indentation_str) if indentation_str != '' else 0])}['{key}'] = {value}"
                    )
            else:
                if (
                    is_float(key)
                    or is_integer(key)
                    or key == "True"
                    or key == "False"
                    or ("[" in key and "]" in key)
                ):
                    exec(
                        f"data{'' if line == line.strip() else ''.join(str(i) for i in levels[:line.replace(line.lstrip(), '').count(indentation_str) if indentation_str != '' else 0])}[{key}] = '{value}'"
                    )
                else:
                    exec(
                        f"data{'' if line == line.strip() else ''.join(str(i) for i in levels[:line.replace(line.lstrip(), '').count(indentation_str) if indentation_str != '' else 0])}['{key}'] = '{value}'"
                    )
    return data

def loads(yaml: str) -> dict:
    levels = []
    data = {}
    indentation_str = ""

    for line in yaml.split("\n"):
        if line.replace(line.lstrip(), "") != "" and indentation_str == "":
            indentation_str = line.replace(line.lstrip(), "")
        if line.strip() == "":
            continue
        elif line.rstrip()[-1] == ":":
            key = line.strip()[:-1]
            quoteless = (
                is_float(key)
                or is_integer(key)
                or key == "True"
                or key == "False"
                or ("[" in key and "]" in key)
            )

            if len(line.replace(line.strip(), "")) // 2 < len(levels):
                if quoteless:
                    levels[len(line.replace(line.strip(), "")) // 2] = f"[{key}]"
                else:
                    levels[len(line.replace(line.strip(), "")) // 2] = f"['{key}']"
            else:
                if quoteless:
                    levels.append(f"[{line.strip()[:-1]}]")
                else:
                    levels.append(f"['{line.strip()[:-1]}']")
            if quoteless:
                exec(
                    f"data{''.join(str(i) for i in levels[:line.replace(line.lstrip(), '').count(indentation_str) if indentation_str != '' else 0])}[{key}]"
                    + " = {}"
                )
            else:
                exec(
                    f"data{''.join(str(i) for i in levels[:line.replace(line.lstrip(), '').count(indentation_str) if indentation_str != '' else 0])}['{key}']"
                    + " = {}"
                )

            continue

        key = line.split(":")[0].strip()
        value = ":".join(line.split(":")[1:]).strip()

        if (
            is_float(value)
            or is_integer(value)
            or value == "True"
            or value == "False"
            or ("[" in value and "]" in value)
        ):
            if (
                is_float(key)
                or is_integer(key)
                or key == "True"
                or key == "False"
                or ("[" in key and "]" in key)
            ):
                exec(
                    f"data{'' if line == line.strip() else ''.join(str(i) for i in levels[:line.replace(line.lstrip(), '').count(indentation_str) if indentation_str != '' else 0])}[{key}] = {value}"
                )
            else:
                exec(
                    f"data{'' if line == line.strip() else ''.join(str(i) for i in levels[:line.replace(line.lstrip(), '').count(indentation_str) if indentation_str != '' else 0])}['{key}'] = {value}"
                )
        else:
            if (
                is_float(key)
                or is_integer(key)
                or key == "True"
                or key == "False"
                or ("[" in key and "]" in key)
            ):
                exec(
                    f"data{'' if line == line.strip() else ''.join(str(i) for i in levels[:line.replace(line.lstrip(), '').count(indentation_str) if indentation_str != '' else 0])}[{key}] = '{value}'"
                )
            else:
                exec(
                    f"data{'' if line == line.strip() else ''.join(str(i) for i in levels[:line.replace(line.lstrip(), '').count(indentation_str) if indentation_str != '' else 0])}['{key}'] = '{value}'"
                )

    return data

def dumps(yaml: dict, indent="") -> str:
    """A procedure which converts the dictionary passed to the procedure into it's yaml equivalent.

    Args:
        yaml (dict): The dictionary to be converted.

    Returns:
        data (str): The dictionary in yaml form.

    From https://stackoverflow.com/a/71560949/8536677
    """

    data = ""

    for key in yaml.keys():
        if type(yaml[key]) == dict:
            data += f"\n{indent}{key}:\n"
            data += dumps(yaml[key], f"{indent}  ")
        else:
            data += f"{indent}{key}: {yaml[key]}\n"

    return data

def parse_yaml2(yaml: str) -> dict:
    try:
        yamldict = load(yaml)
    except Exception as e:
        print(f"{colors.WARNING}There was an issue parsing the conda.yaml file. Error: {e}{colors.ENDC}")
        sys.exit()

    # get pip deps
    try:
        pip = yamldict['dependencies'].pop('pip')
    except KeyError as e:
        pass

    std_deps = []
    pip_deps = []
    r_deps = []

    # for main yaml
    for section,dictionary in yamldict.items():
        if "dependencies" in section:
            for dep,extra in dictionary.items():
                # if channel has been specified, the dep is in the 'extra'
                if extra:
                    # check if extra is R package
                    if detect_r_deps(extra):
                        r_deps.append(strip(extra))
                    else:
                        std_deps.append(strip(extra))
                # no channel specified
                else:
                    # check if R package
                    if detect_r_deps(dep):
                        r_deps.append(strip(dep))
                    else:
                        std_deps.append(strip(dep))
    # for pip:
    if pip:
        for key,value in pip.items():
            pip_deps.append(strip(key))

    return(std_deps, pip_deps, r_deps)

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
    tested_rlang = defaultdict(dict)

    if args.input:
        for dep in args.input:
            tested_deps[dep] = test_executable(dep)
        pretty_print(tested_deps, type="Conda", pp=args.pretty_print)

    if args.file:
        # only std_deps are supported here
        std_deps, pip_deps = parse_file(args.file)
        for dep in std_deps:
            tested_deps[dep] = test_executable(dep)
        pretty_print(tested_deps, type="Conda", pp=args.pretty_print)

    if args.yaml:
        std_deps, pip_deps, r_deps = parse_yaml2(args.yaml)
        if std_deps:
            for dep in std_deps:
                tested_deps[dep] = test_executable(dep)
            pretty_print(tested_deps, type="Conda", pp=args.pretty_print)
        if pip_deps:
            for dep in pip_deps:
                tested_pips[dep] = test_pip(dep)
            pretty_print(tested_pips, type="Pip", pp=args.pretty_print)
        if r_deps:
            status_of_packages = test_r(r_deps)
            for status,dep in zip(status_of_packages, r_deps):
                tested_rlang[dep] = status 
            pretty_print(tested_rlang, type="Rlang", pp=args.pretty_print)

    # output deps to file
    if args.output:
        write_results(args.output, tested_deps, tested_pips, tested_rlang)

    if "Missing" in tested_deps.values():
        print(f"\n{colors.WARNING}Testing complete - Missing dependencies detected.{colors.ENDC}")
        if args.error:
            sys.exit(1)
        else:
            sys.exit(0)
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
                        default=False,
                        help="Pretty print to stdout?")
    parser.add_argument("-e", "--error",
                        action="store_false",
                        default=False,
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