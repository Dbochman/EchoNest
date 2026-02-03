Andre / Prosecco (Resurrection Notes)
=

This repo is an older internal “office radio” app. Below are modern setup notes
for bringing it back locally or in a container.

Quickstart (Docker Compose)
1. Copy config template:
   - `cp config.example.yaml local_config.yaml`
2. Fill in required secrets in `local_config.yaml`:
   - Google OAuth client ID/secret
   - Spotify client ID/secret
   - YouTube/SoundCloud keys (if needed)
3. Run:
   - `docker-compose up --build`
4. Open:
   - `http://localhost:5000/`

Dev-only auth bypass
- Set `DEBUG=True` and `DEV_AUTH_EMAIL=dev@example.com` (via env or `local_config.yaml`).
- The app will auto-login on localhost only when DEBUG is true.

Google OAuth
- Set redirect URL to:
  - `http://localhost:5000/authentication/callback`

Environment overrides (optional)
- `REDIS_HOST`, `REDIS_PORT`, `DEV_AUTH_EMAIL`, `DEBUG`

Tests
- `SKIP_SPOTIFY_PREFETCH=1 pytest`

---

Welcome t o Andre!
=

Andre is how the Spotify Boston listens to music; we've given you guest access
until {{expires}}.

There are some rules that we ask you to follow, the same rules we give our
employees.

1. Please put things on the office playlist. We want to hear what you like!

2. Variety is fun. Put on one or two songs by a given artist, or a handful in 
   a genre, and then give someone or something else a turn. Weirdness is fine,
   but you may find that short weirdnesses are more readily appreciated than
   long ones.

3. Please don't skip a song once it starts playing. Somebody picked it and
   has been eagerly waiting for it to come on!

4. Anybody is always allowed to lower the volume for any reason. (Go to the volume
   tab on the left and adjust the volume on your floor instead of the main
   overall volume.) If the volume has been down for a while, feel free to turn
   it up a little again.

5. When in doubt, put on your headphones.

It's also worth mentioning we have some songs we play on special occassions; there
are buttons to play those songs under the "Other" tab. You probably shouldn't push
those. "play music here", "show os notifications", and "hide shame" are all fair
game; feel free to click those and see what they do.

If you have a picture on http://www.gravatar.com/, we'll display that as your user
image.

Log in with your email and password

{{email}} / {{passwd}}

at the url

http://andre.spotify.net


Regards,

Andre
