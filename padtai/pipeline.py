from . parsetable import main as parse_table, is_number, strgen, repls

import sys
import argparse
import shutil
import importlib
import re

import janus_swi as janus

from pathlib import Path

from popper.util import Settings, order_prog, format_rule
from popper.loop import learn_solution


def format_prog(prog, settings):
    """
    Formats the list of Prolog rules output by Popper.
    
    The function iterates through each rule in the input list, formats it according to 
    the given settings, and appends the formatted body to the 'formatted' list. It also 
    extracts the head of the formatted rules.

    Parameters:
        prog (list of object): A list of Prolog rules to be formatted.
        settings (object): An object containing settings for formatting the rules.

    Returns:
        tuple: A tuple containing two elements:
            - formatted (list of str): A list of the formatted rule bodies.
            - head (str): The head of the formatted rules.
    """

    formatted = []
    for rule in order_prog(prog):
        # Format rule via builtin Popper functions
        ruleP = format_rule(settings.order_rule(rule))[:-1]

        # Head is always the same
        # Body differs so must be appended to list
        head, body = ruleP.split(':- ')[0], ruleP.split(':- ')[1]
        formatted.append(body)

    return formatted, head


def normalize(strlist, rebinds):
    """
    Normalizes a list of strings. 
    
    The function converts strings to lowercase, parses numbers, and reverts the 
    replacement and rebinding operations done by the table parser.

    Parameters:
        strlist (list of str): A list of strings to be normalized.
        rebinds (dict of str to str): The rebindings of non-integer values that have both 
                                      alpha and numeric characters.

    Returns:
        list of str: The normalized list of strings.
    """

    for i in range(len(strlist)):
        # Convert to lowercase
        strlist[i] = strlist[i].lower()

        # Parse numbers
        if is_number(strlist[i]):
            strlist[i] = int(strlist[i]) if '.' not in strlist[i] else float(strlist[i])
            continue

        # Revert replacement of illegal Popper syntax
        for repl in repls:
            strlist[i] = strlist[i].replace(*repl) if not is_number(strlist[i]) else strlist[i]

        # Revert rebinding of non-integer attributes containing both alpha 
        # and numeric characters
        if not is_number(strlist[i]) and bool(re.search(r'\d', strlist[i])) and \
           not strlist[i] in rebinds.keys():
            rebinds[strlist[i]] = next(strgen)

    return strlist


def parse():
    """
    Parses command-line arguments and returns an object with the parsed arguments.

    Returns:
        An object with the parsed arguments. The object has the following attributes:
            - dataset (str): The path to the dataset.
            - debug (str): The debug level (choice between 'none', 'padtai', 'popper', 
                           and 'all').
            - categorical (bool): A flag indicating whether categorical mode is enabled.
            - sample_size (int): The sample size.
            - max_timeout (int): The maximum timeout.
            - min_coverage (float): The minimum coverage threshold.
            - min_recall (float): The minimum recall threshold.
            - min_precision (float): The minimum precision threshold.
            - intcols (str): A list of the integer columns in string form.
            - grounded (str): A list of the operators to be grounded in string form.
    """

    parser = argparse.ArgumentParser(formatter_class=argparse.MetavarTypeHelpFormatter)

    parser.add_argument('dataset', type=str, metavar="dataset",
                        help='path to the dataset (example: datasets/Adult/Adult-sex.csv)',)
    parser.add_argument('-d', '--debug', choices=['none', 'padtai', 'popper', 'all'],
                        type=str, default='padtai',
                        help='set debug level: none (no debug messages), padtai (padtai debug messages), \
                              popper (popper debug messages), all (padtai and popper debug messages) \
                              (default: padtai)')
    parser.add_argument('-c', '--categorical', action='store_true',
                        help='enable categorical mode (default: false)')
    parser.add_argument('-s', '--solver', choices=['rc2', 'nuwls'],
                        type=str, default='nuwls',
                        help='choose solver: rc2 (default pysat solver), nuwls (recommended solver) \
                              (default: nuwls)')
    parser.add_argument('--sample-size', type=int, default=-1,
                        help='set sample size (default: 3400 / #columns)')
    parser.add_argument('--max-timeout', type=int, default=1200,
                        help='set maximum timeout in seconds (default: 1200 seconds)')
    parser.add_argument('--min-coverage', type=float, default=10,
                        help='set coverage threshold (default: 10%%)')
    parser.add_argument('--min-recall', type=float, default=15,
                        help='set recall threshold (default: 15%%)')
    parser.add_argument('--min-precision', type=float, default=85,
                        help='set precision threshold (default: 85%%)')
    parser.add_argument('--intcols', type=str, default=None,
                        help='set integer columns; expects comma-separated list of integers \
                              (or \'none\') (example: 1,4,5) (default: all integer columns)')
    parser.add_argument('--grounded', type=str, default=None,
                        help='set operators to be grounded (each operator should be provided \
                              as a class under the operators directory); expects comma-separated \
                              list with entries of the form <file>:<class> (or \'none\'), where \
                              <file> is the path to a file under the operators directory and <class> \
                              is the name of the class (default: lt:LTOperator)')

    return parser.parse_args()


