import peewee

from .config import config

if config['database'] == 'postgresql':
    db = peewee.PostgresqlDatabase(config['postgresql']['db_name'], user=config['postgresql']['user'], host=config['postgresql']['host'], password=config['postgresql']['password'])
else:
    db = peewee.SqliteDatabase(config['sqlite']['db_path'], pragmas={'journal_mode': 'wal'})

class Task(peewee.Model):
    id = peewee.BigIntegerField(primary_key=True, unique=True, null=False)
    agent_ip = peewee.CharField(null=False)
    task = peewee.CharField(null=False)
    completed = peewee.BigIntegerField(default=0, null=False)

    class Meta:
        database = db
        db_table = 'tasks'

class Agent(peewee.Model):
    ip = peewee.CharField(null=False)
    checkins = peewee.BigIntegerField(default=0, null=False)
    last_checkin = peewee.BigIntegerField(null=False)
    tasks_sent = peewee.BigIntegerField(default=0, null=False)
    tags = peewee.CharField(null=False, default='')

    class Meta:
        database = db
        db_table = 'agents'

db.create_tables([Task, Agent])