import argparse
import pathfinder


def main():
	parser = argparse.ArgumentParser(description="Execute the Pathfinder.")
	parser.add_argument('--source', type=str,
						help="The provider to use for the Web3 connection.")
	parser.add_argument('--sink', type=str,
						help="The recipient address.")
	parser.add_argument('--amount', type=str, default="0",
						help="The amount in wei.")
	cli_args = parser.parse_args()

	print(cli_args)

	from_ = cli_args.source
	to = cli_args.sink
	value = cli_args.amount

	## INITILIZE PATHFINDER
	p = pathfinder.Pathfinder("gateway", "land")

	args= p.get_args_for_path(from_, to, value)[:-1]
	#args = p.draw_shanky_from_tx_hash("0xc815c59cc2a1ea4800ded3e92d755da0b4b75aee5114046988e84bdc3f8212fc")

	print(args[0])
	print(args[1])
	print(args[2])
	print(args[3])
	#p.aggregate_token_flows(*args)

	colors = 0
	try:
		p.simulate_path(*args, from_)
		print("Sim succeeded")
	except:
		print("Sim failed")

	shanky = p.get_shanky(*args)
	p.draw_shanky(*shanky, colors)

# Add code here to call specific methods on the `pathfinder` object,
# potentially based on additional command line arguments.


if __name__ == "__main__":
	main()

