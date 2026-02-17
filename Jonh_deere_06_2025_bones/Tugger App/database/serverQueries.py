import pyodbc

from handler.handler\
    import exceptionHandler

@exceptionHandler("Error selecting badges from SQL Server.")
def selectServerBadges(databaseURL: str):
    """
    Select all badges from SQL Server database.

    Returns:
        badges (list[str] | None)
    """

    try:
        connection = pyodbc.connect(databaseURL, autocommit=False)
        cursor = connection.cursor()

        query = """
            SELECT DISTINCT EMPLOYEE_BADGE
            FROM TELEMETRY_Employee_Badges;
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # Extract the badge value from each row (each row as a tuple)
        badges = [row[0] for row in rows] 
        return badges

    except:
        return None
    
    finally:
        cursor.close()
        connection.close()