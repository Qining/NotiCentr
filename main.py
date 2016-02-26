import getpass

from NotiCentr.notifier import EmailSender, SmtpServer, EmailReceiver, ImapServer
from NotiCentr.msg import EmailMsg
from NotiCentr.account import EmailAccount


password = getpass.getpass()


def send():
    global password
    me = 'noticentr@gmail.com'
    to = ['noticentr@gmail.com']
    server = SmtpServer()
    account = EmailAccount(me, password)
    sender = EmailSender('noticentr@gmail.com', server, account)
    mail = EmailMsg('BasicTest', me, to, 'This is a basic test.')
    return sender.send(mail)


def recv():
    global password
    me = 'noticentr@gmail.com'
    server = ImapServer()
    account = EmailAccount(me, password)
    receiver = EmailReceiver(server, account)
    r, msg = receiver.get_lastest_email_in_folder()
    return r, msg


def main():
    global password
    print "Password of noticentr@gmail.com:"
    #  password = getpass.getpass()
    rc = send()
    print "send() return code:", rc
    rc, msg = recv()
    print "recv() return code:", rc
    print "recv() return msg:", msg.Subject_, msg.From_, msg.Text_


if __name__ == "__main__":
    main()
    print "This should be printed out"