def load_table(table_path, batch_size, offset, line_offset,
               out_path, rebinds, int_cols, grounded_ops, categories):
    """
    Load a batch from the given dataset into Prolog.

    Parameters:
        table_path (str): The path to the dataset.
        batch_size (int): The number of rows to load per batch.
        offset (int): The byte offset to start loading from.
        line_offset (int): The line offset to start loading from.
        out_path (str): The path to the directory containing the Popper files.
        rebinds (dict of str to str): The rebindings of non-integer values that have both 
                                      alpha and numeric characters.
        int_cols (list of int): The indices of the integer columns in the dataset.
        grounded_ops (list of object): A list of operators to be grounded.
        categories (list of str): A list of categories.

    Returns:
        table_pairs (list of tuple): A list of table pairs containing the row id, protected 
                                     value, and any integers that appear in the rule.
        categories_count (dict of str to int): A dictionary mapping categories to their counts.
    """
    
    categories_count = {}

    # No observed impact in memory usage, even in large datasets (e.g., KDD)
    table_pairs = []
    cols = []

    with open(table_path, 'r') as f:
        column_names = next(f)
        cols = normalize(column_names.split(',')[:-1], rebinds)

        # If first iteration, add offset of column names
        if offset == 0:
            offset += len(column_names) + 1

        # Mark operators and columns as dynamic because definitions
        # will be updated during validation 
        with open(out_path + "/dynamic.pl", 'w+') as fP:
            for op in grounded_ops:
                fP.write(":- dynamic {}/{}.\n".format(op.operator(), op.arity()))
            for col in cols:
                fP.write(":- dynamic {}/2.\n".format(col))

        # Load dynamic information
        dyn_path = out_path + "/dynamic.pl"
        janus.consult(dyn_path)

        # Load background knowledge
        bk_path = out_path + "/bk.pl"
        janus.consult(bk_path)

        # Unload dynamic procedures
        # Need to retract because removed rows make ids inconsistent
        facts = ["{}(_,_)".format(col) for col in cols]
        for fact in facts:
            janus.query_once("retractall({})".format(fact))
        for op in grounded_ops:
            janus.query_once("retractall({}({}))".format(op.operator(), ("_," * op.arity())[:-1]))

        i = line_offset
        rows_count = 0

        f.seek(offset)
        for row in f:
            # Stop iterating once we've read the entire batch
            if rows_count > batch_size:
                break

            # Update offset
            offset += (len(row) + 1)

            # Increment number of processed rows
            rows_count += 1

            # Extract protected attribute
            protected = row.strip().split(',')[-1].lower()

            for repl in repls:
                protected = protected.replace(*repl) if not is_number(protected) else protected

            # If new value of protected attribute, add as new category
            if protected not in categories:
                categories.append(protected)

            # Increment category count
            # Needed to calculate recall
            categories_count[protected] = categories_count[protected] + 1 if protected in categories_count else 1

            # Prepare facts to load non-protected attributes into Prolog
            rowP = normalize(row.split(',')[:-1], rebinds)
            facts = [("{}(V0,Vn)".format(cols[j]), { "V0": i, "Vn": rebinds[rowP[j]] if rowP[j] in rebinds else rowP[j]}) for j in range(len(rowP))]

            # Load integer values into Prolog
            rowPP = [rowP[j] for j in int_cols] if int_cols else rowP
            ints_in_row = list(map(lambda n: int(n) if '.' not in n else float(n), filter(is_number, map(str, rowPP))))
            for n in ints_in_row:
                try:
                    janus.query_once("assert(int_{}(Vn))".format(n.replace('-', '_minus_').replace('.', '_')), { "Vn": n })
                except:
                    continue

            # Load non-protected attributes into Prolog 
            # Need to go through all rows since some may have been deleted
            for fact in facts:
                janus.query_once("assert({})".format(fact[0]), fact[1])

            # Each table pair contains id, protected value, and any integers
            # that appear in the rule
            table_pairs.append((i, protected, ints_in_row))

            i += 1

    return cols, table_pairs, categories_count, rows_count - 1, offset


