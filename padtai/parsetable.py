#!/usr/bin/env python3

import sys
import importlib
import argparse
import re
import random
import itertools

from pathlib import Path
from collections import Counter


def generate_unique():
    """
    Generates 10-character unique strings.

    Yields:
        str: A unique string consisting of 10 lowercase alphabetic characters.
    """

    alphabet = 'abcdefghijklmnopqrstuvwxyz'
    for combination in itertools.product(alphabet, repeat=10):
        yield ''.join(combination)


def is_number(str):
    """
    Determines if a given string represents a valid number.

    Parameters:
        str (str): The string to be evaluated.

    Returns:
        bool: True if the string represents a number (integer or float), 
              including negative numbers; otherwise, False.
    """

    return str.replace('.', '', 1).isdigit() or (str[0] == '-' and str[1:].replace('.', '', 1).isdigit())


def filter_duplicates(rows, protected):
    """
    Applies the conflict removal algorithm described in S4.2 of the paper.

    Filters out duplicate rows based on their non-protected attributes and selects the 
    most common associated protected value for each unique row.

    Parameters:
        rows (list of list): A list of the sampled rows. Includes the non-protected 
                             attributes but not the protected attribute.
        protected (list of list): A list of protected values corresponding to each row.

    Returns:
        tuple: A tuple containing two lists:
            - rowsP (list of list): A list of unique rows after filtering duplicates.
            - protectedP (list of list): A list of the most common protected values 
              associated with each unique row.
    """

    # Maps each non-protected attribute combination to its associated protected values
    attrs_to_protected = {}

    for i in range(len(rows)):
        key = tuple(rows[i])

        if key in attrs_to_protected:
            attrs_to_protected[key].append(protected[i][0])
        else:
            attrs_to_protected[key] = [protected[i][0]]

    rowsP = []
    protectedP = []

    # Implements majority voting system for duplicate rows
    for key in attrs_to_protected:
        protected_count = Counter(attrs_to_protected[key])
        most_common_2 = protected_count.most_common(2)

        # Must be strictly greater
        if len(most_common_2) == 1 or most_common_2[0][1] > most_common_2[1][1]:
            rowsP.append(list(key))
            protectedP.append([most_common_2[0][0]])

    return rowsP, protectedP


# Iterator to generate unique strings
strgen = generate_unique()

# List of string replacements from dataset to Popper syntax
repls = ('-', '_'), ('/', '_'), ('&', '_and_'), (' ', '_'), ('+', '_plus_'), ('<', '_lt_'), ('>', '_gt_'), \
        ('<=', '_lte_'), ('>=', '_gte_'), ('==', '_eq_'), ('=', '_eq_'), ('!=', '_neq_'), \
        ('[', ''), (']', ''), ('(', ''), (')', ''), ('.', '_'), (',', '_'), ('\'', ''), ('%', '')


def generate_bias(cols, rows, int_cols, grounded_ops, categorical=False, category=None):
    """
    Generates bias file for a given dataset and configuration.

    Parameters:
        cols (list of str): A list of the column names of the dataset. Includes both 
                            the non-protected and protected columns.
        rows (list of list): A list of the sampled rows. Includes both the non-protected
                             and protected attributes.
        int_cols (list of bool): A list of booleans indicating whether each column 
                                 is an integer.
        grounded_ops (list of object): A list of operators to be grounded.
        categorical (bool, optional): A flag indicating whether the bias is for a 
                                      run in categorical mode. Defaults to False.
        category (str, optional): The category for a categorical run. Defaults to None.

    Returns:
        list of str: A list with bias information.
    """
    
    bias = []
    colsP = cols[:-1] if categorical else cols

    # Type information of non-protected/protected attributes
    # Integer attributes have single type "int", unless otherwise specified in int_cols
    # Non-integer attributes have type corresponding to column
    attr_classes = ["attr_{}".format(colsP[j]) if not int_cols[j] else "int" for j in range(len(colsP))]
    for row in rows:
        attr_names = ["attr_{}_{}".format(colsP[j], row[j].replace('-', '_minus_').replace('.', '_')) if not int_cols[j] else \
                      "int_{}".format(row[j].replace('-', '_minus_').replace('.', '_')) for j in range(len(colsP))]
        bias += ["constant({},{}).".format(attr_names[j], attr_classes[j]) for j in range(len(colsP))]

    # Arity of head (protected) predicate
    arity = 1 if categorical else 2
    head_name = category if categorical else cols[-1]
    bias += ["head_pred({},{}).".format(head_name, arity)]

    # Arity of grounded operators
    for op in grounded_ops:
        bias += ["body_pred({},{}).".format(op.operator(), op.arity())]

    # Arity of body (non-protected) predicates
    for col in cols[:-1]:
        bias += ["body_pred({},2).".format(col)]

    # Type information of head (protected) predicate
    if categorical:
        bias += ["type({},(ex,)).".format(category)]
    else:
        bias += ["type({},(ex,attr_{})).".format(cols[-1], cols[-1]) if not int_cols[-1] else "type({},(ex,int)).".format(cols[-1])]

    # Type information of grounded operators
    # Grounded operators can only be applied to integer attributes
    for op in grounded_ops:
        bias += ["type({},({})).".format(op.operator(), ("int," * op.arity())[:-1])]

    # Type information of body (non-protected) predicates
    for i in range(len(cols) - 1):
        bias += ["type({},(ex,attr_{})).".format(cols[i], cols[i]) if not int_cols[i] else "type({},(ex,int)).".format(cols[i])]

    # Boilerplate facts
    bias += [":- clause(C), #count{V : var_type(C,V,ex)} != 1."]
    bias += ["body_pred(P,1):- constant(P,_)."]
    bias += ["type(P,(T,)):- constant(P,T)."]

    return list(dict.fromkeys(bias))


