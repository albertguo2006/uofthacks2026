from .mongo import get_db


class Collections:
    @staticmethod
    def users():
        return get_db().users

    @staticmethod
    def events():
        return get_db().events

    @staticmethod
    def sessions():
        return get_db().sessions

    @staticmethod
    def tasks():
        return get_db().tasks

    @staticmethod
    def jobs():
        return get_db().jobs

    @staticmethod
    def passports():
        return get_db().passports

    @staticmethod
    def videos():
        return get_db().videos

    @staticmethod
    def interventions():
        return get_db().interventions

    @staticmethod
    def saved_code():
        return get_db().saved_code

    @staticmethod
    def proctoring_sessions():
        return get_db().proctoring_sessions

    @staticmethod
    def chat_messages():
        return get_db().chat_messages

    @staticmethod
    def skill_proficiencies():
        return get_db().skill_proficiencies

    @staticmethod
    def db():
        return get_db()
