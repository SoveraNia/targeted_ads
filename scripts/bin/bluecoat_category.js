var page = require('webpage').create(), fs = require('fs'), address;

var system = require('system');

query = system.args[1];

address = 'http://sitereview.bluecoat.com/sitereview.jsp'

var options = {
  scriptInjectWaitTime : 5000,
  scriptExecTimeout : 10000,
  totalTimeout : 45000,
  query : query
}

var time = Date.now();

page.onConsoleMessage = function(msg) {
  console.log(msg);
  if (msg == '__quit__')
    phantom.exit();
}

page.open(address, function(status) {
  if (status != 'success') {
    console.log('<PHANTOMJS><ERR>\tUnable to load the address!\t' + address);
  } else {
    var current_time = Date.now();
    current_time = current_time - time;
    console.log('<PHANTOMJS>\tLoading took ' + current_time + ' ms!\t' + address);
    results = page.evaluate(function(options) {
      // Inject Javascript after 5s
      window.setTimeout(function() {
        var dataInput = document.getElementById('search');
        dataInput.value = options.query;
        var button = document.getElementById('submit');
        button.click();
        window.setTimeout(function() {
          var cats = document.querySelectorAll("#submissionForm > span > span > a");
          for (var i = 0; i < cats.length; i++) {
            console.log('<CATEGOTY>\t' + cats[i].innerHTML)
          }
          console.log('__quit__');
        }, options.scriptInjectWaitTime)
      }, options.scriptInjectWaitTime)
    }, options);
  }
})

window.setTimeout(function() {
  console.log('<PHANTOMJS>\tPage load too slow:\t' + address);
  phantom.exit();
}, options.totalTimeout);