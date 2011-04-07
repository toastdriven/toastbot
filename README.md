Toastbot
========

A clean, extensible IRC bot using Node.js.

**Author:** Daniel Lindsley <daniel@toastdriven.com>  
**License:** Dual licensed BSD/GPL  
**Version:** 0.1.0


Requirements
------------

* Node.js 0.4.4+
* node-irc (``npm install irc``)


Usage
-----

Create your own ``bot.js`` file & drop in:

    var toastbot = require('toastbot');
    
    // Simple.
    var bot = new toastbot.Toastbot('myircbot', '#testchannel');
    
    // Complex.
    // var bot = new toastbot.Toastbot('myircbot', '#testchannel', {
    //   username: 'myircbot',
    //   realname: 'My IRC Bot',
    // });
    
    bot.setup();

Then run it with ``node bot.js``.


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
* ``log_dir`` - Controls what directory the logs should go in (default: ``install_directory/logs``).
* ``variants`` - Used to override ways to address the bot. Should be strings (default: ``[self.nick+': ', self.nick+', ', self.nick+'- ', self.nick+' - ']``).


Available "handlers"
--------------------

Handlers are how the bot can perform actions based on an incoming message. They
are simple methods hanging off the bot object. The built-in list consists of:

* ``help`` - Provides a description of what I respond to.
* ``dance`` - Get down and funky.
* ``wiki`` - Search Wikipedia for a topic.
* ``metar`` - Fetch a NOAA METAR by station code.
* ``twitter`` - Search Twitter for a topic.


Extending the bot
-----------------

Adding on further handlers is relatively simple. At its most basic, it's simply
adding on a new method decorated with ``toastbot.handler``. For example, logging 
how many times a user has said something in the channel might look like:

    var toastbot = require('../lib/toastbot');
    
    // Add on the new method.
    toastbot.Toastbot.prototype.how_chatty = toastbot.handler(toastbot.method(function(self, nick, text) {
      self.talkers = self.talkers || {};
      
      if(self.talkers[nick]) {
        self.talkers[nick] += 1;
      }
      else {
        self.talkers[nick] = 1;
      }
      
      // Prove it's working. In real use, you'd log to a file or a datastore.
      console.log(JSON.stringify(self.talkers));
    }));
    // Add documentation for the ``how_chatty`` command.
    toastbot.Toastbot.prototype.how_chatty.__doc__ = "Logs how often a user has said something."
    
    // Add to handlers & run as normal.
    var bot = new toastbot.Toastbot('testbot', '#testchannel', {
      log_dir: '/tmp/be_quiet.log'
    });
    bot.setup();

Note that this command does not require addressing the bot at all. If you want
a command that the bot responds to, you might write something like:

    // Assume the previous example, but adding...
    toastbot.Toastbot.prototype.stool_pigeon = toastbot.handler(toastbot.method(function(self, nick, text) {
      var text = self.is_direct_command('stool_pigeon', text);

      if(! text) {
        return null;
      }

      self.talkers = self.talkers || {};
      return nick+': '+JSON.stringify(self.talkers);
    }));
    // Add documentation for the ``stool_pigeon`` command.
    toastbot.Toastbot.prototype.stool_pigeon.__doc__ = "Rat out the talkers."
    
This checks to see if the bot is being directly addressed then returns a
string-ified version of the ``talker`` stats. The included handlers demonstrate
even more complex behavior, such as how to do network fetches or asynchronous
responses.

To disable handlers:

    var toastbot = require('../lib/toastbot');
    var bot = new toastbot.Toastbot('testbot', '#testchannel');
    
    bot.twitter.disable();

    // to enable a disabled handler:

    bot.twitter.enable();

Using the `enable` and `disable` methods on a handler will do the obvious thing. 
If you want to check if a particular handler is enabled, you can check using
``bot.twitter.enabled()``.
