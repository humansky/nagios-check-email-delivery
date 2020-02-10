#!/usr/bin/python3
import sys, smtplib, ssl, time

from optparse import OptionParser
parser = OptionParser()
parser.add_option("-w", "--warning", dest="warning", type="int", default=15, metavar="<seconds>",
                  help="Warn if it takes longer than <seconds> to connect to the SMTP server. Default is 15 seconds.")
parser.add_option("-c", "--critical", dest="critical", type="int", default=30, metavar="<seconds>",
                  help="Return a critical status if it takes longer than <seconds> to connect to the SMTP server. Default is 30 seconds.")
parser.add_option("-t", "--timeout", dest="timeout", type="int", default=60, metavar="<seconds>",
                  help="Abort with critical status if it takes longer than <seconds> to connect to the SMTP server. Default is 60 seconds. The difference between timeout and critical is that, with the default settings, if it takes 45 seconds to connect to the server then the connection will succeed but the plugin will return CRITICAL because it took longer than 30 seconds.")
parser.add_option("-H", "--hostname", dest="hostname", default='localhost', metavar="<server>",
                  help="Address or name of the SMTP server. Examples: mail.server.com, 192.168.1.100. Default is localhost.")
parser.add_option("-p", "--port", dest="port", type="int", metavar="<port>",
                  help="Service port on the SMTP server. Default is 25 for regular SMTP, 465 for SSL, and 587 for TLS.")
parser.add_option("--tls", dest="tls", action="store_true", default=False,
                  help="Enable TLS/AUTH protocol. When using this option, the default port is 587. You can specify a port from the command line using the --port option.")
parser.add_option("--ssl", dest="ssl", action="store_true", default=False,
                  help="Enable SSL protocol. When using this option, the default port is 465. You can override with the --port option.")
parser.add_option("-U", "--username", dest="username", metavar="<username>",
                  help="Username to use when connecting to SMTP server.")
parser.add_option("-P", "--password", dest="password", metavar="<password>",
                  help="Password to use when connecting to SMTP server.")
parser.add_option("--body", dest="body", metavar="<message>",
                  help="Use this option to specify the body of the email message.")
parser.add_option("--header", dest="header", action="append", metavar="<header>",
                  help="Use this option to set an arbitrary header in the message. You can use it multiple times.")
parser.add_option("--mailto", dest="mailto", action="append", metavar="recipient@your.net",
                  help="You can send a message to multiple recipients by repeating this option or by separating the email addresses with commas (no whitespace allowed).")
parser.add_option("--mailfrom", dest="mailfrom", metavar="sender@your.net",
                  help="Use this option to set the 'from' address in the email.")
parser.add_option("-v", "--verbose", dest="verbose", action="store_true", default=False,
                  help="Display additional information. Useful for troubleshooting.")

(options, args) = parser.parse_args()

# Set default port value
if options.tls and not options.port:
    options.port = 587
elif options.ssl and not options.port:
  options.port = 465
elif not options.port:
  options.port = 25

status = { 'OK' : 0, 'WARNING' : 1, 'CRITICAL' : 2, 'UNKNOWN' : 3 }

try:
    context = ssl.SSLContext()
    server = smtplib.SMTP(host=options.hostname, port=options.port, timeout=options.timeout)
    server.set_debuglevel(options.verbose)

    if options.tls:
        server.ehlo()
        server.starttls(context=context)
        server.ehlo()

    server.login(options.username, options.password)

    message = "From: %s\n" % (options.mailfrom)
    message += "To: %s\n" % ",".join(options.mailto)
    if options.header:
        message += "\n".join(options.header)
    message += "\n%s" % (options.body)
    server.sendmail(options.mailfrom, options.mailto, message)
except:
    print ("SMTP SEND CRITICAL - Could not connect to %s port %d" % (options.hostname, options.port))
    sys.exit(status['CRITICAL'])

print ("SMTP SEND OK")
sys.exit(status['OK'])
