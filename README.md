# mastodon-shaarli-sync
<img src="https://raw.githubusercontent.com/Kudusch/mastodon-shaarli-sync/main/icon.png" width="200" />

Sync mastodon bookmarks to shaarli

## Installation
```
git clone https://github.com/Kudusch/mastodon-shaarli-sync
cd mastodon-shaarli-sync/
python3 -m virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py

crontab -e

*/5 * * * * [installation_path]/mastodon-shaarli-sync/venv/bin/python3 [installation_path]/mastodon-shaarli-sync/main.py >> [installation_path]/mastodon-shaarli-sync/log.txt
```
