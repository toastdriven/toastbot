var toastbot = require('./toastbot');

/*
var config = {
  server: 'irc.freenode.net',
  nick: 'toastbot',
  userName: 'toastbot',
  realName: 'ToastBot',
  debug: false,
  channels: [
    '#toastdriven'
  ]
}
*/

var bot = new toastbot.Toastbot({
  handlers: [
    'help',
    'dance',
    'wiki',
    'metar',
    'twitter',
  ]
});
bot.setup();
