# Utilise PyMySQL comme pilote MySQL (pur Python, aucune compilation requise).
# PyMySQL s'enregistre sous le nom "MySQLdb" attendu par le backend Django.
import pymysql

pymysql.install_as_MySQLdb()
