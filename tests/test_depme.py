import pytest
from depme.main import *

def test_pip_success():

  out = check_pip("collections") 
  assert out == "Installed"

def test_pip_missing():
  tool = "biopython"
  assert check_pip(tool=tool) == "Missing"
