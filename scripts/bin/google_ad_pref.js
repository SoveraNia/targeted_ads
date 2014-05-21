var page = require('webpage').create(), fs = require('fs'), address;

var system = require('system');

address = 'https://www.google.com/settings/ads'

var options = {
  scriptInjectWaitTime : 5000,
  scriptExecTimeout : 10000,
  totalTimeout : 45000
}

var time = Date.now();

var scraper_finished = true;
var remarketing_finished = true;

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
        // Gender
        var div_gender = document.querySelectorAll('.jK > .tm > .nm > .km > div > .ii');
        if (div_gender.length > 0) 
          console.log('<AD_PREF>\tGender:\t' + div_gender[0].innerHTML);
        else
          console.log('<AD_PREF>\tGender:\tNONE');
        // Age
        var div_age = document.querySelectorAll('.XJ > .tm > .nm > .km > div > .ii');
        if (div_age.length > 0) 
          console.log('<AD_PREF>\tAge:\t' + div_age[0].innerHTML);
        else
          console.log('<AD_PREF>\tAge:\tNONE');
        // Language
        var div_lang = document.querySelectorAll('.pK > .tm > .nm > .km > div > .ii');
        if (div_lang.length > 0) 
          console.log('<AD_PREF>\tLanguage:\t' + div_lang[0].innerHTML);
        else
          console.log('<AD_PREF>\tLanguage:\tNONE');
        // Interest
        var div_interest = document.querySelectorAll('.bL > .dK > table > tbody > tr > .aL');
        if (div_interest.length > 0) {
          for (var i = 0; i < div_interest.length; i ++) 
            console.log('<AD_PREF>\tInterest:\t' + div_interest[i].innerHTML);
        } else
          console.log('<AD_PREF>\tInterest:\tNONE');
        console.log('__quit__');
      }, options.scriptInjectWaitTime)
    }, options);
  }
})

window.setTimeout(function() {
  console.log('<PHANTOMJS>\tPage load too slow:\t' + address);
  phantom.exit();
}, options.totalTimeout);