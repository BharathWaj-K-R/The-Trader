import argparse
from .agent import TradingAgent


def main():
    parser = argparse.ArgumentParser(description="The-Trader paper agent")
    sub = parser.add_subparsers(dest="command", required=True)

    for name in ("backtest", "paper"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--symbol", default="BTC/USDT")
        cmd.add_argument("--timeframe", default="30m")
        cmd.add_argument("--bars", type=int, default=300)

    cmd = sub.add_parser("improve")
    cmd.add_argument("--symbol", default="BTC/USDT")
    cmd.add_argument("--timeframe", default="30m")
    cmd.add_argument("--bars", type=int, default=500)
    cmd.add_argument("--cycles", type=int, default=5)

    args = parser.parse_args()
    agent = TradingAgent()

    if args.command in {"backtest", "paper"}:
        result, trades = agent.backtest(args.symbol, args.timeframe, args.bars)
        print(result)
        print(f"trades={len(trades)}")
    else:
        result, history = agent.improve(args.symbol, args.timeframe, args.bars, args.cycles)
        print(result)
        print("strategy=", agent.params.as_dict())
        for experiment in history:
            print(experiment)


if __name__ == "__main__":
    main()
