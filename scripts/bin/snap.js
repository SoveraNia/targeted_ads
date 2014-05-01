var page = require('webpage').create();
page.open('http://www.cricbuzz.com', function () {
    window.setTimeout(function(){
        page.render('video.png');
        phantom.exit();
    },3000);
});