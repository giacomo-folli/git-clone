import argparse, collections, hashlib, os
import struct, zlib

from . import cli
from .lib import sbam


def main() -> None:
    cli_service = cli.Service()
    args = cli_service.parser.parse_args()

    sbam_service = sbam.Service()
    sbam_service.run(args)