def generate_constants(cols, rows, rebinds, int_cols):
    """
    Generates decision points (DP) for each attribute in the dataset, based on their 
    type (integer or non-integer). Non-integer attributes containing both
    alpha and numeric characters are mapped to unique strings.

    Parameters:
        cols (list of str): A list of the column names of the dataset. Includes both 
                            the non-protected and protected columns by default, or only
                            the non-protected columns in categorical mode.
        rows (list of list): A list of the sampled rows. Includes both the non-protected 
                             and protected attributes by default, or only the non-protected
                             attributes in categorical mode.
        rebinds (dict of str to str): The rebindings of non-integer values that have both 
                                      alpha and numeric characters.
        int_cols (list of bool): A list of booleans indicating whether each column is 
                                 an integer.

    Returns:
        list of str: A list of decision points in the format "attr_name_{value}({value|rebind})." 
                     for non-integer attributes or "int_value({value})." for integer attributes.
    """

    consts = []
    for row in rows:
        consts += ["attr_{}_{}({}).".format(cols[j], row[j].replace('-', '_minus_').replace('.', '_'), rebinds[row[j]] if row[j] in rebinds else row[j]) \
                   if not int_cols[j] else "int_{}({}).".format(row[j].replace('-', '_minus_').replace('.', '_'), row[j]) for j in range(len(row))]

    return list(dict.fromkeys(consts))


def generate_background(cols, rows, protected, rebinds, int_cols, sample_size, grounded_ops):
    """
    Generates column relations (CR) and pair relations (PR) for a given dataset 
    and configuration.

    Parameters:
        cols (list of str): A list of the column names of the dataset. Includes the 
                            non-protected columns but not the protected column.
        rows (list of list): A list of the sampled rows. Includes the non-protected 
                             attributes but not the protected attribute.
        protected (list of list): A list of the protected values corresponding to each row.
        rebinds (dict of str to str): The rebindings of non-integer values that have both 
                                      alpha and numeric characters.
        int_cols (list of bool): A list of booleans indicating whether each column 
                                 is an integer.
        sample_size (int): The sample size to consider.
        grounded_ops (list of object): A list of operators to be grounded.

    Returns:
        list of str: A list of column and pair relations.
    """

    facts = []
    int_attrs = []

    # Column relations for non-protected attributes
    # In the meantime, capture any integer attributes that the tool sees
    for (i, row) in zip(range(max(sample_size, len(rows))), rows):
        facts += ["{}({},{}).".format(cols[j], i, rebinds[row[j]] if row[j] in rebinds else row[j]) for j in range(len(row))]
        int_attrs += [row[i] for i in range(len(row)) if int_cols[i]]

    # Capture integer attributes in protected column
    for row in protected:
        if int_cols[-1]:
            int_attrs += row

    int_attrs = list(dict.fromkeys(int_attrs))
    int_attrs = list(map(lambda n: int(n) if '.' not in n else float(n), int_attrs))
    int_attrs.sort()

    # Pair relations for grounded operations over integer attributes
    for op in grounded_ops:
        facts += op.ground(int_attrs)

    return list(dict.fromkeys(facts))


