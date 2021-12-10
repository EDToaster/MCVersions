#! /usr/bin/python3
import argparse
import requests
import json
from typing import List
from dataclasses import dataclass, field
from collections import defaultdict
from os import path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape
env = Environment(
    loader=FileSystemLoader("resources"),
    autoescape=select_autoescape()
)

VERSION_MANIFEST_JSON = "https://launchermeta.mojang.com/mc/game/version_manifest.json"

def parse_args():
    """ Parses arguments
        
        returns: 
            { output_directory, force } object
    """
    parser = argparse.ArgumentParser(description='Fetch Minecraft Server Versions and Links')
    parser.add_argument('-o', '--output_directory', type=str, required=True, help='Output directory all data files')
    return parser.parse_args()

@dataclass
class Download:
    """ Class for holding downloads """
    sha1: str
    size: int
    url: str

@dataclass
class Version:
    """ Class for holding Version """
    url: str
    id_: str
    type_: str
    release_time: str 
    server: Download
    server_mappings: Download

@dataclass
class VersionManifest:
    """ Class for holding the Version Manifest 
        version_string: a string of release/snapshot that can
                        deliniate between two version manifests
    """
    version_string: str
    versions: List[Version]


EXPERIMENTAL_1_18_VERSIONS: List[Version] = [
    Version(
        None,
        "1.18-exp1",
        "experimental",
        "2021-09-01T00:00:00+00:00",
        Download(
            None,
            None,
            "https://launcher.mojang.com/v1/objects/231bba2a21e18b8c60976e1f6110c053b7b93226/1_18_experimental-snapshot-1.zip"
        ),
        None
    ),
    Version(
        None,
        "1.18-exp2",
        "experimental",
        "2021-09-02T00:00:00+00:00",
        Download(
            None,
            None,
            "https://launcher.mojang.com/v1/objects/0adfe4f321aa45248fc88ac888bed5556633e7fb/1_18_experimental-snapshot-2.zip"
        ),
        None
    ),
    Version(
        None,
        "1.18-exp3",
        "experimental",
        "2021-09-03T00:00:00+00:00",
        Download(
            None,
            None,
            "https://launcher.mojang.com/v1/objects/846648ff9fe60310d584061261de43010e5c722b/1_18_experimental-snapshot-3.zip"
        ),
        None
    ),
    Version(
        None,
        "1.18-exp4",
        "experimental",
        "2021-09-04T00:00:00+00:00",
        Download(
            None,
            None,
            "https://launcher.mojang.com/v1/objects/b92a360cbae2eb896a62964ad8c06c3493b6c390/1_18_experimental-snapshot-4.zip"
        ),
        None
    ),
    Version(
        None,
        "1.18-exp5",
        "experimental",
        "2021-09-05T00:00:00+00:00",
        Download(
            None,
            None,
            "https://launcher.mojang.com/v1/objects/d9cb7f6fb4e440862adfb40a385d83e3f8d154db/1_18_experimental-snapshot-5.zip"
        ),
        None
    ),
    Version(
        None,
        "1.18-exp6",
        "experimental",
        "2021-09-06T00:00:00+00:00",
        Download(
            None,
            None,
            "https://launcher.mojang.com/v1/objects/4697c84c6a347d0b8766759d5b00bc5a00b1b858/1_18_experimental-snapshot-6.zip"
        ),
        None
    ),
    Version(
        None,
        "1.18-exp7",
        "experimental",
        "2021-09-08T00:00:00+00:00",
        Download(
            None,
            None,
            "https://launcher.mojang.com/v1/objects/ab4ecebb133f56dd4c4c4c3257f030a947ddea84/1_18_experimental-snapshot-7.zip"
        ),
        None
    ),
]

def process_version(url) -> Version:
    """ Fetches a specific version from the url and filters the information

        returns: Version
    """
    # retrieve None instead of KeyError
    version = defaultdict(lambda: None, json.loads(requests.get(url).content))

    # set id
    id_ = version['id']
    type_ = version['type']
    release_time = version['releaseTime']

    server = None
    server_mappings = None

    if version['downloads'] is not None:
        downloads = defaultdict(lambda: None, version['downloads'])

        if downloads['server'] is not None:
            d = defaultdict(lambda: None, downloads['server'])
            server = Download(d['sha1'], d['size'], d['url'])

        if downloads['server_mappings'] is not None:
            d = defaultdict(lambda: None, downloads['server_mappings'])
            server_mappings = Download(d['sha1'], d['size'], d['url'])


    # set url, id, type, release_time
    v = Version(url, id_, type_, release_time, server, server_mappings)
    print(v)
    return v

def process_version_manifest(previous_version_string) -> VersionManifest:
    """ Fetches the version manifest and parses it
    """
    vm = requests.get(VERSION_MANIFEST_JSON).content
    vm_json = json.loads(vm)
    url_list = [v["url"]for v in vm_json["versions"]]

    version_string = f"{vm_json['latest']['release']}/{vm_json['latest']['snapshot']}"

    if previous_version_string == version_string:
        return None

    version_list = [process_version(url) for url in url_list] + EXPERIMENTAL_1_18_VERSIONS
    version_list = sorted(version_list, key = lambda v: datetime.fromisoformat(v.release_time))[::-1]
    
    return VersionManifest(version_string, version_list)

def generate_and_print_md(version_list, version_string, readme_file, dedupe_file) -> str:

    readme_template = env.get_template("README.md.jinja")
    dedupe_template = env.get_template("dedupe.jinja")

    readme = readme_template.render(version_list=version_list, version_string=version_string)
    dedupe = dedupe_template.render(version_string=version_string)


    with open(readme_file, "w") as f:
        f.write(readme)
    with open(dedupe_file, "w") as f:
        f.write(dedupe)

def main():
    args = parse_args()
    output_dir = args.output_directory

    readme_file = path.join(output_dir, "README.md")
    dedupe_file = path.join(output_dir, "dedupe")

    previous_version_string = None
    try:
        with open(dedupe_file, "r") as f:
            previous_version_string = f.readline()
    except FileNotFoundError:
        print("dedupe path not found, going to assume this is first time running this script") 

    version_manifest = process_version_manifest(previous_version_string)
    if version_manifest is None:
        print(f"Previous version {previous_version_string} is the same, not going to fetch versions")
        return

    generate_and_print_md(version_manifest.versions, version_manifest.version_string, readme_file, dedupe_file)

    print(f"Finished writing versions {version_manifest.version_string}")

if __name__ == "__main__":
    main()