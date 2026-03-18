import argparse

from system_design_space_importer.discovery import run_discovery
from system_design_space_importer.extractor import run_extract
from system_design_space_importer.fetcher import run_fetch
from system_design_space_importer.mapper import run_map
from system_design_space_importer.packager import run_package
from system_design_space_importer.paths import RunLayout
from system_design_space_importer.validator import run_validate


def build_parser():
    parser = argparse.ArgumentParser(prog="sds-importer")
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_shared_options(command_parser, require_seed=False):
        command_parser.add_argument("--out-dir", required=True)
        command_parser.add_argument("--run-id", required=True)
        if require_seed:
            command_parser.add_argument("--seed", required=True)
            command_parser.add_argument("--profile", default="chapters_only")
            command_parser.add_argument("--max-pages", type=int)

    discover_parser = subparsers.add_parser("discover")
    add_shared_options(discover_parser, require_seed=True)

    fetch_parser = subparsers.add_parser("fetch")
    add_shared_options(fetch_parser)

    extract_parser = subparsers.add_parser("extract")
    add_shared_options(extract_parser)

    map_parser = subparsers.add_parser("map")
    add_shared_options(map_parser)

    validate_parser = subparsers.add_parser("validate")
    add_shared_options(validate_parser)

    package_parser = subparsers.add_parser("package")
    add_shared_options(package_parser)

    run_parser = subparsers.add_parser("run")
    add_shared_options(run_parser, require_seed=True)

    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    layout = RunLayout(out_dir=args.out_dir, run_id=args.run_id)

    if args.command == "discover":
        run_discovery(layout, seed=args.seed, profile=args.profile, max_pages=args.max_pages)
    elif args.command == "fetch":
        run_fetch(layout)
    elif args.command == "extract":
        run_extract(layout)
    elif args.command == "map":
        run_map(layout)
    elif args.command == "validate":
        run_validate(layout)
    elif args.command == "package":
        run_package(layout)
    elif args.command == "run":
        run_discovery(layout, seed=args.seed, profile=args.profile, max_pages=args.max_pages)
        run_fetch(layout)
        run_extract(layout)
        run_map(layout)
        run_validate(layout)
        run_package(layout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
