import datetime


class Msg(object):
    def __init__(self):
        return


class EmailMsg(Msg):
    def __init__(self, Subject, From, To, Text="", Bcc=[], date_time=None):
        assert(isinstance(To, list))
        assert(isinstance(Subject, str))
        self.Subject_ = Subject
        self.From_ = From
        self.To_ = To
        self.Text_ = Text
        self.Bcc_ = Bcc
        self.date_time_ = date_time
        if date_time is not None:
            assert isinstance(date_time, datetime.datetime)