def validate_rules(head, rules, table_pairs, grounded_ops, categorical, categories, categories_count):
    """
    Validates a set of rules against a dataset and calculates performance metrics.

    The function evaluates each rule in the provided list against the dataset represented
    by `table_pairs`. It calculates the coverage, recall, and precision of each rule and
    returns these metrics.

    Parameters:
        head (str): The head of the rules to be validated.
        rules (list of str): A list of rules to be validated.
        table_pairs (list of tuple): A list of tuples representing the dataset, where each
                                     tuple contains a row id, a protected value, and any
                                     integers that appear in the rule.
        grounded_ops (list of object): A list of operators to be grounded.
        categorical (bool): A flag indicating whether categorical mode is enabled.
        categories (list of str): A list of categories.
        categories_count (dict of str to int): A dictionary mapping categories to their counts.

    Returns:
        tuple: A tuple containing three lists:
            - coverages (list of float): The coverage percentage for each rule.
            - recalls (list of float): The recall percentage for each rule.
            - precisions (list of float): The precision percentage for each rule.
    """
    
    # Metrics for output rules
    counts = []
    coverages = []
    recalls = []
    precisions = []

    for rule in rules:
        head_formatted = re.sub("[\(].*?[\)]", "", head)
        rule_formatted = re.sub("[\(].*?[\)]", "", rule)

        # Counts: rule with matching protected and non-protected attributes (count),
        # and rules with matching non-protected attributes only (count_all)
        count = 0
        count_all = 0

        # Extract integers in rule
        int_preds = filter(lambda el: re.search(r'^int_(?:_minus_)?\d+_?\d*$', el), rule_formatted.split(','))
        ints_formatted = map(lambda el: el[4:].replace('_minus_', '-').replace('_', '.'), int_preds)
        ints_in_rule = list(map(lambda n: int(n) if '.' not in n else float(n), ints_formatted))

        for (i, protected, ints_in_row) in table_pairs:
            for op in grounded_ops:
                for j in ints_in_row + ints_in_rule:
                    for k in ints_in_row + ints_in_rule:
                        # Query operators for integers in row + rule
                        query = op.query((j, k))

                        # Query only if there is something to query
                        if query[0] != "":
                            janus.query_once(*query)

            matches_head = True

            # In categorical mode, count only rules where head matches protected attribute
            if categorical:
                matches_head = protected == head_formatted

            if is_number(protected):
                protected = int(protected) if '.' not in protected else float(protected)

            # Can the rule unify with the row (protected and non-protected attributes)?
            # Row was already loaded in load_table(...)
            query_dict = { "V0": i } if categorical else { "V0": i, "V1": protected }
            res = janus.query_once(rule, query_dict)['truth'] and matches_head

            # Can the rule unify with the row (non-protected attributes only)?
            res_all = janus.query_once(rule, { "V0": i })['truth']

            if res:
                count += 1
            if res_all:
                count_all += 1

        # Unload grounded operators
        # Needed because they will be reloaded for next rule
        for op in grounded_ops:
            janus.query_once("retractall({}({}))".format(op.operator(), ("_," * op.arity())[:-1])) # unload less-than

        category = head_formatted if categorical else next(category for category in categories if any(attr.endswith(category) for attr in list(map(lambda el: el.split('_', 2)[-1] if el.startswith("attr") else el, rule_formatted.split(',')))))
        category_count = categories_count[category]

        coverage = count / len(table_pairs) * 100
        recall = count / category_count * 100
        precision = count / count_all * 100 if count_all != 0 else 0  # bad rule (functional test)

        counts.append(count)
        coverages.append(coverage)
        recalls.append(recall)
        precisions.append(precision)

    return counts, coverages, recalls, precisions


