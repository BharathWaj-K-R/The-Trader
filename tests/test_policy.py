from app.policy import ExecutionPolicy


def test_stop_loss_is_triggered():
    policy = ExecutionPolicy(stop_loss_fraction=0.03, take_profit_fraction=0.06)
    assert policy.protective_exit(100, 96.5) == "protective_stop_loss"


def test_take_profit_is_triggered():
    policy = ExecutionPolicy(stop_loss_fraction=0.03, take_profit_fraction=0.06)
    assert policy.protective_exit(100, 106) == "protective_take_profit"


def test_no_exit_inside_band():
    policy = ExecutionPolicy(stop_loss_fraction=0.03, take_profit_fraction=0.06)
    assert policy.protective_exit(100, 102) is None
