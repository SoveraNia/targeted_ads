var page = require('webpage').create(), fs = require('fs'), address;
var system = require('system');

if (system.args.length < 2) {
  console.log('Usage:');
  console.log('phantomjs --load-plugins=true --disk-cache=no --web-security=no --cookies-file=COOKIE_FILE phantomjs_start.js URL OPTIONS')
  console.log('')
  console.log("Available options:")
  console.log("\tdnt=1\t\t\t\tEnable Do-not-track HTTP header")
  console.log("\tidentify_ads=1\t\t\tEnable advertisement extraction")
  console.log("\tlog_requests=\tall\t\tLog all HTTP requests.")
  console.log("\t\t\ttrackers\tLog only trackers based on Ghostery database.")
  console.log("\tdelay=MS\t\t\tSet the elapsed time before scripts are being injected on the page. Default is 1000.")
  console.log("\tblock=DOM_1+DOM_2+...\t\tBlock all HTTP requests that go through designated domains.")
  console.log("\tcookie_block=DOM_1+DOM_2+...\tBlock all designated domains from setting cookies. (Testing)")
  console.log("\tcookie_allow=DOM_1+DOM_2+...\tAllow only designated domains to set cookies. (Testing))")
  phantom.exit(1);
} else {
  address = system.args[1];
}

page.settings.webSecurityEnabled = false;

var identifyAds = false;
var dnt = false;
var identifyTrackers = false;
var log_requests = false;
var blocked_domains = [];
var cookie_blocked_domains = [];
var cookie_allowed_domains = [];

var options = {
  scriptInjectWaitTime : 5000,
  scriptExecTimeout : 10000,
  totalTimeout : 60000
}

if (system.args.length >= 3) {
  input_options = system.args[2].split(',');
} else {
  input_options = [];
}
// Read input options
for (var i = 0; i < input_options.length; i++) {
  var key = input_options[i].toUpperCase();
  var value = null;
  if (input_options[i].indexOf('=') >= 0) {
    temp = input_options[i].split('=');
    key = temp[0].toUpperCase();
    value = temp[1].toUpperCase();
  }
  if (key == "DNT") {
    console.log("<PHANTOMJS><DEBUG>\tDnt enabled")
    dnt = true;
  } 
  else if (key == "IDENTIFY_ADS") {
    console.log("<PHANTOMJS><DEBUG>\tAd identifying enabled")
    identifyAds = true;
  }
  else if (key == "LOG_REQUESTS") {
    if (value == "ALL") {
      console.log("<PHANTOMJS><DEBUG>\tLogging all requests")
      log_requests = true;
      identifyTrackers = true;
    } else if (value == "TRACKERS") {
      console.log("<PHANTOMJS><DEBUG>\tLogging trackers")
      identifyTrackers = true;
    }
  } 
  else if (key == "DELAY") {
    console.log("<PHANTOMJS><DEBUG>\tScript inject delay set to: " + parseInt(value));
    options.scriptInjectWaitTime = parseInt(value);
  }
  else if (key == "BLOCK") {
    var b_domains = value.split('+');
    for (var j = 0; j < b_domains.length; j++) {
      console.log("<PHANTOMJS><DEBUG>\tBlocking domain: " + b_domains[j]);
      blocked_domains.push(b_domains[j]);
    }
  }
  else if (key == "COOKIE_BLOCK") {
    var cb_domains = value.split('+');
    for (var j = 0; j < cb_domains.length; j++) {
      console.log("<PHANTOMJS><DEBUG>\tCookie-blocking domain: " + cb_domains[j]);
      cookie_blocked_domains.push(cb_domains[j]);
    }
  }
  else if (key == "COOKIE_ALLOW") {
    var ca_domains = value.split('+');
    for (var j = 0; j < ca_domains.length; j++) {
      console.log("<PHANTOMJS><DEBUG>\tCookie-allowing domain: " + ca_domains[j]);
      cookie_allowed_domains.push(ca_domains[j]);
    }
  }
}

if (system.args.length > 3) {
  for (var i = 3; i < system.args.length; i++) {
    blocked_domains.push(system.args[i]);
  }
}

