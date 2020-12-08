import requests
import argparse


def upload(build_file: str, version: str, token: str):
    auth = {'Authorization': f'token {token}'}
    response = requests.post(f"https://api.anaconda.org/release/mantid/mantidimaging/{version}",
                             headers=auth,
                             data={
                                 "announce": "Announce",
                                 "description": "Mantid Imaging package",
                                 "requirements": "numpy"
                             })
    print(response)

    response = requests.post(f"https://api.anaconda.org/stage/mantid/mantidimaging/{version}/{build_file}",
                             headers=auth)
    print(response)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--version", type=str)
    parser.add_argument("-f", "--build_file", type=str)
    parser.add_argument("-t", "--token", type=str)

    args = parser.parse_args()
    upload(args.build_file, args.version, args.token)
