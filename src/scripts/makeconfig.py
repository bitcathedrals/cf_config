import argparse

from cfconfig.cloud_config import CloudConfig

def exec():
    parser = argparse.ArgumentParser("Generate configurations from static configuration and AWS CF stacks.")

    parser.add_argument("profile", help="aws credentials profile (required)")
    parser.add_argument("config", help="config filename (required)")
    parser.add_argument("environment", help="AWS environment (required)")

    parser.add_argument("--output", help="output filename or STDOUT if not specified")

    args = parser.parse_args()
    
    config = CloudConfig(args.profile,
                         args.config,
                         args.environment)

    if args.output:
        config.write_configuration(args.output)
    else:
        config.print_configuration()

if __name__ == "__main__":
    exec()