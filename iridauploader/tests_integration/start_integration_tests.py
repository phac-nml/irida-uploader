"""
This file is used to kick off the integration tests

it can be used from command line like so:
  $ xvfb-run --auto-servernum --server-num=1 python3 start_integration_tests.py <branch>
where <branch> is the IRIDA github branch to test against

This will start a xvfb instance to run the tests inside
"""

import argparse
import sys

import iridauploader.tests_integration.tests_integration as tests_integration

# parse a single argument that determines which IRIDA branch we are testing against
argument_parser = argparse.ArgumentParser(description='This program parses sequencing runs and uploads them to IRIDA.')
argument_parser.add_argument('branch', help='Which IRIDA branch to run integration tests against')
argument_parser.add_argument('db_host', help="Override database host",
                             nargs='?', action='store', default=False)
argument_parser.add_argument('db_port', help="Override database port",
                             nargs='?', action='store', default=False)


def main():
    # parse argument
    args = argument_parser.parse_args()

    # Start integration tests on specified branch
    if args.db_host and args.db_port:
        return tests_integration.start(args.branch, args.db_host, args.db_port)
    else:
        return tests_integration.start(args.branch)


if __name__ == "__main__":
    sys.exit(main())
