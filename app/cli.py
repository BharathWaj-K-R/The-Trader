import argparse

from .agent import TradingAgent


def market_args(parser, default_bars=700):
    parser.add_argument("--symbol", default="BTC/USDT")
    parser.add_argument("--timeframe", default="30m")
    parser.add_argument("--bars", type=int, default=default_bars)


def main():
    parser = argparse.ArgumentParser(description="The-Trader paper research platform")
    sub = parser.add_subparsers(dest="command", required=True)

    for name in ("backtest", "paper"):
        cmd = sub.add_parser(name)
        market_args(cmd, 300)

    cmd = sub.add_parser("improve")
    market_args(cmd, 700)
    cmd.add_argument("--cycles", type=int, default=10)

    cmd = sub.add_parser("walk-forward")
    market_args(cmd, 700)
    cmd.add_argument("--folds", type=int, default=4)
    cmd.add_argument("--cycles", type=int, default=6)

    cmd = sub.add_parser("stress-test")
    market_args(cmd, 500)

    sub.add_parser("daemon", help="run continuous paper ticks")

    args = parser.parse_args()
    if args.command == "daemon":
        from .scheduler import run_scheduler
        run_scheduler()
        return

    agent = TradingAgent()
    if args.command in {"backtest", "paper"}:
        result, trades, analytics = agent.backtest(args.symbol, args.timeframe, args.bars)
        print("goal=", result)
        print("analytics=", analytics)
        print(f"trades={len(trades)}")
        return

    if args.command == "improve":
        result, history = agent.improve(args.symbol, args.timeframe, args.bars, args.cycles)
        print("goal=", result)
        print("strategy=", agent.params.as_dict())
        for experiment in history:
            print(experiment)
        return

    if args.command == "walk-forward":
        print(agent.walk_forward(args.symbol, args.timeframe, args.bars, args.folds, args.cycles))
        return

    print(agent.stress_test(args.symbol, args.timeframe, args.bars))


if __name__ == "__main__":
    main()
