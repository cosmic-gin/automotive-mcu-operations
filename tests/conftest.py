import os

import pytest
from sqlalchemy import create_engine


@pytest.fixture
def postgres_engine():
    url = os.getenv("MCU_TEST_POSTGRES_URL")
    if not url:
        pytest.skip("Set MCU_TEST_POSTGRES_URL to a dedicated disposable database")
    root = create_engine(url)
    # A separate schema keeps test table replacement isolated even on a shared server.
    from uuid import uuid4

    from sqlalchemy import text

    schema = f"mcu_test_{uuid4().hex}"
    with root.begin() as connection:
        connection.execute(text(f"CREATE SCHEMA {schema}"))
    engine = create_engine(url, connect_args={"options": f"-c search_path={schema}"})
    try:
        yield engine
    finally:
        engine.dispose()
        with root.begin() as connection:
            connection.execute(text(f"DROP SCHEMA {schema} CASCADE"))
        root.dispose()
