from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect, text


def test_upgrade_head_creates_alembic_version_table(tmp_path: Path) -> None:
    database_path = tmp_path / "model_flow.db"
    config = Config(str(Path(__file__).parents[1] / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database_path}")

    command.upgrade(config, "head")

    engine = create_engine(f"sqlite:///{database_path}")
    assert inspect(engine).has_table("alembic_version")
    with engine.connect() as connection:
        assert (
            connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
            == "0004"
        )
    assert inspect(engine).has_table("domain_events")
    indexes = {index["name"] for index in inspect(engine).get_indexes("task_nodes")}
    assert "ix_task_nodes_run_status_priority" in indexes