// Build tracker database
tracker_list = [];
tracker_reg_exp_all = null;
if (identifyTrackers) {
  try {
    var f = fs.open('/var/www/ad_detect/resources/bugs.json', 'r');
    var tracker_string = f.read();
    var temp_tracker_db = JSON.parse(tracker_string);
    for (var i = 0; i < temp_tracker_db.bugs.length; i++) {
      bug = temp_tracker_db.bugs[i];
      // if (bug.type == 'analytics' || bug.type == 'tracker')
      tracker_list.push(bug.pattern);
    }
    delete temp_tracker_db;
  }
  catch (e) {
    console.log('Error loading tracker db! '+e);
  }
}
tracker_reg_exp_all = new RegExp(tracker_list.join('|'), 'i');

function isTracker(url) {
  var tracker_id = false;
  if (!tracker_db.all_regex.test(url))
      return false;

  for (var id in tracker_db.regexs) {
      if (tracker_db.regexs[id].test(url)) {
          tracker_id = id;
          break;
      }
  }
  return tracker_id;
}

page.customHeaders = {
  'x-project-homepage': 'http://ad-measurement.cs.ucr.edu/'
};

page.onResourceRequested = function(requestData, request) {
  // console.log("Request\t" + JSON.stringify(requestData))
  if (dnt || blocked_domains.length > 0 || identifyTrackers || log_requests) {
    var blocked = false;
    for (var i = 0; i < blocked_domains.length; i++) {
      if (requestData['url'].split('&')[0].toUpperCase().indexOf(blocked_domains[i]) >= 0) {
        console.log("<PHANTOMJS><DEBUG>\tRequest Blocked\t" + requestData['url']);
        blocked = true;
        request.abort();
        break;
      }
    }
    if (!blocked && dnt) {
      request.setHeader("DNT", 1);
    }
    if (!blocked) {
      if (identifyTrackers && tracker_reg_exp_all.test(requestData['url'])) {
        referer = "NONE";
        for (var x = 0; x < requestData['headers'].length; x++)
          if (requestData['headers'][x]['name'].toUpperCase() == "REFERER")
            referer = requestData['headers'][x]['value']
        console.log("<MSG><RESULT>\tTracker Detected:\t" + requestData['url'] + '\t' + referer);
      } else if (log_requests) {
        console.log("<MSG><RESULT>\tRequest Detected:\t" + requestData['url']);
      }
    }
  }
}

function filterCookies() {
  // console.log(JSON.stringify(phantom.cookies));
  //var new_cookies = [];
  var to_be_removed = []
  for (var i = 0; i < phantom.cookies.length; i++) {
    dom = phantom.cookies[i].domain.toLowerCase();
    // Blocking mode
    if (cookie_blocked_domains.length > 0) {
      for (var j = 0; j < cookie_blocked_domains.length; j++) {
        if (cookie_blocked_domains[j].toLowerCase() == dom || dom.indexOf('.' + cookie_blocked_domains[j].toLowerCase()) >= 0) {
          to_be_removed.push(phantom.cookies[i].name);
          break;
        } else {
          //new_cookies.push(phantom.cookies[i]);
        }
      }
    }
    // Allowing mode
    else if (cookie_allowed_domains.length > 0) {
      match = false;
      for (var j = 0; j < cookie_allowed_domains.length; j++) {
        if (cookie_allowed_domains[j].toLowerCase() == dom || dom.indexOf('.' + cookie_allowed_domains[j].toLowerCase()) >= 0) {
          match = true;
          //new_cookies.push(phantom.cookies[i]);
          break;
        }
      }
      if (!match)
        to_be_removed.push(phantom.cookies[i].name);
    }
  }
  for (var i = 0; i < to_be_removed.length; i++) {
    console.log("Deleting\t" + to_be_removed[i]);
    phantom.deleteCookie(to_be_removed[i])
  }
  // console.log(JSON.stringify(phantom.cookies));
}
filterCookies();

var time = Date.now();

var scraper_finished = true;
var remarketing_finished = true;

