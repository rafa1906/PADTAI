from padtai.pipeline import main as run

import sys
import os
import argparse
import contextlib
import re

from io import StringIO
from zipfile import ZipFile

@contextlib.contextmanager
def capture_output(capturer):
    """
    Context manager to temporarily redirect sys.stdout to a given capturer.

    Parameters:
        capturer (StringIO): An instance of StringIO or similar object to capture the output.
    """

    prev = sys.stdout
    sys.stdout = capturer
    try:
        yield
    finally:
        sys.stdout = prev


def parse_rule(str):
    """
    Parses a debug string containing a rule and its metrics.

    Parameters:
        str (str): A string containing debug information about a rule and its metrics. 
                   The string is expected to be in the following format:
                   "[DEBUG] Rule: <rule>
                    Coverage (%): <coverage>, Recall (%): <recall>, Precision (%): <precision>"

    Returns:
        dict: A dictionary containing the parsed rule and its metrics, with the keys:
            - 'rule': The rule extracted from the input string.
            - 'coverage': The coverage metric extracted from the input string.
            - 'recall': The recall metric extracted from the input string.
            - 'precision': The precision metric extracted from the input string.
    """

    # Split input into rule and metrics parts
    parts = str.splitlines()

    # Extract rule
    rule = parts[0].split('[DEBUG] Rule:', 1)[-1].strip()

    # Extract metrics
    metrics = parts[1].split(',')

    # Extract coverage, recall, precision
    coverage = float(metrics[1].split('Coverage (%):', 1)[-1].strip())
    recall = float(metrics[2].split('Recall (%):', 1)[-1].strip())
    precision = float(metrics[3].split('Precision (%):', 1)[-1].strip())

    return {
        'rule': rule,
        'coverage': coverage,
        'recall': recall,
        'precision': precision
    }


def distinct_rules(rule1, rule2):
    """
    Determines if two rules are distinct based on their predicates.

    Parameters:
        rule1 (dict): A dictionary containing a rule with a 'rule' key.
        rule2 (dict): A dictionary containing a rule with a 'rule' key.

    Returns:
        bool: True if the predicates of the two rules are distinct, False otherwise.
    """

    # Remove the part before and including ':-' and split by commas
    body1 = rule1['rule'].split(':-', 1)[-1].strip().split(',')
    body2 = rule2['rule'].split(':-', 1)[-1].strip().split(',')

    # Remove parentheses and their contents
    preds1 = [re.sub(r'\(.*?\)', '', part).strip() for part in body1]
    preds2 = [re.sub(r'\(.*?\)', '', part).strip() for part in body2]

    # Are the predicates equal regardless of order?
    return set(preds1) != set(preds2)


