import json
from itertools import product
from threading import local


from approvaltests.ApprovalException import ApprovalException
from approvaltests.FileApprover import FileApprover
from approvaltests.Namer import Namer
from approvaltests.ReceivedFileLauncherReporter import ReceivedFileLauncherReporter
from approvaltests.StringWriter import StringWriter
from approvaltests.reporters.diff_reporter import DiffReporter

DEFAULT_REPORTER = local()


def set_default_reporter(reporter):
    global DEFAULT_REPORTER
    DEFAULT_REPORTER.v = reporter
    

def get_default_reporter():
    if not hasattr(DEFAULT_REPORTER, "v") or DEFAULT_REPORTER.v is None:
        return DiffReporter()
    return DEFAULT_REPORTER.v


def verify(data, reporter=None):
    if reporter is None:
        reporter = get_default_reporter()
    approver = FileApprover()
    namer = get_default_namer()
    writer = StringWriter(data)

    error = approver.verify(namer, writer, reporter)
    if error is not None:
        raise ApprovalException(error)


def get_default_namer():
    return Namer()


def verify_all(header, alist, formatter=None, reporter=None):
    if formatter is None:
        formatter = PrintList().print_item 
    text = header + '\n\n'
    for i in alist:
        text += formatter(i) + '\n'
    verify(text, reporter)


def verify_all_combinations(function_under_test, input_arguments, formatter=None, reporter=None):
    """Run func with all possible combinations of args and verify outputs against the recorded approval file.

    Args:
        function_under_test (function): function under test.
        input_arguments: list of values to test for each input argument.  For example, a function f(product, quantity)
            could be tested with the input_arguments [['water', 'cola'], [1, 4]], which would result in outputs for the
            following calls being recorded and verified: f('water', 1), f('water', 4), f('cola', 1), f('cola', 4).
        formatter (function): function for formatting the function inputs/outputs before they are recorded to an
            approval file for comparison.
        reporter (approvaltests.Reporter.Reporter): an approval reporter.

    Raises:
        ApprovalException: if the results to not match the approved results.
    """
    if formatter is None:
        formatter = args_and_result_formatter
    approval_strings = []
    for args in product(*input_arguments):
        try:
            result = function_under_test(*args)
        except Exception as e:
            result = e
        approval_strings.append(formatter(args, result))
    verify(''.join(approval_strings), reporter=reporter)


def verify_as_json(object, reporter=None):
    n_ = to_json(object) + "\n"
    verify(n_, reporter)

def to_json(object):
    return json.dumps(
        object,
        sort_keys=True,
        indent=4,
        separators=(',', ': '),
        default=lambda o: o.__dict__)


class PrintList(object):
    index = 0

    @classmethod
    def print_item(cls, x):
        text = str(cls.index) + ') ' + str(x)
        cls.index += 1
        return text


def args_and_result_formatter(args, result):
    return 'args: {} => {}\n'.format(repr(args), repr(result))

  
def verify_file(file_name, reporter=None):
    with open(file_name, 'r') as f:
        file_contents = f.read()
        verify(file_contents, reporter)