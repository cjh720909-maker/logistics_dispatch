from sqlalchemy import create_engine

local_engine = create_engine(
    "sqlite:///data/local.db",
    echo=False,
    future=True,
)