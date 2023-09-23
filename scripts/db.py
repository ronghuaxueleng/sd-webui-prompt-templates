# -*- coding: utf-8 -*-

import datetime
from peewee import *

from modules import scripts

base_dir = scripts.basedir()
db = SqliteDatabase(base_dir + '/template.db')


class Template(Model):
    id = PrimaryKeyField()
    prompt = TextField(null=True)
    negativePrompt = TextField(null=True)
    raw = TextField(unique=True)
    state = IntegerField(null=True)
    filename = CharField(null=True)
    timestamp = DateTimeField(null=True, default=datetime.datetime.now)

    class Meta:
        database = db


def delete_note():
    return Template.delete().execute()


def init_table():
    db.connect()
    db.create_tables([Template])


if __name__ == '__main__':
    db.connect()
    db.create_tables([Template])
