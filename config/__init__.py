import pymysql

pymysql.install_as_MySQLdb()
import os

if os.getenv("DB_ENGINE", "sqlite").lower() in ("mysql", "mariadb"):
    try:
        import pymysql
    except ImportError as exc:
        raise ImportError(
            "DB_ENGINE is set to mysql/mariadb, but PyMySQL is not installed. "
            "Install it with `pip install PyMySQL`."
        ) from exc
    pymysql.install_as_MySQLdb()
