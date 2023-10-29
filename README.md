# depme
Lazy detect dependencies for workflows like Snakemake and Nextflow

### Install

You can pip install this tool (no dependencies!):

```
Soon
```

Or pull the single python file (no dependencies!) directly from github:

```
soon
```

### Usage

`depme` can parse input from the terminal:

```
depme snakemake mafft minimap2
```

from a generic text file (one dependency per line):
```
depme -f deps.txt
```

from conda.yaml:
```
depme -y deps.yaml
```

as a module inside python script (eg in a snakemake pipeline):
```
from depme.main import run
from argparse import Namespace

packages = ['snakemake', 'mafft', 'minimap2']

args = Namespace(
    file=None, 
    yaml=None,
    output=None,
    pretty_print=True,
    error=True,
    input=packages,
    )
    
run(args)
```

pretty print the results to help end users:
```
depme -p snakemake mafft minimap2 

Conda Dependencies
     snakemake          Installed
     mafft              Missing
     minimap2           Not tested

Testing complete - Missing dependencies detected.
```

output to text file:
```
depme -p -o check.txt snakemake mafft minimap2 
```

return error code if any missing deps are detected:
```
depme -p -e -o check.txt snakemake mafft minimap2 
```

### Why

I wrote this tool to lazy test dependencies from `Conda`, `Pip`, `Rlang` without having to remember specific enchantation for each tool.

### How

For `pip` it's as simple as:

```
from importlib import util
util.find_spec('biopython')  
```

For `Rlang` get the full path to the module and check length:
```
nzchar(system.file(package = 'dplyr'))
```
There's more wrangling of R code, see the code for more details.

For external tools (eg `seqkit`) which are installed via `conda` (or other methods), `depme` has a python dict which it uses as to lookup how to check if the tool is installed. This usually amounts to running the tool with `--help` or `--version` then checking error code. 

If your favorite tool is returning `Not tested`, add it to the `tools_lib` dict in the `main.py` file. Alternatively, create a new issue.

### Citations:

1. Special thanks for the Nextstrain `augur` folks for developing in the open. The [command runner is from here](https://github.com/nextstrain/augur/blob/master/augur/io/shell_command_runner.py)
2. Originally I wrote a basic yaml parser but I was quickly overwhelmed by the complexity of edge cases. Luckily SO user `user16779014` was kind enough to share their solution which works very well.

Written on the train frantically in 40 minute bursts. 
