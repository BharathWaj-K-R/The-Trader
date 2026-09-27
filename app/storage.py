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
            CREATE TABLE IF NOT EXISTS ai_insights(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                kind TEXT NOT NULL,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                model TEXT NOT NULL,
                payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS notifications(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                symbol TEXT NOT NULL,
                strategy_action TEXT NOT NULL,
                ai_action TEXT,
                risk_approved INTEGER NOT NULL,
                payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS notification_outcomes(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                notification_id INTEGER NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                correct INTEGER NOT NULL,
                realized_return REAL NOT NULL,
                notes TEXT NOT NULL DEFAULT '',
                FOREIGN KEY(notification_id) REFERENCES notifications(id)
            );
            CREATE INDEX IF NOT EXISTS idx_notification_outcomes_symbol
                ON notifications(symbol, created_at);
            """
        )
        columns = {row["name"] for row in self.db.execute("PRAGMA table_info(notification_outcomes)").fetchall()}
        if "human_action" not in columns:
            self.db.execute("ALTER TABLE notification_outcomes ADD COLUMN human_action TEXT NOT NULL DEFAULT 'not_recorded'")
        self.db.commit()

    def add_run(self, kind, symbol, metadata):
        cur = self.db.execute("INSERT INTO runs(kind,symbol,metadata) VALUES(?,?,?)", (kind, symbol, json.dumps(metadata)))
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
        self.db.execute("INSERT INTO strategy_versions(params,score,active) VALUES(?,?,1)", (json.dumps(params), score))
        self.db.commit()

    def active_strategy(self):
        row = self.db.execute("SELECT params, score FROM strategy_versions WHERE active=1 ORDER BY id DESC LIMIT 1").fetchone()
        return {"params": json.loads(row["params"]), "score": row["score"]} if row else None

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

    def add_ai_insight(self, kind, symbol, timeframe, model, payload):
        self.db.execute(
            "INSERT INTO ai_insights(kind,symbol,timeframe,model,payload) VALUES(?,?,?,?,?)",
            (kind, symbol, timeframe, model, json.dumps(payload)),
        )
        self.db.commit()

    def recent_ai_insights(self, limit=30):
        rows = self.db.execute("SELECT * FROM ai_insights ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [{**dict(row), "payload": json.loads(row["payload"])} for row in rows]

    def add_notification(self, decision):
        cur = self.db.execute(
            "INSERT INTO notifications(symbol,strategy_action,ai_action,risk_approved,payload) VALUES(?,?,?,?,?)",
            (
                decision["symbol"],
                decision["strategy_action"],
                decision.get("ai_action"),
                int(decision["risk_approved"]),
                json.dumps(decision),
            ),
        )
        self.db.commit()
        return cur.lastrowid

    def recent_notifications(self, limit=50):
        rows = self.db.execute("SELECT * FROM notifications ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [{**dict(row), "payload": json.loads(row["payload"])} for row in rows]

    def add_notification_outcome(self, notification_id, correct, realized_return, human_action="not_recorded", notes=""):
        if human_action not in {"acted", "not_acted", "not_recorded"}:
            raise ValueError("human_action must be acted, not_acted, or not_recorded")
        self.db.execute(
            "INSERT INTO notification_outcomes(notification_id,correct,realized_return,human_action,notes) VALUES(?,?,?,?,?)",
            (notification_id, int(correct), float(realized_return), human_action, notes),
        )
        self.db.commit()

    def recent_notification_outcomes(self, symbol, limit=100):
        rows = self.db.execute(
            """SELECT o.* FROM notification_outcomes o
               JOIN notifications n ON n.id=o.notification_id
               WHERE n.symbol=? ORDER BY o.id DESC LIMIT ?""",
            (symbol, limit),
        ).fetchall()
        return [dict(row) for row in rows]

    def count_notifications_today(self, symbol):
        row = self.db.execute(
            "SELECT COUNT(*) AS n FROM notifications WHERE symbol=? AND date(created_at)=date('now')",
            (symbol,),
        ).fetchone()
        return int(row["n"])

    def notification_in_cooldown(self, symbol, minutes):
        if minutes <= 0:
            return False
        row = self.db.execute(
            "SELECT created_at FROM notifications WHERE symbol=? ORDER BY id DESC LIMIT 1",
            (symbol,),
        ).fetchone()
        if not row:
            return False
        value = row["created_at"]
        row2 = self.db.execute(
            "SELECT (julianday('now') - julianday(?)) * 1440.0 AS minutes",
            (value,),
        ).fetchone()
        return float(row2["minutes"]) < minutes

    def recent(self, table, limit=50):
        allowed = {
            "trades", "experiments", "runs", "strategy_versions",
            "research_reports", "paper_accounts", "ai_insights",
            "notifications", "notification_outcomes",
        }
        if table not in allowed:
            raise ValueError("invalid table")
        rows = self.db.execute(f"SELECT * FROM {table} ORDER BY rowid DESC LIMIT ?", (limit,)).fetchall()
        return [dict(row) for row in rows]
