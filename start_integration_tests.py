import argparse

import tests_integration.tests_integration as tests_integration


argument_parser = argparse.ArgumentParser(description='This program parses sequencing runs and uploads them to IRIDA.')
argument_parser.add_argument('branch', help='Which IRIDA branch to run integration tests against')


def main():
    args = argument_parser.parse_args()
    tests_integration.start(args.branch)


if __name__ == "__main__":
    main()
