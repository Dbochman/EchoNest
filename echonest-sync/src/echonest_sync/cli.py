"""CLI entry point for echonest-sync."""

import logging
import platform
import sys
from importlib.metadata import version as pkg_version

import click

from .config import DEFAULT_CONFIG_PATH, load_config, save_config, set_token


DEFAULT_SERVER = "https://echone.st"
DEFAULT_CODE = "futureofmusic"


def _get_version():
    try:
        return pkg_version("echonest-sync")
    except Exception:
        return "dev"


@click.group(invoke_without_command=True)
@click.version_option(version=_get_version(), prog_name="echonest-sync")
@click.option("--server", "-s", help="EchoNest server URL")
@click.option("--token", "-t", help="API bearer token")
@click.option("--drift-threshold", "-d", type=int, help="Seconds before correcting drift (default 3)")
@click.option("--config", "-c", "config_path", help=f"Config file path (default {DEFAULT_CONFIG_PATH})")
@click.option("--verbose", "-v", is_flag=True, help="Debug logging")
@click.pass_context
def main(ctx, server, token, drift_threshold, config_path, verbose):
    """Sync your local Spotify with an EchoNest server."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    ctx.obj["config_path"] = config_path
    ctx.obj["cli_overrides"] = {
        "server": server,
        "token": token,
        "drift_threshold": drift_threshold,
    }

    # If no subcommand, run sync (default behavior)
    if ctx.invoked_subcommand is not None:
        return

    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )
    log = logging.getLogger("echonest_sync")

    config = load_config(config_path=config_path, cli_overrides=ctx.obj["cli_overrides"])

    if not config["server"]:
        log.error("Server URL required (--server, ECHONEST_SERVER, or config file)")
        log.error("Run 'echonest-sync login' to set up your connection")
        sys.exit(1)
    if not config["token"]:
        log.error("API token required (--token, ECHONEST_TOKEN, or config file)")
        log.error("Run 'echonest-sync login' to set up your connection")
        sys.exit(1)

    from .player import create_player
    from .sync import SyncAgent

    player = create_player()
    system = platform.system()

    log.info("echonest-sync")
    log.info("  server:    %s", config["server"])
    log.info("  platform:  %s", system)
    log.info("  drift:     %ds", config["drift_threshold"])

    if not player.is_running():
        log.warning("Spotify does not appear to be running — start it first")

    agent = SyncAgent(
        server=config["server"],
        token=config["token"],
        player=player,
        drift_threshold=config["drift_threshold"],
    )
    try:
        agent.run()
    except KeyboardInterrupt:
        log.info("Stopped")


@main.command()
@click.option("--server", "-s", prompt="Server", default=DEFAULT_SERVER, show_default=True,
              help="EchoNest server URL")
@click.option("--code", "-c", prompt="Invite code", default=DEFAULT_CODE, show_default=True,
              help="Invite code for token exchange")
def login(server, code):
    """Authenticate with an EchoNest server and save credentials."""
    import requests

    server = server.rstrip("/")

    try:
        resp = requests.post(
            f"{server}/api/sync-token",
            json={"invite_code": code},
            timeout=10,
        )
    except requests.exceptions.ConnectionError:
        click.echo("Error: could not reach server", err=True)
        sys.exit(1)

    if resp.status_code == 200:
        data = resp.json()
        token = data.get("token", "")
        server_url = data.get("server", server)
        set_token(token)
        save_config({"server": server_url})
        click.echo(f"Logged in to {server_url}")
        click.echo("Run 'echonest-sync' to start syncing.")
        click.echo("")
        click.echo("Tip: link your account at the server to add songs under your name.")
        click.echo(f"     Visit {server_url}/sync/link in your browser.")
    elif resp.status_code == 403:
        click.echo("Error: invalid invite code", err=True)
        sys.exit(1)
    elif resp.status_code == 429:
        click.echo("Error: too many attempts — try again later", err=True)
        sys.exit(1)
    else:
        click.echo(f"Error: server returned {resp.status_code}", err=True)
        sys.exit(1)


@main.command()
def logout():
    """Remove saved credentials."""
    from .config import delete_token

    delete_token()
    click.echo("Token removed from keyring.")


@main.command()
@click.option("--config", "-c", "config_path", help="Config file path")
def status(config_path):
    """Show current configuration and connection status."""
    from .config import get_token as _get_token

    config = load_config(config_path=config_path)
    token = _get_token()

    click.echo(f"echonest-sync {_get_version()}")
    click.echo("")

    # Server
    server = config.get("server")
    if server:
        click.echo(f"  Server:  {server}")
    else:
        click.echo("  Server:  (not configured)")

    # Auth
    if token:
        click.echo("  Auth:    logged in (token in keyring)")
    else:
        click.echo("  Auth:    not logged in")

    # Linked account
    email = config.get("email")
    if email:
        click.echo(f"  Account: {email}")
    else:
        click.echo("  Account: not linked")

    click.echo("")

    if not server or not token:
        click.echo("Run 'echonest-sync login' to get started.")
    elif not email:
        click.echo(f"Tip: link your account at {server}/sync/link")