def print_results(out_rules, metrics_out_rules, top_coverage_rules, top_recall_rules, 
                  top_precision_rules, top_precision_recall_gt_1_rules):
    """
    Prints the results of rule evaluation, including top rules by coverage, recall, 
    and precision, as well as the solution rules and their average metrics.

    Parameters:
        out_rules (list of str): The list of solution rules.
        metrics_out_rules (list of list of float): The metrics (coverage, recall, precision) 
                                                   for each solution rule.
        top_coverage_rules (list of tuple): The top five rules sorted by coverage, each represented 
                                            as a tuple containing the rule and its metrics.
        top_recall_rules (list of tuple): The top five rules sorted by recall, each represented 
                                          as a tuple containing the rule and its metrics.
        top_precision_rules (list of tuple): The top five rules sorted by precision, each represented 
                                             as a tuple containing the rule and its metrics.
        top_precision_recall_gt_1_rules (list of tuple): The top rules sorted by precision 
                                                         with recall greater than or equal to 1%, 
                                                         each represented as a tuple containing 
                                                         the rule and its metrics.
    """

    print("\n+++++++++++++++ Max. Coverages +++++++++++++++++")

    for rule in top_coverage_rules:
        print("{}\nCoverage (%): {:.2f}, Recall (%): {:.2f}, Precision (%): {:.2f}".format(*rule))

    print("++++++++++++++++++++++++++++++++++++++++++++++++\n")

    print("\n++++++++++++++++ Max. Recalls ++++++++++++++++++")

    for rule in top_recall_rules:
        print("{}\nCoverage (%): {:.2f}, Recall (%): {:.2f}, Precision (%): {:.2f}".format(*rule))

    print("++++++++++++++++++++++++++++++++++++++++++++++++\n")

    print("\n+++++++++++++++ Max. Precisions ++++++++++++++++")

    for rule in top_precision_rules:
        print("{}\nCoverage (%): {:.2f}, Recall (%): {:.2f}, Precision (%): {:.2f}".format(*rule))

    print("++++++++++++++++++++++++++++++++++++++++++++++++\n")

    print("\n++++++++ Max. Precisions (Recall >= 1%) ++++++++")

    for rule in top_precision_recall_gt_1_rules:
        print("{}\nCoverage (%): {:.2f}, Recall (%): {:.2f}, Precision (%): {:.2f}".format(*rule))

    print("++++++++++++++++++++++++++++++++++++++++++++++++\n")

    print("\n+++++++++++++++++++ Solution +++++++++++++++++++")

    for out_rule in out_rules:
        print(out_rule)

    if out_rules != []:
        avgs = [sum(metric) / len(metric) for metric in zip(*metrics_out_rules)]
        print("\nAvg. Coverage (%): {:.2f}, Avg. Recall (%): {:.2f}, Avg. Precision (%): {:.2f}".format(*avgs))

    print("++++++++++++++++++++++++++++++++++++++++++++++++\n")


