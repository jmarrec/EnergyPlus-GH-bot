# EnergyPlus-GH-bot

This bot is a Github App that is meant to help manage the EnergyPlus repository.

It uses gidgethub (v6.0.0+), and aiohttp.


## What the bot does

- **`/stage`**
The Bot triggers the workflow that does clang-tidy.


## Configuration

Run the bot with `python3 -m epbot`. It listens on the port given by the `PORT` environment variable.

Set the following environment variables:

`GH_SECRET`: The secret key from your GitHub App

`GH_APP_CLIENT_ID`: The Client ID of your GitHub App (looks like `Iv23li...`), used as the JWT issuer

`GH_PRIVATE_KEY`: The private key of your GitHub App. It looks like:

```
-----BEGIN RSA PRIVATE KEY-----
...somereallylongtext...
-----END RSA PRIVATE KEY-----
```
