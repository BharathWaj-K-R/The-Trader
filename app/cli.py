import argparse

from .agent import TradingAgent


def main():
    parser = argparse.ArgumentParser(description="The-Trader paper research platform")
    sub = parser.add_subparsers(dest="command", required=True)

    for name in ("backtest", "paper"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--symbol", default="BTC/USDT")
        cmd.add_argument("--timeframe", default="30m")
        cmd.add_argument("--bars", type=int, default=300)

    cmd = sub.add_parser("improve")
    cmd.add_argument("--symbol", default="BTC/USDT")
    cmd.add_argument("--timeframe", default="30m")
    cmd.add_argument("--bars", type=int, default=700)
    cmd.add_argument("--cycles", type=int, default=10)

    cmd = sub.add_parser("walk-forward")
    cmd.add_argument("--symbol", default="BTC/USDT")
    cmd.add_argument("--timeframe", default="30m")
    cmd.add_argument("--bars", type=int, default=700)
    cmd.add_argument("--folds", type=int, default=4)
    cmd.add_argument("--cycles", type=int, default=6)

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

    report = agent.walk_forward(args.symbol, args.timeframe, args.bars, args.folds, args.cycles)
    print(report)


if __name__ == "__main__":
    main()
