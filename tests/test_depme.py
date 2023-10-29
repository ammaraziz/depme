from depme.main import *
import unittest

def test_pip_success():

  out = check_pip("collections") 
  assert out == "Installed"

def test_pip_missing():
  tool = "biopython"
  assert check_pip(tool=tool) == "Missing"

def test_load_yaml():
  '''
  check that yaml can be parsed.
  '''
  yamldict = load("tests/conda.yaml")
  print(yamldict)
  assert yamldict and len(yamldict.keys()) > 1

def test_parse_yaml():
  '''
  check that we can parse the yaml file correctly
  '''

  expected_std = ['python=3.9', 'snakemake', 'cutadapt', 'bbmap', 'irma', 'minimap2']
  expected_pip = ['icecream', 'pix', 'biopython=1.78']
  expected_r = ['r-base', 'r-optparse', 'r-tidyr']

  std_deps, pip_deps, r_deps = parse_yaml2("tests/conda.yaml")
  print(std_deps, pip_deps, r_deps)

  assert expected_std == std_deps
  assert expected_pip == pip_deps
  assert expected_r == r_deps

def test_check_exe():
  '''
  test if this script can detect `which` program
  test if a fake program doesn't exist
  '''
  assert  check_exe('which') == "Installed"
  assert check_exe('thisprogramshouldntexist') == "Not tested"

def test_api():
  '''
  check if loading depme as a module works
  '''
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
  
  try:
    run(args)
    assert False
  except SystemExit:
    assert True