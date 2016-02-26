import getpass
from datetime import datetime

from NotiCentr.notifier import EmailSender, SmtpServer, ImapServer, EmailReceiver
from NotiCentr.msg import EmailMsg
from NotiCentr.account import EmailAccount

notifier_email = 'noticentr@gmail.com'
password = getpass.getpass()


def send_an_email(to, subject, text):
    global notifier_email
    global password
    server = SmtpServer()
    account = EmailAccount(notifier_email, password)
    sender = EmailSender(notifier_email, server, account)
    mail = EmailMsg(subject, notifier_email, to, text)
    return sender.send(mail)


def recv_latest_email():
    global notifier_email
    global password
    server = ImapServer()
    account = EmailAccount(notifier_email, password)
    receiver = EmailReceiver(server, account)
    r, msg = receiver.get_lastest_email_in_folder()
    return r, msg


def setup():
    print "SETUP!"


def teardown():
    print "TEAR DOWN!"


def test_send_and_receive():
    print "RUN"

    test_time_stamp = datetime.ctime(datetime.now())
    test_subject = 'Test email sent at:' + test_time_stamp
    test_text = 'Test content, sent at:' + test_time_stamp
    test_to_addresses = [notifier_email]
    rc = send_an_email(to=test_to_addresses,
                       subject=test_subject,
                       text=test_text)
    if rc != 0:
        raise Exception("send_an_test_email() returns non-zero")

    rc, msg = recv_latest_email()
    if rc != 0:
        raise Exception("recv_latest_email() returns non-zero")

    assert msg.Subject_ == test_subject
    assert msg.Text_.strip() == test_text.strip(
    ), "Expected:\n{exp}\nActual:\n{act}\n".format(exp=test_text,
                                                   act=msg.Text_)
