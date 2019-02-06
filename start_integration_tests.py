import argparse

import tests_integration.tests_integration as tests_integration

# parse a single argument that determines which IRIDA branch we are testing against
argument_parser = argparse.ArgumentParser(description='This program parses sequencing runs and uploads them to IRIDA.')
argument_parser.add_argument('branch', help='Which IRIDA branch to run integration tests against')


def main():
    # parse argument
    args = argument_parser.parse_args()
    # Start integration tests on specified branch
    tests_integration.start(args.branch)


if __name__ == "__main__":
    main()