def generate_functest(col):
    """
    Generates functional test for protected column. Functional test ensures that output is
    functional, i.e., no two rules apply to the same row.

    Parameters:
        col (str): The name of the column to generate the functional test for.

    Returns:
        list of str: A list with the functional test.
    """

    functest = []

    functest += ["non_functional(Atom1):-"]
    functest += ["\tAtom1=..[{},A,B],".format(col)]
    functest += ["\tAtom2=..[{},A,C],".format(col)]
    functest += ["\tcall(Atom2),"]
    functest += ["\tB \= C."]

    return list(dict.fromkeys(functest))


def generate_exs(col, rows, rebinds, sample_size, categorical=False, category=None):
    """
    Generates examples for a given dataset and configuration.

    Parameters:
        col (str): The name of the protected column.
        rows (list of list): A list of the sampled rows. Includes only the protected 
                             attribute, and not the non-protected attributes.
        rebinds (dict of str to str): The rebindings of non-integer values that have both 
                                      alpha and numeric characters.
        sample_size (int): The sample size to consider.
        categorical (bool, optional): A flag indicating whether the examples are for a 
                                      run in categorical mode. Defaults to False.
        category (str, optional): The category for a categorical run. Defaults to None.

    Returns:
        list of str: A list with examples. 
            If categorical is False (i.e., the run is non-categorical), an example is of
            the form "pos({protected_name}({id},{protected_value})).".
            If categorical is True (i.e., the run is categorical), an example is of the 
            form "pos({category}({id})).". if the protected value matches the category,
            and "neg({category}({id}))." if it does not.
    """

    exs = []
    for (i, row) in zip(range(max(sample_size, len(rows))), rows):
        if categorical:
            exs += ["{}({}({})).".format("pos" if row[0] == category else "neg", category, i)]
        else:
            exs += ["pos({}({},{})).".format(col, i, rebinds[row[0]] if row[0] in rebinds else row[0])]

    return list(dict.fromkeys(exs))


def generate_popper_files(path, bias, consts, facts, exs, functest=[]):
    """
    Generates the Popper files (bias.pl, bk.pl, and exs.pl) in the specified path.

    Parameters:
        path (str): The path where the Popper files will be generated.
        bias (list of str): A list with bias information.
        consts (list of str): A list of decision points.
        facts (list of str): A list of column and pair relations.
        exs (list of str): A list of examples.
        functest (list of str, optional): A list with the functional test. 
                                          Defaults to the empty list.
    """

    Path(path).mkdir(parents=True, exist_ok=True)

    # Write bias information to bias file
    with open(path + "/bias.pl", 'w+') as f:
        f.writelines(line + "\n" for line in bias)

    # Write decision points, column and pair relations, and functional
    # test to background knowledge file
    with open(path + "/bk.pl", 'w+') as f:
        f.writelines(line + "\n" for line in sorted(consts))
        f.writelines(line + "\n" for line in sorted(facts))
        f.writelines(line + "\n" for line in functest)

    # Write examples to examples file
    with open(path + "/exs.pl", 'w+') as f:
        f.writelines(line + "\n" for line in sorted(exs))


