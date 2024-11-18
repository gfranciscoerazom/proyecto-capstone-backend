from sqlmodel import create_engine

# region connection string
sqlite_file_name = "data/database.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
# endregion

# region settings
connect_args = {"check_same_thread": False}
# endregion

# region engine
engine = create_engine(sqlite_url, echo=True, connect_args=connect_args)
# endregion
