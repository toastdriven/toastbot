# -*- coding: utf-8 -*-
import irc

import codecs
import datetime
import os
import re
import socket
import subprocess
import urllib

import pyquery
import requests

try:
    import simplejson as json
except ImportError:
    import json


__author__ = 'Daniel Lindsley'
__version__ = (0, 4, 1)
__license__ = 'BSD'


class NotHandled(Exception):
    pass


class ToastBot(object):
    server = 'irc.freenode.net'
    port = 6667
    username = None
    realname = 'ToastBot'
    debug = False
    log_dir = os.path.join(os.path.dirname(__file__), 'logs')
    variant_endings = [
        ': ',
        ', ',
        '- ',
        ' - ',
    ]

    def __init__(self, nick, channel, **kwargs):
        self.nick = nick
        self.channel = channel
        self.client = None

        if 'server' in kwargs:
            self.server = kwargs['server']

        if 'port' in kwargs:
            self.port = kwargs['port']

        if 'username' in kwargs:
            self.username = kwargs['username']

        if 'realname' in kwargs:
            self.realname = kwargs['realname']

        if 'debug' in kwargs:
            self.debug = kwargs['debug']

        if 'log_dir' in kwargs:
            self.log_dir = kwargs['log_dir']

        self.variants = [self.nick + variant for variant in self.variant_endings]
        self.enabled_commands = [
            self.help,
            self.dance,
            self.woodies,
            self.wiki,
            self.metar,
            self.twitter,
            self.fatpita,
            self.corgibomb,
        ]

    def run(self):
        patterns = [
            (self.client.ping_re, self.client.handle_ping),
            (self.client.part_re, self.handle_part),
            (self.client.join_re, self.handle_join),
            (self.client.chanmsg_re, self.handle_channel_message),
            (self.client.privmsg_re, self.handle_private_message),
        ]
        self.client.logger.debug('entering receive loop')

        while 1:
            try:
                data = self.client._sock_file.readline()
            except socket.error:
                data = None

            if not data:
                self.client.logger.info('server closed connection')
                self.client.close()
                return True

            data = data.rstrip()

            for pattern, callback in patterns:
                match = pattern.match(data)
                if match:
                    callback(**match.groupdict())

    def setup(self):
        self.ensure_log_directory()
        self.client = irc.IRCConnection(self.server, self.port, self.nick, verbosity=2)
        self.client.connect()
        self.client.join(self.channel)
        self.run()

    def ensure_log_directory(self):
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)

            if self.debug:
                self.log('Ensured the log directory exists.')

    def log(self, message):
        now = datetime.datetime.now()
        log_filename = "%4d%2d%2d.log" % (now.year, now.month, now.day)
        log_filepath = os.path.join(self.log_dir, log_filename)

        with codecs.open(log_filepath, 'a', encoding='utf-8') as log:
            log.write(u'[%4d-%02d-%02d %02d:%02d:%02d] %s\n' % (
                now.year,
                now.month,
                now.day,
                now.hour,
                now.minute,
                now.second,
                message
            ))

    def say(self, response):
        if not isinstance(response, (list, tuple)):
            response = [response]

        for resp in response:
            self.log(u"%s: %s" % (self.nick, resp))
            self.client.respond(resp.encode('utf-8'), channel=self.channel)

    def handle_join(self, nick, channel):
        self.log(u"%s joined %s." % (nick, channel))

    def handle_part(self, nick, channel):
        self.log(u"%s left %s." % (nick, channel))

    def clean_message(self, text):
        clean_text = text.strip()
        clean_text = clean_text.replace('\u0001', '')
        return clean_text

    def said_to_me(self, text):
        for variant in self.variants:
            if text.startswith(variant):
                return ['direct', text.replace(variant, '', 1)]
            elif variant in text:
                return ['indirect', text]

        return ['nomention', text]

    def is_direct_command(self, name, text):
        address, text = self.said_to_me(text)

        if address != 'direct':
            return None

        if text.lower() != name:
            return None

        return text

    def handle_channel_message(self, nick, channel, message):
        cleaned_text = self.clean_message(message)

        if cleaned_text.startswith('ACTION'):
            self.log(u"* %s %s" % (nick, cleaned_text.replace('ACTION', '', 1)))
        else:
            self.log(u"%s: %s" % (nick, cleaned_text))

        for command in self.enabled_commands:
            try:
                response = command(nick, cleaned_text)

                if response is True:
                    # It's doing it's own output.
                    return

                self.say(response)
            except NotHandled:
                # Nope, not that one. Try the next command.
                continue

    def handle_private_message(self, nick, text):
        cleaned_text = self.clean_message(text)
        self.log(u"PM <- %s: %s" % (nick, cleaned_text))
        message = "Sorry, I don't respond to PMs yet."
        self.log(u"PM -> %s: %s" % (nick, message))
        self.client.respond(message, nick=nick)

    # Available commands
    def help(self, nick, text):
        """Provides a description of what I respond to."""
        text = self.is_direct_command('help', text)

        if not text:
            raise NotHandled()

        commands = [
            u'%s: Valid commands - ' % nick,
        ]

        for command in self.enabled_commands:
            commands.append("  - %s = %s" % (command.__name__, command.__doc__ or 'No documentation.'))

        return commands

    def dance(self, nick, text):
        """Get down and funky."""
        text = self.is_direct_command('dance', text)

        if not text:
            raise NotHandled()

        sweet_moves = [
            "_O_",
            "\\O_",
            "_O/",
            "\\O/",
        ]
        return sweet_moves

    def woodies(self, nick, text):
        """Best quote on the internet."""
        if not 'woodies' in text:
            raise NotHandled()

        return 'U GUYZ R THE BEST AND GIVE ME A BILLION WOODIES A DAY! [https://code.djangoproject.com/ticket/7712#comment:2]'

    def wiki(self, nick, text):
        """Search Wikipedia for a topic."""
        address, text = self.said_to_me(text)

        if address != 'direct':
            raise NotHandled()

        if not text.startswith('wiki'):
            raise NotHandled()

        search_terms = text.replace('wiki ', '')
        resp = requests.get('http://en.wikipedia.org/w/index.php?search=%s' % urllib.quote_plus(search_terms), headers={'User-Agent': 'Mozilla/4.0 (toastbot)'})

        if resp.status_code in (404, 500):
            self.log("Failed to load wiki entry for '%s'." % search_terms)
            return True

        return u"%s: %s" % (nick, resp.url)

    def metar(self, nick, text):
        """Fetch a NOAA METAR by station code."""
        address, text = self.said_to_me(text)

        if address != 'direct':
            raise NotHandled()

        if not text.startswith('metar'):
            raise NotHandled()

        station = text.replace('metar ', '')
        url = "ftp://tgftp.nws.noaa.gov/data/observations/metar/stations/%s.TXT" % station.upper()
        proc = subprocess.Popen('curl %s' % url, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()

        if proc.returncode != 0:
            self.log("Failed to load metar entry for '%s'." % station);
            return u"%s: Sorry, couldn't find that station." % nick

        return u"%s: %s" % (nick, stdout.replace('\n', ' ').replace('\r', ''))

    def twitter(self, nick, text):
        """Search Twitter for a topic."""
        address, text = self.said_to_me(text)

        if address != 'direct':
            raise NotHandled()

        if not text.startswith('twitter'):
            raise NotHandled()

        search_terms = text.replace('twitter ', '')
        resp = requests.get('http://search.twitter.com/search.json?rpp=5&result_type=recent&q=%s' % urllib.quote_plus(search_terms), headers={'User-Agent': 'Mozilla/4.0 (toastbot)'})

        if resp.status_code != 200:
            self.log("Failed to load wiki entry for '%s'." % search_terms)
            self.say(u"%s: Sorry, Twitter isn't responding." % nick)
            return True

        try:
            resp_data = json.loads(resp.content)
            results = [
                u'%s: Top 5 results - ' % nick,
            ]

            for tweet in resp_data.get('results', []):
                results.append(u"  - @%s: %s" % (tweet['from_user'], tweet['text']))

            return results
        except:
            self.log("FAIL WHALE for '%s'." % search_terms)
            self.say(u"%s: Twitter fail whale'd." % nick)
            return True

    def fatpita(self, nick, text):
        """Get a random fatpita image. For the lulz."""
        text = self.is_direct_command('fatpita', text)

        if not text:
            raise NotHandled()

        resp = requests.get('http://fatpita.net/', headers={'User-Agent': 'Mozilla/4.0 (toastbot)'})

        if resp.status_code in (404, 500):
            self.log("Failed to load random fatpita image.")
            return True

        return u"%s: %s" % (nick, resp.url)

    def corgibomb(self, nick, text):
        """CORGI BOMB!"""
        text = self.is_direct_command('corgibomb', text)

        if not text:
            raise NotHandled()

        resp = requests.get('http://www.tumblr.com/tagged/corgi', headers={'User-Agent': 'Mozilla/4.0 (toastbot)'})

        if resp.status_code in (404, 500):
            self.log("Failed to load corgibomb image.")
            return True

        doc = pyquery.PyQuery(resp.content)
        corgi_js = doc('.image_thumbnail:first').attr('onclick')

        # Because Tumblr LOL.
        tumblr_rage = re.search(r"this\.src=\'(?P<pic>.*?)\'", corgi_js)

        if tumblr_rage:
            corgi_pic = tumblr_rage.groupdict()['pic']
            return u"%s: %s" % (nick, corgi_pic)
        else:
            return u"%s: Sorry, Tumblr is being crappy. No pic for you." % nick
