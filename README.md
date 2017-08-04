# µchan - anonymous imageboard software

[*Demo site*](https://uchan.plebco.de/)

µchan is a modern take on internet messaging board software, also known as a *BBS*, *textboard* or *imageboard*.

It has all the basic features you expect from a message board: boards for different topics, support for attaching images to posts and a system for moderating. µchan is anonymous and requires no account to post.

In addition to the basic features, µchan supports creating boards by everyone, and the moderation interface is extensive and clear. Moderator permissions give extra control over the capabilities of a mod. See the [roadmap](https://github.com/Floens/uchan/issues/1) for a list of features that are implemented.

µchan is super light-weight. It supports users that have JavaScript disabled. You can even browse it with the original Nintento DS!

Any questions or issues can be asked on #uchan @ rizon or by creating an issue here on GitHub.


## Who is µchan for?
You can use µchan to set up your own message board. See the [setup](SETUP) guide for more info.
The goal of µchan is to be the go-to software for messaging board software.

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

Run `make upgrade` and then `make setup`. The setup step will ask for a username and password for the admin account.

#### Upgrading

To upgrade to the newest version of µchan, run `make upgrade`. This pulls the newest version from git, runs a database upgrade and restarts the stack.
