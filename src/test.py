import argparse
import pathfinder


def main():
	parser = argparse.ArgumentParser(description="Execute the Pathfinder.")
	parser.add_argument('--source', type=str,
						help="The provider to use for the Web3 connection.")
	parser.add_argument('--sink', type=str,
						help="The recipient address.")
	parser.add_argument('--amount', type=str,
						help="The amount in wei.")
	parser.add_argument('--pathfinder-url', type=str, default="http://65.109.109.165:8080/",
						help="The url to the pathfinder service.")

	cli_args = parser.parse_args()

	print(cli_args)

	from_ = cli_args.source
	to = cli_args.sink
	value = cli_args.amount

	p = pathfinder.Pathfinder(cli_args.pathfinder_url)
	hubTransferArgs= p.get_args_for_path(from_, to, value)[:-1]

	print(hubTransferArgs[0])
	print(hubTransferArgs[1])
	print(hubTransferArgs[2])
	print(hubTransferArgs[3])

	colors = 0
	try:
		p.simulate_path(*hubTransferArgs, from_)
		print("Sim succeeded")
	except:
		print("Sim failed")

	shanky = p.get_shanky(*hubTransferArgs)
	p.draw_shanky(*shanky, colors)


if __name__ == "__main__":
	main()

