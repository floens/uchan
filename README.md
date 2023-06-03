# µchan - anonymous imageboard software

µchan is a modern take on internet messaging board software, also known as a *BBS*,
*textboard* or *imageboard*.

It has all the basic features you expect from a message board: boards for different
topics, support for attaching images to posts and a system for moderating. µchan is
anonymous and requires no account to post.

In addition to the basic features, µchan supports creating boards by everyone, and the
moderation interface is extensive and clear. Moderator permissions give extra control
over the capabilities of a mod.

µchan is super light-weight. It supports users that have JavaScript disabled. You can
even browse it with the original Nintento DS!

## Installation and documentation

To access the installation instructions for the software project, please visit the
documentation website. The website should provide detailed step-by-step guidance on how
to install and set up µchan.

## Who is µchan for?

You can use µchan to set up your own message board. The goal of µchan is to be the go-to
software for messaging board software.

A quick rundown of what we support:
* Full support for javascript-less browsers.
* Posting
    * No account required
    * Markdown like formatting
    * Multiple files per post possible
    * Catalog
    * Captcha's can be enabled per board.
    * Captcha verifications are remembered for a few hours
    * Tripcode support for both classic and secure tripcodes
* Extension
    * Add-on to the base site
    * Watcher auto-updates the page when new replies are available
    * Inline image expansion
    * Quick replying
* Moderating
    * Public registration as moderators
    * Boards are created by moderators
        * Moderators can be invited to moderate a board
        * Control over permissions of invited moderators
        * All moderation actions are logged and visible
    * Reports
        * Dedicated interface for managing reports
        * Clear reports, remove posts and ban posters
    * Bans
        * Individual ip's or rangebans
        * Can be restricted to boards or global ban
        * Can be timed or indefinite
* Pages
    * Dynamic creation of pages
    * Linked at the bottom of a page
    * Markdown like formatting

Missing a feature? Request it by [creating an
issue](https://github.com/floens/uchan/issues/new).


## What is different about µchan?

This software is meant to replace older solutions that aren't of this age anymore.
Traditional messaging boards are static: each time a user submits a message it generates
new files to update the board. Changing layouts and the likes requires full rebuilds of
the site.

µchan takes a modern dynamic approach, and generates pages when they are requested. On
top of that is a good caching mechanism, so that responses are delivered just as fast as
static files. It can handle the load when your site grows, adding new servers to take up
the extra load, there is no single point of failure.
