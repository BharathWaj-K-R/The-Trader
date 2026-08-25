import json
import sqlite3
from pathlib import Path


class Store:
    def __init__(self, path="data/agent.db"):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, check_same_thread=False)
        self.db.row_factory = sqlite3.Row
        self.db.executescript(
            """
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
            CREATE TABLE IF NOT EXISTS paper_accounts(
                account_id TEXT PRIMARY KEY,
                updated_at TEXT NOT NULL,
                state TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS research_reports(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                kind TEXT NOT NULL,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                report TEXT NOT NULL
            );
            """
        )
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
            "INSERT INTO trades(run_id,timestamp,side,price,quantity,fee,pnl,reason) VALUES(?,?,?,?,?,?,?,?)",
            (run_id, trade.timestamp.isoformat(), trade.side, trade.price, trade.quantity, trade.fee, trade.pnl, trade.reason),
        )
        self.db.commit()

    def add_experiment(self, baseline, candidate, baseline_score, candidate_score, accepted, reason):
        self.db.execute(
            "INSERT INTO experiments(baseline,candidate,baseline_score,candidate_score,accepted,reason) VALUES(?,?,?,?,?,?)",
            (json.dumps(baseline), json.dumps(candidate), baseline_score, candidate_score, int(accepted), reason),
        )
        self.db.commit()

    def activate_strategy(self, params, score):
        self.db.execute("UPDATE strategy_versions SET active=0")
        self.db.execute(
            "INSERT INTO strategy_versions(params,score,active) VALUES(?,?,1)",
            (json.dumps(params), score),
        )
        self.db.commit()

    def active_strategy(self):
        row = self.db.execute(
            "SELECT params, score FROM strategy_versions WHERE active=1 ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if not row:
            return None
        return {"params": json.loads(row["params"]), "score": row["score"]}

    def save_paper_state(self, account_id, state):
        self.db.execute(
            "INSERT INTO paper_accounts(account_id,updated_at,state) VALUES(?,?,?) ON CONFLICT(account_id) DO UPDATE SET updated_at=excluded.updated_at,state=excluded.state",
            (account_id, state.get("updated_at", ""), json.dumps(state)),
        )
        self.db.commit()

    def get_paper_state(self, account_id):
        row = self.db.execute("SELECT state FROM paper_accounts WHERE account_id=?", (account_id,)).fetchone()
        return json.loads(row["state"]) if row else None

    def delete_paper_state(self, account_id):
        self.db.execute("DELETE FROM paper_accounts WHERE account_id=?", (account_id,))
        self.db.commit()

    def add_research_report(self, kind, symbol, timeframe, report):
        self.db.execute(
            "INSERT INTO research_reports(kind,symbol,timeframe,report) VALUES(?,?,?,?)",
            (kind, symbol, timeframe, json.dumps(report)),
        )
        self.db.commit()

    def recent(self, table, limit=50):
        allowed = {"trades", "experiments", "runs", "strategy_versions", "research_reports", "paper_accounts"}
        if table not in allowed:
            raise ValueError("invalid table")
        return [dict(row) for row in self.db.execute(f"SELECT * FROM {table} ORDER BY rowid DESC LIMIT ?", (limit,)).fetchall()]
