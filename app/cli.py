import argparse
import json

from .agent import TradingAgent


def market_args(parser, default_bars=700):
    parser.add_argument("--symbol", default="BTC/USDT")
    parser.add_argument("--timeframe", default="30m")
    parser.add_argument("--bars", type=int, default=default_bars)


def main():
    parser = argparse.ArgumentParser(description="The-Trader research and execution platform")
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

    cmd = sub.add_parser("full-research")
    market_args(cmd, 800)
    cmd.add_argument("--cycles", type=int, default=10)
    cmd.add_argument("--folds", type=int, default=4)

    sub.add_parser("execution-status")
    cmd = sub.add_parser("execution-preflight")
    cmd.add_argument("--symbol", default="BTC/USDT")
    cmd = sub.add_parser("execution-arm")
    cmd.add_argument("--token", required=True)
    sub.add_parser("execution-disarm")
    sub.add_parser("kill-switch")
    cmd = sub.add_parser("kill-switch-reset")
    cmd.add_argument("--token", required=True)
    cmd = sub.add_parser("execute-signal")
    market_args(cmd, 120)
    cmd = sub.add_parser("reconcile")
    cmd.add_argument("--symbol", default="BTC/USDT")

    sub.add_parser("daemon", help="run continuous execution according to EXECUTION_MODE")

    args = parser.parse_args()
    if args.command == "daemon":
        from .scheduler import run_scheduler
        run_scheduler()
        return

    agent = TradingAgent()

    if args.command in {"backtest", "paper"}:
        result, trades, analytics = agent.backtest(args.symbol, args.timeframe, args.bars)
        print(json.dumps({"goal": result, "analytics": analytics, "trade_count": len(trades)}, indent=2, default=str))
        return

    if args.command == "improve":
        result, history = agent.improve(args.symbol, args.timeframe, args.bars, args.cycles)
        print(json.dumps({"goal": result, "strategy": agent.params.as_dict(), "experiments": history}, indent=2, default=str))
        return

    if args.command == "walk-forward":
        print(json.dumps(agent.walk_forward(args.symbol, args.timeframe, args.bars, args.folds, args.cycles), indent=2, default=str))
        return

    if args.command == "stress-test":
        print(json.dumps(agent.stress_test(args.symbol, args.timeframe, args.bars), indent=2, default=str))
        return

    if args.command == "full-research":
        print(json.dumps(agent.full_research(args.symbol, args.timeframe, args.bars, args.cycles, args.folds), indent=2, default=str))
        return

    if args.command == "execution-status":
        print(json.dumps(agent.execution_status(), indent=2, default=str))
        return

    if args.command == "execution-preflight":
        print(json.dumps(agent.execution_preflight(args.symbol), indent=2, default=str))
        return

    if args.command == "execution-arm":
        print(json.dumps(agent.arm_execution(args.token), indent=2, default=str))
        return

    if args.command == "execution-disarm":
        print(json.dumps(agent.disarm_execution(), indent=2, default=str))
        return

    if args.command == "kill-switch":
        print(json.dumps(agent.activate_kill_switch(), indent=2, default=str))
        return

    if args.command == "kill-switch-reset":
        print(json.dumps(agent.reset_kill_switch(args.token), indent=2, default=str))
        return

    if args.command == "execute-signal":
        print(json.dumps(agent.execute_signal(args.symbol, args.timeframe), indent=2, default=str))
        return

    if args.command == "reconcile":
        print(json.dumps(agent.reconcile_execution(args.symbol), indent=2, default=str))
        return


if __name__ == "__main__":
    main()
