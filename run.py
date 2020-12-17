#!/usr/bin/env python3
"""Run the gear: set up for and call command-line command."""

import json
import sys
from pathlib import Path

import flywheel_gear_toolkit
from flywheel_gear_toolkit.interfaces.command_line import exec_command
from flywheel_gear_toolkit.licenses.freesurfer import install_freesurfer_license
from flywheel_gear_toolkit.utils.zip_tools import zip_output

SUBJECTS_DIR = Path("/usr/local/freesurfer/subjects")
LICENSE_FILE = "/usr/local/freesurfer/license.txt"


def main(gtk_context):

    gtk_context.init_logging("debug")
    gtk_context.log_config()
    log = gtk_context.log

    acquisition_id =  gtk_context.config_json["inputs"]["anatomical"]["hierarchy"]["id"]
    file_name =  gtk_context.config_json["inputs"]["anatomical"]["location"]["name"]
    log.info(f"acquisition {acquisition_id} {file_name}")

    fw = gtk_context.client
    full_file = fw.get_acquisition_file_info(acquisition_id, file_name)
    field_strength = full_file.info.get('MagneticFieldStrength')
    log.info(f"field_strength = {field_strength}")

    # grab environment for gear (saved in Dockerfile)
    with open("/tmp/gear_environ.json", "r") as f:
        environ = json.load(f)

    install_freesurfer_license(gtk_context, LICENSE_FILE)

    subject_id = fw.get_analysis(gtk_context.destination["id"]).parents.subject
    subject = fw.get_subject(subject_id)
    subject_id = subject.label

    subject_dir = Path(SUBJECTS_DIR / subject_id)
    work_dir = gtk_context.output_dir / subject_id
    if not work_dir.is_symlink():
        work_dir.symlink_to(subject_dir)

    anat_dir = Path("/flywheel/v0/input/anatomical")
    anatomical_list = list(anat_dir.rglob("*.nii*"))
    anatomical = str(anatomical_list[0])

    # The main command line command to be run:
    command = [
        "recon-all",
        "-i",
        anatomical,
        "-subjid",
        subject_id]
    if field_strength == 3:
        command.append("-3T")
    command += ["-all",
        "&&",
        "segmentBS.sh",
        subject_id,
        "&&",
        "gtmseg",
        "--s",
        subject_id,
    ]

    try:
        return_code = 0

        exec_command(
            command,
            environ=environ,
            dry_run=False,  # Set to True for testing
            shell=True,
            cont_output=True,
        )

    except RuntimeError as exc:
        log.critical(exc)
        log.exception("Unable to execute command.")
        return_code = 1

    # zip entire output/<subject_id> folder into
    #  <gear_name>_<subject_id>_<analysis.id>.zip
    zip_file_name = (
        gtk_context.manifest["name"]
        + f"_{subject_id}_{gtk_context.destination['id']}.zip"
    )
    if subject_dir.exists():
        log.info("Saving %s in %s as output", subject_id, SUBJECTS_DIR)
        zip_output(str(gtk_context.output_dir), subject_id, zip_file_name)
    else:
        log.error("Could not find %s in %s", subject_id, SUBJECTS_DIR)

    # clean up: remove symbolic link to subject so it won't be in output
    if work_dir.exists():
        log.debug('removing output directory "%s"', str(work_dir))
        work_dir.unlink()
    else:
        log.info("Output directory does not exist so it cannot be removed")

    log.info("Gear is done.  Returning %d", return_code)

    sys.exit(return_code)


if __name__ == "__main__":
    gear_toolkit_context = flywheel_gear_toolkit.GearToolkitContext()
    main(gear_toolkit_context)
