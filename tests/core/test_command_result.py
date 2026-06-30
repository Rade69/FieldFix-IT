from app.core.command_result import CommandResult


def test_succeeded_true_on_zero_exit_code():
    result = CommandResult(command="ping 1.1.1.1", exit_code=0)
    assert result.succeeded


def test_succeeded_false_on_nonzero_exit_code():
    result = CommandResult(command="ping 1.1.1.1", exit_code=1)
    assert not result.succeeded


def test_succeeded_false_on_timeout_even_if_exit_code_zero():
    result = CommandResult(command="slow-cmd", exit_code=0, timed_out=True)
    assert not result.succeeded


def test_succeeded_false_when_exit_code_missing():
    result = CommandResult(command="unknown")
    assert not result.succeeded


def test_defaults():
    result = CommandResult(command="ipconfig")
    assert result.stdout == ""
    assert result.stderr == ""
    assert result.parsed_json is None
    assert result.requires_admin is False
