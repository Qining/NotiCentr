import copy
import sys
import imaplib
import email
import datetime
import logging

from multiprocessing import Process, TimeoutError
from functools import partial

from NotiCentr.msg import EmailMsg
from NotiCentr.account import EmailAccount

from twisted.mail.smtp import sendmail
from twisted.internet.task import react
from twisted.python import log

from email.mime.text import MIMEText


logging.basicConfig(level=logging.DEBUG)


class SmtpServer:
    """
    Info about SMTP server, including host, port, authentication flags etc.
    By default use gmail SMTP server.
    """

    def __init__(self,
                 host="smtp.gmail.com",
                 port=587,
                 require_authentication=True,
                 require_transport_security=True):
        self.host_ = host
        # smtp port:
        self.port_ = port
        self.require_authentication_ = require_authentication
        self.require_transport_security_ = require_transport_security


class EmailSender:
    """
    Use twisted.internet.task.react to send an email and exit.
    """

    class _Package:
        def __init__(self, to_addresses, shared_content, ):
            self.to_addresses_ = to_addresses
            self.shared_content_ = shared_content

    def __init__(self, from_address, smtp_server, account):
        assert isinstance(smtp_server, SmtpServer)
        assert isinstance(from_address, str)
        assert isinstance(account, EmailAccount)
        self.from_address_ = from_address
        self.smtp_server_ = copy.deepcopy(smtp_server)
        self.account_ = copy.deepcopy(account)

    def send(self, msg, timeout=5):
        """
        Send the email and exit. Note this will exit current process!

        @param msg: An EmailMsg type object to be sent.
        """
        assert isinstance(msg, EmailMsg)
        # shared_content can be seen by all receivers.
        shared_content = MIMEText(msg.Text_)
        shared_content["Subject"] = msg.Subject_
        shared_content["To"] = ", ".join(msg.To_)
        assert msg.From_ == self.from_address_
        # pkg_to_be_send will be sent by _actual_send()
        pkg = EmailSender._Package(to_addresses=list(msg.To_),
                                   shared_content=shared_content)
        p = Process(target=self._actual_send, args=(pkg, ))
        try:
            p.start()
            p.join(timeout)
        except TimeoutError:
            raise Exception(self.__class__.__name__, ": send() timeout.")
            return 1
        return p.exitcode

    def _actual_send(self, pkg):
        def _reactor_send(reactor, pkg):
            require_trans_sec = self.smtp_server_.require_transport_security_
            require_auth = self.smtp_server_.require_authentication_
            log.startLogging(sys.stdout)
            log.msg('To addresses:', pkg.to_addresses_)
            d = sendmail(self.smtp_server_.host_,
                         self.from_address_,
                         pkg.to_addresses_,
                         pkg.shared_content_,
                         port=self.smtp_server_.port_,
                         username=self.account_.user_name_,
                         password=self.account_.password_,
                         requireAuthentication=require_auth,
                         requireTransportSecurity=require_trans_sec)

            #  d.addBoth(print)
            return d

        react(_reactor_send, (pkg, ))


class ImapServer:
    """
    Info about IMAP server, actually only including a host address.
    """

    def __init__(self):
        self.host_ = "imap.gmail.com"
        # port:
        # imap should all use port 993.


