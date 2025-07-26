import requests
from typing import Annotated
import configparser
from mcp.server.fastmcp import FastMCP
import os

# import logging
# logging.basicConfig(level=logging.DEBUG)

OWNER = "" 
REPO = ""

ALL_COMMIT = []

mcp = FastMCP("mcp-vuln-github-commit")

def request_json(method:str, url:str, headers:dict) -> dict:
    '''json request 함수'''
    req = None
    if(method == 'GET'):
        req = requests.get
    elif(method == 'POST'):
        req = requests.post

    resp = req(url, headers=headers)
    if resp.status_code != 200:
        return {"error": f"error {resp.status_code}: {resp.text}"}

    return resp.json()
"""
def is_latest_commit() -> bool:
    '''현재 저장된 커밋이 최신인지 확인하는 함수'''
    headers = {}
    with open('latest_commit', 'r') as f:
        latest = f.readline().strip()
        
    return latest == ALL_COMMIT[0]["sha"]

def find_parents_commit(commits: Annotated[str, "자식 commit"], sha:Annotated[str, "자식 commit 해시"]) -> list:
    '''최신 커밋에서 부모(로컬에 저장된) 커밋을 찾는 함수'''
    for commit in commits:
        if commit["sha"] == sha:
            return [parent["sha"] for parent in commit.get("parents", [])]
    return []
"""

@mcp.tool()
def get_all_commit():
    '''github api를 통해 전체 commit을 가져오는 함수'''
    headers = {}
    COMMIT_PATH = f"https://api.github.com/repos/{OWNER}/{REPO}/commits"
    resp = request_json('GET', COMMIT_PATH, headers=headers)
    commit_list = []
    for output in resp:
        # 필요한 속성은 추가할 것
        commit_list.append({
            "sha": output["sha"],
            "message": output["commit"]["message"],
            "author": output["commit"]["author"]["name"],
            "date": output["commit"]["author"]["date"],
            "url": output["commit"]["url"],
        })

        parents_list = []
        for parent in output["parents"]:
            parents_list.append({
                "parents_sha": parent["sha"],
                "parents_url": parent["url"],
            })

        commit_list.append(parents_list)
    
    ALL_COMMIT = commit_list

@mcp.tool()
def compare_commit_log_files(base: Annotated[str, "기준 커밋 해시"], target: Annotated[str, "비교 대상 커밋 해시"]) -> tuple:
    '''base 커밋에서 target 커밋로의 바뀐 파일 내용들을 반환하는 함수'''
    headers = {}
    COMPARE_PATH = f"https://api.github.com/repos/{OWNER}/{REPO}/compare/{base}...{target}"
    resp = request_json('GET', COMPARE_PATH, headers=headers)

    files = []
    for output in resp['files']:
        files.append({
            "filename":output["filename"], # 파일 이름
            "patch":output["patch"], # patch된 코드 내용
            "changes":output["changes"], # 바뀐 총 코드 라인 수 (additions + deletions)
            "additions":output["additions"], # 추가된 코드 라인 수
            "deletions":output["deletions"], # 삭제된 코드 라인 수
            "status":output["status"], # 커밋 메세지
        })

    return files 

@mcp.tool()
def check_commit_log_files(commit_hash:Annotated[str, "특정 커밋 해시"]) -> dict:
    '''특정 커밋 로그에서 메타데이터와 바뀐 파일을 가져오는 함수'''
    headers = {}
    COMMITS_PATH = f"https://api.github.com/repos/{OWNER}/{REPO}/commits/{commit_hash}"
    resp = request_json('GET', COMMITS_PATH, headers=headers)

    files = []
    for output in resp['files']:
        files.append({
            "filename":output["filename"], # 파일 이름
            "patch":output["patch"], # patch된 코드 내용
            "changes":output["changes"], # 바뀐 총 코드 라인 수 (additions + deletions)
            "additions":output["additions"], # 추가된 코드 라인 수
            "deletions":output["deletions"], # 삭제된 코드 라인 수
            "status":output["status"], # 커밋 메세지
        })

    return files 
    

@mcp.prompt()
def prompt(msg: str) -> str:
    return f"""

    * github commit log에 대해 취약점을 분석을 목표로 함 *

    [도구]
    - get_all_commit(): 해당 레포의 모든 커밋을 가져오는 함수
    - compare_commit_log_files(base: str, target: str) -> dict: 두 커밋을 비교한 로그를 가져오는 함수 / base는 기준 커밋 해시, target은 비교 대상 커밋 해시
    - check_commit_log_files(commit_hash: str) -> dict:  특정 커밋 로그를 가져오는 함수 / commit_hash는 특정 커밋 해시

    요청 메세지: {msg}

    취약한 코드를 보여주고, 취약점 분석과 함께 평가해줘.

    """

def set_repository():
    
    global OWNER
    global REPO

    config = configparser.ConfigParser()
    config.read(os.path.dirname(os.path.abspath(__file__)) + '\\settings.ini')

    OWNER = config['Repository']['owner']
    REPO = config['Repository']['repo']

def main():
    set_repository()
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()