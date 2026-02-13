"""CLI entry point for echonest-sync."""

import logging
import platform
import sys

import click

from .config import DEFAULT_CONFIG_PATH, load_config
from .player import create_player
from .sync import SyncAgent


@click.command()
@click.option("--server", "-s", help="EchoNest server URL")
@click.option("--token", "-t", help="API bearer token")
@click.option("--drift-threshold", "-d", type=int, help="Seconds before correcting drift (default 3)")
@click.option("--config", "-c", "config_path", help=f"Config file path (default {DEFAULT_CONFIG_PATH})")
@click.option("--verbose", "-v", is_flag=True, help="Debug logging")
def main(server, token, drift_threshold, config_path, verbose):
    """Sync your local Spotify with an EchoNest server."""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )
    log = logging.getLogger("echonest_sync")

    config = load_config(
        config_path=config_path,
        cli_overrides={
            "server": server,
            "token": token,
            "drift_threshold": drift_threshold,
        },
    )

    if not config["server"]:
        log.error("Server URL required (--server, ECHONEST_SERVER, or config file)")
        sys.exit(1)
    if not config["token"]:
        log.error("API token required (--token, ECHONEST_TOKEN, or config file)")
        sys.exit(1)

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
