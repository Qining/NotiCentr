class Account(object):
    def __init__(self):
        return


class EmailAccount(Account):
    def __init__(self, user_name, password):
        self.user_name_ = user_name
        self.password_ = password
