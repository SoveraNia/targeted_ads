var Chrome = require('chrome-remote-interface');
var events = require('events');
var util = require('util');
var common = require('./common.js');
var Page = require('./Page.js');

var CLEANUP_SCRIPT =
    'var x;' +
    'x=chrome.benchmarking.clearCache; x&&x();' +
    'x=chrome.benchmarking.clearHostResolverCache; x&&x();' +
    'x=chrome.benchmarking.clearPredictorCache; x&&x();' +
    'x=chrome.benchmarking.closeConnections; x&&x();';

var Client = function (urls, options) {
    var self = this;

    self.pages = [];

    var fs  = require("fs");
    var path = __dirname + '/find_object_locations_onlypos.js'
    var location_code = fs.readFileSync(path).toString();
    var resource_output = options['resource_output'];
    console.error('Client: ' + options['port']);

    var opt = {'host': options.host,
               'port': options.port};

    Chrome(opt, function (chrome) {
        // load the next URL or exit if done
        function loadNextURL() {
            var id = self.pages.length;
            var url = urls[id];
            if (url) {
                //if (!url.match(/^http[s]?:/)) {
                //    url = 'http://' + url;
                //}
                var page = new Page(id, url);
                self.emit('pageStart', url);

                chrome.Runtime.evaluate({'expression': CLEANUP_SCRIPT}, function (error, response) {
                    // error with the communication or with the JavaScript code
                    if (error || (response && response.wasThrown)) {
                        common.dump('Cannot inject JavaScript: ' +
                            JSON.stringify(response, null, 4));
                            self.emit('error');
                    } else {
                        page.start();
                        chrome.Page.navigate({'url': url});
                        self.pages.push(page);
                    }
                });
            }
            return url;
        }

        // start!
        self.emit('connect');
        chrome.Page.enable();
        chrome.Network.enable();
        //chrome.Network.setCacheDisabled({'cacheDisabled': true});
        chrome.Network.clearBrowserCookies();
        chrome.Network.clearBrowserCache();
        chrome.Console.enable();
        var messages = [];
        var finished = false;
        var misses = 0;

        loadNextURL();


        // This will timeout after 40 seconds no matter what
        setTimeout(function() {
            if (finished) {}
            else {
                console.error('internal timeout, exiting');
                finished = true;
                chrome.Page.navigate({'url': 'chrome://blank/'});
                setTimeout(function() {
                    process.exit(1);
                }, 1000);
            }
        }, 120000);

        // This will timeout 4 sec * 2
        function smallTimeout() {
            misses++;
            if (finished) {}
            else if (misses < 8) {
                //console.error('inside timeout, misses:' + misses);
                setTimeout(smallTimeout, 4000);
                //setTimeout(smallTimeout, 8000);
            } else {
                //console.error('inside timeout, used was FALSE');
                console.error('internal small timeout, exiting');
                finished = true;
                chrome.Page.navigate({'url': 'chrome://blank/'});
                setTimeout(function() {
                    process.exit(2);
                }, 1000);
            }
        }
        setTimeout(smallTimeout, 4000);
        //setTimeout(smallTimeout, 8000);


        chrome.on('event', function (message) {
            if (!finished) {
                misses = 0;
                //console.error('used reset');
                messages.push(message);
                if (message.method) {
                    var page = self.pages.slice(-1)[0];

                    if (message.method == 'Page.domContentEventFired') {
                        common.dump('<-- ' + message.method + ': ' + page.url);
                        page.domLoaded();
                    } else if (message.method == 'Page.loadEventFired') {
                        common.dump('<-- ' + message.method + ': ' + page.url);
                        page.end();
                    } else if (message.method.match(/^Network./)) {
                        page.processMessage(message);
                        // if a response has been received, get the resource content text
                        if (message.method == 'Network.loadingFinished') {
                            var mid = message.params.requestId;
                            var mime = page.entries[mid].responseEvent.response.mimeType;
                            if (mime.slice(0, 6).toUpperCase() !== 'image/'.toUpperCase()) {
                                chrome.Network.getResponseBody({'requestId': message.params.requestId}, function (error, response) {
                                    page.entries[message.params.requestId].content = response.body;
                                });
                            }
                        }
                    } else {
                        common.dump('Unhandled message: ' + message.method);
                    }

                    if (typeof page === 'undefined'){
                        console.error('page.isDone() check error, exiting');
                        finished = true;
                        setTimeout(function() {
                            chrome.Page.navigate({'url': 'chrome://blank/'});
                            process.exit(3);
                        }, 1500);
                    }
                    
                    if (typeof page !== 'undefined' && page.isDone()) {
                        common.dump('page.isDone(): ' + page.isDone());
                        finished = true;
                        self.emit(page.isOk() ? 'pageEnd' : 'pageError', page.url);
                        // chrome.Runtime.enable();
                        
                        chrome.Runtime.evaluate({'expression': location_code});
                        //console.error('inject wait'.green);
                        setTimeout(function() {
                            //console.error('inject wait finished'.green);
                            json_datas = [];
                            getLocData(chrome, json_datas); // you have to wait a bit for the json_datas array to populate
                            //console.error('log write wait'.green);
                            setTimeout(function() {
                                //console.error('json_datas.length:' + json_datas.length);
                                if (json_datas.length == 1) {
                                    //console.error('log write wait finished'.green);
                                    loc_data = json_datas.pop();
                                    writeToLocationLog(loc_data, resource_output);

                                    if (!loadNextURL()) {
                                        chrome.Page.navigate({'url': 'chrome://blank/'});
                                        setTimeout(function() {
                                            common.dump("Emitting 'end' event");
                                            chrome.close();
                                            self.emit('end', getHAR.call(self), messages);
                                            finished = false;
                                            process.exit(0);
                                        }, 1500);
                                    }
                                } else {
                                    //console.error('failed to get resource metrics'.green);
                                    if (!loadNextURL()) {
                                        chrome.Page.navigate({'url': 'chrome://blank/'});   
                                        setTimeout(function() {
                                            chrome.close();
                                            finished = false;
                                            process.exit(4);
                                        }, 1500);
                                    }
                                }
                            }, 500);
                        }, 3500);
                    }
                } else {
                    common.dump('<-- #' + message.id + ' ' +
                                JSON.stringify(message.result));
                }
            }
        });
    }).on('error', function (error) {
        common.dump("Emitting 'error' event: " + error.message);
        self.emit('error');
    });
}

