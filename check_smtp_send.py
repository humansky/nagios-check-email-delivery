#!/usr/bin/python3
"""Nagios plugin for end smtp checking"""
import json
import smtplib, ssl, time
import argparse
import logging
import nagiosplugin

_log = logging.getLogger('nagiosplugin')

class SmtpSend(nagiosplugin.Resource):
    """
    The `SmtpSend` cdeterines the deatlay ....
    """

    def __init__(self, options):
        self.options = options
        self.connection = options.hostname + ':' + str(options.port) + '[' + options.loginname + ']'
        _log.debug(self.__class__.__name__ + ': ' + str(self))

    def __str__(self):
        return self.connection

    def _get_server(self):
        options = self.options
        context = ssl.SSLContext()
        server = smtplib.SMTP(host=options.hostname, port=options.port, timeout=options.timeout)
        server.set_debuglevel(options.verbose)

        if options.tls:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()

        return server

    def _create_message(self):
        options = self.options
        message = "From: %s\n" % (options.mailfrom)
        message += "To: %s\n" % ",".join(options.mailto)
        if options.header:
            message += "\n".join(options.header)
        message += "\n%s" % (options.body)
        _log.debug(message)
        return message

    def probe(self):
        start = time.time()
        server = self._get_server()
        server.login(self.options.logname, self.options.password)
        message = self._create_message()
        server.sendmail(self.options.options.mailfrom, self.options.ptions.mailto, message)
        stop = time.time()
        return [nagiosplugin.Metric('elapsed', stop - start, min=0)]

class SmtpSendSummary(nagiosplugin.Summary):
        """Create status line and long output.
        """
        def verbose(self, results):
            super(SmtpSendSummary, self).verbose(results)
            if 'elapsed' in results:
                return 'elspased: ' + ', '.join(results['elapsed'].resource.connection)

def _build_arg_parser():
    argp = argparse.ArgumentParser()

    argp.add_argument('-w', '--warning', metavar='RANGE',
                      help='warning if elasped time is outside RANGE')
    argp.add_argument('-c', '--critical', metavar='RANGE',
                      help='critical if elasped time is outside RANGE'),
    argp.add_argument('-t', '--timeout', default=60,
                      help='abort execution after TIMEOUT seconds')

    argp.add_argument('-H', '--hostname', default='localhost', metavar='SMTP-server',
                      help="Address or name of the SMTP-server. Examples: mail.server.com, 192.168.1.100. Default is localhost.")
    argp.add_argument("-p", "--port", dest="port", metavar="PORT",
                        help="Service port on the SMTP server. Default is 25 for regular SMTP, 465 for SSL, and 587 for TLS.")
    argp.add_argument("-l", "--logname", dest="loginname", metavar="USERNAME",
                      help="USERNAME to use when connecting to SMTP server.")
    argp.add_argument("-a", "--password", dest="password", metavar="PASSORD",
                  help="Authentication PASSWORD to use when connecting to SMTP server.")

    argp.add_argument("--tls", dest="tls", action="store_true", default=False,
                  help="Enable TLS/AUTH protocol. When using this option, the default port is 587. You can specify a port from the command line using the --port option.")
    argp.add_argument("--ssl", dest="ssl", action="store_true", default=False,
                  help="Enable SSL protocol. When using this option, the default port is 465. You can override with the --port option.")

    argp.add_argument("--mailto", dest="mailto", action="append", metavar="recipient@your.net",
                      help="You can send a message to multiple recipients by repeating this option or by separating the email addresses with commas (no whitespace allowed).")
    argp.add_argument("--mailfrom", dest="mailfrom", metavar="sender@your.net",
                      help="Use this option to set the 'from' address in the email.")
    argp.add_argument("--body", dest="body", metavar="MESSAGE", default='nagios test email',
                  help="Use this option to specify the body of the email MESSAGE.")
    argp.add_argument("--header", dest="header", action="append", metavar="HEADER",
                  help="Use this option to set an arbitrary HEADER in the message. You can use it multiple times.")

    argp.add_argument('-v', '--verbose', action='count', default=0,
                      help='increase output verbosity (use up to 3 times)')

    return argp


def _check_and_adjust_args(args):
    # check all required args are present
    for prop in ['warning', 'critical', 'loginname', 'password', 'mailto', 'mailfrom']:
        if not prop in args or getattr(args, prop)  == None:
            raise RuntimeError("Missing required argument: " + prop)
    args.timeout = int(args.timeout)

@nagiosplugin.guarded
def main():
    argp = _build_arg_parser()
    args = argp.parse_args()
    _check_and_adjust_args(args)
    if args.tls and not args.port:
        args.port = 587
    elif args.ssl and not args.port:
        args.port = 465
    elif not args.port:
        args.port = 25
    _log.debug(args)
    check = nagiosplugin.Check(
        SmtpSend(args),
        SmtpSendSummary())

    check.main(args.verbose, args.timeout)


if __name__ == '__main__':
    main()