class EmailReceiver:
    """
    Use python's imap package to receive emails.
    """

    @staticmethod
    def _extract_body(payload):
        if isinstance(payload, str):
            return payload
        else:
            return '\n'.join([EmailReceiver._extract_body(part.get_payload())
                              for part in payload])

    def __init__(self, imap_server, account):
        assert isinstance(account, EmailAccount)
        assert isinstance(imap_server, ImapServer)
        self.imap_server_ = copy.deepcopy(imap_server)
        self.account_ = copy.deepcopy(account)
        self.mail_box_ = None

    def _login(self):
        self.mail_box_ = imaplib.IMAP4_SSL(self.imap_server_.host_)
        try:
            self.mail_box_.login(self.account_.user_name_,
                                 self.account_.password_)
        except imaplib.IMAP4.error:
            logging.error(' '.join(
                [self.__class__.__name__, ": ", self.account_.user_name_,
                 "login failed."]))
            self.mail_box_ = None
            return -1
        else:
            logging.info(' '.join(
                [self.__class__.__name__, ": ", self.account_.user_name_,
                 "login succeeded."]))
            return 0

    def _logout(self):
        if self.mail_box_:
            self.mail_box_.close()
            self.mail_box_.logout()
        return 0

    class _stateless_wrapper(object):
        wrap_level = 0

        def __init__(self, email_action):
            self.email_action_ = email_action

        def __get__(self, obj, objtype=None):
            if obj is None:
                return self.email_action_
            return partial(self, obj)

        def __call__(self, *args, **kwargs):
            receiver = args[0]
            if receiver.mail_box_ is None:
                receiver._login()

            EmailReceiver._stateless_wrapper.wrap_level += 1

            ret = self.email_action_(*args, **kwargs)

            EmailReceiver._stateless_wrapper.wrap_level -= 1

            if EmailReceiver._stateless_wrapper.wrap_level == 0:
                receiver._logout()

            return ret

    @_stateless_wrapper
    def get_folder_names(self):
        isinstance(self.mail_box_, imaplib.IMAP4_SSL)
        return [r[2] for r in self.mail_box_.list()]

    @_stateless_wrapper
    def get_num_email_in_folder(self, folder="INBOX"):
        assert isinstance(folder, str)
        assert isinstance(self.mail_box_, imaplib.IMAP4_SSL)
        try:
            return int(self.mail_box_.select(folder)[1][0])
        except imaplib.IMAP4.error:
            logging.error(' '.join(
                [self.__class__.__name__, ": ",
                 "get number of emails in folder:", folder, "failed"]))
            return -1

    @_stateless_wrapper
    def get_email_in_folder_by_index(self, index, folder="INBOX"):
        assert isinstance(folder, str)
        assert isinstance(self.mail_box_, imaplib.IMAP4_SSL)
        try:
            num_emails = int(self.mail_box_.select(folder)[1][0])
        except imaplib.IMAP4.error:
            logging.error(' '.join([self.__class__.__name__, ": ",
                                    "select folder:", folder, "failed"]))
            return -1, EmailMsg(Subject='', From='', To=[])
        try:
            email_index_in_str_list = self.mail_box_.search(
                None, 'All')[1][0].split(' ')
        except imaplib.IMAP4.error:
            logging.error(' '.join(
                [self.__class__.__name__, ": ", "search 'All' in folder:",
                 folder, "failed"]))
            return -1, EmailMsg(Subject='', From='', To=[])

        first_email_index = int(email_index_in_str_list[0])
        last_email_index = num_emails + first_email_index - 1
        # index == -1 means get the lastest email.
        if index == -1:
            index = last_email_index
        if index > last_email_index or index < first_email_index:
            logging.error(' '.join([self.__class__.__name__, ": ",
                                    "index out of bound in folder:", folder]))
            return -1, EmailMsg(Subject='', From='', To=[])

        r, data = self.mail_box_.fetch(str(index), '(RFC822)')
        if r != 'OK':
            logging.error(' '.join(
                [self.__class__.__name__, ": ",
                 "fetch latest email in folder:", folder, "failed"]))
            return -1, EmailMsg(Subject='', From='', To=[])
        raw_msg = email.message_from_string(data[0][1])
        # TODO: use regex to extract only the email address part from 'From' and
        # 'To'.
        message = EmailMsg(
            Subject=raw_msg['Subject'],
            From=raw_msg['From'].split('<')[-1].strip('<>'),
            To=[addr.split(' ')[-1].strip('<>')
                for addr in raw_msg['To'].split('>')],
            Text=EmailReceiver._extract_body(raw_msg.get_payload()),
            Bcc=[],
            date_time=datetime.datetime.fromtimestamp(email.utils.mktime_tz(
                email.utils.parsedate_tz(raw_msg['Date']))))
        return 0, message

    @_stateless_wrapper
    def get_lastest_email_in_folder(self, folder="INBOX"):
        return self.get_email_in_folder_by_index(-1, folder)
