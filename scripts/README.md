Instructions to Run Test Scripts
============
1. Requirements
------------

First you will need a PhantomJS 1.9 with Flash plugin support. It can be downloaded here:

http://www.ryanbridges.org/2013/05/21/putting-the-flash-back-in-phantomjs/

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
