![mastodon-shaarli-sync]([http://url/to/img.png](https://kudusch.de/projects/uploads/files/icon.png))

# mastodon-shaarli-sync

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
