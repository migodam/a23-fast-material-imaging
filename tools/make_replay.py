"""Create an empty-output, independently budgeted reproduction workspace.

Copies public frozen code/configuration/input only; never starts a job.
Published evidence, credentials and derived physics caches are not copied.
"""
from pathlib import Path
import argparse,shutil

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--destination',required=True,type=Path)
    args=p.parse_args();source=Path(__file__).resolve().parents[1]
    destination=args.destination.expanduser().resolve()
    if destination.exists() or source==destination or source in destination.parents:
        p.error('destination must be a new directory outside this repository')
    destination.mkdir(parents=True)
    for name in ('src','vendor','tests','configs','data','validation','tools'):
        shutil.copytree(source/name,destination/name,
            ignore=shutil.ignore_patterns('__pycache__','*.pyc','private','.cache'))
    for name in ('FROZEN_CONFIG.json','SOURCE_MANIFEST.json','RUN_SOURCE_SNAPSHOT.json','LICENSE'):
        shutil.copy2(source/name,destination/name)
    print('Copied frozen inputs and code. No physics, labels or training executed.')
    print(destination)

if __name__=='__main__':main()
