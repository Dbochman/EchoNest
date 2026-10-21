"""Entry point for PyInstaller and `python -m echonest_sync`."""
import sys

if __name__ == "__main__":
    if sys.argv[1:] == ["--tls-self-test"]:
        # Run before importing GUI/config/keyring code. This diagnostic makes
        # TLS-only connections to public canaries, never application requests.
        from echonest_sync.tls_health import main
        sys.exit(main())
    else:
        from echonest_sync.app import main
        main()
