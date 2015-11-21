import MySQLdb
import PySQLPool

connection = PySQLPool.getNewConnection(username='root',password='admin',host='localhost',db='recommendation',charset='utf8')

def query(sql):
    query = PySQLPool.getNewQuery(connection,True)
    query.Query(sql)
    return query.record

def execute(sql):
    query = PySQLPool.getNewQuery(connection,True)
    query.Query(sql)
    return query.affectedRows

def insert(sql):
    query = PySQLPool.getNewQuery(connection,True)
    query.Query(sql)
    return query.lastInsertID