util.inherits(Client, events.EventEmitter);

function getLocData(chrome, json_datas) {
    chrome.Runtime.evaluate({'expression': "document.mikes_location_info;", "returnByValue": true}, function (error, response) {
        if (error) throw error;
        //if (typeof json_datas !== 'undefined' && typeof response.result.value !== 'undefined') {
        if (typeof json_datas !== 'undefined') {
            json_data = response.result.value;
            if (typeof json_data !== 'undefined') {
                //console.error('typeof json_data: ' + typeof json_data);
                //console.error('loc data len: ' + json_data.length);
                json_datas.push(json_data);
            }
        }
    });
}

function writeToLocationLog(loc_data, resource_output) {
    var fs = require('fs');

    //console.error('write loc data len: ' + loc_data.length);
    fs.writeFile(resource_output, loc_data, function(err) {
        if(err) {
            console.log(err);
        } else {
            console.log("The file was saved!");
        }
    });
}


function getHAR() {
    var self = this;
    var har = {
        'log': {
            'version' : '1.2',
            'creator' : {
                'name': 'Chrome HAR Capturer',
                'version': '0.3.2'
            },
            'pages': [],
            'entries': []
        }
    };

    // merge pages in one HAR
    for (var i in self.pages) {
        var page = self.pages[i];
        if (page.isOk()) {
            var pageHAR = page.getHAR();
            har.log.pages.push(pageHAR.info);
            Array.prototype.push.apply(har.log.entries, pageHAR.entries);
        }
    }

    return har;
}

module.exports = Client;