page.onConsoleMessage = function(msg) {
  console.log(msg);
  if (msg == '__quit__scraper.js') {
    if (remarketing_finished == true) {
      var out_last_time = Date.now();
      var outer = window.setInterval(function() {
        var out_current_time = Date.now();
        if ((out_current_time - out_last_time) > 1000) {
          t = out_current_time - time;
          console.log('<PHANTOMJS>\tTask terminated! ' + t + ' ms.\t' + address);
          page.close();
          filterCookies();
          phantom.exit();
          window.clearInterval(outer);
        }
      }, 300);
    } else {
      scraper_finished = true;
    }
  }
  if (msg == '__quit__detect_remarketing.js') {
    if (scraper_finished == true) {
      var out_last_time = Date.now();
      var outer = window.setInterval(function() {
        var out_current_time = Date.now();
        if ((out_current_time - out_last_time) > 1000) {
          t = out_current_time - time;
          console.log('<PHANTOMJS>\tTask terminated! ' + t + ' ms.\t' + address);
          page.close();
          filterCookies();
          phantom.exit();
          window.clearInterval(outer);
        }
      }, 300);
    } else {
      remarketing_finished = true;
    }
  }
}

if (identifyAds) {
  scraper_finished = false;
  remarketing_finished = false;
  page.open(address, function(status) {
    if (status !== 'success') {
      console.log('<PHANTOMJS><ERR>\tUnable to load the address!\t' + address);
    } else {
      var current_time = Date.now();
      current_time = current_time - time;
      console.log('<PHANTOMJS>\tLoading took ' + current_time + ' ms!\t' + address);
      results = page.evaluate(function(options) {
        // Inject Javascript after 5s
        window.setTimeout(function() {
          var script = document.createElement("script");
          script.type = "text/javascript";
          script.src = "http://localhost/ad_detect/lib/scraper.js";
          document.body.appendChild(script);
          
          var script = document.createElement("script");
          script.type = "text/javascript";
          script.src = "http://localhost/ad_detect/lib/detect_remarketing.js";
          document.body.appendChild(script);
        }, options.scriptInjectWaitTime)
      }, options);
    }
  
    // Terminate tast in k seconds
    var out_last_time = Date.now();
    var outer = window.setInterval(function() {
      var out_current_time = Date.now();
      if ((out_current_time - out_last_time) > options.scriptInjectWaitTime
          + options.scriptExecTimeout) {
        t = out_current_time - time;
        console.log('<PHANTOMJS>\tTask terminated! ' + t + ' ms.\t' + address);
        window.clearInterval(outer);
        page.close();
        filterCookies();
        phantom.exit();
      }
    }, 200);
  });
} else {
  remarketing_finished = false;
  page.open(address, function(status) {
    if (status !== 'success') {
      console.log('<PHANTOMJS><ERR>\tUnable to load the address!:\t' + address);
    } else {
      var current_time = Date.now();
      current_time = current_time - time;
      console.log('<PHANTOMJS>\tLoading took ' + current_time + ' ms!\t' + address);
      results = page.evaluate(function(options) {
        // Inject Javascript after 5s
        window.setTimeout(function() {
          var script = document.createElement("script");
          script.type = "text/javascript";
          script.src = "http://localhost/ad_detect/lib/detect_remarketing.js";
          document.body.appendChild(script);
        }, options.scriptInjectWaitTime)
      }, options);
    }
  
    // Terminate tast in k seconds
    var out_last_time = Date.now();
    var outer = window.setInterval(function() {
      var out_current_time = Date.now();
      if ((out_current_time - out_last_time) > options.scriptInjectWaitTime
          + options.scriptExecTimeout) {
        t = out_current_time - time;
        console.log('<PHANTOMJS>\tTask terminated! ' + t + ' ms.\t' + address);
        window.clearInterval(outer);
        page.close();
        filterCookies();
        phantom.exit();
      }
    }, 200);
  });
}
window.setTimeout(function() {
  console.log('<PHANTOMJS>\tPage load too slow:\t' + address);
  phantom.exit();
}, options.totalTimeout);