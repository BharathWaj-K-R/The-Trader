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
            CREATE TABLE IF NOT EXISTS execution_control(
                account_id TEXT PRIMARY KEY,
                updated_at TEXT NOT NULL,
                armed INTEGER NOT NULL DEFAULT 0,
                kill_switch INTEGER NOT NULL DEFAULT 0,
                metadata TEXT NOT NULL DEFAULT '{}'
            );
            CREATE TABLE IF NOT EXISTS execution_orders(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                account_id TEXT NOT NULL,
                client_order_id TEXT,
                exchange_order_id TEXT,
                symbol TEXT NOT NULL,
                order_type TEXT NOT NULL,
                side TEXT NOT NULL,
                amount REAL NOT NULL,
                price REAL,
                status TEXT NOT NULL,
                filled REAL DEFAULT 0,
                average REAL,
                fee REAL,
                raw TEXT NOT NULL DEFAULT '{}'
            );
            CREATE INDEX IF NOT EXISTS idx_execution_orders_account_created
                ON execution_orders(account_id, created_at);
            CREATE TABLE IF NOT EXISTS execution_snapshots(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                account_id TEXT NOT NULL,
                snapshot TEXT NOT NULL
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

    def save_execution_control(self, account_id, armed, kill_switch, metadata=None):
        self.db.execute(
            """INSERT INTO execution_control(account_id,updated_at,armed,kill_switch,metadata)
               VALUES(?,datetime('now'),?,?,?)
               ON CONFLICT(account_id) DO UPDATE SET
                 updated_at=datetime('now'), armed=excluded.armed,
                 kill_switch=excluded.kill_switch, metadata=excluded.metadata""",
            (account_id, int(armed), int(kill_switch), json.dumps(metadata or {})),
        )
        self.db.commit()

    def get_execution_control(self, account_id):
        row = self.db.execute(
            "SELECT * FROM execution_control WHERE account_id=?", (account_id,)
        ).fetchone()
        if not row:
            return {"account_id": account_id, "armed": False, "kill_switch": False, "metadata": {}}
        return {
            "account_id": account_id,
            "armed": bool(row["armed"]),
            "kill_switch": bool(row["kill_switch"]),
            "metadata": json.loads(row["metadata"] or "{}"),
            "updated_at": row["updated_at"],
        }

    def add_execution_order(self, account_id, order):
        cur = self.db.execute(
            """INSERT INTO execution_orders(
                account_id,client_order_id,exchange_order_id,symbol,order_type,side,
                amount,price,status,filled,average,fee,raw
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                account_id, order.get("clientOrderId"), order.get("id"), order["symbol"],
                order["type"], order["side"], order["amount"], order.get("price"),
                order.get("status") or "open", order.get("filled") or 0,
                order.get("average"), order.get("fee", {}).get("cost") if isinstance(order.get("fee"), dict) else None,
                json.dumps(order),
            ),
        )
        self.db.commit()
        return cur.lastrowid

    def update_execution_order(self, exchange_order_id, order):
        self.db.execute(
            """UPDATE execution_orders SET status=?,filled=?,average=?,fee=?,raw=?
               WHERE exchange_order_id=?""",
            (
                order.get("status") or "unknown", order.get("filled") or 0,
                order.get("average"), order.get("fee", {}).get("cost") if isinstance(order.get("fee"), dict) else None,
                json.dumps(order), exchange_order_id,
            ),
        )
        self.db.commit()

    def recent_execution_orders(self, account_id, limit=50):
        return [
            dict(row)
            for row in self.db.execute(
                "SELECT * FROM execution_orders WHERE account_id=? ORDER BY id DESC LIMIT ?",
                (account_id, limit),
            ).fetchall()
        ]

    def count_execution_orders_today(self, account_id):
        row = self.db.execute(
            """SELECT COUNT(*) AS n FROM execution_orders
               WHERE account_id=? AND date(created_at)=date('now')""",
            (account_id,),
        ).fetchone()
        return int(row["n"])

    def add_execution_snapshot(self, account_id, snapshot):
        self.db.execute(
            "INSERT INTO execution_snapshots(account_id,snapshot) VALUES(?,?)",
            (account_id, json.dumps(snapshot)),
        )
        self.db.commit()

    def recent_execution_snapshots(self, account_id, limit=20):
        return [
            {**dict(row), "snapshot": json.loads(row["snapshot"])}
            for row in self.db.execute(
                "SELECT * FROM execution_snapshots WHERE account_id=? ORDER BY id DESC LIMIT ?",
                (account_id, limit),
            ).fetchall()
        ]

    def recent(self, table, limit=50):
        allowed = {
            "trades", "experiments", "runs", "strategy_versions",
            "research_reports", "paper_accounts", "execution_orders",
            "execution_control", "execution_snapshots",
        }
        if table not in allowed:
            raise ValueError("invalid table")
        return [
            dict(row)
            for row in self.db.execute(
                f"SELECT * FROM {table} ORDER BY rowid DESC LIMIT ?", (limit,)
            ).fetchall()
        ]