def main(table_path, int_cols, grounded_ops, sample_size, categorical, path):
    """
    Main function to generate Popper files for a given dataset and configuration.

    Parameters:
        table_path (str): The path to the dataset file.
        int_cols (list of int): The indices of the integer columns in the dataset.
        grounded_ops (list of object): A list of operators to be grounded.
        sample_size (int): The sample size to consider.
        categorical (bool): A flag indicating whether the run is in categorical mode.

    Returns:
        random_n (list of list of str): The random sample of the dataset.
        rebinds (dict of str to str): The rebindings of values that have both alpha 
                                      and numeric characters.
    """

    with open(table_path, 'r') as f:
        # First line of dataset is column names
        column_names = next(f).strip().lower().split(',')

        # Calculate sample size dynamically in order to mantain
        # total number of cells approx. constant
        if sample_size == -1:
            sample_size = 3400 // len(column_names)

        # Read dataset and select random sample
        # No observed impact in memory usage, even in large datasets (e.g., KDD)
        records = f.readlines()
        records_sample = records if len(records) <= sample_size else random.sample(records, sample_size)
        random_n = [line.strip().lower().split(',') for line in records_sample]

        # Replace all substrings corresponding to illegal syntax in Popper 
        for repl in repls:
            column_names = list(map(lambda col: col.replace(*repl) if not is_number(col) else col, column_names))
            random_n = list(map(lambda row: list(map(lambda el: el.replace(*repl) if not is_number(el) else el, row)), random_n))

    # Did the user specify which columns are integer columns?
    if int_cols == None:
        # Which columns contain integers?
        # Only check first row; isn't an issue because of rebinds
        int_cols = [True if is_number(attr) else False for attr in random_n[0]] 
    else:
        int_cols = [True if i in int_cols else False for i in range(len(random_n[0]))]

    # Rename values that have both alpha and numeric characters as unique string
    rebinds = {}
    for row in random_n:
        for attr in row:
            if not is_number(attr) and bool(re.search(r'\d', attr)) and \
               not attr in rebinds.keys():
                rebinds[attr] = next(strgen)

    # Extract non-protected/protected attributes
    non_protected_columns = column_names[:-1]
    protected_columns = column_names[-1:]
    non_protected_random_n = list(map(lambda l: l[:-1], random_n))
    protected_random_n = list(map(lambda l: l[-1:], random_n))

    # Handle conflicts between sampled rows
    non_protected_random_n, protected_random_n = filter_duplicates(non_protected_random_n, protected_random_n)

    # Facts are independent of whether in categorical mode or not
    facts = generate_background(non_protected_columns, non_protected_random_n, protected_random_n, rebinds, int_cols, sample_size, grounded_ops)

    # If running in categorical mode, generate bias/background/examples 
    # for each protected value/category at a time
    if categorical:
        for category in map(lambda l: l[-1], random_n):
            bias = generate_bias(column_names, random_n, int_cols, grounded_ops, categorical, category)

            # Don't generate constants for protected column
            consts = generate_constants(non_protected_columns, non_protected_random_n, rebinds, int_cols[:-1])  
            exs = generate_exs(protected_columns[0], protected_random_n, rebinds, sample_size, categorical, category)

            out_path = path + "-" + category

            generate_popper_files(out_path, bias, consts, facts, exs)

    # If running in non-categorical mode, generate single instance of
    # bias/background/examples and add functional test to ensure output is functional
    else:
        bias = generate_bias(column_names, random_n, int_cols, grounded_ops)
        consts = generate_constants(column_names, random_n, rebinds, int_cols)
        functest = generate_functest(protected_columns[0])
        exs = generate_exs(protected_columns[0], protected_random_n, rebinds, sample_size)

        out_path = path

        generate_popper_files(out_path, bias, consts, facts, exs, functest)

    # Need to return sample and rebindings to be used by the pipeline 
    return random_n, rebinds


# Not called by padtai.py
# For running the table parser *only*
if __name__ == '__main__':
    parser = argparse.ArgumentParser(formatter_class=argparse.MetavarTypeHelpFormatter)
    
    parser.add_argument('dataset', type=str, metavar="dataset",
                        help='path to the dataset (example: datasets/Adult/Adult-sex.csv)',)
    parser.add_argument('-c', '--categorical', action='store_true',
                        help='enable categorical mode (default: false)')
    parser.add_argument('-o', '--out', type=str, metavar="path", default=None,
                        help='set output directory for generated files (default: dataset name)')
    parser.add_argument('--sample-size', type=int, default=-1,
                        help='set sample size (default: 3400 / #columns)')
    parser.add_argument('--intcols', type=str, default=None,
                        help='set integer columns; expects comma-separated list of integers \
                              (or \'none\') (example: 1,4,5) (default: all integer columns)')
    parser.add_argument('--grounded', type=str, default=None,
                        help='set operators to be grounded (each operator should be provided \
                              as a class under the operators directory); expects comma-separated \
                              list with entries of the form <file>:<class> (or \'none\'), where \
                              <file> is the path to a file under the operators directory and <class> \
                              is the name of the class (default: lt:LTOperator)')
    
    args = parser.parse_args()

    table_path = args.dataset
    int_cols = list(map(int, args.intcols.split(','))) if args.intcols and \
               args.intcols != "none" else [] if args.intcols else None
    grounded_paths = args.grounded.split(',') if args.grounded and \
                     args.grounded != "none" else [] if args.grounded else None
    sample_size = args.sample_size
    categorical = args.categorical
    path = args.out if args.out else Path(table_path).stem

    # By default, load only less-than operator
    grounded_ops = []
    if '--grounded' not in sys.argv:
        from operators.lt import LTOperator
        grounded_ops += [ LTOperator() ]

    # If specified, load operators to be grounded
    elif sys.argv[sys.argv.index('--grounded') + 1] != "none":
        for path in grounded_paths:
            file, op = path.split(':')
            OpClass = getattr(importlib.import_module('operators.' + file), op)
            grounded_ops.append(OpClass())

    main(table_path, int_cols, grounded_ops, sample_size, categorical, path)
