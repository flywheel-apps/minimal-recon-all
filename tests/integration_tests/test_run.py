#!/usr/bin/env python3
"""Test in a gear-like environment by unzipping config.json, input/, output, etc."""

import json
import os
import shutil
import zipfile
from pathlib import Path
from unittest import TestCase

import flywheel_gear_toolkit
import pytest
from flywheel_gear_toolkit.utils.zip_tools import unzip_archive

import run


DRY_FILE = (
    "/flywheel/v0/output/freesurfer-recon-all_TOME_3024_5db3392669d4f3002a16ec4c.zip"
)


def test_platform_works(capfd, install_gear, print_captured, search_sysout):

    user_json = Path(Path.home() / ".config/flywheel/user.json")
    if not user_json.exists():
        TestCase.skipTest("", f"No API key available in {str(user_json)}")

    install_gear("platform.zip")

    with flywheel_gear_toolkit.GearToolkitContext(input_args=[]) as gtk_context:

        with pytest.raises(SystemExit) as excinfo:

            run.main(gtk_context)

        captured = capfd.readouterr()
        print_captured(captured)

        assert excinfo.type == SystemExit
        assert excinfo.value.code == 0
        assert search_sysout(captured, "-3T -all && segmentBS.sh sub-TOME3024")


def test_dry_run_works(capfd, install_gear, print_captured, search_sysout):

    user_json = Path(Path.home() / ".config/flywheel/user.json")
    if not user_json.exists():
        TestCase.skipTest("", f"No API key available in {str(user_json)}")

    install_gear("dry_run.zip")

    with flywheel_gear_toolkit.GearToolkitContext(input_args=[]) as gtk_context:

        with pytest.raises(SystemExit) as excinfo:

            run.main(gtk_context)

        captured = capfd.readouterr()
        print_captured(captured)

        # print("run.METADATA", json.dumps(run.METADATA, indent=4))

        assert excinfo.type == SystemExit
        assert excinfo.value.code == 0
        assert search_sysout(captured, "gtmseg --s TOME_3024")