def print_results(rules):
    """
    Prints the results of rule evaluations based on different thresholds for coverage, recall, and precision.
    It also identifies and prints the rules with the maximum recall, precision, and coverage.

    Parameters:
        rules (list of dict): A list of dictionaries where each dictionary represents a rule with its metrics.
                              Each dictionary should have the keys 'rule', 'coverage', 'recall', and 'precision'.
    """

    print("\n+++++++++++++ Solution (20/90/15) ++++++++++++++")

    metrics = []
    for rule in rules:
        if rule['coverage'] > 15 and rule['recall'] > 20 and rule['precision'] > 90:
            print(rule['rule'])
            metrics.append([rule['coverage'], rule['recall'], rule['precision']])

    if metrics != []:
        avgs = [sum(metric) / len(metric) for metric in zip(*metrics)]
        print("\nAvg. Coverage (%): {:.2f}, Avg. Recall (%): {:.2f}, Avg. Precision (%): {:.2f}".format(*avgs))

    print("++++++++++++++++++++++++++++++++++++++++++++++++\n")

    print("\n+++++++++++++ Solution (15/85/10) ++++++++++++++")

    metrics = []
    for rule in rules:
        if rule['coverage'] > 10 and rule['recall'] > 15 and rule['precision'] > 85:
            print(rule['rule'])
            metrics.append([rule['coverage'], rule['recall'], rule['precision']])

    if metrics != []:
        avgs = [sum(metric) / len(metric) for metric in zip(*metrics)]
        print("\nAvg. Coverage (%): {:.2f}, Avg. Recall (%): {:.2f}, Avg. Precision (%): {:.2f}".format(*avgs))

    print("++++++++++++++++++++++++++++++++++++++++++++++++\n")

    print("\n++++++++++++++ Solution (10/80/5) ++++++++++++++")

    metrics = []
    for rule in rules:
        if rule['coverage'] > 5 and rule['recall'] > 10 and rule['precision'] > 80:
            print(rule['rule'])
            metrics.append([rule['coverage'], rule['recall'], rule['precision']])

    if metrics != []:
        avgs = [sum(metric) / len(metric) for metric in zip(*metrics)]
        print("\nAvg. Coverage (%): {:.2f}, Avg. Recall (%): {:.2f}, Avg. Precision (%): {:.2f}".format(*avgs))

    print("++++++++++++++++++++++++++++++++++++++++++++++++\n")

    print("\n+++++++++++++ Solution (5/80/2.5) ++++++++++++++")

    metrics = []
    for rule in rules:
        if rule['coverage'] > 2.5 and rule['recall'] > 5 and rule['precision'] > 80:
            print(rule['rule'])
            metrics.append([rule['coverage'], rule['recall'], rule['precision']])

    if metrics != []:
        avgs = [sum(metric) / len(metric) for metric in zip(*metrics)]
        print("\nAvg. Coverage (%): {:.2f}, Avg. Recall (%): {:.2f}, Avg. Precision (%): {:.2f}".format(*avgs))

    print("++++++++++++++++++++++++++++++++++++++++++++++++\n")

    print("\n++++++++++++++++ Max. Recall ++++++++++++++++++")

    top_recall_rule = sorted(rules, key=lambda el: (el['recall'], el['coverage'], el['precision']))[-1]
    print("{}\nCoverage (%): {:.2f}, Recall (%): {:.2f}, Precision (%): {:.2f}".format(top_recall_rule['rule'],
                                                                                       top_recall_rule['coverage'], 
                                                                                       top_recall_rule['recall'], 
                                                                                       top_recall_rule['precision']))

    print("++++++++++++++++++++++++++++++++++++++++++++++++\n")

    print("\n+++++++++++++++ Max. Precision ++++++++++++++++")

    top_precision_rule = sorted(rules, key=lambda el: (el['precision'], el['recall'], el['coverage']))[-1]
    print("{}\nCoverage (%): {:.2f}, Recall (%): {:.2f}, Precision (%): {:.2f}".format(top_precision_rule['rule'],
                                                                                       top_precision_rule['coverage'], 
                                                                                       top_precision_rule['recall'], 
                                                                                       top_precision_rule['precision']))

    print("++++++++++++++++++++++++++++++++++++++++++++++++\n")

    print("\n+++++++++++++++ Max. Coverage +++++++++++++++++")

    top_coverage_rule = sorted(rules, key=lambda el: (el['coverage'], el['recall'], el['precision']))[-1]
    print("{}\nCoverage (%): {:.2f}, Recall (%): {:.2f}, Precision (%): {:.2f}".format(top_coverage_rule['rule'],
                                                                                       top_coverage_rule['coverage'], 
                                                                                       top_coverage_rule['recall'], 
                                                                                       top_coverage_rule['precision']))

    print("++++++++++++++++++++++++++++++++++++++++++++++++\n")


