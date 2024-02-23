```shell
git clone https://github.com/CirclesUBI/path-visualizer.git
cd path-visualizer/src

pip install plotly
pip install web3

python test.py --source "0x6FAe976eb90127B895ceDdf8311864cdA42AC6Ac" \
	--sink "0x42cEDde51198D1773590311E2A340DC06B24cB37" \
	--amount 999999999999999999999999999 \
	--pathfinder-url "https://pathfinder.circlesubi.id"
```
