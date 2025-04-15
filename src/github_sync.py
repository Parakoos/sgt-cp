import storage
import ssl
import socketpool
import wifi
import time
import supervisor
from adafruit_requests import Session
from os import getenv

GITHUB_USER = getenv("GITHUB_USER")
GITHUB_REPO = getenv("GITHUB_REPO")
GITHUB_BRANCH = getenv("GITHUB_BRANCH")
GITHUB_TOKEN = getenv("GITHUB_TOKEN")
GITHUB_USER_AGENT = getenv("GITHUB_USER_AGENT")

try:
	storage.remount("/", readonly=False)
except RuntimeError as e:
	print('Failed to remount the file-system to be writeable. Cannot pull data from GitHub without that.')
	raise e

pool = socketpool.SocketPool(wifi.radio)
ssl_context = ssl.create_default_context()
session = Session(pool, ssl_context)
headers={'Authorization':f"Bearer {GITHUB_TOKEN}",'User-Agent':GITHUB_USER_AGENT}

with session.get(f'https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/branches/{GITHUB_BRANCH}', headers=headers) as response:
	json = response.json()
	tree_url = json['commit']['commit']['tree']['url']

with session.get(f"{tree_url}?recursive=1", headers=headers) as response:
	json = response.json()
	files = json['tree']

for file in files:
	if file['type'] == 'blob' and file['path'].endswith('.mpy'):
		print(file['path'])
		with session.get(file['url'], headers=headers|{'accept': 'application/vnd.github.raw+json'}) as response:
			with open(file['path'], "w") as fp:
				fp.write(response.content if file['path'].endswith('.mpy') else response.text)
print('Pulled down the latest data from GitHub! Reloading in 1 second.')
time.sleep(1)
supervisor.reload()