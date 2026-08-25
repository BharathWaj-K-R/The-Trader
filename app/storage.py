import json
import sqlite3
from pathlib import Path

class Store:
    def __init__(self, path="data/agent.db"):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS runs(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            kind TEXT NOT NULL,
            symbol TEXT NOT NULL,
            metadata TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS trades(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER,
            timestamp TEXT NOT NULL,
            side TEXT NOT NULL,
            price REAL NOT NULL,
            quantity REAL NOT NULL,
            fee REAL NOT NULL,
            pnl REAL NOT NULL,
            reason TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS experiments(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            baseline TEXT NOT NULL,
            candidate TEXT NOT NULL,
            baseline_score REAL NOT NULL,
            candidate_score REAL NOT NULL,
            accepted INTEGER NOT NULL,
            reason TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS strategy_versions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            params TEXT NOT NULL,
            score REAL NOT NULL,
            active INTEGER NOT NULL
        );
        """)
        self.db.commit()

    def add_run(self, kind, symbol, metadata):
        cur = self.db.execute(
            "INSERT INTO runs(kind,symbol,metadata) VALUES(?,?,?)",
            (kind, symbol, json.dumps(metadata)),
        )
        self.db.commit()
        return cur.lastrowid

    def add_trade(self, run_id, trade):
        self.db.execute(
            "INSERT INTO trades(run_id,timestamp,side,price,quantity,fee,pnl,reason) "
            "VALUES(?,?,?,?,?,?,?,?)",
            (run_id, trade.timestamp.isoformat(), trade.side, trade.price,
             trade.quantity, trade.fee, trade.pnl, trade.reason),
        )
        self.db.commit()

    def add_experiment(self, baseline, candidate, baseline_score,
                       candidate_score, accepted, reason):
        self.db.execute(
            "INSERT INTO experiments(baseline,candidate,baseline_score,candidate_score,accepted,reason) "
            "VALUES(?,?,?,?,?,?)",
            (json.dumps(baseline), json.dumps(candidate), baseline_score,
             candidate_score, int(accepted), reason),
        )
        self.db.commit()

    def activate_strategy(self, params, score):
        self.db.execute("UPDATE strategy_versions SET active=0")
        self.db.execute(
            "INSERT INTO strategy_versions(params,score,active) VALUES(?,?,1)",
            (json.dumps(params), score),
        )
        self.db.commit()

    def recent(self, table, limit=50):
        if table not in {"trades", "experiments", "runs", "strategy_versions"}:
            raise ValueError("invalid table")
        return [dict(row) for row in self.db.execute(
            f"SELECT * FROM {table} ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()]