def main(run_as_package=False,args={}):
    """
    Main function to execute the rule learning and validation process.

    The function parses command-line arguments, loads the dataset, applies
    specified operators, and evaluates rules based on coverage, recall, and
    precision metrics. It also handles the output of top-performing rules.

    Parameters:
        run_as_package (bool): A flag indicating whether to run the program in package mode
        args (argparse.Namespace): An object containing the command-line arguments.
    """

    args = args if run_as_package else parse()

    table_path = args.dataset
    int_cols = list(map(int, args.intcols.split(','))) if args.intcols and \
               args.intcols != "none" else [] if args.intcols else None
    grounded_paths = args.grounded.split(',') if args.grounded and \
                     args.grounded != "none" else [] if args.grounded else None
    sample_size = args.sample_size
    categorical = args.categorical
    debug = args.debug
    solver = args.solver
    max_timeout = args.max_timeout
    min_coverage = args.min_coverage
    min_recall = args.min_recall
    min_precision = args.min_precision

    # By default, load only less-than operator
    grounded_ops = []
    if '--grounded' not in sys.argv:
        from . operators.lt import LTOperator
        grounded_ops += [ LTOperator() ]

    # If specified, load operators to be grounded
    elif sys.argv[sys.argv.index('--grounded') + 1] != "none":
        for path in grounded_paths:
            file, op = path.split(':')
            OpClass = getattr(importlib.import_module('.operators.' + file, 'padtai'), op)
            grounded_ops.append(OpClass())

    random_n, rebinds = parse_table(table_path, int_cols, grounded_ops, sample_size, categorical, Path(table_path).stem)

    # Categories are possible values of protected attribute
    categories = list(dict.fromkeys(map(lambda l: l[-1], random_n)))

    out_paths = []
    if categorical:
        for category in categories:
            out_paths.append(Path(table_path).stem + "-" + category)
    else:
        out_paths = [ Path(table_path).stem ]

    # Solution rules and corresponding coverage/recall/precision metrics
    out_rules = []
    metrics_out_rules = []

    # Top coverage, recall and precision (all and with >1% recall) rules
    top_coverage_rules = []
    top_recall_rules = []
    top_precision_rules = []
    top_precision_recall_gt_1_rules = []

    for out_path in out_paths:
        # Popper settings
        # Generated files on out_path
        # NuWLS solver offers slightly better performance than rc2
        if solver == 'rc2':
            settings = Settings(timeout=max_timeout, 
                                kbpath=out_path, 
                                max_vars=5, 
                                functional_test=not categorical, 
                                quiet=(debug == 'none' or debug == 'padtai'))
        else:
            settings = Settings(timeout=max_timeout, 
                                kbpath=out_path, 
                                max_vars=5, 
                                functional_test=not categorical, 
                                quiet=(debug == 'none' or debug == 'padtai'), 
                                anytime_solver='nuwls')

        # Run Popper on generated files and obtain candidate rules
        prog, _, _ = learn_solution(settings)

        if prog != None:
            rules, head = format_prog(prog, settings)
        else:
            if debug == 'padtai' or debug == 'all':
                print("[DEBUG] Couldn't find a solution")
            
            return

        # Initial settings
        batch_size = 2000
        offset = 0
        line_offset = 0
        coverages, recalls, precisions = [], [], []

        while batch_size == 2000:
            # Output debug information if in 'padtai' or 'all' mode
            if debug == 'padtai' or debug == 'all':
                print("[DEBUG] Testing batch {}...".format((line_offset // batch_size) + 1))

            # Load batch (sampled and non-sampled rows) into Prolog
            cols, table_pairs, \
            categories_count, \
            batch_size, offset = load_table(table_path, batch_size, offset, line_offset,
                                            out_path, rebinds, int_cols, grounded_ops, categories)

            # Validate rules and calculate coverage/recall/precision metrics
            counts_batch, \
            coverages_batch, \
            recalls_batch, \
            precisions_batch = validate_rules(head, rules, table_pairs, grounded_ops,
                                              categorical, categories, categories_count)

            # Update metrics
            if coverages == []:
                counts, coverages, recalls, precisions = counts_batch, coverages_batch, \
                                                         recalls_batch, precisions_batch 
            else:
                for i in range(len(rules)):
                    counts[i] += counts_batch[i]
                    coverages[i] = (coverages[i] * line_offset + coverages_batch[i] * batch_size) \
                                 / (line_offset + batch_size)
                    recalls[i] = (recalls[i] * line_offset + recalls_batch[i] * batch_size) \
                               / (line_offset + batch_size)
                    precisions[i] = (precisions[i] * line_offset + precisions_batch[i] * batch_size) \
                                  / (line_offset + batch_size)

            # Update offset
            line_offset += batch_size

        # Output debug information if in 'padtai' or 'all' mode
        for i in range(len(rules)):
            if debug == 'padtai' or debug == 'all':
                print("[DEBUG] Rule: {}:- {}".format(head, rules[i]))
                print("        Count: {}, Coverage (%): {:.2f}, ".format(counts[i], coverages[i]) + \
                      "Recall (%): {:.2f}, Precision (%): {:.2f}".format(recalls[i], precisions[i]))
        
        # Unload dynamic procedures
        # Needed because they may be called multiple times (via test scripts)
        facts = ["{}(_,_)".format(col) for col in cols]
        for fact in facts:
            janus.query_once("retractall({})".format(fact))
        for op in grounded_ops:
            janus.query_once("retractall({}({}))".format(op.operator(), ("_," * op.arity())[:-1]))

        # Unload static procedures
        janus.query_once('unload_file("{}")'.format(out_path + "/bias.pl"))
        janus.query_once('unload_file("{}")'.format(out_path + "/bk.pl"))
        janus.query_once('unload_file("{}")'.format(out_path + "/exs.pl"))

        # Collect top coverage, recall and precision (all and with >1% recall) results
        for i in range(len(rules)):
            if coverages[i] >= min_coverage and recalls[i] >= min_recall and precisions[i] >= min_precision:
                out_rules.append("{}:- {}".format(head, rules[i]))
                metrics_out_rules.append([coverages[i], recalls[i], precisions[i]])

            idx = next((j for j in range(len(top_coverage_rules)) if top_coverage_rules[j][1] < coverages[i]), len(top_coverage_rules))
            top_coverage_rules.insert(idx, ("Rule: {}:- {}".format(head, rules[i]), coverages[i], recalls[i], precisions[i]))
            top_coverage_rules = top_coverage_rules[:5]

            idx = next((j for j in range(len(top_recall_rules)) if top_recall_rules[j][2] < recalls[i]), len(top_recall_rules))
            top_recall_rules.insert(idx, ("Rule: {}:- {}".format(head, rules[i]), coverages[i], recalls[i], precisions[i]))
            top_recall_rules = top_recall_rules[:5]

            idx = next((j for j in range(len(top_precision_rules)) if top_precision_rules[j][3] < precisions[i]), len(top_precision_rules))
            top_precision_rules.insert(idx, ("Rule: {}:- {}".format(head, rules[i]), coverages[i], recalls[i], precisions[i]))
            top_precision_rules = top_precision_rules[:5]

            if recalls[i] >= 1:
                idx = next((j for j in range(len(top_precision_recall_gt_1_rules)) if top_precision_recall_gt_1_rules[j][3] < precisions[i]), len(top_precision_recall_gt_1_rules))
                top_precision_recall_gt_1_rules.insert(idx, ("Rule: {}:- {}".format(head, rules[i]), coverages[i], recalls[i], precisions[i]))
                top_precision_recall_gt_1_rules = top_precision_recall_gt_1_rules[:5]

        # Remove Popper files
        try:
            shutil.rmtree(out_path)
        except OSError as _:
            sys.exit("[ERROR] Something went very wrong, couldn't delete {}".format(out_path))

    # Print solution and top metrics rules
    print_results(out_rules, metrics_out_rules, top_coverage_rules, top_recall_rules, 
                  top_precision_rules, top_precision_recall_gt_1_rules)


if __name__ == '__main__':
    main()
