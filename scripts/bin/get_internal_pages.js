var page = require('webpage').create(), fs = require('fs'), address, count;

var system = require('system');
if (system.args.length < 3) {
  console.log('<PHANTOMJS>\tNo address provided!');
  phantom.exit(1);
} else {
  address = system.args[1];
  count = parseInt(system.args[2]);
}

var options = {
  pageLoadTime: 5000,
  urlCount: count
}

page.onConsoleMessage = function(msg) {
  console.log(msg);
}

page.open(address, function(status) {
  if (status !== 'success') {
    console.log('<PHANTOMJS><ERR>\tUnable to load the address!:\t' + address);
  } else {
    results = page.evaluate(function(options) {
      function parseUri(str) {  
        var o = parseUri.options, m = o.parser[o.strictMode ? "strict" : "loose"]
            .exec(str), uri = {}, i = 14;

        while (i--)
          uri[o.key[i]] = m[i] || "";

        uri[o.q.name] = {};
        uri[o.key[6]] = "http://" + uri[o.key[6]];
        uri[o.key[12]].replace(o.q.parser, function($0, $1, $2) {
          if ($1)
            uri[o.q.name][$1] = $2;
        });

        return uri;
      }
      
      parseUri.options = {
        strictMode : false,
        key : [ "source", "protocol", "authority", "userInfo", "user", "password",
            "host", "port", "relative", "path", "directory", "file", "query",
            "anchor" ],
        q : {
          name : "queryKey",
          parser : /(?:^|&)([^&=]*)=?([^&]*)/g
        },
        parser : {
          strict : /^(?:([^:\/?#]+):)?(?:\/\/((?:(([^:@]*)(?::([^:@]*))?)?@)?([^:\/?#]*)(?::(\d*))?))?((((?:[^?#\/]*\/)*)([^?#]*))(?:\?([^#]*))?(?:#(.*))?)/,
          loose : /^(?:(?![^:@]+:[^:@\/]*@)([^:\/?#.]+):)?(?:\/\/)?((?:(([^:@]*)(?::([^:@]*))?)?@)?([^:\/?#]*)(?::(\d*))?)(((\/(?:[^?#](?![^?#\/]*\.[^?#\/.]+(?:[?#]|$)))*\/?)?([^?#\/]*))(?:\?([^#]*))?(?:#(.*))?)/
        }
      };
      
      var host = parseUri(document.URL).host;
      var domain;
      if (host.match(/.*?\..*\./))
        domain = host.replace(host.match(/.*?\./)[0], "");
      else
        domain = host.replace(host.match(/.*\/\//)[0], "");
      
      var aList = document.querySelectorAll('a');
      var urlList = []
      for (var i = 0; i < aList.length; i++) {
        if (aList[i].href.indexOf(domain) > 0 && aList[i].href != document.URL && aList[i].href.indexOf('?') < 0)
          urlList.push(aList[i].href);
      }
      
      if (urlList.length < options.urlCount) {
        for (var i = 0; i < urlList.length; i++)
          console.log("<MSG><RESULT>\t" + urlList[i]);
      } else {
        count = 0;
        used = {};
        while (count != options.urlCount) {
          var i = Math.floor((Math.random()*urlList.length));
          if ((urlList[i] in used) == false) {
            console.log("<MSG><RESULT>\t" + urlList[i]);
            used[urlList[i]] = true;
            count ++;
          }
        }
      }
    }, options);
    phantom.exit();
  }
});
window.setTimeout(function() {
  console.log('<PHANTOMJS>\tPage load too slow:\t' + address);
  phantom.exit();
}, 15000);