def main(args):
    """
    Executes the main logic for processing datasets, extracting rules, and printing results.

    Parameters:
        args (argparse.Namespace): An object containing the command-line arguments.
    """

    rules = []

    datasets = next(os.walk(args.dir), (None, None, []))[2]
    for dataset in datasets:
        # If dataset is zipped, unzip the dataset
        if dataset.endswith(".zip"):
            with ZipFile(args.dir + dataset, 'r') as zip_ref:
                zip_ref.extractall(args.dir)
                datasets.append(dataset[:-4] + '.csv')

            continue

        # If dataset is marked as to be ignored, skip it
        if any(attr != "none" and dataset.split('-')[-1][:-4] == attr \
               for attr in args.ignore_attributes):
            continue

        # Build dataset path
        args.dataset = args.dir + dataset

        # Perform three runs for each dataset
        for i in range(3):
            print("[+] Testing {} (run {} of 3)".format(args.dataset, i + 1))

            # Capture sys.stdout
            capturer = StringIO()
            with capture_output(capturer):
                run(run_as_package=True,args=args)

            # Read and parse the output
            out = capturer.getvalue()
            out_rules = []
            add_next_line = False
            for line in out.splitlines():
                if line.startswith("[DEBUG] Rule:"):
                    out_rules.append(line.strip())
                    add_next_line = True

                elif add_next_line:
                    out_rules[-1] += "\n" + line.strip()
                    add_next_line = False

            rules += list(map(parse_rule, out_rules))

    # Filter duplicates
    rules_no_duplicates = []
    for rule in rules:
        if all(distinct_rules(rule, other_rule) for other_rule in rules_no_duplicates):
            rules_no_duplicates.append(rule)

    # Print only if at least one rule was found
    if rules_no_duplicates != []:
        print_results(rules_no_duplicates)

    # Clean table files if extracted from zip
    if any(dataset.endswith(".zip") for dataset in datasets):
        for dataset in datasets:
            if dataset.endswith(".csv"):
                try:
                    os.remove(os.path.join(args.dir, dataset))
                except:
                    continue


if __name__ == '__main__':
    # Force line buffering
    # Needed for shell scripts
    sys.stdout.reconfigure(line_buffering=True)

    parser = argparse.ArgumentParser(formatter_class=argparse.MetavarTypeHelpFormatter)

    parser.add_argument('dir', type=str, metavar="dir",
                        help='path to a directory with dataset(s) to test \
                              (example: datasets/Adult/)',)
    parser.add_argument('-s', '--solver', choices=['rc2', 'nuwls'],
                        type=str, default='nuwls',
                        help='choose solver: rc2 (default pysat solver), nuwls (recommended solver) \
                              (default: nuwls)')
    parser.add_argument('--sample-size', type=int, default=-1,
                        help='set sample size (default: 3400 / #columns)')
    parser.add_argument('--max-timeout', type=int, default=1200,
                        help='set maximum timeout in seconds (default: 1200 seconds)')
    parser.add_argument('--intcols', type=str, default=None,
                        help='set integer columns; expects comma-separated list of integers \
                              (or \'none\') (example: 1,4,5) (default: all integer columns)')
    parser.add_argument('--grounded', type=str, default=None,
                        help='set operators to be grounded (each operator should be provided \
                              as a class under the operators directory); expects comma-separated \
                              list with entries of the form <file>:<class> (or \'none\'), where \
                              <file> is the path to a file under the operators directory and <class> \
                              is the name of the class (default: lt:LTOperator)')
    parser.add_argument('--ignore-attributes', type=str, default="none",
                        help='set protected attributes to ignore (datasets must be of the form \
                              <dataset>-<attr>.csv, where <attr> is the protected attribute in question); \
                              expects comma-separated list with names of attributes (or \'none\') \
                              (example: age) (default: none)')
    
    args = parser.parse_args()

    # These arguments cannot be user-set
    # Thresholds hold most permissive settings, but are irrelevant here because
    # in this script solution is extracted from debug information
    args.debug = 'padtai'
    args.categorical = False
    args.min_coverage = 2.5
    args.min_recall = 5
    args.min_precision = 80

    # Parse attributes to be ignored
    args.ignore_attributes = args.ignore_attributes.split(',')

    # Fix for case where user-provided directory path doesn't end with a slash
    if not (args.dir).endswith('/'):
        args.dir += '/'

    main(args)