from setuptools import setup, find_packages

setup(name='depme',
      version='0.0.1',
      description='',
      author='Ammar Aziz',
      author_email='ammar.aziz@mh.org.au',
      license='GPL3',
      python_requires='>=3.9.15',
      entry_points={"console_scripts": ["depme = depme.main:main"]}
      )
