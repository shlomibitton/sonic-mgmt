import mysql.connector
import logging

from ngts.constants.constants import InfraConst

logger = logging.getLogger()


class DB:
    def __init__(self, host=InfraConst.MYSQL_SERVER, user=InfraConst.MYSQL_USER, password=InfraConst.MYSQL_PASSWORD,
                 database=InfraConst.MYSQL_DB):
        self.connection = mysql.connector.connect(user=user, password=password, host=host, database=database)

    def insert(self, table, columns_values):
        """
        This method doing insert into MySQL DB to specific table.
        It took table name and dictionary with key(columns) and values(column values)
        """
        columns = []
        values = []
        for k, v in columns_values.items():
            columns.append(k)
            values.append(v)

        query = 'INSERT INTO {}(`{}`) VALUES{}'.format(table, '`,`'.join(columns), tuple(values))
        cursor = self.connection.cursor()
        cursor.execute(query)
        self.connection.commit()
        cursor.close()
