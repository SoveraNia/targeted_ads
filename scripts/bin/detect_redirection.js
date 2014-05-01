var fs = require('fs'), address;

var system = require('system');
if (system.args.length < 2) {
  console.log('<PHANTOMJS>\tNo address provided!');
  phantom.exit(1);
} else {
  address = system.args[1];
}

function renderPage(url) {
  var page = require('webpage').create();
  var currentURL = url; 
  var redirectURL = null;

  /*
  page.onResourceRequested = function(requestData, request) {
    console.log(requestData['url']);
    console.log(JSON.stringify(requestData['headers']));
  }
  */
  
  page.onResourceReceived = function(resource) {
    if (currentURL == resource.url && resource.redirectURL) {
      console.log("<MSG><RESULT>\tRedirecting\t" + url + '\tto\t' + resource.redirectURL);
      currentURL = resource.redirectURL;
    }
  };

  page.open(url, function(status) {
    /*
    if (status == 'success') {
      console.log("<MSG><RESULT>\tDestination\t" + currentURL);
    } else {
      // ...
    }
    */
    window.setTimeout(function() {
      console.log("<MSG><RESULT>\tDestination\t" + page.url);
      phantom.exit();
    }, 5000)
    // phantom.exit();
  });
}
renderPage(address)
window.setTimeout(function() {
  console.log('<PHANTOMJS>\tPage load too slow:\t' + address);
  phantom.exit();
}, 30000);
