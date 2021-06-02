#! /usr/bin/python3
import argparse
import requests
import json
import dill
from dataclasses import dataclass
from collections import defaultdict
from os import path
from jinja2 import Environment, FileSystemLoader, select_autoescape
env = Environment(
    loader=FileSystemLoader("resources"),
    autoescape=select_autoescape()
)

VERSION_MANIFEST_JSON = "https://launchermeta.mojang.com/mc/game/version_manifest.json"

def parse_args():
    """ Parses arguments
        
        returns: 
            { output_directory } object
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

def process_version(url):
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

def process_version_manifest():
    """ Fetches the version manifest and parses it
    """
    vm = requests.get(VERSION_MANIFEST_JSON).content
    vm_json = json.loads(vm)
    url_list = [v["url"]for v in vm_json["versions"]]
    
    return [process_version(url) for url in url_list]

def generate_markdown(version_list, template_file) -> str:
    template = env.get_template(template_file)
    return template.render(version_list=version_list)

def main():
    args = parse_args()
    output_dir = args.output_directory

    dill_file = path.join(output_dir, "versions.dill")
    markdown_file = path.join(output_dir, "README.md")
    markdown_template = "template.md.jinja"

    version_list = None

    # check if there is already a dill file
    if path.exists(dill_file):
        # load from file
        print(f"Dill file {dill_file} exists, using that")
        with open(dill_file, "rb") as f:
            version_list = dill.load(f)
    else:
        print(f"Dill file {dill_file} does not exist, querying")
        version_list = process_version_manifest()
        # write to file
        with open(dill_file, "wb") as f:
            f.write(dill.dumps(version_list))

    markdown = generate_markdown(version_list, markdown_template)
    with open(markdown_file, "w") as f:
        f.write(markdown)






if __name__ == "__main__":
    main()