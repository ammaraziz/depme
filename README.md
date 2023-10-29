# depme
Lazy detect dependencies for workflows like Snakemake and Nextflow

### Install

You can pip install this tool (no dependencies!):

```
Soon
```

or pull the single python file (no dependencies!) directly from github:

```
curl https://raw.githubusercontent.com/ammaraziz/depme/main/depme/main.py > depme.py
python depme.py
```
or from github:

```
git clone https://github.com/ammaraziz/depme
cd depme && pip install .
depme -h
```

### Usage

`depme` can parse input from the terminal:

```
# !note! only tools are supported for this input - no python/R packages
depme snakemake mafft minimap2
```

from a generic text file (one dependency per line):
```
# !note! only tools are supported for this input - no python/R packages
depme -f deps.txt
```

from conda.yaml:
```
# preferred input method
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

Managing external dependencies can be a nightmare. Below are details on how `depme` detects dependencies.

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

For external tools (eg `seqkit`) which are installed via `conda` (or other methods), `depme` has a python dict which it uses are a lookup table for running tool specific commands. This usually amounts to `[tool] --help` or `[tool] --version` then checking bash status code. 

If your favorite tool is returning `Not tested`, add it to the `tools_lib` dict in the `main.py` file. Alternatively, create a new issue.

### Citations:

1. Special thanks for the `Nextstrain` folks for coding and developing in the open. The `augur` repository has been a huge boon to my productivity and coding skills. The [command runner is from here](https://github.com/nextstrain/augur/blob/master/augur/io/shell_command_runner.py)
2. Originally I wrote a basic yaml parser but I was quickly overwhelmed by the complexity of edge cases. Luckily SO user `user16779014` was kind enough to share their solution which works very well.

Written on the train frantically in 40 minute bursts. 
