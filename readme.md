```shell
git clone https://github.com/CirclesUBI/path-visualizer.git
cd path-visualizer/src

pip install plotly
pip install web3

python test.py --source "0xDE374ece6fA50e781E81Aac78e811b33D16912c7" \
	--sink "0x431a8E4FD58E0D5729C146AD18c47e8122614Cf3" \
	--amount 999999999999999999999999999 \
	--pathfinder-url "https://pathfinder.circlesubi.id"
```
