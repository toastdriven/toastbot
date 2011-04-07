var fs = require('fs');
var http = require('http');
var irc = require('irc');
var path = require('path');
var spawn = require('child_process').spawn;


var __author__ = 'Daniel Lindsley <daniel@toastdriven.com>';
var __version__ = [0, 1, 0];


var zero_pad = function(value, width) {
  var adjusted = value.toString();
  var width = width || 2;
  
  while(adjusted.length < width) {
    adjusted = '0'+adjusted;
  }
  
  return adjusted;
};


var method = function(fn) {
  return function() {
    return fn.apply(this, [this].concat([].slice.call(arguments)));
  }
};

var handler = function(fn) {
  var retval = function() {
    return fn.apply(this, arguments);
  };
  var enabled = true;

  retval.enabled = function() {
    return enabled;
  };

  retval.disable = function() {
    enabled = false;
  };

  retval.enable = function() {
    enabled = true;
  };

  return retval;
};

var Toastbot = method(function(self, nick, channel, options) {
  options = options || {};
  
  self.nick = nick;
  self.channel = channel;
  self.client = null;
  
  self.server = options.server || 'irc.freenode.net';
  self.username = options.username || self.nick;
  self.realname = options.realname || 'ToastBot';
  self.debug = options.debug || false;
  self.log_dir = options.log_dir || path.join(path.dirname(path.dirname(__filename)), 'logs');
  self.variants = options.variants || [
    self.nick+': ',
    self.nick+', ',
    self.nick+'- ',
    self.nick+' - '
  ];
});

// ==============================================
// Initialization and bookkeeping methods
// ==============================================

Toastbot.prototype.setup = method(function(self) {
  self.ensure_log_directory();
  
  self.client = new irc.Client(self.server, self.nick, {
    userName: self.username,
    realName: self.realname,
    debug: self.debug,
    channels: [self.channel]
  });
  
  self.client.on('join'+self.channel, function() {
    self.log('Joined '+self.channel);
  });
  self.client.on('message'+self.channel, function(nick, text) {
    self.handle_message(nick, text);
  });
  self.client.on('pm', function(nick, text) {
    self.handle_pm(nick, text);
  });
  self.client.on('error', function(raw_message) {
    console.log(raw_message.command);
  });
});

Toastbot.prototype.ensure_log_directory = method(function(self) {
  fs.mkdir(self.log_dir, '0777', function() {
    if(self.debug == true) {
      self.log('Ensured the log directory exists.');
    }
  });
});

Toastbot.prototype.get_date = method(function(self) {
  var today = new Date();
  return {
    today: today,
    year: today.getFullYear(),
    month: zero_pad(today.getMonth()),
    day: zero_pad(today.getDate()),
    hour: zero_pad(today.getHours()),
    minute: zero_pad(today.getMinutes()),
    second: zero_pad(today.getSeconds())
  };
});

Toastbot.prototype.log = method(function(self, message) {
  var date = self.get_date();
  
  var log_filename = '' + date.year + date.month + date.day + '.log';
  var log_filepath = path.join(self.log_dir, log_filename);
  
  fs.open(log_filepath, 'a', function(err, fd) {
    if(err) {
      console.log(err.toString());
      return;
    }
    
    var entry = '['+date.year+'-'+date.month+'-'+date.day+' '+date.hour+':'+date.minute+':'+date.second+'] ' + message+'\n';
    fs.write(fd, entry, function(err, written, buffer) {
      if(err) {
        console.log(err.toString());
      }
      fs.close(fd);
    });
  });
});

Toastbot.prototype.say = method(function(self, response) {
  if(response instanceof Array == false) {
    response = [response];
  }
  
  for(var roffset in response) {
    self.log(self.nick+': '+response[roffset]);
    self.client.say(self.channel, response[roffset]);
  }
});

Toastbot.prototype.clean_message = method(function(self, text) {
  var clean_text = text.trim();
  // Strip off crazy chars on actions.
  clean_text = clean_text.replace(/\u0001/g, '');
  return clean_text;
});

Toastbot.prototype.said_to_me = method(function(self, text) {
  for(var offset in self.variants) {
    if(text.indexOf(self.variants[offset]) == 0) {
      return ['direct', text.replace(self.variants[offset], '').trim()];
    }
    else if(text.indexOf(self.variants[offset]) > 0) {
      return ['indirect', text];
    }
    else {
      return ['nomention'];
    }
  }
});

Toastbot.prototype.is_direct_command = method(function(self, name, text) {
  var to_me = self.said_to_me(text);
  
  if(to_me[0] != 'direct') {
    return null;
  }
  
  // Use the modified text.
  text = to_me[1];
  
  if(text.toLowerCase() != name) {
    return null;
  }
  
  return text;
});

Toastbot.prototype.handle_message = method(function(self, nick, text) {
  var clean_text = self.clean_message(text);
  
  if(clean_text.substr(0, 6) == 'ACTION') {
    self.log('* '+nick+' '+clean_text.substr(5));
  }
  else {
    self.log(nick+": "+clean_text);
  }
 
  // Run the message through the handlers.
  for(var func_name in self) if(self[func_name].enabled && self[func_name].enabled()) {
    var response = self[func_name](nick, clean_text);
    
    if(response == null) {
      // Choosing not to handle this message.
      continue;
    }
    
    if(response == true) {
      // We're waiting on a callback. It'll handle the ``.say``.
      return;
    }
    
    // We got something back to say!
    self.say(response);
    return;

  }
});

