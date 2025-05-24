# HAR-V
Acronym meaning tbd

A verification system for a school Discord server.

## Project Info
- Run `pip install -r requirements.txt` to install dependencies.
- Formatting follows default Ruff config.


## `config.json`
`token`: Discord bot token

`guild`: ID of corresponding Discord server

`form_url`: Full URL to the verification Google Form (including pre-fill)

`form_webhook`: ID of webhook used to transmit form responses

`user_contact_channel`: ID of Discord channel accessible to unverified users

`mod_contact_channel`: ID of Discord channel used to communicate with moderators (most likely same channel as webhook)

`mod_role`: ID of moderator role

`verified_role`: ID of verification role in `guild`
