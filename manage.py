# @ Time    : 2020/11/16 21:19

from lghome import create_app, db
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand

app = create_app('dev')


# 数据库迁移
manage = Manager(app)
Migrate(app, db)
manage.add_command('db', MigrateCommand)


if __name__ == '__main__':
    manage.run()