Toastbot.prototype.handle_pm = method(function(self, nick, text) {
  var clean_text = self.clean_message(text);
  self.log("PM <- "+nick+": "+clean_text);
  var message = "Sorry, I don't respond to PMs yet.";
  self.client.say(nick, message);
  self.log("PM -> "+nick+": "+message);
});


// Exports.

exports.Toastbot = Toastbot;
exports.zero_pad = zero_pad;
exports.method = method;
exports.handler = handler;

// ==============================================
// Handlers!
// ==============================================


Toastbot.prototype.help = handler(method(function(self, nick, text) {
  var text = self.is_direct_command('help', text);
  
  if(! text) {
    return null;
  }
  
  var commands = [
    nick+": Valid commands -"
  ];
 

  for(var func_name in self) if(self[func_name].enabled && self[func_name].enabled()) {
    commands.push('   - '+func_name+' = '+(self[func_name].__doc__ || 'No documentation.'));
  } 
  
  return commands;
}));

Toastbot.prototype.help.__doc__ = "Provides a description of what I respond to.";

Toastbot.prototype.dance = handler(method(function(self, nick, text) {
  var text = self.is_direct_command('dance', text);
  
  if(! text) {
    return null;
  }
  
  var sweet_moves = [
    "_O_",
    "\\O_",
    "_O/",
    "\\O/",
  ];
  
  return sweet_moves;
}));
Toastbot.prototype.dance.__doc__ = "Get down and funky.";

Toastbot.prototype.wiki = handler(method(function(self, nick, text) {
  var to_me = self.said_to_me(text);
  
  if(to_me[0] != 'direct') {
    return null;
  }
  
  // Use the modified text.
  text = to_me[1];
  
  if(text.indexOf('wiki') != 0) {
    return null;
  }
  
  var search_terms = text.replace('wiki ', '');
  var options = {
    host: 'en.wikipedia.org',
    method: 'GET',
    path: '/w/index.php?search='+escape(search_terms),
    headers: {
      'User-Agent': 'Mozilla/4.0 (toastbot)'
    }
  };
  
  var req = http.get(options, function(res) {
    if(res.statusCode.toString() == '302') {
      self.say(nick+': '+res.headers['location']);
    }
  }).on('error', function(e) {
    self.log("Failed to load wiki entry for '"+search_terms+"': "+e.message);
  });
  
  return true;
}));
Toastbot.prototype.wiki.__doc__ = "Search Wikipedia for a topic.";

Toastbot.prototype.metar = handler(method(function(self, nick, text) {
  var to_me = self.said_to_me(text);
  
  if(to_me[0] != 'direct') {
    return null;
  }
  
  // Use the modified text.
  text = to_me[1];
  
  if(text.indexOf('metar') != 0) {
    return null;
  }
  
  var station = text.replace('metar ', '');
  var url = 'ftp://tgftp.nws.noaa.gov/data/observations/metar/stations/'+station.toUpperCase()+'.TXT';
  var curl = spawn('curl', [url]);
  var buffer = '';
  
  curl.stdout.on('data', function (data) {
    buffer += data;
  });
  
  curl.on('exit', function (code) {
    if(buffer.length > 0) {
      self.say(nick+': '+buffer.replace('\n', ' ').replace('\r', ''));
    }
    else {
      self.log("Failed to load metar entry for '"+station+"'.");
      self.say(nick+': Sorry, couldn\'t find that station.')
    }
  });
  
  return true;
}));
Toastbot.prototype.metar.__doc__ = "Fetch a NOAA METAR by station code.";

Toastbot.prototype.twitter = handler(method(function(self, nick, text) {
  var to_me = self.said_to_me(text);
  
  if(to_me[0] != 'direct') {
    return null;
  }
  
  // Use the modified text.
  text = to_me[1];
  
  if(text.indexOf('twitter') != 0) {
    return null;
  }
  
  var search_terms = text.replace('twitter ', '');
  var options = {
    host: 'search.twitter.com',
    method: 'GET',
    path: '/search.json?rpp=5&result_type=recent&q='+escape(search_terms),
    headers: {
      'User-Agent': 'Mozilla/4.0 (toastbot)'
    }
  };
  
  var req = http.get(options, function(res) {
    if(res.statusCode.toString() == '200') {
      var buffer = '';
      
      res.on('data', function(data) {
        buffer += data;
      });
      
      res.on('end', function() {
        var data = JSON.parse(buffer);
        var results = [
          nick+': Top 5 results'
        ];
        
        for(var offset in data['results']) {
          var tweet = data['results'][offset];
          results.push('   - @'+tweet.from_user+': '+tweet.text);
        }
        self.say(results);
      })
    }
    else {
      self.log("Failed to load Twitter search for '"+search_terms+"': "+res.statusCode);
      self.say(nick+': Sorry, Twitter isn\'t responding.');
    }
  }).on('error', function(e) {
    self.log("Failed to load wiki entry for '"+search_terms+"': "+e.message);
  });
  
  return true;
}));
Toastbot.prototype.twitter.__doc__ = "Search Twitter for a topic.";
