Toastbot
========

A clean, extensible IRC bot using Python, irckit, gevent & requests.

**Author:** Daniel Lindsley<br>
**License:** BSD<br>
**Version:** 0.4.1


Requirements
------------

* Python 2.6+
* gevent
* irckit
* requests


Usage
-----

Create your own ``bot.py`` file & drop in:

    import toastbot

    bot = toastbot.ToastBot('myircbot', '#myircchannel')
    bot.setup()

Then run it with ``python bot.py``.


Configuration
-------------

The ``Toastbot`` object requires ``nick`` & ``channel`` arguments & can take a
variety of non-required options.

### Required arguments

* ``nick`` - The nickname of the bot, as a string.
* ``channel`` - The channel the bot should connect to, as a string.

### Options

* ``server`` - The server the bot should connect to (default: ``irc.freenode.net``).
* ``username`` -The username the bot should identify as (default: ``nick``);
* ``realname`` - The human readable name the bot should provide (default: 'ToastBot').
* ``debug`` - Controls if the IRC connection should dump debug messages (default: ``false``).
* ``log_dir`` - Controls what directory the logs should go in (default: ``$INSTALL_DIRECTORY/logs``).
* ``variants`` - Used to override ways to address the bot. Should be strings (default: ``[self.nick+': ', self.nick+', ', self.nick+'- ', self.nick+' - ']``).


Available "handlers"
--------------------

Handlers are how the bot can perform actions based on an incoming message. They
are simple methods hanging off the bot object. The built-in list consists of:

* ``help`` - Provides a description of what I respond to.
* ``dance`` - Get down and funky.
* ``woodies`` - Best quote on the internet..
* ``wiki`` - Search Wikipedia for a topic.
* ``metar`` - Fetch a NOAA METAR by station code.
* ``twitter`` - Search Twitter for a topic.
* ``fatpita`` - Get a random fatpita image. For the lulz.
* ``corgibomb`` - CORGI BOMB


Extending the bot
-----------------

Adding on further handlers is relatively simple. At its most basic, it's simply
adding on a new method decorated with ``toastbot.handler``. For example, logging
how many times a user has said something in the channel might look like:

    import toastbot

    class MyBot(toastbot.ToastBot):
        talkers = {}

        def __init__(self, *args, **kwargs):
            super(MyBot, self).__init__(*args, **kwargs)
            self.enabled_commands += [
                self.how_chatty,
            ]

        def how_chatty(self, nick, text):
            """Logs how often a user has said something."""
            if nick in self.talkers:
                self.talkers[nick] += 1
            else:
                self.talkers[nick] = 1

            print self.talkers.items()


    bot = MyBot('myircbot', '#myircchannel')
    bot.setup()

Note that this command does not require addressing the bot at all. If you want
a command that the bot responds to, you might write something like:

    import toastbot

    class StoolPigeon(toastbot.ToastBot):
        # Assume the previous example, but adding...
        def __init__(self, *args, **kwargs):
            super(StoolPigeon, self).__init__(*args, **kwargs)
            self.enabled_commands += [
                self.stool_pigeon,
            ]

        def stool_pigeon(self, nick, text):
            """Rat out the talkers."""
            text = self.is_direct_command('stool_pigeon', text)

            if not text:
                raise NotHandled()

            return str(self.talkers)

    bot = StoolPigeon('myircbot', '#myircchannel')
    bot.setup()

This checks to see if the bot is being directly addressed then returns a
string-ified version of the ``talker`` stats. The included handlers demonstrate
even more complex behavior, such as how to do network fetches or asynchronous
responses.

To disable handlers:

    import toastbot

    class MyBot(toastbot.ToastBot):
        talkers = {}

        def __init__(self, *args, **kwargs):
            super(MyBot, self).__init__(*args, **kwargs)
            self.enabled_commands = [func for func in self.enabled_commands if func.__name__ != 'twitter']

    bot = MyBot('myircbot', '#myircchannel')
    bot.setup()
