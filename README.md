# µchan - anonymous imageboard software

µchan is a modern take on internet messaging board software, also known as a *BBS*, *textboard* or *imageboard*.

It has all the basic features you expect from a message board: boards for different topics, support for attaching images to posts and a system for moderating. µchan is anonymous and requires no account to post.

In addition to the basic features, µchan supports creating boards by everyone, and the moderation interface is extensive and clear. Moderator permissions give extra control over the capabilities of a mod. See the [roadmap](https://github.com/Floens/uchan/issues/1) for a list of features that are implemented.

µchan is super light-weight. It supports users that have JavaScript disabled. You can even browse it with the original Nintento DS!

## Who is µchan for?
You can use µchan to set up your own message board.
The goal of µchan is to be the go-to software for messaging board software.

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

This isn't a full comprehensive list of features, see the demo site for a live instance of µchan.
Missing a feature? Request it by [creating an issue](https://github.com/Floens/uchan/issues/new).


## What is different about µchan?
This software is meant to replace older solutions that aren't of this age anymore. Traditional messaging boards are static: each time a user submits a message it generates new files to update the board. Changing layouts and the likes requires full rebuilds of the site.

µchan takes a modern dynamic approach, and generates pages when they are requested. On top of that is a good caching mechanism, so that responses are delivered just as fast as static files. It can handle the load when your site grows, adding new servers to take up the extra load, there is no single point of failure.

# Docker setup

µchan requires multiple services to run. To ease the setup and running of µchan, a docker compose configuration was created, with a manage script.

This setup can be used in production environments. As your site grows, you can adjust the configuration as needed.

Data is stored in the `./data` directory, including the database, logs and media storage.

*Please report any bugs you find with this tool.*

#### Requirements

A system with support for Docker, Linux is preferred.

#### Installation

Install Docker, either from your package manager, or follow the instructions [from the docker site](https://docs.docker.com/engine/installation/).

Copy `config.ini.sample` to `config.ini`. Take a good look at the `site_url`, the captcha parameters and `local_cdn_web_path`.
Copy `.env.sample` to `.env` and adjust the port uchan should be available at.

##### Behind a proxy
If you plan to run uchan behind a proxy, for example if you already run a nginx server, and want to put uchan under a separate domain,
then you need to adjust a few parameters to make sure the correct ip is given to uchan.
In the config, change `proxy_fixer_num_proxies` to 3. In the varnish config (located at docker/varnish/uchan.vcl)
uncomment the block that adds the ip forwarding. And finally, change the port in .env to something else.
Make sure that port isn't reachable directly from the outside. After this you can configure your server to forward all requests to localhost
with the specified port, as a proxy.

#### Setup

Run `make upgrade` and then `make setup`. The setup step will ask for a username and password for the admin account.

#### Troubleshooting

Run `docker-compose logs <component>` for logs of a component, where component is either `app` or `worker`.


#### Upgrading

To upgrade to the newest version of µchan, run `git pull origin` and then `make upgrade`. This pulls the newest version from git, runs a database upgrade and restarts the stack.
