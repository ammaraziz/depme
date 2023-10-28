import depme
def test_pip_success():
  assert test_pip("collections") == "Installed"

def test_pip_missing():
  assert test_pip("biopython") == "Missing"
