Instructions to Run Test Scripts
============
1. Environment Setup
------------
First you will need a PhantomJS 1.9 with Flash plugin support. It can be downloaded here:

http://www.ryanbridges.org/2013/05/21/putting-the-flash-back-in-phantomjs/

On my computer and servers I'm putting the PhantomJS program under "~/Lab_TargetedAds/phantomjs/phantomjs--linux-x86_64/". You can put it elsewhere but that might require you to fix some paths in other scripts.

Next, you need to install Flash plugin. On Ubuntu, you can get it through following commands:

```
sudo apt-add-repository "deb http://archive.ubuntu.com/ubuntu quantal main restricted multiverse universe"
sudo apt-get -y update
sudo apt-get -y install flashplugin-installer
```

If you are running on a remote server, you are going to need Xvfb virtual frame buffer. Although PhantomJS is a headless browser, it need Xvfb to correctly render Flash objects.

Here are commands to install Xvfb:

```
# Xvfb
sudo apt-get --no-install-recommends -y install build-essential git-core g++
sudo apt-get --no-install-recommends -y install openssl chrpath libssl-dev libfontconfig1-dev libglib2.0-dev libx11-dev libxext-dev libfreetype6-dev libxcursor-dev libxrandr-dev libxv-dev libxi-dev libgstreamermm-0.10-dev xvfb 
# Xvfb Fonts
sudo apt-get -y install x11-xkb-utils
sudo apt-get -y install xfonts-base xfonts-100dpi xfonts-75dpi xfonts-scalable xfonts-cyrillic
```

After everything is installed, you can use the following command to start Xvfb display:

```
Xvfb :99 -screen 0 1280x1024x24 &
export DISPLAY=:99
```

Finally, you will need Apache Httpd server, PHP and its curl support.

```
sudo apt-get -y install apache2
sudo apt-get -y install php5
sudo apt-get -y install php5-curl
sudo apt-get -y install libapache2-mod-php5
```

2. Setting up scripts
------------
Check out everything under "scripts" folder. For me I'm putting them under "~/Lab_TargetedAds/src". You can put them elsewhere but that might require you to fix some paths in other scripts.

Next, you need to host some Javascript and PHP files on your Apache server. To do this, first create folder "ad_detect" under your Apache server's HTML directory (e.g. "/var/www/html"). 
Then copy "resources" folder, "lib/js" folder and "bin/get_url_category.php" to the "ad_detect" folder you just created.
Then rename the copied "js" folder into "lib".
The resulting file structure under the "ad_detect" folder should look like this:

```
lib
lib/detect_remarketing.js
lib/scraper.js
resources
resources/ad_db.json
resources/ad_providers.json
resources/bugs.json
resources/landing_patterns.json
resources/redirection_db.json
get_url_category.php
```

Now you should be able to run python scripts located under "test_scripts" folder.
See the scripts themselves for parameter instructions.