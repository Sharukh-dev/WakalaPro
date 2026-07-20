from app import app
from extensions import db
from sqlalchemy import text


with app.app_context():

    with db.engine.connect() as connection:

        columns = connection.execute(
            text("PRAGMA table_info(operator)")
        ).fetchall()


        existing_columns = [
            column[1]
            for column in columns
        ]


        new_columns = {
            "deposit_commission": "FLOAT DEFAULT 0",
            "withdraw_commission": "FLOAT DEFAULT 0",
            "airtime_commission": "FLOAT DEFAULT 0"
        }


        for column, definition in new_columns.items():

            if column not in existing_columns:

                connection.execute(
                    text(
                        f"ALTER TABLE operator ADD COLUMN {column} {definition}"
                    )
                )

                print(
                    f"Added column: {column}"
                )

            else:

                print(
                    f"Already exists: {column}"
                )


        connection.commit()


print("Operator commission migration completed.")