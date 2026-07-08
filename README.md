# TLE Server

A tool to aggregate satellite TLE data in various formats, cache it and serve it back to clients.

Supported formats:
- JSON
- CSV
- TLE (technically 3le)

## Endpoints

`/stats`

Various information like stored elements count,
groups and NORAD IDs of elements available inside of them
and data about currently used sources.

`/elements`

Request orbital elements. The following URL parameters are available:
- group: Get elements for all objects specified in an existing group.
Can be specified multiple times and mixed with `norad`
- norad: Get elements for an object by its NORAD ID.
Can be specified multiple times and mixed with `group`
- format: The format that the elements should be returned in.
Choices are csv, json and tle.

## Installation

```bash
# Start in whichever directory you want to install to

# Clone repository and enter
git clone https://github.com/DB8LE/tle-server.git
cd tle-server

# Create venv and enter it
python3 -m venv venv
source ./venv/bin/activate

# Install dependencies
# Note: optionally, systemctl journal support can be enabled by running
# `pip install .[journal]` instead. Journal support requires the dependency python3-systemd
pip install .


# Define data sources and groups
cp sources.example.toml sources.toml
nano sources.toml
cp groups.example.toml groups.toml
nano groups.toml

# Run
./venv/bin/python3 ./venv/bin/tle-server # (--help for config options)
```