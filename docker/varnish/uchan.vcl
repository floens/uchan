vcl 4.0;

backend default {
  .host = "nginx";
  .port = "5003";
}

acl app {
  "app";
  "worker";
}

#sub vcl_fetch {
#    set obj.ttl = 1m;
#}

sub vcl_recv {
  # Happens before we check if we have this in cache already.
  #
  # Typically you clean up the request here, removing cookies you don't need,
  # rewriting the request, etc.
  # set req.backend = default;

  if (req.method == "PURGE") {
    if (!client.ip ~ app) {
      return (synth(405, "Not allowed."));
    }

    return (purge);
  }

  # Forward the ip. If you don't run varnish as the first server, for example if you have uchan proxied by some other
  # front end server, then you need to enable this.
  # UNCOMMENT BELOW
  #if (req.restarts == 0) {
  #  set req.http.X-Forwarded-For = req.http.X-Forwarded-For + ", " + client.ip;
  #}

  # Only cache GET or HEAD requests. This makes sure the POST requests are always passed.
  if (req.method != "GET" && req.method != "HEAD") {
    return (pass);
  }

  # The endpoints change their content based on ip, etc. Never cache them.
  if (req.url ~ "^/banned/" || req.url ~ "^/verify/" || req.url ~ "^/post/" || req.url ~ "^/post_manage/") {
    return (pass);
  }

  # Remove verification cookie from client
  # The verification cookie has been designed to not interfere with any requests,
  # except for /verify/ and POST requests, which are never cached.
  set req.http.Cookie = regsuball(req.http.Cookie, "verification=[^;]+(; )?", "");

  # Remove a ";" prefix in the cookie if present
  set req.http.Cookie = regsuball(req.http.Cookie, "^;\s*", "");

  # Are there cookies left with only spaces or that are empty?
  if (req.http.cookie ~ "^\s*$") {
    unset req.http.cookie;
  }
}

sub vcl_backend_response {
  set beresp.grace = 10m;
}

