import utils
from utils import colors
import argparse
import sys

def register_arguments():
    parser = argparse.ArgumentParser(
        description="Snakedeps - Test dependencies",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument('input', nargs='*', 
                        help="Read from std input")
    parser.add_argument("-f", "--file",
                        help="Read deps from .txt - one per line"),
    parser.add_argument("-y", "--yaml",
                        help="Read deps from .yaml file - eg used in conda install.")

    return(parser.parse_args())

def main():
    args = register_arguments()
    # check if both positional and file inputs are provided 
    # return helpful message
    if len(args.input) > 1 and args.file or args.yaml:
        print(f"{colors.WARNING}Specify either from terminal or from file. Can't not perform checks on both.{colors.ENDC}")
        sys.exit()

    tools_dict = {"snakemake" : "Missing",
                  "nextflow" : "Installed"}
    #print(utils.test_executable(exe))
    utils.pretty_print(tools_dict)
    std_deps, pip_deps = utils.parse_yaml("../conda.yaml")
    

if __name__ == "__main__":
    main()