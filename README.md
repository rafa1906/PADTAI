# PADTAI

PADTAI (Proxy Attribute Discovery for Trustworthy AI) is a proxy attribute discovery tool based on [Inductive Logic Programming](https://arxiv.org/pdf/2008.07912.pdf). If you use PADTAI, please cite the paper [Proxy Attribute Discovery in Machine Learning Datasets via Inductive Logic Programming]() (TACAS 2025).

### Requirements
#### Prerequisites
- [Python](https://www.python.org/) (3.10 or above)
- [SWI-Prolog](https://www.swi-prolog.org) (9.2.0 or above)
- [git](https://git-scm.com/)

#### Dependencies
- [Clingo](https://potassco.org/clingo/) (5.6.2 or above)
- [Janus-swi](https://github.com/SWI-Prolog/packages-swipy)
- [pysat](https://pysathq.github.io)
- [bitarray](https://github.com/ilanschnell/bitarray)
- [Popper](https://github.com/logic-and-learning-lab/Popper)
- [NuWLS](https://ojs.aaai.org/index.php/AAAI/article/view/25505)

If you are running Ubuntu and already have Python installed, you can set up all dependencies automatically by running the script `install_deps.sh`. To set them up manually, see the instructions below.

#### SWI-Prolog
If you are running Ubuntu, you can use the official PPA:

```bash
sudo apt-get install software-properties-common
sudo apt-add-repository ppa:swi-prolog/stable
sudo apt-get update
sudo apt-get install swi-prolog
```

If you are using another OS, refer to the [SWI-Prolog](https://www.swi-prolog.org/build/) website for installation instructions.

**IMPORTANT:** Do not use the `snapd` version, as it will not work with *Janus-swi*.

#### Python dependencies
Install Python dependencies with the command ```pip3 install -r requirements.txt```.

#### NuWLS
Install NuWLS with the commands:

```bash
wget https://maxsat-evaluations.github.io/2023/mse23-solver-src/anytime/NuWLS-c-2023.zip
unzip NuWLS-c-2023.zip
cd NuWLS-c-2023/code
make
cd ../bin
echo -e "\nexport PATH=\$PATH:$PWD" >> ~/.bashrc
exec bash
```

If you have any issue with NuWLS, run PADTAI with the flag ```--solver rc2```, e.g., ```python3 padtay.py datasets/Adult/Adult-sex.csv --solver rc2```.

### Installation
Install PADTAI with the commands:

```bash
git clone https://github.com/rafa1906/PADTAI.git
cd PADTAI
./install_deps.sh
```

If you prefer to set up the dependencies manually, run the command ```pip3 install .``` once you are finished to install the PADTAI module.

To confirm that the installation was successful, run the command ```python3 padtai.py datasets/Adult/Adult-sex.csv --grounded none``` and check if you get some output after about a minute.

#### Package
To use PADTAI as a package, make sure you have the required dependencies installed and run the command ```pip3 install git+https://github.com/rafa1906/PADTAI@master```.

Afterwards, you can import PADTAI and use it in your code:

```python
from padtai.pipeline import main as run

run(run_as_package=True,args={...})
```

### Usage
Run PADTAI with the command:

```bash
python3 padtai.py [-h] [-d {none,padtai,popper,all}] [-c] [-s {rc2,nuwls}] 
                  [--sample-size int] [--max-timeout int] [--min-coverage float]
                  [--min-recall float] [--min-precision float] [--intcols str]
                  [--grounded str]
                  dataset
```

PADTAI takes the following arguments:

- Required arguments:
    - `dataset` specifies path to the target dataset (example: datasets/Adult/Adult-sex.csv)

- Optional arguments:
    - `-h` and `--help` show the help message and exit
    - `-d {none,padtai,popper,all}` and `--debug {none,padtai,popper,all}` set debug level: `none` (no debug messages), `padtai` (padtai debug messages), `popper` (popper debug messages), `all` (padtai and popper debug messages) (default: `padtai`)
    - `-c` and `--categorical` enable categorical mode (default: false)
    - `-s {rc2,nuwls}` and `--solver {rc2,nuwls}` choose solver: `rc2` (default pysat solver), `nuwls` (recommended solver) (default: `nuwls`)
    - `--sample-size <int>` sets sample size (default: 3400 / #columns)
    - `--max-timeout <int>` sets maximum timeout in seconds (default: 1200 seconds)
    - `--min-coverage <float>` sets coverage threshold (default: 10%)
    - `--min-recall <float>` sets recall threshold (default: 15%)
    - `--min-precision <float>` sets precision threshold (default: 85%)
    - `--intcols <str>` specifies which columns should be treated as being of integer type; it expects a comma-separated list of integers (or `none`) (example: 1,4,5) (default: all integer columns)
    - `--grounded <str>` sets operators to be grounded (each operator should be provided as a class under the `operators` directory); it expects a comma-separated list with entries of the form `<file>:<class>` (or `none`), where `<file>` is the path to a file under the `operators` directory and `<class>` is the name of the class (default: `lt:LTOperator`)

**IMPORTANT:** For reasons beyond our control, the *Credit Card* dataset has a memory leak when grounding the less-than operation. For systems similar to the one described in the paper, we recommend testing it with the parameter `--intcols 0,1` to address this issue. For example:

```bash
python3 padtai.py datasets/"Credit Card"/CreditCard-sex.csv --intcols 0,1
```

#### Operators
PADTAI supports the grounding of user-defined operators. The user needs only provide a file under the `padtai/operators` directory with a class implementing `BaseOperator` (see: `padtai/operators/base.py`). This class must implement four methods: `operator()`, `arity()`, `ground(int_list)`, and `query(int_pair)`. Two examples are provided: `lt.py` (less-than operator) and `sum.py` (sum operator). If you add a new operator, rerun the command ```pip3 install .``` to update the PADTAI installation.

To tell Popper to include these operators, run PADTAI with the flag `--grounded <file>:<class>`, where `<file>` is the path to the file from the `operators` directory and `<class>` is the name of the class (example: `sum:SumOperator`).

#### Table parser
You can run only the table parser module by using the command:

```bash
python3 padtai/parsetable.py [-h] [-c] [-o path] [--sample-size int] [--intcols str] 
                             [--grounded str] 
                             dataset
```

The table parser module takes the following arguments:

- Required arguments:
    - `dataset` specifies path to the target dataset (example: datasets/Adult/Adult-sex.csv)

- Optional arguments:
    - `-h` and `--help` show the help message and exit
    - `-c` and `--categorical` enable categorical mode (default: false)
    - `-o <path>` and `--out <path>` set output directory for generated files (default: dataset name)
    - `--sample-size <int>` sets sample size (default: 3400 / #columns)
    - `--intcols <str>` specifies which columns should be treated as being of integer type; it expects a comma-separated list of integers (or `none`) (example: 1,4,5) (default: all integer columns)
    - `--grounded <str>` sets operators to be grounded (each operator should be provided as a class under the `operators` directory); it expects a comma-separated list with entries of the form `<file>:<class>` (or `none`), where `<file>` is the path to a file under the `operators` directory and `<class>` is the name of the class (default: `lt:LTOperator`)

### Testing

#### Testing single dataset
PADTAI includes scripts to automate the testing of the methodology described in the paper. To test a single dataset, use the command:

```bash
python3 script/test_dataset.py [-h] [-s {rc2,nuwls}] [--sample-size int] [--max-timeout int]
                               [--intcols str] [--grounded str] [--ignore-attributes str]
                               dir
```

The script takes the following arguments:

- Required arguments:
    - `dir` specifies path a directory with dataset(s) to test (example: datasets/Adult/)

- Optional arguments:
    - `-h` and `--help` show the help message and exit
    - `-s {rc2,nuwls}` and `--solver {rc2,nuwls}` choose solver: `rc2` (default pysat solver), `nuwls` (recommended solver) (default: `nuwls`)
    - `--sample-size <int>` sets sample size (default: 3400 / #columns)
    - `--max-timeout <int>` sets maximum timeout in seconds (default: 1200 seconds)
    - `--intcols <str>` specifies which columns should be treated as being of integer type; it expects a comma-separated list of integers (or `none`) (example: 1,4,5) (default: all integer columns)
    - `--grounded <str>` sets operators to be grounded (each operator should be provided as a class under the `operators` directory); it expects a comma-separated list with entries of the form `<file>:<class>` (or `none`), where `<file>` is the path to a file under the `operators` directory and `<class>` is the name of the class (default: `lt:LTOperator`)
    - `--ignore-attributes <str>` specifies which protected attributes to ignore (assuming datasets of the form `<dataset>-<attr>.csv`, where `<attr>` is the protected attribute in question); it expects a comma-separated list with names of attributes (or `none`) (example: age) (default: none)

The script will run PADTAI on each dataset three times, as described in the paper. The solution will be collected by taking the union of the three runs.

The script's intended usage is to test a single dataset (possibly with  multiple protected attributes). While it will work if you pass it multiple datasets, it will interpret the derived rules as being part of a single solution, and will not differentiate between the various datasets.

**IMPORTANT:** The *KDD* dataset is zipped due to GitHub space constraints. If the script detects a ZIP file, it will unzip it before testing.

#### Testing all datasets
To test all datasets, run the command: 

```bash
./scripts/test_all.sh
```

Depending on your system, testing all datasets may take around a day.

Note that, due to the non-deterministic nature of the sampling and ILP procedures, the results may not exactly match those of the paper.

#### Testing subset of datasets
If you wish to test a smaller representative subset of datasets, run the command:

```bash
./scripts/test_subset.sh
```

This will test the *Adult*, *Ricci*, and *German Credit* datasets. Expect it to take around five to six hours.

#### Timeouts
If you still want to run the tests faster, you can lower the timeout by passing the flag `--max-timeout <int>` to the shell scripts. For example:

```bash
./scripts/test_all.sh --max-timeout 900
```

To ensure most relevant rules are inferred, we recommend not using a timeout lower than 900 seconds (15 minutes).

#### Grounding

Alternatively, you can disable the grounding of arithmetic operations by passing the flag `--grounded none` to the shell scripts. For example:

```bash
./scripts/test_all.sh --grounded none
```

Disabling grounding significantly reduces execution times (expect all tests to take between one and two hours) but will lead to missing relevant rules (e.g., the *combine* proxy in the *Ricci* dataset). 