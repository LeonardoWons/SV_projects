from datetime import datetime

import sqlite3 as sql

from globals\
    import LOCAL_BADGE_DB_PATH, LOCAL_BADGE_TABLE, LOCAL_CURRENT_USER_TABLE

from handler.handler\
    import exceptionHandler

#? ---------- Database queries ---------- #?
@exceptionHandler("Error creating local badge database or tables.")
def configureLocalBadgesDB():
    """
    Create local badges database and tables if it doesn't exist.
        
    Returns:
        commit (True | False)
    """
    
    global LOCAL_BADGE_DB_PATH, LOCAL_BADGE_TABLE, LOCAL_CURRENT_USER_TABLE

    try:
        # Create table if it doesnt exist
        connection = sql.connect(LOCAL_BADGE_DB_PATH, autocommit=False)
        cursor = connection.cursor()

        cursor.execute(f""" 
            CREATE TABLE IF NOT EXISTS {LOCAL_BADGE_TABLE}(
                ID INTEGER PRIMARY KEY AUTOINCREMENT, 
                EMPLOYEE_BADGE VARCHAR(20)
            );
        """)

        cursor.execute(f""" 
            CREATE TABLE IF NOT EXISTS {LOCAL_CURRENT_USER_TABLE}(
                ID INTEGER PRIMARY KEY AUTOINCREMENT, 
                EMPLOYEE_BADGE VARCHAR(20),
                DATE_TIME VARCHAR(20)
            );
        """)

        connection.commit()
        return True
    
    except:
        connection.rollback()
        return False
    
    finally:
        cursor.close()
        connection.close()


#? ---------- Badges table queries ---------- #?
@exceptionHandler("Error updating badges into local badges table.")
def updateLocalBadges(badges):
    """
    Clear the current local badge table and insert new rows.
    
    Args:
        badges (list): list of badge IDs from eployees.
        
    Returns:
        commit (True | False).
    """
    
    global LOCAL_BADGE_DB_PATH, LOCAL_BADGE_TABLE

    connection = sql.connect(LOCAL_BADGE_DB_PATH, autocommit=False)
    cursor = connection.cursor()

    try:
        # Delete all records from the table
        cursor.execute(f"""DELETE FROM {LOCAL_BADGE_TABLE};""")

        # Insert new records
        for badge in badges:
            cursor.execute(
                f"""INSERT INTO {LOCAL_BADGE_TABLE}(EMPLOYEE_BADGE) VALUES(?);""",
                (badge,)
            )

        connection.commit()
        return True

    except:
        connection.rollback()
        return False

    finally:
        cursor.close()
        connection.close()

@exceptionHandler("Error selecting row from local badges table.")
def selectLocalBadge(badge: str):
    """
    Function to search for a specific badge in the table.
    
    Args:
        badge (str): Badge ID of the employee.
        
    Returns:
        badge (str | None)
    """
    
    global LOCAL_BADGE_DB_PATH, LOCAL_BADGE_TABLE

    connection = sql.connect(LOCAL_BADGE_DB_PATH, autocommit=False)
    cursor = connection.cursor()
    
    try:
        cursor.execute(
            f"""SELECT * FROM {LOCAL_BADGE_TABLE} WHERE EMPLOYEE_BADGE = ?;""", 
            (badge,)
        )

        badge = cursor.fetchone()
        return badge
    
    except:
        return None

    finally:
        cursor.close()
        connection.close()


#? ---------- Current user table queries ---------- #?
@exceptionHandler("Error updating current user into local current user table.")
def updateLocalCurrentUser(badge: str):
    """
    Clear the current local user table and insert the new current user badge.
    
    Args:
        badge (str): Badge ID of the current employee.
        
    Returns:
        commit (True | False).
    """
    
    global LOCAL_BADGE_DB_PATH, LOCAL_CURRENT_USER_TABLE

    connection = sql.connect(LOCAL_BADGE_DB_PATH, autocommit=False)
    cursor = connection.cursor()

    currentDateTime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        # Delete all records from the current user table
        cursor.execute(f"""DELETE FROM {LOCAL_CURRENT_USER_TABLE};""")

        # Insert the new current user record
        cursor.execute(
            f"""INSERT INTO {LOCAL_CURRENT_USER_TABLE}(EMPLOYEE_BADGE, DATE_TIME) VALUES(?,?);""",
            (badge, currentDateTime)
        )

        connection.commit()
        return True

    except:
        connection.rollback()
        return False

    finally:
        cursor.close()
        connection.close()

# @exceptionHandler("Error selecting current user from local current user table.")
# def selectLocalCurrentUser():
#     """
#     Clear the current local user table and insert the new current user badge.
    
#     Args:
#         badge (str): Badge ID of the current employee.
        
#     Returns:
#         commit (True | False).
#     """
    
#     global LOCAL_BADGE_DB_PATH, LOCAL_CURRENT_USER_TABLE

#     connection = sql.connect(LOCAL_BADGE_DB_PATH, autocommit=False)
#     cursor = connection.cursor()

#     try:
#         # Delete all records from the current user table
#         cursor.execute(f"""SELECT * FROM {LOCAL_CURRENT_USER_TABLE};""")
#         currentUser = cursor.fetchone()

#         connection.commit()
#         return currentUser

#     except:
#         connection.rollback()
#         return None

#     finally:
#         cursor.close()
#         connection.close()