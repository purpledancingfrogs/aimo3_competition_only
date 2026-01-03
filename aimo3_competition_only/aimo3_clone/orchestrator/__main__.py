import sys, json, subprocess

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--mission', required=True)
    args = parser.parse_args()
    mission_file = args.mission

    with open(mission_file,'r') as f:
        mission=json.load(f)

    for step in mission['payload']['steps']:
        if step['op']=='RUN_SCRIPT':
            subprocess.run([sys.executable, step['path']], check=True)
